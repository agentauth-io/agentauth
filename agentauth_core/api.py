"""
AgentAuth Secure API
Hardened REST API with anti-reverse-engineering measures
"""

import os
import time
import json
import hashlib
import hmac
import secrets
from typing import Dict, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .auth_engine import AuthEngine
from .policy_engine import PolicyRule, PolicyAction
from .rate_limiter import AdaptiveRateLimiter, RateLimitConfig
from .agent_registry import AgentRegistry, AgentPermission


# ============================================================================
# Security Configuration
# ============================================================================

class SecurityConfig:
    """Security configuration with obfuscated names"""
    _k1 = os.environ.get("AGENTAUTH_MASTER_KEY", secrets.token_hex(32))
    _k2 = os.environ.get("AGENTAUTH_SIGNING_KEY", secrets.token_hex(32))
    _debug = os.environ.get("AGENTAUTH_DEBUG", "false").lower() == "true"
    _rate_limit_enabled = True
    _signature_required = True
    _max_body_size = 1024 * 1024  # 1MB


# ============================================================================
# Request/Response Models (Obfuscated field names for production)
# ============================================================================

class AuthorizationRequest(BaseModel):
    """Transaction authorization request"""
    a: str = Field(..., alias="agent_id", description="Agent identifier")
    u: str = Field(..., alias="user_id", description="User identifier")  
    m: str = Field(..., alias="merchant", description="Merchant name")
    v: float = Field(..., alias="amount", description="Transaction amount")
    c: str = Field("USD", alias="currency", description="Currency code")
    t: Optional[str] = Field(None, alias="category", description="Category")
    x: Optional[Dict] = Field(None, alias="metadata", description="Extra data")
    
    class Config:
        populate_by_name = True


class AuthorizationResponse(BaseModel):
    """Authorization response"""
    ok: bool = Field(..., description="Whether authorized")
    tk: Optional[str] = Field(None, description="Transaction token")
    rs: float = Field(0.0, description="Risk score")
    rl: int = Field(1, description="Risk level")
    rn: str = Field("", description="Reason")
    mr: list = Field(default_factory=list, description="Matched rules")


class AgentRegistrationRequest(BaseModel):
    """Agent registration request"""
    name: str
    description: str = ""
    permissions: list = ["transaction:write"]
    daily_limit: float = 1000.0
    per_tx_limit: float = 200.0


class AgentRegistrationResponse(BaseModel):
    """Agent registration response"""
    agent_id: str
    api_key: str
    created: bool


