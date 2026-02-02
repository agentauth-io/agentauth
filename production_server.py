"""
AgentAuth Production Server
===========================
Enterprise-grade REST API with PostgreSQL, Redis, and full observability.

Run with: uvicorn production_server:app --host 0.0.0.0 --port 8000 --workers 4
"""

import os
import time
import json
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
import asyncpg

# Import core
from core import AgentAuthCore, PolicyBuilder, AuthorizationStatus
from core.policy import PolicyEffect

# =============================================================================
# Configuration
# =============================================================================

class Config:
    """Production configuration from environment."""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/agentauth")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security
    MASTER_SECRET = os.getenv("AGENTAUTH_MASTER_SECRET")  # Required in production
    API_KEY_HEADER = "X-API-Key"
    
    # Rate limiting - Flexible multi-tier configuration
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_SECOND = int(os.getenv("RATE_LIMIT_PER_SECOND", "50"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "500"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "5000"))
    RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "100"))  # Burst allowance
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "1"))  # Sliding window size
    
    # Rate limit tiers (can be overridden per API key)
    RATE_LIMIT_TIERS = {
        "free": {"per_second": 10, "per_minute": 100, "per_hour": 1000, "burst": 20},
        "startup": {"per_second": 25, "per_minute": 300, "per_hour": 3000, "burst": 50},
        "growth": {"per_second": 50, "per_minute": 500, "per_hour": 5000, "burst": 100},
        "enterprise": {"per_second": 200, "per_minute": 2000, "per_hour": 50000, "burst": 500},
        "unlimited": {"per_second": 0, "per_minute": 0, "per_hour": 0, "burst": 0},  # 0 = unlimited
    }
    
    # Billing Plans - Monthly Authorization Quotas
    BILLING_PLANS = {
        "free": {
            "name": "Free",
            "price_monthly": 0,
            "authorizations_monthly": 1000,
            "stripe_price_id": None,
            "features": ["1,000 authorizations/month", "Basic API access", "Community support"],
        },
        "startup": {
            "name": "Startup",
            "price_monthly": 99,
            "authorizations_monthly": 50000,
            "stripe_price_id": os.getenv("STRIPE_PRICE_STARTUP", "price_startup"),
            "features": ["50,000 authorizations/month", "Webhooks", "Email support", "Custom policies"],
        },
        "growth": {
            "name": "Growth",
            "price_monthly": 499,
            "authorizations_monthly": 500000,
            "stripe_price_id": os.getenv("STRIPE_PRICE_GROWTH", "price_growth"),
            "features": ["500,000 authorizations/month", "Priority support", "Advanced analytics", "SSO"],
        },
        "enterprise": {
            "name": "Enterprise",
            "price_monthly": -1,  # Custom pricing
            "authorizations_monthly": -1,  # Unlimited
            "stripe_price_id": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise"),
            "features": ["Unlimited authorizations", "Dedicated support", "SLA guarantee", "On-premise option"],
        },
    }
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # Metrics
    METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# =============================================================================
# Database Models
# =============================================================================

SCHEMA_SQL = """
-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    owner VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    permissions JSONB DEFAULT '["authorize"]',
    rate_limit_tier VARCHAR(32) DEFAULT 'free',
    rate_limit_override JSONB,
    billing_plan VARCHAR(32) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    revoked_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Subscriptions table (linked to API keys)
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
    plan VARCHAR(32) NOT NULL DEFAULT 'free',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    authorizations_used INTEGER DEFAULT 0,
    authorizations_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    canceled_at TIMESTAMP
);

-- Monthly usage tracking
CREATE TABLE IF NOT EXISTS monthly_usage (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
    billing_period VARCHAR(7) NOT NULL,  -- YYYY-MM format
    authorizations_count INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    denied_count INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(api_key_id, billing_period)
);

-- Authorization logs (immutable audit)
CREATE TABLE IF NOT EXISTS authorization_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) UNIQUE NOT NULL,
    api_key_id INTEGER REFERENCES api_keys(id),
    agent_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(64) NOT NULL,
    amount DECIMAL(15, 2),
    merchant VARCHAR(255),
    category VARCHAR(64),
    status VARCHAR(32) NOT NULL,
    reason TEXT,
    risk_score DECIMAL(5, 4),
    policy_id VARCHAR(64),
    token_id VARCHAR(64),
    evaluation_time_ms DECIMAL(10, 3),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- User spending limits
CREATE TABLE IF NOT EXISTS user_limits (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    daily_limit DECIMAL(15, 2) DEFAULT 500.00,
    monthly_limit DECIMAL(15, 2) DEFAULT 5000.00,
    per_transaction_limit DECIMAL(15, 2) DEFAULT 200.00,
    blocked_categories TEXT[] DEFAULT ARRAY['gambling', 'crypto', 'adult'],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Daily spending aggregates
CREATE TABLE IF NOT EXISTS daily_spending (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_spent DECIMAL(15, 2) DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Policies
CREATE TABLE IF NOT EXISTS policies (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    effect VARCHAR(32) NOT NULL,
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    rules JSONB NOT NULL,
    constraints JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_auth_logs_agent ON authorization_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_auth_logs_user ON authorization_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_logs_created ON authorization_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_daily_spending_user_date ON daily_spending(user_id, date);
"""


# =============================================================================
# Request/Response Models
# =============================================================================

