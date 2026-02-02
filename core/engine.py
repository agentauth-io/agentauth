"""
AgentAuth Core - Authorization Engine
=====================================
PROPRIETARY AND CONFIDENTIAL

This is the main authorization engine that ties everything together.
It's the primary entry point for all authorization decisions.

Flow:
1. Request comes in with agent, action, and context
2. Policy engine evaluates applicable policies
3. Risk scoring is applied
4. Decision is made (allow/deny/require_approval)
5. If allowed, authorization token is generated
6. Everything is logged to audit trail

Architecture:
                    ┌─────────────────────┐
                    │   Authorization     │
                    │      Request        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Rate Limiter      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Policy Engine     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
       │    DENY     │  │   ALLOW     │  │  APPROVAL   │
       └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              │         ┌──────▼──────┐         │
              │         │ Token Gen   │         │
              │         └──────┬──────┘         │
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Audit Log        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Response          │
                    └─────────────────────┘
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from .crypto import KeyManager, generate_id, hash_sha256
from .tokens import (
    TokenGenerator, TokenVerifier, AuthorizationToken,
    TokenFlag, TokenType
)
from .policy import (
    PolicyEngine, PolicyDecision, PolicyEffect,
    Policy, PolicyBuilder
)


class AuthorizationStatus(Enum):
    """Authorization result status."""
    APPROVED = "approved"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class AuthorizationRequest:
    """
    Incoming authorization request.
    
    This represents an agent asking "can I do this action?"
    """
    agent_id: str
    user_id: str
    action: str
    resource: str
    amount: Optional[float] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: generate_id("req"))
    timestamp: float = field(default_factory=time.time)
    
    def to_context(self) -> Dict[str, Any]:
        """Convert to policy evaluation context."""
        ctx = {
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }
        if self.amount is not None:
            ctx["amount"] = self.amount
        if self.merchant:
            ctx["merchant"] = self.merchant
        if self.category:
            ctx["category"] = self.category
        if self.metadata:
            ctx["metadata"] = self.metadata
        return ctx
    
    def hash(self) -> str:
        """Get deterministic hash of request for audit."""
        content = json.dumps(self.to_context(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class AuthorizationResponse:
    """
    Authorization decision response.
    
    This is what gets returned to the agent.
    """
    status: AuthorizationStatus
    request_id: str
    authorized: bool
    token: Optional[str] = None  # Base64 token if authorized
    token_id: Optional[str] = None
    reason: str = ""
    risk_score: float = 0.0
    policy_id: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[float] = None
    evaluation_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "request_id": self.request_id,
            "authorized": self.authorized,
            "token": self.token,
            "token_id": self.token_id,
            "reason": self.reason,
            "risk_score": self.risk_score,
            "policy_id": self.policy_id,
            "constraints": self.constraints,
            "expires_at": self.expires_at,
            "evaluation_time_ms": self.evaluation_time_ms
        }


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    In production, use Redis or similar for distributed rate limiting.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self._config = config or RateLimitConfig()
        self._requests: Dict[str, List[float]] = {}  # key -> timestamps
    
    def check(self, key: str) -> Tuple[bool, str]:
        """
        Check if request is allowed.
        
        Returns:
            (allowed, reason)
        """
        now = time.time()
        
        # Get request history
        if key not in self._requests:
            self._requests[key] = []
        
        timestamps = self._requests[key]
        
        # Clean old timestamps
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        timestamps = [t for t in timestamps if t > day_ago]
        self._requests[key] = timestamps
        
        # Check limits
        last_minute = sum(1 for t in timestamps if t > minute_ago)
        if last_minute >= self._config.requests_per_minute:
            return (False, f"Rate limit: {self._config.requests_per_minute}/minute exceeded")
        
        last_hour = sum(1 for t in timestamps if t > hour_ago)
        if last_hour >= self._config.requests_per_hour:
            return (False, f"Rate limit: {self._config.requests_per_hour}/hour exceeded")
        
        if len(timestamps) >= self._config.requests_per_day:
            return (False, f"Rate limit: {self._config.requests_per_day}/day exceeded")
        
        # Check burst
        last_second = sum(1 for t in timestamps if t > now - 1)
        if last_second >= self._config.burst_limit:
            return (False, f"Burst limit: {self._config.burst_limit}/second exceeded")
        
        # Allowed - record request
        timestamps.append(now)
        return (True, "")
    
    def reset(self, key: str):
        """Reset rate limit for a key."""
        self._requests.pop(key, None)


@dataclass
class SpendingTracker:
    """
    Tracks spending for budget enforcement.
    
    In production, this would be backed by a database.
    """
    user_id: str
    daily_limit: float = 500.0
    monthly_limit: float = 5000.0
    _daily_spent: float = 0.0
    _monthly_spent: float = 0.0
    _last_reset_day: int = 0
    _last_reset_month: int = 0
    _transactions: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        import datetime
        now = datetime.datetime.now()
        self._last_reset_day = now.day
        self._last_reset_month = now.month
    
    def _maybe_reset(self):
        """Reset counters if day/month changed."""
        import datetime
        now = datetime.datetime.now()
        
        if now.day != self._last_reset_day:
            self._daily_spent = 0.0
            self._last_reset_day = now.day
        
        if now.month != self._last_reset_month:
            self._monthly_spent = 0.0
            self._last_reset_month = now.month
    
    def check_budget(self, amount: float) -> Tuple[bool, str, float]:
        """
        Check if amount is within budget.
        
        Returns:
            (allowed, reason, remaining_daily)
        """
        self._maybe_reset()
        
        if self._daily_spent + amount > self.daily_limit:
            return (
                False,
                f"Daily limit exceeded: ${self._daily_spent:.2f} + ${amount:.2f} > ${self.daily_limit:.2f}",
                self.daily_limit - self._daily_spent
            )
        
        if self._monthly_spent + amount > self.monthly_limit:
            return (
                False,
                f"Monthly limit exceeded",
                self.daily_limit - self._daily_spent
            )
        
        return (True, "", self.daily_limit - self._daily_spent - amount)
    
    def record_spend(self, amount: float, transaction_id: str):
        """Record a successful spend."""
        self._maybe_reset()
        self._daily_spent += amount
        self._monthly_spent += amount
        self._transactions.append({
            "transaction_id": transaction_id,
            "amount": amount,
            "timestamp": time.time()
        })
    
    @property
    def daily_remaining(self) -> float:
        self._maybe_reset()
        return max(0, self.daily_limit - self._daily_spent)


class AuthorizationEngine:
    """
    The main authorization engine.
    
    This is the heart of AgentAuth - it makes authorization decisions.
    """
    
    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        policy_engine: Optional[PolicyEngine] = None
    ):
        """
        Initialize the authorization engine.
        
        Args:
            key_manager: Cryptographic key manager (generates if not provided)
            policy_engine: Policy evaluation engine (creates default if not provided)
        """
        self._key_manager = key_manager or KeyManager()
        self._policy_engine = policy_engine or PolicyEngine()
        self._token_generator = TokenGenerator(self._key_manager)
        self._token_verifier = TokenVerifier(self._key_manager)
        self._rate_limiter = RateLimiter()
        self._spending_trackers: Dict[str, SpendingTracker] = {}
        self._audit_log: List[Dict] = []
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "approved": 0,
            "denied": 0,
            "rate_limited": 0,
            "errors": 0
        }
        
        # Initialize default policies
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Set up default policies."""
        # Per-transaction limit
        tx_limit = (
            PolicyBuilder("pol_tx_limit", "Transaction Limit")
            .allow()
            .when("amount").less_than_or_equal(200.0)
            .with_priority(10)
            .with_description("Allow transactions up to $200")
            .build()
        )
        
        # Block high-risk categories
        category_block = (
            PolicyBuilder("pol_category_block", "Block High Risk Categories")
            .deny()
            .when("category").is_in(["gambling", "crypto", "adult", "weapons"])
            .with_priority(100)
            .with_description("Block high-risk purchase categories")
            .build()
        )
        
        # Allow common merchants
        merchant_allow = (
            PolicyBuilder("pol_merchant_allow", "Trusted Merchants")
            .allow()
            .when("merchant").is_in([
                "Amazon", "Walmart", "Target", "Apple", "Best Buy",
                "Whole Foods", "Costco", "Home Depot", "Uber", "Lyft"
            ])
            .with_priority(5)
            .build()
        )
        
        self._policy_engine.add_policy(tx_limit)
        self._policy_engine.add_policy(category_block)
        self._policy_engine.add_policy(merchant_allow)
    
    def _get_spending_tracker(self, user_id: str) -> SpendingTracker:
        """Get or create spending tracker for user."""
        if user_id not in self._spending_trackers:
            self._spending_trackers[user_id] = SpendingTracker(user_id=user_id)
        return self._spending_trackers[user_id]
    
    def authorize(self, request: AuthorizationRequest) -> AuthorizationResponse:
        """
        Process an authorization request.
        
        This is the main entry point for authorization decisions.
        
        Args:
            request: The authorization request
            
        Returns:
            AuthorizationResponse with decision
        """
        start_time = time.time()
        self._stats["total_requests"] += 1
        
        try:
            # 1. Rate limiting
            rate_key = f"{request.agent_id}:{request.user_id}"
            allowed, reason = self._rate_limiter.check(rate_key)
            if not allowed:
                self._stats["rate_limited"] += 1
                return self._create_response(
                    request, AuthorizationStatus.RATE_LIMITED,
                    reason=reason, start_time=start_time
                )
            
            # 2. Budget check (if amount specified)
            if request.amount is not None and request.amount > 0:
                tracker = self._get_spending_tracker(request.user_id)
                budget_ok, budget_reason, remaining = tracker.check_budget(request.amount)
                if not budget_ok:
                    self._stats["denied"] += 1
                    return self._create_response(
                        request, AuthorizationStatus.DENIED,
                        reason=budget_reason, start_time=start_time
                    )
            
            # 3. Policy evaluation
            context = request.to_context()
            decision = self._policy_engine.evaluate(context)
            
            # 4. Make final decision
            if decision.effect == PolicyEffect.DENY:
                self._stats["denied"] += 1
                return self._create_response(
                    request, AuthorizationStatus.DENIED,
                    reason=decision.explanation,
                    risk_score=decision.risk_score,
                    policy_id=decision.policy_id,
                    start_time=start_time
                )
            
            if decision.effect == PolicyEffect.REQUIRE_APPROVAL:
                return self._create_response(
                    request, AuthorizationStatus.REQUIRES_APPROVAL,
                    reason=decision.explanation,
                    risk_score=decision.risk_score,
                    policy_id=decision.policy_id,
                    start_time=start_time
                )
            
            # 5. Generate authorization token
            token = self._token_generator.create_authorization(
                agent_id=request.agent_id,
                user_id=request.user_id,
                action=request.action,
                resource=request.resource,
                amount=request.amount,
                merchant=request.merchant,
                category=request.category,
                ttl_seconds=3600,
                flags=TokenFlag.ONE_TIME if request.amount and request.amount > 100 else TokenFlag.NONE,
                policy_hash=decision.policy_id
            )
            
            # 6. Record spending (if applicable)
            if request.amount and request.amount > 0:
                tracker = self._get_spending_tracker(request.user_id)
                tracker.record_spend(request.amount, token.token_id)
            
            # 7. Log to audit trail
            self._log_audit(request, decision, token)
            
            self._stats["approved"] += 1
            
            return self._create_response(
                request, AuthorizationStatus.APPROVED,
                reason=decision.explanation,
                risk_score=decision.risk_score,
                policy_id=decision.policy_id,
                token=token.to_base64(self._key_manager),
                token_id=token.token_id,
                expires_at=token.header.expiry,
                constraints=decision.constraints,
                start_time=start_time
            )
            
        except Exception as e:
            self._stats["errors"] += 1
            return self._create_response(
                request, AuthorizationStatus.ERROR,
                reason=f"Internal error: {str(e)}",
                start_time=start_time
            )
    
    def _create_response(
        self,
        request: AuthorizationRequest,
        status: AuthorizationStatus,
        reason: str = "",
        risk_score: float = 0.0,
        policy_id: Optional[str] = None,
        token: Optional[str] = None,
        token_id: Optional[str] = None,
        expires_at: Optional[float] = None,
        constraints: Optional[Dict] = None,
        start_time: float = 0
    ) -> AuthorizationResponse:
        """Create authorization response."""
        return AuthorizationResponse(
            status=status,
            request_id=request.request_id,
            authorized=status == AuthorizationStatus.APPROVED,
            token=token,
            token_id=token_id,
            reason=reason,
            risk_score=risk_score,
            policy_id=policy_id,
            constraints=constraints or {},
            expires_at=expires_at,
            evaluation_time_ms=(time.time() - start_time) * 1000
        )
    
    def _log_audit(
        self,
        request: AuthorizationRequest,
        decision: PolicyDecision,
        token: Optional[AuthorizationToken]
    ):
        """Log to audit trail."""
        entry = {
            "timestamp": time.time(),
            "request_id": request.request_id,
            "request_hash": request.hash(),
            "agent_id": request.agent_id,
            "user_id": request.user_id,
            "action": request.action,
            "amount": request.amount,
            "merchant": request.merchant,
            "decision": decision.effect.value,
            "policy_id": decision.policy_id,
            "risk_score": decision.risk_score,
            "token_id": token.token_id if token else None
        }
        
        # Sign the audit entry
        entry_json = json.dumps(entry, sort_keys=True)
        signature = self._key_manager.audit_signing_key.sign(entry_json.encode())
        entry["signature"] = signature.hex()
        
        self._audit_log.append(entry)
    
    def verify_token(self, token_b64: str) -> Tuple[bool, Optional[AuthorizationToken], str]:
        """
        Verify an authorization token.
        
        Args:
            token_b64: Base64-encoded token
            
        Returns:
            (valid, token, error_message)
        """
        try:
            token = self._token_verifier.verify_base64(token_b64)
            return (True, token, "")
        except Exception as e:
            return (False, None, str(e))
    
    def revoke_token(self, token_id: str):
        """Revoke a token."""
        self._token_verifier.revoke(token_id)
    
    def add_policy(self, policy: Policy):
        """Add a policy to the engine."""
        self._policy_engine.add_policy(policy)
    
    def remove_policy(self, policy_id: str):
        """Remove a policy."""
        self._policy_engine.remove_policy(policy_id)
    
    def set_user_limits(
        self,
        user_id: str,
        daily_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None
    ):
        """Set spending limits for a user."""
        tracker = self._get_spending_tracker(user_id)
        if daily_limit is not None:
            tracker.daily_limit = daily_limit
        if monthly_limit is not None:
            tracker.monthly_limit = monthly_limit
    
    def get_user_spending(self, user_id: str) -> Dict[str, Any]:
        """Get spending info for a user."""
        tracker = self._get_spending_tracker(user_id)
        return {
            "daily_limit": tracker.daily_limit,
            "daily_spent": tracker._daily_spent,
            "daily_remaining": tracker.daily_remaining,
            "monthly_limit": tracker.monthly_limit,
            "monthly_spent": tracker._monthly_spent,
            "transactions": len(tracker._transactions)
        }
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit entries."""
        return self._audit_log[-limit:]
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            **self._stats,
            "approval_rate": (
                self._stats["approved"] / self._stats["total_requests"]
                if self._stats["total_requests"] > 0 else 0
            ),
            "policies_loaded": len(self._policy_engine.list_policies()),
            "users_tracked": len(self._spending_trackers)
        }
    
    def export_public_keys(self) -> Dict[str, str]:
        """Export public keys for token verification."""
        return self._key_manager.export_public_keys()


# Test the authorization engine
if __name__ == "__main__":
    print("AgentAuth Core Authorization Engine Test")
    print("=" * 50)
    
    # Initialize engine
    engine = AuthorizationEngine()
    print(f"[+] Engine initialized with {len(engine._policy_engine.list_policies())} policies")
    
    # Set user limits
    engine.set_user_limits("user_demo", daily_limit=500.0)
    print(f"[+] Set daily limit to $500 for user_demo")
    
    # Test cases
    test_requests = [
        AuthorizationRequest(
            agent_id="agent_shopping_001",
            user_id="user_demo",
            action="purchase",
            resource="order_12345",
            amount=49.99,
            merchant="Amazon",
            category="electronics"
        ),
        AuthorizationRequest(
            agent_id="agent_shopping_001",
            user_id="user_demo",
            action="purchase",
            resource="order_12346",
            amount=299.99,  # Over $200 limit
            merchant="Apple",
            category="electronics"
        ),
        AuthorizationRequest(
            agent_id="agent_shopping_001",
            user_id="user_demo",
            action="purchase",
            resource="order_12347",
            amount=25.00,
            merchant="CryptoExchange",
            category="crypto"  # Blocked category
        ),
    ]
    
    print("\n[*] Processing authorization requests:\n")
    
    for req in test_requests:
        response = engine.authorize(req)
        print(f"  Request: {req.action} ${req.amount} at {req.merchant}")
        print(f"    Status: {response.status.value.upper()}")
        print(f"    Reason: {response.reason}")
        print(f"    Risk: {response.risk_score:.0%}")
        if response.token_id:
            print(f"    Token: {response.token_id}")
        print()
    
    # Show spending
    spending = engine.get_user_spending("user_demo")
    print(f"[+] User spending: ${spending['daily_spent']:.2f} / ${spending['daily_limit']:.2f}")
    
    # Show stats
    print(f"\n[+] Engine stats: {engine.stats}")
    
    # Show audit log
    print(f"\n[+] Audit entries: {len(engine.get_audit_log())}")
    
    print("\n[*] All authorization engine tests passed!")