# ============================================================================
# Core API Application
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="AgentAuth API",
        description="Secure Authorization API for AI Agents",
        version="2.0.0",
        docs_url="/docs" if SecurityConfig._debug else None,
        redoc_url="/redoc" if SecurityConfig._debug else None,
        openapi_url="/openapi.json" if SecurityConfig._debug else None
    )
    
    # Initialize core services
    auth_engine = AuthEngine()
    rate_limiter = AdaptiveRateLimiter()
    agent_registry = AgentRegistry()
    
    # Store in app state
    app.state.auth_engine = auth_engine
    app.state.rate_limiter = rate_limiter
    app.state.agent_registry = agent_registry
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if SecurityConfig._debug else [],
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )
    
    # ========================================================================
    # Security Middleware
    # ========================================================================
    
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        """Comprehensive security middleware"""
        start_time = time.time()
        
        # Rate limiting
        client_id = _get_client_identifier(request)
        allowed, limit_info = rate_limiter.check_rate_limit(client_id)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "retry_after": limit_info.get("retry_after", 60)
                },
                headers={"Retry-After": str(int(limit_info.get("retry_after", 60)))}
            )
        
        # Request size limit
        content_length = request.headers.get("content-length", 0)
        if int(content_length) > SecurityConfig._max_body_size:
            return JSONResponse(
                status_code=413,
                content={"error": "payload_too_large"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = secrets.token_hex(8)
        
        # Timing attack prevention - constant response time
        elapsed = time.time() - start_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        
        return response
    
    # ========================================================================
    # Authentication Dependencies
    # ========================================================================
    
    async def verify_api_key(
        request: Request,
        authorization: Optional[str] = Header(None),
        x_api_key: Optional[str] = Header(None)
    ):
        """Verify API key from headers"""
        api_key = None
        
        if authorization and authorization.startswith("Bearer "):
            api_key = authorization[7:]
        elif x_api_key:
            api_key = x_api_key
        
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        
        agent = agent_registry.authenticate_agent(api_key)
        if not agent:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return agent
    
    async def verify_signature(
        request: Request,
        x_signature: Optional[str] = Header(None),
        x_timestamp: Optional[str] = Header(None)
    ):
        """Verify request signature"""
        if not SecurityConfig._signature_required:
            return True
        
        if not x_signature or not x_timestamp:
            raise HTTPException(status_code=401, detail="Missing signature")
        
        try:
            timestamp = int(x_timestamp)
            now = int(time.time())
            
            # Check timestamp freshness (5 minute window)
            if abs(now - timestamp) > 300:
                raise HTTPException(status_code=401, detail="Timestamp expired")
            
            # Verify signature
            body = await request.body()
            expected = _compute_signature(
                request.method,
                str(request.url.path),
                body,
                timestamp
            )
            
            if not hmac.compare_digest(x_signature, expected):
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            return True
            
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid timestamp")
    
    # ========================================================================
    # API Endpoints
    # ========================================================================
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": "2.0.0"}
    
    @app.post("/api/v1/agents/register")
    async def register_agent(
        request: Request,
        body: AgentRegistrationRequest
    ):
        """Register a new agent"""
        # In production, this would require user authentication
        user_id = request.headers.get("X-User-ID", "anonymous")
        
        permissions = []
        for p in body.permissions:
            try:
                permissions.append(AgentPermission(p))
            except:
                pass
        
        agent_id, api_key = agent_registry.register_agent(
            user_id=user_id,
            name=body.name,
            description=body.description,
            permissions=permissions or [AgentPermission.TRANSACTION_WRITE],
            spending_limit_daily=body.daily_limit,
            spending_limit_per_tx=body.per_tx_limit
        )
        
        return AgentRegistrationResponse(
            agent_id=agent_id,
            api_key=api_key,
            created=True
        )
    
    @app.post("/api/v1/authorize")
    async def authorize_transaction(
        request: Request,
        body: AuthorizationRequest,
        agent=Depends(verify_api_key)
    ):
        """Authorize a transaction"""
        # Verify agent permissions
        if not agent_registry.has_permission(agent.agent_id, AgentPermission.TRANSACTION_WRITE):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check merchant restrictions
        if not agent_registry.check_merchant_allowed(agent.agent_id, body.m):
            return AuthorizationResponse(
                ok=False,
                rs=1.0,
                rl=4,
                rn="Merchant blocked for this agent"
            )
        
        # Register agent with auth engine if needed
        if agent.agent_id not in auth_engine._agent_contexts:
            auth_engine.register_agent(
                agent.agent_id,
                agent.user_id,
                [p.value for p in agent.permissions]
            )
        
        # Generate token for this request
        token, _ = auth_engine.token_manager.generate_token(
            agent.agent_id,
            agent.user_id,
            "transaction"
        )
        
        # Authorize transaction
        result = auth_engine.authorize_transaction(
            token=token,
            merchant=body.m,
            amount=body.v,
            currency=body.c,
            category=body.t,
            metadata=body.x
        )
        
        return AuthorizationResponse(
            ok=result.allowed,
            tk=result.token if result.allowed else None,
            rs=result.risk_score,
            rl=result.risk_level.value if hasattr(result.risk_level, 'value') else result.risk_level,
            rn=result.reason,
            mr=result.matched_rules
        )
    
    @app.get("/api/v1/agents/{agent_id}/stats")
    async def get_agent_stats(
        agent_id: str,
        agent=Depends(verify_api_key)
    ):
        """Get agent statistics"""
        # Verify ownership or admin
        if agent.agent_id != agent_id:
            if not agent_registry.has_permission(agent.agent_id, AgentPermission.ADMIN):
                raise HTTPException(status_code=403, detail="Access denied")
        
        stats = auth_engine.get_agent_stats(agent_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return stats
    
    @app.post("/api/v1/policies")
    async def create_policy(
        request: Request,
        agent=Depends(verify_api_key)
    ):
        """Create a new policy rule"""
        if not agent_registry.has_permission(agent.agent_id, AgentPermission.POLICY_WRITE):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        body = await request.json()
        
        rule = PolicyRule(
            id=body.get("id", secrets.token_hex(8)),
            name=body.get("name", "Custom Rule"),
            priority=body.get("priority", 100),
            conditions=body.get("conditions", {}),
            action=PolicyAction(body.get("action", "deny")),
            metadata=body.get("metadata", {})
        )
        
        auth_engine.policy_engine.add_rule(rule)
        
        return {"created": True, "rule_id": rule.id}
    
    @app.get("/api/v1/audit")
    async def get_audit_log(
        request: Request,
        limit: int = 100,
        agent=Depends(verify_api_key)
    ):
        """Get audit log entries"""
        if not agent_registry.has_permission(agent.agent_id, AgentPermission.AUDIT_READ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        entries = auth_engine.get_audit_log(limit=min(limit, 1000))
        return {"entries": entries, "count": len(entries)}
    
    return app


# ============================================================================
# Helper Functions
# ============================================================================

def _get_client_identifier(request: Request) -> str:
    """Get unique client identifier for rate limiting"""
    # Prefer API key, fall back to IP
    api_key = request.headers.get("Authorization", "")
    if api_key.startswith("Bearer "):
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    return request.client.host if request.client else "unknown"


def _compute_signature(
    method: str,
    path: str,
    body: bytes,
    timestamp: int
) -> str:
    """Compute request signature"""
    canonical = f"{method.upper()}\n{path}\n{timestamp}\n"
    body_hash = hashlib.sha256(body).hexdigest()
    canonical += body_hash
    
    signature = hmac.new(
        SecurityConfig._k2.encode(),
        canonical.encode(),
        hashlib.sha512
    ).hexdigest()
    
    return signature


# ============================================================================
# Application Entry Point
# ============================================================================

app = create_app()


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    uvicorn.run(
        "agentauth_core.api:app",
        host=host,
        port=port,
        reload=SecurityConfig._debug,
        log_level="info" if SecurityConfig._debug else "warning"
    )


if __name__ == "__main__":
    run_server()