class AuthorizeRequest(BaseModel):
    """Authorization request from client."""
    agent_id: str = Field(..., description="Unique agent identifier")
    user_id: str = Field(..., description="User on whose behalf agent acts")
    action: str = Field(default="purchase", description="Action type")
    amount: Optional[float] = Field(None, description="Transaction amount")
    merchant: Optional[str] = Field(None, description="Merchant name")
    category: Optional[str] = Field(None, description="Transaction category")
    resource: Optional[str] = Field(None, description="Resource identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AuthorizeResponse(BaseModel):
    """Authorization response to client."""
    authorized: bool
    status: str
    request_id: str
    token: Optional[str] = None
    token_id: Optional[str] = None
    reason: str
    risk_score: float
    policy_id: Optional[str] = None
    constraints: Dict[str, Any] = {}
    expires_at: Optional[float] = None
    evaluation_time_ms: float


class TokenVerifyRequest(BaseModel):
    """Token verification request."""
    token: str


class UserLimitsRequest(BaseModel):
    """Set user spending limits."""
    user_id: str
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    per_transaction_limit: Optional[float] = None
    blocked_categories: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    database: str
    redis: str
    uptime_seconds: float


# =============================================================================
# Application State
# =============================================================================

class AppState:
    """Application state container."""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[redis.Redis] = None
        self.core: Optional[AgentAuthCore] = None
        self.start_time: float = time.time()
        self.request_count: int = 0
        self.error_count: int = 0


state = AppState()


# =============================================================================
# Default Policies
# =============================================================================

DEFAULT_POLICIES = [
    {
        "id": "default-allow-reads",
        "name": "Allow Read Operations",
        "effect": "allow",
        "priority": 100,
        "enabled": True,
        "rules": {
            "actions": ["read", "view", "list", "get", "query", "search"],
            "resources": ["*"]
        },
        "constraints": {}
    },
    {
        "id": "default-allow-purchases",
        "name": "Allow Standard Purchases",
        "effect": "allow",
        "priority": 90,
        "enabled": True,
        "rules": {
            "actions": ["purchase", "buy", "order"],
            "max_amount": 500.0,
            "resources": ["*"]
        },
        "constraints": {
            "max_transaction": 500.0,
            "require_user_id": True
        }
    },
    {
        "id": "default-allow-writes",
        "name": "Allow Write Operations",
        "effect": "allow",
        "priority": 80,
        "enabled": True,
        "rules": {
            "actions": ["write", "create", "update", "modify", "edit"],
            "resources": ["*"]
        },
        "constraints": {}
    },
    {
        "id": "block-high-risk",
        "name": "Block High Risk Transactions",
        "effect": "deny",
        "priority": 200,  # High priority - evaluated first
        "enabled": True,
        "rules": {
            "actions": ["transfer", "withdraw", "delete"],
            "min_amount": 10000.0
        },
        "constraints": {
            "reason": "High-value sensitive operations require manual approval"
        }
    },
    {
        "id": "block-gambling",
        "name": "Block Gambling Category",
        "effect": "deny",
        "priority": 190,
        "enabled": True,
        "rules": {
            "categories": ["gambling", "casino", "betting"]
        },
        "constraints": {
            "reason": "Gambling transactions are blocked by policy"
        }
    }
]


async def load_default_policies():
    """Load default policies into database and core engine."""
    
    if not state.db_pool:
        print("[!] No database - skipping policy load")
        return
    
    async with state.db_pool.acquire() as conn:
        # Check if policies exist
        count = await conn.fetchval("SELECT COUNT(*) FROM policies")
        
        if count > 0:
            # Load existing policies into core
            rows = await conn.fetch("SELECT * FROM policies WHERE enabled = true")
            for row in rows:
                try:
                    policy = PolicyBuilder(row["id"], row["name"]).build()
                    # Convert string effect to enum
                    effect_str = row["effect"].upper()
                    policy.effect = PolicyEffect[effect_str] if effect_str in PolicyEffect.__members__ else PolicyEffect.ALLOW
                    policy.priority = row["priority"]
                    state.core.add_policy(policy)
                except Exception as e:
                    print(f"[!] Failed to load policy {row['id']}: {e}")
            print(f"[+] Loaded {len(rows)} existing policies")
            return
        
        # Insert default policies
        print(f"[+] Loading {len(DEFAULT_POLICIES)} default policies...")
        
        for policy_data in DEFAULT_POLICIES:
            await conn.execute(
                """
                INSERT INTO policies (id, name, effect, priority, enabled, rules, constraints)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    effect = EXCLUDED.effect,
                    priority = EXCLUDED.priority,
                    rules = EXCLUDED.rules,
                    constraints = EXCLUDED.constraints,
                    updated_at = NOW()
                """,
                policy_data["id"],
                policy_data["name"],
                policy_data["effect"],
                policy_data["priority"],
                policy_data["enabled"],
                json.dumps(policy_data["rules"]),
                json.dumps(policy_data["constraints"])
            )
            
            # Add to core engine
            try:
                policy = PolicyBuilder(policy_data["id"], policy_data["name"]).build()
                effect_str = policy_data["effect"].upper()
                policy.effect = PolicyEffect[effect_str] if effect_str in PolicyEffect.__members__ else PolicyEffect.ALLOW
                policy.priority = policy_data["priority"]
                state.core.add_policy(policy)
            except Exception as e:
                print(f"[!] Failed to add policy to core: {e}")
        
        print(f"[+] Default policies loaded successfully")


# =============================================================================
# Lifespan Management
# =============================================================================

# =============================================================================
# Helper Functions
# =============================================================================

async def log_authorization_db(
    conn,
    api_key_id: int,
    request_id: str,
    agent_id: str,
    user_id: str,
    action: str,
    amount: Optional[float],
    merchant: Optional[str],
    category: Optional[str],
    status: str,
    reason: str,
    policy_id: Optional[str],
    eval_time: float
):
    """Log authorization to database."""
    try:
        if state.db_pool:
            async with state.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO authorization_logs 
                    (request_id, api_key_id, agent_id, user_id, action, amount, merchant, category, status, reason, policy_id, evaluation_time_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    request_id, api_key_id, agent_id, user_id, action, 
                    amount, merchant, category, status, reason, policy_id, eval_time
                )
    except Exception as e:
        print(f"[!] Failed to log authorization: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    
    # Startup
    print(f"[+] Starting AgentAuth Production Server...")
    print(f"    Environment: {Config.ENVIRONMENT}")
    
    # Initialize database
    try:
        state.db_pool = await asyncpg.create_pool(
            Config.DATABASE_URL,
            min_size=5,
            max_size=20
        )
        async with state.db_pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
        print(f"[+] Database connected: PostgreSQL")
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        # Continue without DB for development
    
    # Initialize Redis
    try:
        state.redis = redis.from_url(Config.REDIS_URL)
        await state.redis.ping()
        print(f"[+] Redis connected")
    except Exception as e:
        print(f"[!] Redis connection failed: {e}")
        state.redis = None
    
    # Initialize core
    if Config.MASTER_SECRET:
        state.core = AgentAuthCore.from_master_secret(Config.MASTER_SECRET)
        print(f"[+] Core initialized from master secret")
    else:
        state.core = AgentAuthCore()
        print(f"[!] Core initialized with NEW master secret (not for production!)")
        print(f"    Master: {state.core.export_master_secret()[:16]}...")
    
    # Load default policies if none exist
    await load_default_policies()
    
    print(f"[+] Server ready!")
    
    yield
    
    # Shutdown
    print(f"[+] Shutting down...")
    if state.db_pool:
        await state.db_pool.close()
    if state.redis:
        await state.redis.close()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AgentAuth API",
    description="Enterprise Authorization Infrastructure for AI Agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Restricted to allowed origins
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "https://agentauth.in,https://www.agentauth.in").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Idempotency-Key"],
)


# Rate limit headers middleware
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit headers to all responses."""
    response = await call_next(request)
    
    # Add rate limit info if available
    if hasattr(request.state, "rate_limit_info"):
        info = request.state.rate_limit_info
        limits = info.get("limits", {})
        current = info.get("current", {})
        
        # Standard rate limit headers
        response.headers["X-RateLimit-Tier"] = info.get("tier", "pro")
        response.headers["X-RateLimit-Limit-Second"] = str(limits.get("per_second", 0))
        response.headers["X-RateLimit-Limit-Minute"] = str(limits.get("per_minute", 0))
        response.headers["X-RateLimit-Limit-Hour"] = str(limits.get("per_hour", 0))
        response.headers["X-RateLimit-Remaining-Second"] = str(max(0, limits.get("per_second", 0) - current.get("second", 0)))
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, limits.get("per_minute", 0) - current.get("minute", 0)))
        response.headers["X-RateLimit-Burst-Remaining"] = str(current.get("burst_remaining", 0))
    
    return response


# =============================================================================
# Dependencies
# =============================================================================

async def verify_api_key(x_api_key: str = Header(None)) -> Dict[str, Any]:
    """Verify API key and return key info."""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Hash the key
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, owner, permissions, rate_limit_tier, rate_limit_override, billing_plan
                FROM api_keys
                WHERE key_hash = $1 AND revoked_at IS NULL
                """,
                key_hash
            )
            
            if not row:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Update last used
            await conn.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
                row["id"]
            )
            
            result = dict(row)
            # Ensure billing_plan has a default
            if not result.get("billing_plan"):
                result["billing_plan"] = "free"
            return result
    
    # Development mode - accept any key
    if Config.DEBUG:
        return {"id": 0, "owner": "dev", "permissions": ["*"], "billing_plan": "growth"}
    
    raise HTTPException(status_code=401, detail="API key validation unavailable")


