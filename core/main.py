"""
AgentAuth Core - Main Entry Point
=================================
PROPRIETARY AND CONFIDENTIAL

This is the unified entry point for the AgentAuth core system.
It combines all components into a single, easy-to-use interface.

Usage:
    from core import AgentAuthCore
    
    # Initialize with new keys
    auth = AgentAuthCore()
    
    # Or restore from master secret
    auth = AgentAuthCore.from_master_secret("hex_string")
    
    # Authorize a transaction
    response = auth.authorize(
        agent_id="agent_123",
        user_id="user_abc",
        action="purchase",
        amount=49.99,
        merchant="Amazon",
        category="electronics"
    )
    
    if response.authorized:
        # Use response.token for payment
        print(f"Approved! Token: {response.token_id}")
"""

import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from .crypto import KeyManager, MasterSecret
from .tokens import TokenGenerator, TokenVerifier, AuthorizationToken
from .policy import PolicyEngine, Policy, PolicyBuilder, PolicyEffect
from .engine import (
    AuthorizationEngine, AuthorizationRequest, AuthorizationResponse,
    AuthorizationStatus
)
from .audit import AuditLog, AuditEventType
from .risk import RiskScoringEngine, RiskAssessment


class AgentAuthCore:
    """
    The unified AgentAuth authorization system.
    
    This class provides a single interface to all AgentAuth capabilities:
    - Authorization decisions
    - Token generation and verification
    - Policy management
    - Risk scoring
    - Audit logging
    - Spending limits
    
    Security Model:
    - All cryptographic operations use proven algorithms
    - Master secret is the root of trust
    - All decisions are logged to tamper-evident audit log
    - Tokens are cryptographically signed and encrypted
    """
    
    VERSION = "0.1.0"
    
    def __init__(
        self,
        master_secret: Optional[MasterSecret] = None,
        audit_path: Optional[str] = None
    ):
        """
        Initialize AgentAuth core.
        
        Args:
            master_secret: Master secret for key derivation.
                          If None, generates a new one.
            audit_path: Path to persist audit log (optional).
        """
        # Initialize cryptographic key manager
        self._key_manager = KeyManager(master_secret)
        
        # Initialize policy engine
        self._policy_engine = PolicyEngine()
        
        # Initialize authorization engine
        self._auth_engine = AuthorizationEngine(
            key_manager=self._key_manager,
            policy_engine=self._policy_engine
        )
        
        # Initialize risk scoring
        self._risk_engine = RiskScoringEngine()
        
        # Initialize audit log
        self._audit_log = AuditLog(
            signing_key=self._key_manager.audit_signing_key,
            persistence_path=audit_path
        )
        
        # Track initialization
        self._initialized_at = time.time()
        self._request_count = 0
        
        # Log system start
        self._audit_log.append(
            event_type=AuditEventType.SYSTEM_EVENT,
            data={
                "event": "system_initialized",
                "version": self.VERSION,
                "audit_persistence": audit_path is not None
            }
        )
    
    @classmethod
    def from_master_secret(
        cls,
        master_hex: str,
        audit_path: Optional[str] = None
    ) -> "AgentAuthCore":
        """
        Initialize from existing master secret.
        
        Use this to restore the system from backup.
        
        Args:
            master_hex: Master secret as hex string
            audit_path: Path to persist audit log
            
        Returns:
            Initialized AgentAuthCore
        """
        master = MasterSecret.from_hex(master_hex)
        return cls(master_secret=master, audit_path=audit_path)
    
    def authorize(
        self,
        agent_id: str,
        user_id: str,
        action: str,
        amount: Optional[float] = None,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
        resource: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuthorizationResponse:
        """
        Authorize an action.
        
        This is the main entry point for authorization decisions.
        
        Args:
            agent_id: Identifier of the requesting agent
            user_id: Identifier of the user on whose behalf the agent acts
            action: Action being authorized (e.g., "purchase", "transfer")
            amount: Transaction amount (if applicable)
            merchant: Merchant name (if applicable)
            category: Category (if applicable)
            resource: Resource identifier (auto-generated if not provided)
            metadata: Additional context for the request
            
        Returns:
            AuthorizationResponse with decision and token (if approved)
        """
        self._request_count += 1
        
        # Create request
        request = AuthorizationRequest(
            agent_id=agent_id,
            user_id=user_id,
            action=action,
            resource=resource or f"resource_{self._request_count}",
            amount=amount,
            merchant=merchant,
            category=category,
            metadata=metadata or {}
        )
        
        # Log request
        self._audit_log.append(
            event_type=AuditEventType.AUTHORIZATION_REQUEST,
            data={
                "request_id": request.request_id,
                "action": action,
                "amount": amount,
                "merchant": merchant,
                "category": category
            },
            agent_id=agent_id,
            user_id=user_id
        )
        
        # Get risk assessment
        if amount and merchant and category:
            risk = self._risk_engine.assess(
                user_id=user_id,
                agent_id=agent_id,
                amount=amount,
                merchant=merchant,
                category=category,
                metadata=metadata
            )
            
            # Add risk to request metadata for policy evaluation
            request.metadata["risk_score"] = risk.overall_score
            request.metadata["risk_level"] = risk.level.value
        
        # Authorize
        response = self._auth_engine.authorize(request)
        
        # Log decision
        self._audit_log.append(
            event_type=AuditEventType.AUTHORIZATION_DECISION,
            data={
                "request_id": request.request_id,
                "status": response.status.value,
                "authorized": response.authorized,
                "reason": response.reason,
                "risk_score": response.risk_score,
                "policy_id": response.policy_id,
                "token_id": response.token_id
            },
            agent_id=agent_id,
            user_id=user_id
        )
        
        # Record transaction if approved
        if response.authorized and amount and merchant and category:
            self._risk_engine.record_transaction(
                user_id=user_id,
                amount=amount,
                merchant=merchant,
                category=category
            )
        
        return response
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Verify an authorization token.
        
        Args:
            token: Base64-encoded token
            
        Returns:
            (valid, token_data, error_message)
        """
        valid, token_obj, error = self._auth_engine.verify_token(token)
        
        if valid and token_obj:
            self._audit_log.append(
                event_type=AuditEventType.TOKEN_VERIFIED,
                data={
                    "token_id": token_obj.token_id,
                    "valid": True
                },
                agent_id=token_obj.payload.agent_id,
                user_id=token_obj.payload.user_id
            )
            return (True, token_obj.summary(), "")
        
        return (False, None, error)
    
    def revoke_token(self, token_id: str):
        """
        Revoke an authorization token.
        
        Args:
            token_id: Token identifier to revoke
        """
        self._auth_engine.revoke_token(token_id)
        
        self._audit_log.append(
            event_type=AuditEventType.TOKEN_REVOKED,
            data={"token_id": token_id}
        )
    
    # Policy Management
    
    def add_policy(self, policy: Policy):
        """Add a policy to the system."""
        self._policy_engine.add_policy(policy)
        
        self._audit_log.append(
            event_type=AuditEventType.POLICY_CREATED,
            data={
                "policy_id": policy.id,
                "policy_name": policy.name,
                "effect": policy.effect.value,
                "hash": policy.hash()
            }
        )
    
    def remove_policy(self, policy_id: str):
        """Remove a policy."""
        policy = self._policy_engine.get_policy(policy_id)
        if policy:
            self._policy_engine.remove_policy(policy_id)
            
            self._audit_log.append(
                event_type=AuditEventType.POLICY_DELETED,
                data={"policy_id": policy_id, "policy_name": policy.name}
            )
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self._policy_engine.get_policy(policy_id)
    
    def list_policies(self) -> List[Dict]:
        """List all policies."""
        return [p.to_dict() for p in self._policy_engine.list_policies()]
    
    # User/Agent Management
    
    def set_user_limits(
        self,
        user_id: str,
        daily_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None
    ):
        """Set spending limits for a user."""
        self._auth_engine.set_user_limits(
            user_id=user_id,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit
        )
    
    def get_user_spending(self, user_id: str) -> Dict[str, Any]:
        """Get current spending status for a user."""
        return self._auth_engine.get_user_spending(user_id)
    
    def set_agent_trust(self, agent_id: str, trust_score: float):
        """
        Set trust level for an agent.
        
        Args:
            agent_id: Agent identifier
            trust_score: 0.0 (untrusted) to 1.0 (fully trusted)
        """
        self._risk_engine.set_agent_trust(agent_id, trust_score)
    
    def assess_risk(
        self,
        user_id: str,
        agent_id: str,
        amount: float,
        merchant: str,
        category: str
    ) -> RiskAssessment:
        """
        Get risk assessment without authorizing.
        
        Useful for preview/simulation.
        """
        return self._risk_engine.assess(
            user_id=user_id,
            agent_id=agent_id,
            amount=amount,
            merchant=merchant,
            category=category
        )
    
    # Audit
    
    def get_audit_log(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict]:
        """Get audit log entries."""
        entries = self._audit_log.get_entries(
            limit=limit,
            user_id=user_id,
            agent_id=agent_id
        )
        return [e.to_dict() for e in entries]
    
    def verify_audit_chain(self) -> Tuple[bool, str]:
        """Verify audit log integrity."""
        valid, seq, msg = self._audit_log.verify_chain()
        return (valid, msg)
    
    def export_audit(self, path: str, format: str = "json"):
        """Export audit log to file."""
        self._audit_log.export(path, format)
    
    # System
    
    def export_master_secret(self) -> str:
        """
        Export master secret for backup.
        
        WARNING: This is extremely sensitive. Store securely!
        """
        return self._key_manager.export_master_secret()
    
    def export_public_keys(self) -> Dict[str, str]:
        """Export public keys (safe to share)."""
        return self._key_manager.export_public_keys()
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "version": self.VERSION,
            "initialized_at": self._initialized_at,
            "uptime_seconds": time.time() - self._initialized_at,
            "total_requests": self._request_count,
            "auth_stats": self._auth_engine.stats,
            "policy_count": len(self._policy_engine.list_policies()),
            "audit_entries": self._audit_log.length,
            "risk_stats": self._risk_engine.stats
        }


# Convenience function to create common policies
def create_spending_policy(
    daily_limit: float = 500.0,
    per_transaction_limit: float = 200.0,
    blocked_categories: Optional[List[str]] = None
) -> List[Policy]:
    """
    Create standard spending control policies.
    
    Args:
        daily_limit: Maximum daily spending
        per_transaction_limit: Maximum per transaction
        blocked_categories: Categories to block
        
    Returns:
        List of Policy objects
    """
    policies = []
    
    # Transaction limit
    tx_limit = (
        PolicyBuilder("pol_tx_limit", "Per-Transaction Limit")
        .allow()
        .when("amount").less_than_or_equal(per_transaction_limit)
        .with_priority(10)
        .with_description(f"Allow transactions up to ${per_transaction_limit}")
        .with_constraint("limit", per_transaction_limit)
        .build()
    )
    policies.append(tx_limit)
    
    # Blocked categories
    if blocked_categories is None:
        blocked_categories = ["gambling", "crypto", "adult", "weapons"]
    
    if blocked_categories:
        category_block = (
            PolicyBuilder("pol_blocked_categories", "Blocked Categories")
            .deny()
            .when("category").is_in(blocked_categories)
            .with_priority(100)
            .with_description(f"Block categories: {', '.join(blocked_categories)}")
            .build()
        )
        policies.append(category_block)
    
    return policies


# Test the core system
if __name__ == "__main__":
    print("AgentAuth Core System Test")
    print("=" * 50)
    
    # Initialize
    core = AgentAuthCore()
    print(f"[+] AgentAuth v{core.VERSION} initialized")
    print(f"    Master secret: {core.export_master_secret()[:16]}... (KEEP SECURE!)")
    
    # Add spending policies
    policies = create_spending_policy(
        daily_limit=500.0,
        per_transaction_limit=200.0
    )
    for policy in policies:
        core.add_policy(policy)
    print(f"[+] Added {len(policies)} policies")
    
    # Set user limits
    core.set_user_limits("user_demo", daily_limit=500.0)
    
    # Set agent trust
    core.set_agent_trust("agent_trusted", 0.9)
    
    # Test authorization
    print("\n[*] Testing authorizations:\n")
    
    tests = [
        ("Normal purchase", 49.99, "Amazon", "electronics"),
        ("Over limit", 299.99, "Apple", "electronics"),
        ("Blocked category", 25.00, "CryptoEx", "crypto"),
    ]
    
    for name, amount, merchant, category in tests:
        response = core.authorize(
            agent_id="agent_trusted",
            user_id="user_demo",
            action="purchase",
            amount=amount,
            merchant=merchant,
            category=category
        )
        
        status = "APPROVED" if response.authorized else "DENIED"
        print(f"  {name}: {status}")
        print(f"    Amount: ${amount}, Merchant: {merchant}")
        print(f"    Reason: {response.reason}")
        if response.token_id:
            print(f"    Token: {response.token_id}")
        print()
    
    # Verify audit
    valid, msg = core.verify_audit_chain()
    print(f"[+] Audit chain verification: {'PASS' if valid else 'FAIL'}")
    
    # Show stats
    stats = core.stats
    print(f"\n[+] System Stats:")
    print(f"    Requests: {stats['total_requests']}")
    print(f"    Policies: {stats['policy_count']}")
    print(f"    Audit entries: {stats['audit_entries']}")
    
    # Show spending
    spending = core.get_user_spending("user_demo")
    print(f"\n[+] User spending: ${spending['daily_spent']:.2f} / ${spending['daily_limit']:.2f}")
    
    print("\n[*] All core system tests passed!")
