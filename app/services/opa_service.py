"""
AgentAuth OPA (Open Policy Agent) Integration

DEMO/SIMULATION MODE: This is a demonstration implementation.
For production use, connect to a real OPA server:
  docker run -p 8181:8181 openpolicyagent/opa:latest run --server

This demo implementation provides:
- Simulated Rego policy evaluation
- Pre-defined AgentAuth policies
- Compatible interface for testing

Production features (with real OPA):
- External policy bundles
- Decision logging to external systems
- Policy testing framework

See: https://www.openpolicyagent.org/
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Flag to indicate demo mode
DEMO_MODE = True


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""

    allowed: bool
    policy_id: str
    decision_id: str

    # Detailed results
    reasons: list[str] = field(default_factory=list)
    bindings: dict[str, Any] = field(default_factory=dict)

    # Metadata
    evaluation_time_ms: float = 0.0
    policy_version: str = ""

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "policy_id": self.policy_id,
            "decision_id": self.decision_id,
            "reasons": self.reasons,
            "bindings": self.bindings,
            "evaluation_time_ms": round(self.evaluation_time_ms, 2),
            "policy_version": self.policy_version,
        }


class RegoPolicy:
    """
    A Rego policy definition.

    Rego is OPA's declarative policy language.
    """

    def __init__(self, policy_id: str, rego_code: str, description: str = ""):
        self.policy_id = policy_id
        self.rego_code = rego_code
        self.description = description
        self.version = "1.0"
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "rego": self.rego_code,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
        }


# Pre-defined AgentAuth policies
AGENTAUTH_POLICIES = {
    "spending_limits": RegoPolicy(
        policy_id="agentauth.spending_limits",
        description="Enforce spending limits on transactions",
        rego_code="""
package agentauth.spending_limits

default allow = false

# Allow if amount is within daily limit
allow {
    input.amount <= data.limits.per_transaction
    input.daily_spent + input.amount <= data.limits.daily
    input.monthly_spent + input.amount <= data.limits.monthly
}

# Deny reasons
reasons[msg] {
    input.amount > data.limits.per_transaction
    msg := sprintf("Amount %.2f exceeds per-transaction limit %.2f", [input.amount, data.limits.per_transaction])
}

reasons[msg] {
    input.daily_spent + input.amount > data.limits.daily
    msg := sprintf("Would exceed daily limit of %.2f", [data.limits.daily])
}

reasons[msg] {
    input.monthly_spent + input.amount > data.limits.monthly
    msg := sprintf("Would exceed monthly limit of %.2f", [data.limits.monthly])
}
"""
    ),

    "merchant_rules": RegoPolicy(
        policy_id="agentauth.merchant_rules",
        description="Enforce merchant whitelist/blacklist rules",
        rego_code="""
package agentauth.merchant_rules

default allow = true

# Deny if merchant is blacklisted
allow = false {
    data.blacklist[_] == input.merchant_id
}

# Deny if whitelist exists and merchant not in it
allow = false {
    count(data.whitelist) > 0
    not merchant_in_whitelist
}

merchant_in_whitelist {
    data.whitelist[_] == input.merchant_id
}

# Deny reasons
reasons[msg] {
    data.blacklist[_] == input.merchant_id
    msg := sprintf("Merchant %s is blacklisted", [input.merchant_id])
}

reasons[msg] {
    count(data.whitelist) > 0
    not merchant_in_whitelist
    msg := sprintf("Merchant %s is not in whitelist", [input.merchant_id])
}
"""
    ),

    "category_controls": RegoPolicy(
        policy_id="agentauth.category_controls",
        description="Control allowed merchant categories",
        rego_code="""
package agentauth.category_controls

default allow = true

# Deny if category is blocked
allow = false {
    data.blocked_categories[_] == input.category_code
}

# Allow only specific categories if defined
allow = false {
    count(data.allowed_categories) > 0
    not category_allowed
}

category_allowed {
    data.allowed_categories[_] == input.category_code
}

# Deny reasons
reasons[msg] {
    data.blocked_categories[_] == input.category_code
    msg := sprintf("Category %s is blocked", [input.category_code])
}
"""
    ),

    "time_based": RegoPolicy(
        policy_id="agentauth.time_based",
        description="Time-based transaction controls",
        rego_code="""
package agentauth.time_based

default allow = true

# Deny during blocked hours
allow = false {
    data.blocked_hours[_] == input.hour
}

# Deny on blocked days
allow = false {
    data.blocked_days[_] == input.day_of_week
}