async def check_rate_limit(
    request: Request,
    api_key_info: Dict = Depends(verify_api_key)
) -> bool:
    """
    Advanced multi-window rate limiting with:
    - Per-second, per-minute, per-hour limits
    - Burst allowance with token bucket
    - Configurable tiers per API key
    - Graceful degradation if Redis is down
    - Rate limit headers in response
    """
    
    # Check if rate limiting is enabled
    if not Config.RATE_LIMIT_ENABLED:
        return True
    
    if not state.redis:
        return True  # Fail open if Redis unavailable
    
    key_id = api_key_info.get("id", "unknown")
    tier_name = api_key_info.get("rate_limit_tier", "free")
    custom_limits = api_key_info.get("rate_limit_override")
    
    # Get rate limits for this key
    if custom_limits and isinstance(custom_limits, dict):
        limits = custom_limits
    elif tier_name in Config.RATE_LIMIT_TIERS:
        limits = Config.RATE_LIMIT_TIERS[tier_name]
    else:
        limits = Config.RATE_LIMIT_TIERS["free"]
    
    # Unlimited tier - bypass all checks
    if limits.get("per_second", 0) == 0 and limits.get("per_minute", 0) == 0:
        return True
    
    now = int(time.time())
    now_ms = int(time.time() * 1000)
    
    try:
        pipe = state.redis.pipeline()
        
        # === Token Bucket for Burst ===
        burst_key = f"ratelimit:burst:{key_id}"
        burst_limit = limits.get("burst", 100)
        
        # === Sliding Window Counters ===
        # Per-second window
        second_key = f"ratelimit:sec:{key_id}:{now}"
        # Per-minute window (current minute)
        minute_key = f"ratelimit:min:{key_id}:{now // 60}"
        # Per-hour window (current hour)
        hour_key = f"ratelimit:hour:{key_id}:{now // 3600}"
        
        # Increment all counters atomically
        pipe.incr(second_key)
        pipe.expire(second_key, 5)  # 5 second TTL for cleanup
        
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # 2 minute TTL
        
        pipe.incr(hour_key)
        pipe.expire(hour_key, 7200)  # 2 hour TTL
        
        # Token bucket for burst (refills over time)
        pipe.get(burst_key)
        
        results = await pipe.execute()
        
        second_count = results[0]
        minute_count = results[2]
        hour_count = results[4]
        burst_tokens = int(results[6] or burst_limit)
        
        # Check limits and determine which one is exceeded
        exceeded = None
        limit_info = {}
        
        per_second = limits.get("per_second", 50)
        per_minute = limits.get("per_minute", 500)
        per_hour = limits.get("per_hour", 5000)
        
        if per_second > 0 and second_count > per_second:
            # Check if we have burst tokens
            if burst_tokens > 0:
                # Use a burst token
                await state.redis.decr(burst_key)
                await state.redis.expire(burst_key, 60)  # Tokens refill after 60s
            else:
                exceeded = "second"
                limit_info = {"limit": per_second, "current": second_count, "reset": 1}
        
        if not exceeded and per_minute > 0 and minute_count > per_minute:
            exceeded = "minute"
            limit_info = {"limit": per_minute, "current": minute_count, "reset": 60 - (now % 60)}
        
        if not exceeded and per_hour > 0 and hour_count > per_hour:
            exceeded = "hour"
            limit_info = {"limit": per_hour, "current": hour_count, "reset": 3600 - (now % 3600)}
        
        # Store rate limit info in request for headers
        request.state.rate_limit_info = {
            "tier": tier_name,
            "limits": {
                "per_second": per_second,
                "per_minute": per_minute,
                "per_hour": per_hour,
                "burst": burst_limit
            },
            "current": {
                "second": second_count,
                "minute": minute_count,
                "hour": hour_count,
                "burst_remaining": max(0, burst_tokens - 1)
            },
            "exceeded": exceeded
        }
        
        if exceeded:
            # Refill some burst tokens gradually
            await state.redis.incrby(burst_key, 1)
            await state.redis.expire(burst_key, 60)
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {limit_info['limit']}/{exceeded}",
                    "limit": limit_info["limit"],
                    "current": limit_info["current"],
                    "window": exceeded,
                    "retry_after": limit_info["reset"],
                    "tier": tier_name,
                    "upgrade_info": "Contact support for higher limits or use 'enterprise' tier"
                },
                headers={
                    "Retry-After": str(limit_info["reset"]),
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(now + limit_info["reset"]),
                    "X-RateLimit-Window": exceeded
                }
            )
        
        return True
        
    except redis.RedisError as e:
        # Fail open if Redis is down - log but don't block
        print(f"Rate limit check failed (Redis error): {e}")
        return True


# =============================================================================
# Billing & Quota Management
# =============================================================================

async def get_billing_period() -> str:
    """Get current billing period in YYYY-MM format."""
    return datetime.now().strftime("%Y-%m")


async def get_subscription_for_key(api_key_id: int) -> Optional[Dict[str, Any]]:
    """Get subscription info for an API key."""
    if not state.db_pool:
        # Development mode - return free plan
        return {
            "plan": "free",
            "status": "active",
            "authorizations_limit": Config.BILLING_PLANS["free"]["authorizations_monthly"],
            "authorizations_used": 0,
        }
    
    async with state.db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.*, a.billing_plan, a.owner
            FROM api_keys a
            LEFT JOIN subscriptions s ON s.api_key_id = a.id
            WHERE a.id = $1
            """,
            api_key_id
        )
        
        if not row:
            return None
        
        plan = row.get("plan") or row.get("billing_plan") or "free"
        plan_config = Config.BILLING_PLANS.get(plan, Config.BILLING_PLANS["free"])
        
        return {
            "plan": plan,
            "status": row.get("status", "active"),
            "authorizations_limit": plan_config["authorizations_monthly"],
            "authorizations_used": row.get("authorizations_used", 0),
            "stripe_customer_id": row.get("stripe_customer_id"),
            "current_period_start": row.get("current_period_start"),
            "current_period_end": row.get("current_period_end"),
        }


async def get_monthly_usage(api_key_id: int, billing_period: str = None) -> Dict[str, Any]:
    """Get monthly usage for an API key."""
    if billing_period is None:
        billing_period = await get_billing_period()
    
    if not state.db_pool:
        # Development mode - use Redis
        if state.redis:
            key = f"usage:{api_key_id}:{billing_period}"
            count = await state.redis.get(key)
            return {
                "billing_period": billing_period,
                "authorizations_count": int(count) if count else 0,
                "successful_count": 0,
                "denied_count": 0,
            }
        return {"billing_period": billing_period, "authorizations_count": 0}
    
    async with state.db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM monthly_usage
            WHERE api_key_id = $1 AND billing_period = $2
            """,
            api_key_id, billing_period
        )
        
        if row:
            return dict(row)
        
        return {
            "billing_period": billing_period,
            "authorizations_count": 0,
            "successful_count": 0,
            "denied_count": 0,
        }


async def increment_usage(api_key_id: int, success: bool = True, amount: float = 0) -> bool:
    """Increment monthly usage counter. Returns True if within quota."""
    billing_period = await get_billing_period()
    
    if not state.db_pool:
        # Development mode - use Redis for tracking
        if state.redis:
            key = f"usage:{api_key_id}:{billing_period}"
            await state.redis.incr(key)
            await state.redis.expire(key, 86400 * 35)  # 35 days TTL
        return True
    
    async with state.db_pool.acquire() as conn:
        # Upsert monthly usage
        await conn.execute(
            """
            INSERT INTO monthly_usage (api_key_id, billing_period, authorizations_count, 
                                       successful_count, denied_count, total_amount)
            VALUES ($1, $2, 1, $3, $4, $5)
            ON CONFLICT (api_key_id, billing_period) DO UPDATE SET
                authorizations_count = monthly_usage.authorizations_count + 1,
                successful_count = monthly_usage.successful_count + $3,
                denied_count = monthly_usage.denied_count + $4,
                total_amount = monthly_usage.total_amount + $5,
                updated_at = NOW()
            """,
            api_key_id, billing_period,
            1 if success else 0,
            0 if success else 1,
            amount if success else 0
        )
        
        # Also update subscription counter if exists
        await conn.execute(
            """
            UPDATE subscriptions
            SET authorizations_used = authorizations_used + 1,
                updated_at = NOW()
            WHERE api_key_id = $1
            """,
            api_key_id
        )
    
    return True


