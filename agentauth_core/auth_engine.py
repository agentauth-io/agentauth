"""
AgentAuth Main Authorization Engine
Orchestrates all security modules for comprehensive authorization
"""

import time
import hashlib
import logging
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

from .crypto import SecureTokenManager, HMACValidator
from .policy_engine import PolicyEngine, AuthorizationRequest, AuthorizationResult, PolicyAction


@dataclass
class AgentContext:
    """Context for an authenticated agent"""
    agent_id: str
    user_id: str
    permissions: list
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    request_count: int = 0
    total_amount: float = 0.0


class AuthEngine:
    """
    Main authorization engine that coordinates:
    - Token management
    - Policy evaluation
    - Rate limiting
    - Audit logging
    - Risk assessment
    """
    
    def __init__(
        self,
        master_key: Optional[bytes] = None,
        enable_logging: bool = True
    ):
        self._token_manager = SecureTokenManager(master_key)
        self._policy_engine = PolicyEngine()
        self._agent_contexts: Dict[str, AgentContext] = {}
        self._audit_log: list = []
        self._enable_logging = enable_logging
        
        if enable_logging:
            self._logger = logging.getLogger("agentauth")
            self._logger.setLevel(logging.INFO)
    
    @property
    def policy_engine(self) -> PolicyEngine:
        return self._policy_engine
    
    @property
    def token_manager(self) -> SecureTokenManager:
        return self._token_manager
    
    def register_agent(
        self,
        agent_id: str,
        user_id: str,
        permissions: list = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Register an agent and generate access token
        
        Returns:
            Tuple of (token, metadata)
        """
        permissions = permissions or ["transaction"]
        
        # Create agent context
        context = AgentContext(
            agent_id=agent_id,
            user_id=user_id,
            permissions=permissions
        )
        self._agent_contexts[agent_id] = context
        
        # Generate token
        token, metadata = self._token_manager.generate_token(
            agent_id=agent_id,
            user_id=user_id,
            scope=",".join(permissions),
            ttl_seconds=3600  # 1 hour
        )
        
        self._log_event("AGENT_REGISTERED", {
            "agent_id": agent_id,
            "user_id": user_id,
            "permissions": permissions
        })
        
        return token, metadata
    
    def authorize_transaction(
        self,
        token: str,
        merchant: str,
        amount: float,
        currency: str = "USD",
        category: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> AuthorizationResult:
        """
        Authorize a transaction request
        
        Args:
            token: Agent access token
            merchant: Merchant name/identifier
            amount: Transaction amount
            currency: Currency code
            category: Optional merchant category
            metadata: Optional additional metadata
        
        Returns:
            AuthorizationResult with decision
        """
        # Validate token
        is_valid, payload, error = self._token_manager.validate_token(token)
        
        if not is_valid:
            self._log_event("AUTH_FAILED", {
                "reason": error,
                "merchant": merchant,
                "amount": amount
            })
            return AuthorizationResult(
                allowed=False,
                action=PolicyAction.DENY,
                matched_rules=[],
                risk_score=1.0,
                risk_level=4,
                reason=f"Token validation failed: {error}"
            )
        
        # Get agent context
        agent_context = self._agent_contexts.get(payload.agent_id)
        if not agent_context:
            return AuthorizationResult(
                allowed=False,
                action=PolicyAction.DENY,
                matched_rules=[],
                risk_score=1.0,
                risk_level=4,
                reason="Agent not registered"
            )
        
        # Create authorization request
        request = AuthorizationRequest(
            agent_id=payload.agent_id,
            user_id=payload.user_id,
            merchant=merchant,
            amount=amount,
            currency=currency,
            category=category,
            metadata=metadata or {}
        )
        
        # Evaluate policies
        result = self._policy_engine.evaluate(request)
        
        # Update agent context
        agent_context.last_activity = time.time()
        agent_context.request_count += 1
        if result.allowed:
            agent_context.total_amount += amount
            
            # Generate transaction token
            tx_token, _ = self._token_manager.generate_token(
                agent_id=payload.agent_id,
                user_id=payload.user_id,
                scope="transaction_execute",
                ttl_seconds=60  # 1 minute to complete
            )
            result.token = tx_token
        
        # Log event
        self._log_event("TRANSACTION_AUTH", {
            "agent_id": payload.agent_id,
            "user_id": payload.user_id,
            "merchant": merchant,
            "amount": amount,
            "currency": currency,
            "allowed": result.allowed,
            "risk_score": result.risk_score,
            "matched_rules": result.matched_rules
        })
        
        return result
    
    def revoke_agent(self, agent_id: str) -> bool:
        """Revoke agent access"""
        if agent_id in self._agent_contexts:
            del self._agent_contexts[agent_id]
            self._log_event("AGENT_REVOKED", {"agent_id": agent_id})
            return True
        return False
    
    def get_agent_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for an agent"""
        context = self._agent_contexts.get(agent_id)
        if not context:
            return None
        
        return {
            "agent_id": context.agent_id,
            "user_id": context.user_id,
            "permissions": context.permissions,
            "created_at": context.created_at,
            "last_activity": context.last_activity,
            "request_count": context.request_count,
            "total_amount": context.total_amount,
            "session_duration": time.time() - context.created_at
        }
    
    def get_audit_log(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Retrieve audit log entries"""
        entries = self._audit_log
        
        if start_time:
            entries = [e for e in entries if e["timestamp"] >= start_time]
        
        if end_time:
            entries = [e for e in entries if e["timestamp"] <= end_time]
        
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        
        return entries[-limit:]
    
    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Internal event logging"""
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data,
            "hash": hashlib.sha256(
                f"{time.time()}:{event_type}:{str(data)}".encode()
            ).hexdigest()[:16]
        }
        
        self._audit_log.append(entry)
        
        # Keep only last 10000 entries
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]
        
        if self._enable_logging and hasattr(self, '_logger'):
            self._logger.info(f"[{event_type}] {data}")