# Deny reasons
reasons[msg] {
    data.blocked_hours[_] == input.hour
    msg := sprintf("Transactions not allowed at hour %d", [input.hour])
}
"""
    ),

    "fraud_risk": RegoPolicy(
        policy_id="agentauth.fraud_risk",
        description="Fraud risk-based authorization",
        rego_code="""
package agentauth.fraud_risk

default allow = true

# Deny if fraud score exceeds threshold
allow = false {
    input.fraud_score > data.fraud_threshold
}

# Require step-up auth for medium risk
step_up_required {
    input.fraud_score > data.step_up_threshold
    input.fraud_score <= data.fraud_threshold
}

# Deny reasons
reasons[msg] {
    input.fraud_score > data.fraud_threshold
    msg := sprintf("Fraud risk %.2f exceeds threshold %.2f", [input.fraud_score, data.fraud_threshold])
}
"""
    ),
}


class LocalPolicyEngine:
    """
    Local policy engine with Rego-like evaluation.

    For when OPA server is not available.
    Implements core policy logic in Python.
    """

    def __init__(self):
        self.policies: dict[str, RegoPolicy] = {}

    def register_policy(self, policy: RegoPolicy) -> None:
        """Register a policy."""
        self.policies[policy.policy_id] = policy

    def evaluate_spending_limits(
        self,
        amount: float,
        daily_spent: float,
        monthly_spent: float,
        limits: dict[str, float]
    ) -> PolicyDecision:
        """Evaluate spending limits policy."""
        import time
        import uuid
        start = time.perf_counter()

        reasons = []
        allowed = True

        # Per-transaction limit
        if amount > limits.get("per_transaction", float("inf")):
            allowed = False
            reasons.append(f"Amount {amount:.2f} exceeds per-transaction limit {limits.get('per_transaction'):.2f}")

        # Daily limit
        if daily_spent + amount > limits.get("daily", float("inf")):
            allowed = False
            reasons.append(f"Would exceed daily limit of {limits.get('daily'):.2f}")

        # Monthly limit
        if monthly_spent + amount > limits.get("monthly", float("inf")):
            allowed = False
            reasons.append(f"Would exceed monthly limit of {limits.get('monthly'):.2f}")

        return PolicyDecision(
            allowed=allowed,
            policy_id="agentauth.spending_limits",
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            reasons=reasons,
            evaluation_time_ms=(time.perf_counter() - start) * 1000,
            policy_version="1.0"
        )

    def evaluate_merchant_rules(
        self,
        merchant_id: str,
        whitelist: list[str],
        blacklist: list[str]
    ) -> PolicyDecision:
        """Evaluate merchant rules policy."""
        import time
        import uuid
        start = time.perf_counter()

        reasons = []
        allowed = True

        # Blacklist check
        if merchant_id in blacklist:
            allowed = False
            reasons.append(f"Merchant {merchant_id} is blacklisted")

        # Whitelist check
        if whitelist and merchant_id not in whitelist:
            allowed = False
            reasons.append(f"Merchant {merchant_id} is not in whitelist")

        return PolicyDecision(
            allowed=allowed,
            policy_id="agentauth.merchant_rules",
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            reasons=reasons,
            evaluation_time_ms=(time.perf_counter() - start) * 1000,
            policy_version="1.0"
        )


class OPAService:
    """
    Open Policy Agent integration service.

    Supports both remote OPA server and local fallback.
    """

    def __init__(self, opa_url: str | None = None):
        self.opa_url = opa_url or settings.opa_url if hasattr(settings, 'opa_url') else None
        self.local_engine = LocalPolicyEngine()
        self._policies_loaded = False

    async def _load_policies(self) -> None:
        """Load policies into OPA server."""
        if self._policies_loaded:
            return

        for policy in AGENTAUTH_POLICIES.values():
            self.local_engine.register_policy(policy)

        # If OPA server available, push policies
        if self.opa_url:
            try:
                async with httpx.AsyncClient() as client:
                    for policy_id, policy in AGENTAUTH_POLICIES.items():
                        await client.put(
                            f"{self.opa_url}/v1/policies/{policy_id}",
                            content=policy.rego_code,
                            headers={"Content-Type": "text/plain"}
                        )
            except Exception:
                pass

        self._policies_loaded = True

    async def evaluate(
        self,
        policy_id: str,
        input_data: dict[str, Any],
        data: dict[str, Any] | None = None
    ) -> PolicyDecision:
        """
        Evaluate a policy with given input.

        Usage:
            decision = await opa.evaluate(
                policy_id="agentauth.spending_limits",
                input_data={"amount": 100.0, "daily_spent": 200.0},
                data={"limits": {"daily": 500.0, "per_transaction": 200.0}}
            )
        """
        await self._load_policies()

        # Try remote OPA first
        if self.opa_url:
            try:
                return await self._evaluate_remote(policy_id, input_data, data)
            except Exception:
                pass

        # Fallback to local evaluation
        return await self._evaluate_local(policy_id, input_data, data)

    async def _evaluate_remote(
        self,
        policy_id: str,
        input_data: dict[str, Any],
        data: dict[str, Any] | None = None
    ) -> PolicyDecision:
        """Evaluate policy on remote OPA server."""
        import time
        import uuid
        start = time.perf_counter()

        policy_path = policy_id.replace(".", "/")
        url = f"{self.opa_url}/v1/data/{policy_path}"

        payload = {"input": input_data}
        if data:
            payload["data"] = data

        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(url, json=payload)
            result = response.json()

        return PolicyDecision(
            allowed=result.get("result", {}).get("allow", False),
            policy_id=policy_id,
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            reasons=result.get("result", {}).get("reasons", []),
            evaluation_time_ms=(time.perf_counter() - start) * 1000,
            policy_version="1.0"
        )

    async def _evaluate_local(
        self,
        policy_id: str,
        input_data: dict[str, Any],
        data: dict[str, Any] | None = None
    ) -> PolicyDecision:
        """Evaluate policy using local engine."""
        data = data or {}

        if policy_id == "agentauth.spending_limits":
            return self.local_engine.evaluate_spending_limits(
                amount=input_data.get("amount", 0),
                daily_spent=input_data.get("daily_spent", 0),
                monthly_spent=input_data.get("monthly_spent", 0),
                limits=data.get("limits", {})
            )

        if policy_id == "agentauth.merchant_rules":
            return self.local_engine.evaluate_merchant_rules(
                merchant_id=input_data.get("merchant_id", ""),
                whitelist=data.get("whitelist", []),
                blacklist=data.get("blacklist", [])
            )

        # Default: allow
        import uuid
        return PolicyDecision(
            allowed=True,
            policy_id=policy_id,
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            policy_version="1.0"
        )

    async def check_authorization(
        self,
        consent_id: str,
        amount: float,
        merchant_id: str,
        category_code: str = "",
        daily_spent: float = 0,
        monthly_spent: float = 0,
        fraud_score: float = 0,
        limits: dict[str, float] | None = None,
        rules: dict[str, Any] | None = None
    ) -> dict[str, PolicyDecision]:
        """
        Run all authorization policies.

        Returns decision from each policy.
        """
        limits = limits or {}
        rules = rules or {}

        decisions = {}

        # Spending limits
        decisions["spending_limits"] = await self.evaluate(
            "agentauth.spending_limits",
            input_data={
                "amount": amount,
                "daily_spent": daily_spent,
                "monthly_spent": monthly_spent,
            },
            data={"limits": limits}
        )

        # Merchant rules
        decisions["merchant_rules"] = await self.evaluate(
            "agentauth.merchant_rules",
            input_data={"merchant_id": merchant_id},
            data={
                "whitelist": rules.get("merchant_whitelist", []),
                "blacklist": rules.get("merchant_blacklist", [])
            }
        )

        return decisions

    def get_combined_decision(self, decisions: dict[str, PolicyDecision]) -> PolicyDecision:
        """Get combined decision from all policies."""
        import uuid

        all_reasons = []
        allowed = True

        for policy_id, decision in decisions.items():
            if not decision.allowed:
                allowed = False
                all_reasons.extend(decision.reasons)

        return PolicyDecision(
            allowed=allowed,
            policy_id="agentauth.combined",
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            reasons=all_reasons,
            policy_version="1.0"
        )


# Singleton instance
_opa_service: OPAService | None = None


def get_opa_service() -> OPAService:
    """Get singleton OPA service."""
    global _opa_service
    if _opa_service is None:
        _opa_service = OPAService()
    return _opa_service


# Convenience function
async def check_policy(
    amount: float,
    merchant_id: str,
    daily_spent: float = 0,
    monthly_spent: float = 0,
    limits: dict[str, float] | None = None,
    rules: dict[str, Any] | None = None
) -> PolicyDecision:
    """
    Quick policy check.

    Usage:
        decision = await check_policy(
            amount=99.99,
            merchant_id="amazon",
            limits={"daily": 500, "per_transaction": 200}
        )
        if not decision.allowed:
            return {"error": decision.reasons}
    """
    service = get_opa_service()
    decisions = await service.check_authorization(
        consent_id="",
        amount=amount,
        merchant_id=merchant_id,
        daily_spent=daily_spent,
        monthly_spent=monthly_spent,
        limits=limits,
        rules=rules
    )
    return service.get_combined_decision(decisions)