async def check_billing_quota(
    request: Request,
    api_key_info: Dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Check if API key has remaining authorization quota for the month.
    Returns quota info with allowed status.
    """
    api_key_id = api_key_info.get("id", 0)
    billing_plan = api_key_info.get("billing_plan", "free")
    
    # Get plan limits
    plan_config = Config.BILLING_PLANS.get(billing_plan, Config.BILLING_PLANS["free"])
    monthly_limit = plan_config["authorizations_monthly"]
    
    # Unlimited plan
    if monthly_limit == -1:
        return {
            "allowed": True,
            "plan": billing_plan,
            "limit": -1,
            "used": 0,
            "remaining": -1,
            "usage_percentage": 0,
        }
    
    # Get current usage
    billing_period = await get_billing_period()
    usage = await get_monthly_usage(api_key_id, billing_period)
    used = usage.get("authorizations_count", 0)
    remaining = max(0, monthly_limit - used)
    
    # Store quota info in request state
    quota_info = {
        "allowed": remaining > 0,
        "plan": billing_plan,
        "limit": monthly_limit,
        "used": used,
        "remaining": remaining,
        "usage_percentage": (used / monthly_limit * 100) if monthly_limit > 0 else 0,
        "billing_period": billing_period,
    }
    request.state.quota_info = quota_info
    
    if not quota_info["allowed"]:
        # Quota exceeded - return upgrade info
        upgrade_options = []
        for plan_name, plan_data in Config.BILLING_PLANS.items():
            if plan_data["authorizations_monthly"] > monthly_limit:
                upgrade_options.append({
                    "plan": plan_name,
                    "name": plan_data["name"],
                    "authorizations": plan_data["authorizations_monthly"],
                    "price": plan_data["price_monthly"],
                })
        
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "quota_exceeded",
                "message": f"Monthly authorization quota exceeded ({used}/{monthly_limit})",
                "plan": billing_plan,
                "used": used,
                "limit": monthly_limit,
                "billing_period": billing_period,
                "upgrade_url": "/v1/billing/checkout",
                "upgrade_options": upgrade_options[:3],  # Top 3 options
            },
            headers={
                "X-Quota-Limit": str(monthly_limit),
                "X-Quota-Used": str(used),
                "X-Quota-Remaining": "0",
            }
        )
    
    return quota_info


# =============================================================================
# Billing Endpoints
# =============================================================================

class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    plan: str = Field(..., description="Target plan: startup, growth, or enterprise")
    success_url: str = Field(default="https://agentauth.in/billing?success=true")
    cancel_url: str = Field(default="https://agentauth.in/billing?canceled=true")


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


@app.get("/v1/billing/plans")
async def get_billing_plans():
    """Get available billing plans and their limits."""
    plans = {}
    for plan_name, plan_data in Config.BILLING_PLANS.items():
        plans[plan_name] = {
            "name": plan_data["name"],
            "price_monthly": plan_data["price_monthly"],
            "authorizations_monthly": plan_data["authorizations_monthly"],
            "features": plan_data["features"],
        }
    return {"plans": plans}


@app.get("/v1/billing/usage")
async def get_usage(
    api_key_info: Dict = Depends(verify_api_key)
):
    """Get current usage and quota for the API key."""
    api_key_id = api_key_info.get("id", 0)
    billing_plan = api_key_info.get("billing_plan", "free")
    
    plan_config = Config.BILLING_PLANS.get(billing_plan, Config.BILLING_PLANS["free"])
    billing_period = await get_billing_period()
    usage = await get_monthly_usage(api_key_id, billing_period)
    
    monthly_limit = plan_config["authorizations_monthly"]
    used = usage.get("authorizations_count", 0)
    
    return {
        "plan": billing_plan,
        "plan_name": plan_config["name"],
        "billing_period": billing_period,
        "authorizations": {
            "used": used,
            "limit": monthly_limit,
            "remaining": max(0, monthly_limit - used) if monthly_limit > 0 else -1,
            "percentage": round((used / monthly_limit * 100), 2) if monthly_limit > 0 else 0,
        },
        "rate_limits": Config.RATE_LIMIT_TIERS.get(billing_plan, Config.RATE_LIMIT_TIERS["free"]),
        "successful_authorizations": usage.get("successful_count", 0),
        "denied_authorizations": usage.get("denied_count", 0),
        "total_transaction_amount": float(usage.get("total_amount", 0)),
    }


@app.post("/v1/billing/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    api_key_info: Dict = Depends(verify_api_key)
):
    """
    Create a Stripe Checkout session for subscription upgrade.
    
    Returns a URL to redirect the user to Stripe's hosted checkout.
    """
    if not Config.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe is not configured. Contact support@agentauth.in for enterprise plans."
        )
    
    target_plan = request.plan.lower()
    if target_plan not in Config.BILLING_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {target_plan}")
    
    plan_config = Config.BILLING_PLANS[target_plan]
    if not plan_config.get("stripe_price_id"):
        raise HTTPException(
            status_code=400,
            detail=f"Plan '{target_plan}' requires custom pricing. Contact enterprise@agentauth.in"
        )
    
    try:
        import stripe
        stripe.api_key = Config.STRIPE_SECRET_KEY
        
        api_key_id = api_key_info.get("id", 0)
        owner = api_key_info.get("owner", "unknown")
        
        # Get or create Stripe customer
        customer_id = None
        if state.db_pool:
            async with state.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT stripe_customer_id FROM subscriptions WHERE api_key_id = $1",
                    api_key_id
                )
                if row and row.get("stripe_customer_id"):
                    customer_id = row["stripe_customer_id"]
        
        # Create checkout session
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [{
                "price": plan_config["stripe_price_id"],
                "quantity": 1,
            }],
            "mode": "subscription",
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "metadata": {
                "api_key_id": str(api_key_id),
                "owner": owner,
                "plan": target_plan,
            },
        }
        
        if customer_id:
            session_params["customer"] = customer_id
        else:
            session_params["customer_email"] = owner if "@" in owner else None
        
        session = stripe.checkout.Session.create(**session_params)
        
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe library not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")


@app.post("/v1/billing/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for subscription updates.
    """
    if not Config.STRIPE_SECRET_KEY or not Config.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhooks not configured")
    
    try:
        import stripe
        stripe.api_key = Config.STRIPE_SECRET_KEY
        
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
        
        # Handle subscription events
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            api_key_id = int(session["metadata"].get("api_key_id", 0))
            plan = session["metadata"].get("plan", "startup")
            customer_id = session.get("customer")
            subscription_id = session.get("subscription")
            
            if state.db_pool and api_key_id > 0:
                async with state.db_pool.acquire() as conn:
                    # Update API key billing plan
                    await conn.execute(
                        """
                        UPDATE api_keys 
                        SET billing_plan = $1, rate_limit_tier = $1, updated_at = NOW()
                        WHERE id = $2
                        """,
                        plan, api_key_id
                    )
                    
                    plan_config = Config.BILLING_PLANS.get(plan, Config.BILLING_PLANS["free"])
                    
                    # Create or update subscription
                    await conn.execute(
                        """
                        INSERT INTO subscriptions (
                            api_key_id, plan, status, stripe_customer_id, 
                            stripe_subscription_id, authorizations_limit,
                            current_period_start
                        )
                        VALUES ($1, $2, 'active', $3, $4, $5, NOW())
                        ON CONFLICT (stripe_subscription_id) DO UPDATE SET
                            plan = EXCLUDED.plan,
                            status = 'active',
                            authorizations_limit = EXCLUDED.authorizations_limit,
                            updated_at = NOW()
                        """,
                        api_key_id, plan, customer_id, subscription_id,
                        plan_config["authorizations_monthly"]
                    )
            
            print(f"[Billing] Subscription activated: API key {api_key_id} -> {plan}")
        
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            subscription_id = subscription["id"]
            status = subscription["status"]
            
            if state.db_pool:
                async with state.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE subscriptions
                        SET status = $1, updated_at = NOW()
                        WHERE stripe_subscription_id = $2
                        """,
                        status, subscription_id
                    )
        
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            subscription_id = subscription["id"]
            
            if state.db_pool:
                async with state.db_pool.acquire() as conn:
                    # Downgrade to free
                    result = await conn.fetchrow(
                        "SELECT api_key_id FROM subscriptions WHERE stripe_subscription_id = $1",
                        subscription_id
                    )
                    if result:
                        api_key_id = result["api_key_id"]
                        await conn.execute(
                            "UPDATE api_keys SET billing_plan = 'free', rate_limit_tier = 'free' WHERE id = $1",
                            api_key_id
                        )
                        await conn.execute(
                            """
                            UPDATE subscriptions
                            SET status = 'canceled', canceled_at = NOW(),
                                plan = 'free', authorizations_limit = 1000
                            WHERE stripe_subscription_id = $1
                            """,
                            subscription_id
                        )
            
            print(f"[Billing] Subscription canceled: {subscription_id}")
        
        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")
            
            # Reset monthly usage on successful payment
            if state.db_pool and subscription_id:
                async with state.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE subscriptions
                        SET authorizations_used = 0,
                            current_period_start = NOW(),
                            updated_at = NOW()
                        WHERE stripe_subscription_id = $1
                        """,
                        subscription_id
                    )
        
        return {"status": "ok"}
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe library not installed")
    except Exception as e:
        print(f"[Billing] Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/billing/portal")
async def create_billing_portal(
    return_url: str = "https://agentauth.in/billing",
    api_key_info: Dict = Depends(verify_api_key)
):
    """
    Create a Stripe Billing Portal session for managing subscriptions.
    """
    if not Config.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    api_key_id = api_key_info.get("id", 0)
    
    try:
        import stripe
        stripe.api_key = Config.STRIPE_SECRET_KEY
        
        # Get customer ID
        customer_id = None
        if state.db_pool:
            async with state.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT stripe_customer_id FROM subscriptions WHERE api_key_id = $1",
                    api_key_id
                )
                if row:
                    customer_id = row.get("stripe_customer_id")
        
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="No subscription found. Create one first at /v1/billing/checkout"
            )
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        
        return {"portal_url": session.url}
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe library not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancers."""
    
    db_status = "connected" if state.db_pool else "disconnected"
    redis_status = "connected" if state.redis else "disconnected"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=Config.ENVIRONMENT,
        database=db_status,
        redis=redis_status,
        uptime_seconds=time.time() - state.start_time
    )


@app.post("/v1/bootstrap", include_in_schema=False)
async def bootstrap_api_key(
    bootstrap_secret: str,
    owner: str = "admin"
):
    """
    Create initial admin API key using bootstrap secret.
    Only works if no API keys exist yet or bootstrap secret matches MASTER_SECRET.
    """
    # Verify bootstrap secret matches master secret
    expected = Config.MASTER_SECRET
    if not expected:
        raise HTTPException(status_code=500, detail="Master secret not configured")
    
    # Simple constant-time comparison
    if not secrets.compare_digest(bootstrap_secret, expected):
        raise HTTPException(status_code=403, detail="Invalid bootstrap secret")
    
    # Generate admin API key
    key = f"aa_admin_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12]  # Consistent 12-char prefix
    
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO api_keys (key_hash, key_prefix, owner, name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key_hash) DO NOTHING
                """,
                key_hash, key_prefix, owner, "Bootstrap Admin Key"
            )
    else:
        # In-memory mode for testing
        state.api_keys[key_hash] = {
            "key_prefix": key_prefix,
            "owner": owner,
            "name": "Bootstrap Admin Key",
            "created_at": datetime.utcnow()
        }
    
    return {
        "key": key,  # Only shown once!
        "prefix": key_prefix,
        "owner": owner,
        "name": "Bootstrap Admin Key",
        "warning": "Save this key securely - it will not be shown again!"
    }


# =============================================================================
# Rate Limit Management Endpoints
# =============================================================================

class RateLimitTierResponse(BaseModel):
    """Rate limit tier information."""
    tier: str
    per_second: int
    per_minute: int
    per_hour: int
    burst: int


class RateLimitStatusResponse(BaseModel):
    """Current rate limit status for an API key."""
    tier: str
    limits: Dict[str, int]
    current_usage: Dict[str, int]
    remaining: Dict[str, int]
    reset_times: Dict[str, int]


class SetRateLimitRequest(BaseModel):
    """Request to set rate limit for an API key."""
    tier: Optional[str] = None
    custom_limits: Optional[Dict[str, int]] = None


@app.get("/v1/rate-limits/tiers")
async def get_rate_limit_tiers(
    api_key_info: Dict = Depends(verify_api_key)
) -> Dict[str, RateLimitTierResponse]:
    """Get all available rate limit tiers."""
    return {
        name: RateLimitTierResponse(
            tier=name,
            per_second=limits["per_second"],
            per_minute=limits["per_minute"],
            per_hour=limits["per_hour"],
            burst=limits["burst"]
        )
        for name, limits in Config.RATE_LIMIT_TIERS.items()
    }


@app.get("/v1/rate-limits/status")
async def get_rate_limit_status(
    request: Request,
    api_key_info: Dict = Depends(verify_api_key),
    _rate_limit: bool = Depends(check_rate_limit)
) -> RateLimitStatusResponse:
    """Get current rate limit status for your API key."""
    
    key_id = api_key_info.get("id", "unknown")
    tier_name = api_key_info.get("rate_limit_tier", "pro")
    custom_limits = api_key_info.get("rate_limit_override")
    
    # Get limits
    if custom_limits and isinstance(custom_limits, dict):
        limits = custom_limits
    elif tier_name in Config.RATE_LIMIT_TIERS:
        limits = Config.RATE_LIMIT_TIERS[tier_name]
    else:
        limits = Config.RATE_LIMIT_TIERS["pro"]
    
    now = int(time.time())
    
    # Get current usage from Redis
    current = {"second": 0, "minute": 0, "hour": 0, "burst": limits.get("burst", 100)}
    reset_times = {
        "second": 1,
        "minute": 60 - (now % 60),
        "hour": 3600 - (now % 3600)
    }
    
    if state.redis:
        try:
            pipe = state.redis.pipeline()
            pipe.get(f"ratelimit:sec:{key_id}:{now}")
            pipe.get(f"ratelimit:min:{key_id}:{now // 60}")
            pipe.get(f"ratelimit:hour:{key_id}:{now // 3600}")
            pipe.get(f"ratelimit:burst:{key_id}")
            results = await pipe.execute()
            
            current = {
                "second": int(results[0] or 0),
                "minute": int(results[1] or 0),
                "hour": int(results[2] or 0),
                "burst": int(results[3] or limits.get("burst", 100))
            }
        except:
            pass
    
    return RateLimitStatusResponse(
        tier=tier_name,
        limits={
            "per_second": limits.get("per_second", 0),
            "per_minute": limits.get("per_minute", 0),
            "per_hour": limits.get("per_hour", 0),
            "burst": limits.get("burst", 0)
        },
        current_usage=current,
        remaining={
            "per_second": max(0, limits.get("per_second", 0) - current["second"]),
            "per_minute": max(0, limits.get("per_minute", 0) - current["minute"]),
            "per_hour": max(0, limits.get("per_hour", 0) - current["hour"]),
            "burst": current["burst"]
        },
        reset_times=reset_times
    )


@app.post("/v1/rate-limits/reset")
async def reset_rate_limits(
    api_key_info: Dict = Depends(verify_api_key)
) -> Dict[str, str]:
    """Reset rate limit counters for your API key (admin only)."""
    
    # Check if admin
    permissions = api_key_info.get("permissions", [])
    if "*" not in permissions and "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    key_id = api_key_info.get("id", "unknown")
    now = int(time.time())
    
    if state.redis:
        try:
            # Delete all rate limit keys for this API key
            keys_to_delete = [
                f"ratelimit:sec:{key_id}:{now}",
                f"ratelimit:min:{key_id}:{now // 60}",
                f"ratelimit:hour:{key_id}:{now // 3600}",
                f"ratelimit:burst:{key_id}"
            ]
            await state.redis.delete(*keys_to_delete)
            return {"status": "success", "message": "Rate limits reset"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to reset: {e}")
    
    return {"status": "success", "message": "Rate limits reset (no Redis)"}


@app.put("/v1/api-keys/{key_prefix}/rate-limit")
async def set_api_key_rate_limit(
    key_prefix: str,
    request: SetRateLimitRequest,
    api_key_info: Dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Set rate limit tier or custom limits for an API key (admin only)."""
    
    # Check if admin
    permissions = api_key_info.get("permissions", [])
    if "*" not in permissions and "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if request.tier and request.tier not in Config.RATE_LIMIT_TIERS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid tier. Available: {list(Config.RATE_LIMIT_TIERS.keys())}"
        )
    
    if not state.db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with state.db_pool.acquire() as conn:
        # Find the API key
        row = await conn.fetchrow(
            "SELECT id FROM api_keys WHERE key_prefix = $1 AND revoked_at IS NULL",
            key_prefix
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Update rate limit settings
        if request.tier:
            await conn.execute(
                "UPDATE api_keys SET rate_limit_tier = $1 WHERE id = $2",
                request.tier, row["id"]
            )
        
        if request.custom_limits:
            import json
            await conn.execute(
                "UPDATE api_keys SET rate_limit_override = $1 WHERE id = $2",
                json.dumps(request.custom_limits), row["id"]
            )
        
        # Get updated info
        updated = await conn.fetchrow(
            "SELECT rate_limit_tier, rate_limit_override FROM api_keys WHERE id = $1",
            row["id"]
        )
        
        return {
            "status": "success",
            "key_prefix": key_prefix,
            "rate_limit_tier": updated["rate_limit_tier"],
            "rate_limit_override": updated["rate_limit_override"]
        }


# =============================================================================
# Policy Management Endpoints
# =============================================================================

class PolicyRequest(BaseModel):
    """Create or update policy request."""
    id: str = Field(..., description="Unique policy ID")
    name: str = Field(..., description="Policy name")
    effect: str = Field(..., description="allow or deny")
    priority: int = Field(default=100, description="Priority (higher = evaluated first)")
    enabled: bool = Field(default=True)
    rules: Dict[str, Any] = Field(..., description="Policy rules")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PolicyResponse(BaseModel):
    """Policy response."""
    id: str
    name: str
    effect: str
    priority: int
    enabled: bool
    rules: Dict[str, Any]
    constraints: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@app.get("/v1/policies")
async def list_policies(
    api_key_info: Dict = Depends(verify_api_key)
) -> List[PolicyResponse]:
    """List all policies."""
    
    if not state.db_pool:
        # Return from core engine if no database
        return [
            PolicyResponse(
                id=p.id,
                name=p.name,
                effect=p.effect,
                priority=p.priority,
                enabled=True,
                rules={},
                constraints={}
            )
            for p in state.core.list_policies()
        ]
    
    async with state.db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM policies ORDER BY priority DESC, name ASC"
        )
        
        return [
            PolicyResponse(
                id=row["id"],
                name=row["name"],
                effect=row["effect"],
                priority=row["priority"],
                enabled=row["enabled"],
                rules=row["rules"] if isinstance(row["rules"], dict) else json.loads(row["rules"] or "{}"),
                constraints=row["constraints"] if isinstance(row["constraints"], dict) else json.loads(row["constraints"] or "{}"),
                created_at=row["created_at"].isoformat() if row["created_at"] else None,
                updated_at=row["updated_at"].isoformat() if row["updated_at"] else None
            )
            for row in rows
        ]


@app.get("/v1/policies/{policy_id}")
async def get_policy(
    policy_id: str,
    api_key_info: Dict = Depends(verify_api_key)
) -> PolicyResponse:
    """Get a specific policy."""
    
    if not state.db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with state.db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM policies WHERE id = $1", policy_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return PolicyResponse(
            id=row["id"],
            name=row["name"],
            effect=row["effect"],
            priority=row["priority"],
            enabled=row["enabled"],
            rules=row["rules"] if isinstance(row["rules"], dict) else json.loads(row["rules"] or "{}"),
            constraints=row["constraints"] if isinstance(row["constraints"], dict) else json.loads(row["constraints"] or "{}")
        )


@app.post("/v1/policies")
async def create_policy(
    policy: PolicyRequest,
    api_key_info: Dict = Depends(verify_api_key)
) -> PolicyResponse:
    """Create a new policy."""
    
    # Check if admin
    permissions = api_key_info.get("permissions", [])
    if "*" not in permissions and "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if policy.effect not in ["allow", "deny"]:
        raise HTTPException(status_code=400, detail="Effect must be 'allow' or 'deny'")
    
    if not state.db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with state.db_pool.acquire() as conn:
        # Check if exists
        existing = await conn.fetchval("SELECT id FROM policies WHERE id = $1", policy.id)
        if existing:
            raise HTTPException(status_code=409, detail="Policy with this ID already exists")
        
        await conn.execute(
            """
            INSERT INTO policies (id, name, effect, priority, enabled, rules, constraints)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            policy.id,
            policy.name,
            policy.effect,
            policy.priority,
            policy.enabled,
            json.dumps(policy.rules),
            json.dumps(policy.constraints or {})
        )
        
        # Add to core engine
        try:
            core_policy = PolicyBuilder(policy.id, policy.name).build()
            effect_str = policy.effect.upper()
            core_policy.effect = PolicyEffect[effect_str] if effect_str in PolicyEffect.__members__ else PolicyEffect.ALLOW
            core_policy.priority = policy.priority
            state.core.add_policy(core_policy)
        except Exception as e:
            print(f"[!] Failed to add policy to core: {e}")
        
        return PolicyResponse(
            id=policy.id,
            name=policy.name,
            effect=policy.effect,
            priority=policy.priority,
            enabled=policy.enabled,
            rules=policy.rules,
            constraints=policy.constraints or {}
        )


@app.put("/v1/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    policy: PolicyRequest,
    api_key_info: Dict = Depends(verify_api_key)
) -> PolicyResponse:
    """Update an existing policy."""
    
    # Check if admin
    permissions = api_key_info.get("permissions", [])
    if "*" not in permissions and "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if policy.effect not in ["allow", "deny"]:
        raise HTTPException(status_code=400, detail="Effect must be 'allow' or 'deny'")
    
    if not state.db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with state.db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM policies WHERE id = $1", policy_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        await conn.execute(
            """
            UPDATE policies SET
                name = $2, effect = $3, priority = $4, enabled = $5,
                rules = $6, constraints = $7, updated_at = NOW()
            WHERE id = $1
            """,
            policy_id,
            policy.name,
            policy.effect,
            policy.priority,
            policy.enabled,
            json.dumps(policy.rules),
            json.dumps(policy.constraints or {})
        )
        
        return PolicyResponse(
            id=policy_id,
            name=policy.name,
            effect=policy.effect,
            priority=policy.priority,
            enabled=policy.enabled,
            rules=policy.rules,
            constraints=policy.constraints or {}
        )


@app.delete("/v1/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    api_key_info: Dict = Depends(verify_api_key)
) -> Dict[str, str]:
    """Delete a policy."""
    
    # Check if admin
    permissions = api_key_info.get("permissions", [])
    if "*" not in permissions and "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if not state.db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with state.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM policies WHERE id = $1", policy_id)
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Remove from core
        try:
            state.core.remove_policy(policy_id)
        except:
            pass
        
        return {"status": "success", "message": f"Policy {policy_id} deleted"}


@app.post("/v1/policies/{policy_id}/toggle")
async def toggle_policy(
    policy_id: str,
    api_key_info: Dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Enable or disable a policy."""
    
    # Check if admin
    permissions = api_key_info.get("permissions", [])
    if "*" not in permissions and "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if not state.db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with state.db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT enabled FROM policies WHERE id = $1", policy_id)
        if not row:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        new_state = not row["enabled"]
        await conn.execute(
            "UPDATE policies SET enabled = $1, updated_at = NOW() WHERE id = $2",
            new_state, policy_id
        )
        
        return {"status": "success", "policy_id": policy_id, "enabled": new_state}


@app.post("/v1/authorize", response_model=AuthorizeResponse)
async def authorize(
    request: AuthorizeRequest,
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(verify_api_key),
    _rate_limit: bool = Depends(check_rate_limit),
    quota_info: Dict = Depends(check_billing_quota)
):
    """
    Authorize an agent action.
    
    This is the main authorization endpoint. It evaluates the request
    against policies, checks budgets, calculates risk, and returns
    a cryptographically-signed token if approved.
    
    Billing:
    - Each call counts against your monthly authorization quota
    - Free: 1,000/month, Startup: 50,000/month, Growth: 500,000/month
    - Upgrade at /v1/billing/checkout
    """
    state.request_count += 1
    start_time = time.time()
    request_id = f"req_{secrets.token_hex(8)}"
    
    # Track usage for billing (increment counter)
    api_key_id = api_key_info.get("id", 0)
    
    # =========================================================================
    # Database-driven Policy Evaluation
    # =========================================================================
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            # Get enabled policies ordered by priority (deny-overrides approach)
            policies = await conn.fetch(
                "SELECT * FROM policies WHERE enabled = true ORDER BY priority DESC"
            )
            
            decision = None
            matching_policy = None
            
            for policy in policies:
                rules = policy["rules"] if isinstance(policy["rules"], dict) else json.loads(policy["rules"] or "{}")
                effect = policy["effect"]
                
                # Check if this policy matches the request
                matches = True
                
                # Check action match
                if "actions" in rules:
                    if request.action not in rules["actions"]:
                        matches = False
                
                # Check category match (for deny policies)
                if matches and "categories" in rules:
                    if request.category not in rules["categories"]:
                        matches = False
                
                # Check amount constraints
                if matches and request.amount:
                    if "max_amount" in rules and request.amount > rules["max_amount"]:
                        if effect == "allow":
                            matches = False
                    if "min_amount" in rules and request.amount >= rules["min_amount"]:
                        if effect == "deny":
                            # Deny policy matches high amounts
                            pass
                        else:
                            matches = False
                
                if matches:
                    decision = effect
                    matching_policy = policy
                    
                    # For deny-overrides: if we hit a deny, stop immediately
                    if effect == "deny":
                        break
                    # For allow: keep going to check for higher-priority denies
            
            # If no policy matched, deny by default
            if decision is None:
                decision = "deny"
                reason = "No applicable policies"
            elif decision == "deny":
                constraints = matching_policy["constraints"] if isinstance(matching_policy["constraints"], dict) else json.loads(matching_policy["constraints"] or "{}")
                reason = constraints.get("reason", f"Denied by policy: {matching_policy['name']}")
            else:
                reason = f"Allowed by policy: {matching_policy['name']}"
            
            eval_time = (time.time() - start_time) * 1000
            
            # Generate token for approved requests
            token = None
            token_id = None
            if decision == "allow":
                token_id = f"tok_{secrets.token_hex(12)}"
                # Create a simple signed token
                token_data = json.dumps({
                    "request_id": request_id,
                    "token_id": token_id,
                    "agent_id": request.agent_id,
                    "user_id": request.user_id,
                    "action": request.action,
                    "expires_at": time.time() + 300
                })
                token_hash = hashlib.sha256((token_data + Config.MASTER_SECRET[:32] if Config.MASTER_SECRET else "dev").encode()).hexdigest()[:32]
                token = f"{token_id}.{token_hash}"
            
            # Log to database
            background_tasks.add_task(
                log_authorization_db,
                conn=None,  # Will create new connection
                api_key_id=api_key_info["id"],
                request_id=request_id,
                agent_id=request.agent_id,
                user_id=request.user_id,
                action=request.action,
                amount=request.amount,
                merchant=request.merchant,
                category=request.category,
                status="approved" if decision == "allow" else "denied",
                reason=reason,
                policy_id=matching_policy["id"] if matching_policy else None,
                eval_time=eval_time
            )
            
            # Update spending if approved
            if decision == "allow" and request.amount:
                background_tasks.add_task(update_spending, request.user_id, request.amount)
            
            # Track usage for billing
            background_tasks.add_task(
                increment_usage,
                api_key_id,
                decision == "allow",
                request.amount or 0
            )
            
            return AuthorizeResponse(
                authorized=(decision == "allow"),
                status="approved" if decision == "allow" else "denied",
                request_id=request_id,
                token=token,
                token_id=token_id,
                reason=reason,
                risk_score=0.1 if decision == "allow" else 0.5,
                policy_id=matching_policy["id"] if matching_policy else None,
                constraints={},
                expires_at=time.time() + 300 if token else None,
                evaluation_time_ms=eval_time
            )
    
    # Fallback: Use core engine if no database
    # Check user limits from database
    user_limits = None
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_limits WHERE user_id = $1",
                request.user_id
            )
            if row:
                user_limits = dict(row)
                state.core.set_user_limits(
                    request.user_id,
                    daily_limit=float(row["daily_limit"]),
                    monthly_limit=float(row["monthly_limit"])
                )
            
            # Check daily spending
            if request.amount:
                today = datetime.now().date()
                spending = await conn.fetchrow(
                    """
                    SELECT total_spent FROM daily_spending
                    WHERE user_id = $1 AND date = $2
                    """,
                    request.user_id, today
                )
                if spending:
                    daily_limit = float(row["daily_limit"]) if row else 500.0
                    if float(spending["total_spent"]) + request.amount > daily_limit:
                        return AuthorizeResponse(
                            authorized=False,
                            status="denied",
                            request_id=f"req_{secrets.token_hex(8)}",
                            reason=f"Daily limit exceeded",
                            risk_score=0.8,
                            evaluation_time_ms=0.5
                        )
    
    # Authorize through core
    response = state.core.authorize(
        agent_id=request.agent_id,
        user_id=request.user_id,
        action=request.action,
        amount=request.amount,
        merchant=request.merchant,
        category=request.category,
        resource=request.resource,
        metadata=request.metadata
    )
    
    # Log to database asynchronously
    if state.db_pool and response:
        background_tasks.add_task(
            log_authorization,
            api_key_info["id"],
            request,
            response
        )
    
    # Update spending if approved
    if response.authorized and request.amount and state.db_pool:
        background_tasks.add_task(
            update_spending,
            request.user_id,
            request.amount
        )
    
    # Track usage for billing
    background_tasks.add_task(
        increment_usage,
        api_key_id,
        response.authorized,
        request.amount or 0
    )
    
    return AuthorizeResponse(
        authorized=response.authorized,
        status=response.status.value,
        request_id=response.request_id,
        token=response.token,
        token_id=response.token_id,
        reason=response.reason,
        risk_score=response.risk_score,
        policy_id=response.policy_id,
        constraints=response.constraints,
        expires_at=response.expires_at,
        evaluation_time_ms=response.evaluation_time_ms
    )


@app.post("/v1/token/verify")
async def verify_token(
    request: TokenVerifyRequest,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Verify an authorization token."""
    
    valid, data, error = state.core.verify_token(request.token)
    
    if not valid:
        return {"valid": False, "error": error}
    
    return {"valid": True, "data": data}


@app.post("/v1/token/revoke")
async def revoke_token(
    token_id: str,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Revoke an authorization token."""
    
    state.core.revoke_token(token_id)
    
    # Also add to Redis blacklist for distributed systems
    if state.redis:
        await state.redis.setex(f"revoked:{token_id}", 86400, "1")
    
    return {"success": True, "token_id": token_id}


@app.get("/v1/user/{user_id}/spending")
async def get_user_spending(
    user_id: str,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Get user spending status."""
    
    spending = state.core.get_user_spending(user_id)
    
    # Enrich with database data if available
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            today = datetime.now().date()
            row = await conn.fetchrow(
                """
                SELECT total_spent, transaction_count
                FROM daily_spending
                WHERE user_id = $1 AND date = $2
                """,
                user_id, today
            )
            if row:
                spending["daily_spent_db"] = float(row["total_spent"])
                spending["transaction_count"] = row["transaction_count"]
    
    return spending


@app.put("/v1/user/{user_id}/limits")
async def set_user_limits(
    user_id: str,
    limits: UserLimitsRequest,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Set user spending limits."""
    
    # Update in-memory
    state.core.set_user_limits(
        user_id,
        daily_limit=limits.daily_limit,
        monthly_limit=limits.monthly_limit
    )
    
    # Update in database
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_limits (user_id, daily_limit, monthly_limit, per_transaction_limit)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    daily_limit = COALESCE($2, user_limits.daily_limit),
                    monthly_limit = COALESCE($3, user_limits.monthly_limit),
                    per_transaction_limit = COALESCE($4, user_limits.per_transaction_limit),
                    updated_at = NOW()
                """,
                user_id,
                limits.daily_limit,
                limits.monthly_limit,
                limits.per_transaction_limit
            )
    
    return {"success": True, "user_id": user_id}


@app.get("/v1/audit")
async def get_audit_log(
    limit: int = 100,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Get audit log entries."""
    
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            query = "SELECT * FROM authorization_logs WHERE 1=1"
            params = []
            
            if user_id:
                params.append(user_id)
                query += f" AND user_id = ${len(params)}"
            if agent_id:
                params.append(agent_id)
                query += f" AND agent_id = ${len(params)}"
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # Fallback to in-memory
    return state.core.get_audit_log(limit=limit, user_id=user_id, agent_id=agent_id)


@app.post("/v1/api-key/create")
async def create_api_key(
    owner: str,
    name: Optional[str] = None,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Create a new API key (admin only)."""
    
    # Generate key
    key = f"aa_live_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:12]
    
    if state.db_pool:
        async with state.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO api_keys (key_hash, key_prefix, owner, name)
                VALUES ($1, $2, $3, $4)
                """,
                key_hash, key_prefix, owner, name
            )
    
    return {
        "key": key,  # Only shown once!
        "prefix": key_prefix,
        "owner": owner,
        "name": name
    }


@app.get("/metrics")
async def get_metrics_prometheus():
    """Get system metrics in Prometheus format (unauthenticated for scraping)."""
    
    stats = state.core.stats
    
    # Get real counts from database
    db_stats = {"total": 0, "approved": 0, "denied": 0}
    if state.db_pool:
        try:
            async with state.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'approved') as approved,
                        COUNT(*) FILTER (WHERE status = 'denied') as denied
                    FROM authorization_logs
                """)
                if row:
                    db_stats = {"total": row['total'], "approved": row['approved'], "denied": row['denied']}
        except:
            pass
    
    metrics = f"""# HELP agentauth_requests_total Total authorization requests
# TYPE agentauth_requests_total counter
agentauth_requests_total {db_stats['total']}

# HELP agentauth_approvals_total Total approved requests
# TYPE agentauth_approvals_total counter
agentauth_approvals_total {db_stats['approved']}

# HELP agentauth_denials_total Total denied requests
# TYPE agentauth_denials_total counter
agentauth_denials_total {db_stats['denied']}

# HELP agentauth_errors_total Total errors
# TYPE agentauth_errors_total counter
agentauth_errors_total {state.error_count}

# HELP agentauth_uptime_seconds Server uptime
# TYPE agentauth_uptime_seconds gauge
agentauth_uptime_seconds {time.time() - state.start_time:.2f}

# HELP agentauth_policies_count Number of loaded policies
# TYPE agentauth_policies_count gauge
agentauth_policies_count {stats['policy_count']}

# HELP agentauth_info AgentAuth server info
# TYPE agentauth_info gauge
agentauth_info{{version="1.0.0",environment="{Config.ENVIRONMENT}"}} 1
"""
    
    from starlette.responses import Response
    return Response(content=metrics, media_type="text/plain; charset=utf-8")


@app.get("/v1/metrics")
async def get_metrics(api_key_info: Dict = Depends(verify_api_key)):
    """Get system metrics (JSON format, authenticated)."""
    
    stats = state.core.stats
    
    return {
        "requests_total": state.request_count,
        "errors_total": state.error_count,
        "uptime_seconds": time.time() - state.start_time,
        "policies_count": stats['policy_count'],
        "audit_entries_total": stats['audit_entries'],
        "approvals_total": stats.get('approvals', 0),
        "denials_total": stats.get('denials', 0)
    }


# =============================================================================
# Background Tasks
# =============================================================================

async def log_authorization(api_key_id: int, request: AuthorizeRequest, response):
    """Log authorization to database."""
    
    if not state.db_pool:
        return
    
    try:
        async with state.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO authorization_logs (
                    request_id, api_key_id, agent_id, user_id, action,
                    amount, merchant, category, status, reason,
                    risk_score, policy_id, token_id, evaluation_time_ms
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """,
                response.request_id,
                api_key_id,
                request.agent_id,
                request.user_id,
                request.action,
                request.amount,
                request.merchant,
                request.category,
                response.status.value,
                response.reason,
                response.risk_score,
                response.policy_id,
                response.token_id,
                response.evaluation_time_ms
            )
    except Exception as e:
        print(f"[!] Failed to log authorization: {e}")


async def update_spending(user_id: str, amount: float):
    """Update daily spending in database."""
    
    if not state.db_pool:
        return
    
    try:
        async with state.db_pool.acquire() as conn:
            today = datetime.now().date()
            await conn.execute(
                """
                INSERT INTO daily_spending (user_id, date, total_spent, transaction_count)
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (user_id, date) DO UPDATE SET
                    total_spent = daily_spending.total_spent + $3,
                    transaction_count = daily_spending.transaction_count + 1,
                    updated_at = NOW()
                """,
                user_id, today, amount
            )
    except Exception as e:
        print(f"[!] Failed to update spending: {e}")


# =============================================================================
# Development Mode
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("Starting AgentAuth Production Server in development mode...")
    print("For production, use: uvicorn production_server:app --host 0.0.0.0 --port 8000 --workers 4")
    
    uvicorn.run(
        "production_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
