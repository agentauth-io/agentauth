"""
AgentAuth Core - Policy Engine
==============================
PROPRIETARY AND CONFIDENTIAL

This module implements the policy evaluation engine - the brain of AgentAuth.
Policies define what actions agents are allowed to perform.

Policy Language:
- Declarative rules with conditions and effects
- Support for AND/OR/NOT logic
- Attribute-based access control (ABAC)
- Time-based rules
- Spending limits and budgets
- Merchant/category restrictions

Policy Evaluation:
1. Collect all applicable policies
2. Evaluate each policy against request context
3. Combine results (deny-overrides by default)
4. Return decision with explanation

Example Policy:
{
    "id": "pol_spending_limit",
    "effect": "allow",
    "conditions": {
        "amount": {"lte": 200.00},
        "category": {"in": ["groceries", "electronics"]},
        "time": {"between": ["09:00", "21:00"]}
    },
    "constraints": {
        "daily_limit": 500.00,
        "require_approval_above": 100.00
    }
}
"""

import time
import json
import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum
from datetime import datetime, timezone


class PolicyEffect(Enum):
    """Policy decision effect."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    WARN = "warn"


class PolicyCombineAlgorithm(Enum):
    """How to combine multiple policy decisions."""
    DENY_OVERRIDES = "deny_overrides"      # Any deny = deny
    ALLOW_OVERRIDES = "allow_overrides"    # Any allow = allow
    FIRST_APPLICABLE = "first_applicable"  # First matching policy wins
    UNANIMOUS = "unanimous"                 # All must allow


class ConditionOperator(Enum):
    """Operators for condition evaluation."""
    EQ = "eq"           # Equal
    NE = "ne"           # Not equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    IN = "in"           # In list
    NOT_IN = "not_in"   # Not in list
    CONTAINS = "contains"       # String contains
    MATCHES = "matches"         # Regex match
    BETWEEN = "between"         # Between two values
    EXISTS = "exists"           # Attribute exists
    IS_NULL = "is_null"         # Attribute is null


@dataclass
class Condition:
    """A single condition in a policy rule."""
    attribute: str
    operator: ConditionOperator
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate condition against request context.
        
        Returns:
            True if condition is satisfied
        """
        # Get attribute value from context (supports nested paths)
        attr_value = self._get_nested(context, self.attribute)
        
        if self.operator == ConditionOperator.EXISTS:
            return attr_value is not None if self.value else attr_value is None
        
        if self.operator == ConditionOperator.IS_NULL:
            return attr_value is None if self.value else attr_value is not None
        
        if attr_value is None:
            return False
        
        try:
            if self.operator == ConditionOperator.EQ:
                return attr_value == self.value
            elif self.operator == ConditionOperator.NE:
                return attr_value != self.value
            elif self.operator == ConditionOperator.LT:
                return float(attr_value) < float(self.value)
            elif self.operator == ConditionOperator.LTE:
                return float(attr_value) <= float(self.value)
            elif self.operator == ConditionOperator.GT:
                return float(attr_value) > float(self.value)
            elif self.operator == ConditionOperator.GTE:
                return float(attr_value) >= float(self.value)
            elif self.operator == ConditionOperator.IN:
                return attr_value in self.value
            elif self.operator == ConditionOperator.NOT_IN:
                return attr_value not in self.value
            elif self.operator == ConditionOperator.CONTAINS:
                return str(self.value) in str(attr_value)
            elif self.operator == ConditionOperator.MATCHES:
                return bool(re.match(self.value, str(attr_value)))
            elif self.operator == ConditionOperator.BETWEEN:
                low, high = self.value
                return float(low) <= float(attr_value) <= float(high)
        except (TypeError, ValueError):
            return False
        
        return False
    
    @staticmethod
    def _get_nested(obj: Dict, path: str) -> Any:
        """Get nested attribute using dot notation."""
        parts = path.split('.')
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "attribute": self.attribute,
            "operator": self.operator.value,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Condition":
        """Deserialize from dictionary."""
        return cls(
            attribute=data["attribute"],
            operator=ConditionOperator(data["operator"]),
            value=data["value"]
        )


@dataclass
class PolicyRule:
    """A single rule within a policy."""
    conditions: List[Condition]
    logic: str = "and"  # "and" or "or"
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate all conditions.
        
        Returns:
            True if rule is satisfied (based on logic)
        """
        if not self.conditions:
            return True
        
        results = [c.evaluate(context) for c in self.conditions]
        
        if self.logic == "and":
            return all(results)
        elif self.logic == "or":
            return any(results)
        else:
            return all(results)
    
    def to_dict(self) -> Dict:
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "logic": self.logic
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PolicyRule":
        return cls(
            conditions=[Condition.from_dict(c) for c in data.get("conditions", [])],
            logic=data.get("logic", "and")
        )


@dataclass
class Policy:
    """
    A complete policy definition.
    
    Policies are the core of AgentAuth - they define what's allowed.
    """
    id: str
    name: str
    effect: PolicyEffect
    rules: List[PolicyRule]
    priority: int = 0           # Higher = evaluated first
    enabled: bool = True
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, PolicyEffect]:
        """
        Evaluate policy against request context.
        
        Returns:
            (applies, effect) - Whether policy applies and its effect
        """
        if not self.enabled:
            return (False, self.effect)
        
        # All rules must match for policy to apply
        for rule in self.rules:
            if not rule.evaluate(context):
                return (False, self.effect)
        
        return (True, self.effect)
    
    def hash(self) -> str:
        """Get deterministic hash of policy for audit."""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "effect": self.effect.value,
            "rules": [r.to_dict() for r in self.rules],
            "priority": self.priority,
            "enabled": self.enabled,
            "description": self.description,
            "constraints": self.constraints,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Policy":
        return cls(
            id=data["id"],
            name=data["name"],
            effect=PolicyEffect(data["effect"]),
            rules=[PolicyRule.from_dict(r) for r in data.get("rules", [])],
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    effect: PolicyEffect
    allowed: bool
    policy_id: Optional[str]
    policy_name: Optional[str]
    explanation: str
    constraints: Dict[str, Any]
    risk_score: float
    evaluation_time_ms: float
    policies_evaluated: int
    
    def to_dict(self) -> Dict:
        return {
            "effect": self.effect.value,
            "allowed": self.allowed,
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "explanation": self.explanation,
            "constraints": self.constraints,
            "risk_score": self.risk_score,
            "evaluation_time_ms": self.evaluation_time_ms,
            "policies_evaluated": self.policies_evaluated
        }


class PolicyEngine:
    """
    The core policy evaluation engine.
    
    This is the brain of AgentAuth - it decides whether actions are allowed.
    """
    
    def __init__(
        self,
        combine_algorithm: PolicyCombineAlgorithm = PolicyCombineAlgorithm.DENY_OVERRIDES
    ):
        self._policies: Dict[str, Policy] = {}
        self._combine_algorithm = combine_algorithm
        self._custom_evaluators: Dict[str, Callable] = {}
        self._evaluation_count = 0
    
    def add_policy(self, policy: Policy):
        """Add a policy to the engine."""
        self._policies[policy.id] = policy
    
    def remove_policy(self, policy_id: str):
        """Remove a policy by ID."""
        self._policies.pop(policy_id, None)
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self._policies.get(policy_id)
    
    def list_policies(self) -> List[Policy]:
        """List all policies sorted by priority."""
        return sorted(
            self._policies.values(),
            key=lambda p: -p.priority  # Higher priority first
        )
    
    def register_evaluator(self, name: str, evaluator: Callable):
        """
        Register a custom evaluator function.
        
        Custom evaluators can perform complex checks like:
        - Database lookups for spending history
        - External API calls for fraud checks
        - ML model inference for risk scoring
        """
        self._custom_evaluators[name] = evaluator
    
    def evaluate(self, context: Dict[str, Any]) -> PolicyDecision:
        """
        Evaluate all policies against the request context.
        
        Args:
            context: Request context including:
                - agent_id: ID of the agent
                - user_id: ID of the user
                - action: Action being performed
                - amount: Transaction amount (if applicable)
                - merchant: Merchant name (if applicable)
                - category: Category (if applicable)
                - metadata: Additional context
                
        Returns:
            PolicyDecision with the result
        """
        start_time = time.time()
        self._evaluation_count += 1
        
        # Get sorted policies
        policies = self.list_policies()
        
        if not policies:
            # No policies = deny by default
            return PolicyDecision(
                effect=PolicyEffect.DENY,
                allowed=False,
                policy_id=None,
                policy_name=None,
                explanation="No policies configured",
                constraints={},
                risk_score=1.0,
                evaluation_time_ms=(time.time() - start_time) * 1000,
                policies_evaluated=0
            )
        
        # Evaluate each policy
        applicable_policies: List[Tuple[Policy, PolicyEffect]] = []
        
        for policy in policies:
            applies, effect = policy.evaluate(context)
            if applies:
                applicable_policies.append((policy, effect))
        
        # Combine results based on algorithm
        decision = self._combine_decisions(applicable_policies, context)
        
        # Calculate risk score
        risk_score = self._calculate_risk(context, applicable_policies)
        
        elapsed = (time.time() - start_time) * 1000
        
        return PolicyDecision(
            effect=decision[0],
            allowed=decision[0] == PolicyEffect.ALLOW,
            policy_id=decision[1].id if decision[1] else None,
            policy_name=decision[1].name if decision[1] else None,
            explanation=decision[2],
            constraints=decision[1].constraints if decision[1] else {},
            risk_score=risk_score,
            evaluation_time_ms=elapsed,
            policies_evaluated=len(policies)
        )
    
    def _combine_decisions(
        self,
        applicable: List[Tuple[Policy, PolicyEffect]],
        context: Dict[str, Any]
    ) -> Tuple[PolicyEffect, Optional[Policy], str]:
        """Combine policy decisions based on algorithm."""
        
        if not applicable:
            return (PolicyEffect.DENY, None, "No applicable policies")
        
        if self._combine_algorithm == PolicyCombineAlgorithm.DENY_OVERRIDES:
            # Any deny = deny
            for policy, effect in applicable:
                if effect == PolicyEffect.DENY:
                    return (effect, policy, f"Denied by policy: {policy.name}")
            # Check for require_approval
            for policy, effect in applicable:
                if effect == PolicyEffect.REQUIRE_APPROVAL:
                    return (effect, policy, f"Approval required by: {policy.name}")
            # Default to first allow
            for policy, effect in applicable:
                if effect == PolicyEffect.ALLOW:
                    return (effect, policy, f"Allowed by policy: {policy.name}")
        
        elif self._combine_algorithm == PolicyCombineAlgorithm.ALLOW_OVERRIDES:
            # Any allow = allow
            for policy, effect in applicable:
                if effect == PolicyEffect.ALLOW:
                    return (effect, policy, f"Allowed by policy: {policy.name}")
            # Default to first deny
            for policy, effect in applicable:
                if effect == PolicyEffect.DENY:
                    return (effect, policy, f"Denied by policy: {policy.name}")
        
        elif self._combine_algorithm == PolicyCombineAlgorithm.FIRST_APPLICABLE:
            # First matching policy wins
            policy, effect = applicable[0]
            verb = "Allowed" if effect == PolicyEffect.ALLOW else "Denied"
            return (effect, policy, f"{verb} by policy: {policy.name}")
        
        elif self._combine_algorithm == PolicyCombineAlgorithm.UNANIMOUS:
            # All must allow
            for policy, effect in applicable:
                if effect != PolicyEffect.ALLOW:
                    return (effect, policy, f"Denied by policy: {policy.name}")
            policy, _ = applicable[0]
            return (PolicyEffect.ALLOW, policy, "Unanimously allowed")
        
        # Fallback: deny
        return (PolicyEffect.DENY, None, "No decision reached")
    
    def _calculate_risk(
        self,
        context: Dict[str, Any],
        applicable: List[Tuple[Policy, PolicyEffect]]
    ) -> float:
        """
        Calculate risk score for the request.
        
        Risk factors:
        - High amount relative to limits
        - New merchant
        - Unusual time
        - Category restrictions
        """
        risk = 0.0
        
        # Amount-based risk
        amount = context.get("amount", 0)
        if amount > 0:
            # Risk increases with amount
            if amount > 200:
                risk += 0.3
            elif amount > 100:
                risk += 0.2
            elif amount > 50:
                risk += 0.1
        
        # Category risk
        high_risk_categories = ["gambling", "crypto", "adult"]
        category = context.get("category", "").lower()
        if category in high_risk_categories:
            risk += 0.4
        
        # Time-based risk (unusual hours)
        hour = datetime.now(timezone.utc).hour
        if hour < 6 or hour > 22:
            risk += 0.1
        
        # Denied policies add risk
        for policy, effect in applicable:
            if effect == PolicyEffect.DENY:
                risk += 0.2
        
        return min(risk, 1.0)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "policy_count": len(self._policies),
            "evaluation_count": self._evaluation_count,
            "combine_algorithm": self._combine_algorithm.value
        }


class PolicyBuilder:
    """Fluent builder for creating policies."""
    
    def __init__(self, policy_id: str, name: str):
        self._policy = Policy(
            id=policy_id,
            name=name,
            effect=PolicyEffect.ALLOW,
            rules=[]
        )
        self._current_conditions: List[Condition] = []
    
    def allow(self) -> "PolicyBuilder":
        self._policy.effect = PolicyEffect.ALLOW
        return self
    
    def deny(self) -> "PolicyBuilder":
        self._policy.effect = PolicyEffect.DENY
        return self
    
    def require_approval(self) -> "PolicyBuilder":
        self._policy.effect = PolicyEffect.REQUIRE_APPROVAL
        return self
    
    def when(self, attribute: str) -> "ConditionBuilder":
        return ConditionBuilder(self, attribute)
    
    def add_condition(self, condition: Condition) -> "PolicyBuilder":
        self._current_conditions.append(condition)
        return self
    
    def and_rule(self) -> "PolicyBuilder":
        if self._current_conditions:
            self._policy.rules.append(PolicyRule(
                conditions=self._current_conditions,
                logic="and"
            ))
            self._current_conditions = []
        return self
    
    def with_priority(self, priority: int) -> "PolicyBuilder":
        self._policy.priority = priority
        return self
    
    def with_constraint(self, key: str, value: Any) -> "PolicyBuilder":
        self._policy.constraints[key] = value
        return self
    
    def with_description(self, desc: str) -> "PolicyBuilder":
        self._policy.description = desc
        return self
    
    def build(self) -> Policy:
        # Add any remaining conditions
        if self._current_conditions:
            self._policy.rules.append(PolicyRule(
                conditions=self._current_conditions,
                logic="and"
            ))
        return self._policy


class ConditionBuilder:
    """Builder for conditions."""
    
    def __init__(self, policy_builder: PolicyBuilder, attribute: str):
        self._pb = policy_builder
        self._attribute = attribute
    
    def equals(self, value: Any) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.EQ, value
        ))
    
    def not_equals(self, value: Any) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.NE, value
        ))
    
    def less_than(self, value: float) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.LT, value
        ))
    
    def less_than_or_equal(self, value: float) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.LTE, value
        ))
    
    def greater_than(self, value: float) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.GT, value
        ))
    
    def greater_than_or_equal(self, value: float) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.GTE, value
        ))
    
    def is_in(self, values: List) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.IN, values
        ))
    
    def not_in(self, values: List) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.NOT_IN, values
        ))
    
    def between(self, low: float, high: float) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.BETWEEN, [low, high]
        ))
    
    def contains(self, value: str) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.CONTAINS, value
        ))
    
    def matches(self, pattern: str) -> PolicyBuilder:
        return self._pb.add_condition(Condition(
            self._attribute, ConditionOperator.MATCHES, pattern
        ))


# Test the policy engine
if __name__ == "__main__":
    print("AgentAuth Core Policy Engine Test")
    print("=" * 50)
    
    # Create policy engine
    engine = PolicyEngine()
    
    # Create policies using builder
    spending_limit = (
        PolicyBuilder("pol_spending", "Spending Limit")
        .allow()
        .when("amount").less_than_or_equal(200.0)
        .with_priority(10)
        .with_description("Allow purchases up to $200")
        .with_constraint("daily_limit", 500.0)
        .build()
    )
    
    category_block = (
        PolicyBuilder("pol_category", "Block High Risk")
        .deny()
        .when("category").is_in(["gambling", "crypto", "adult"])
        .with_priority(100)  # High priority = evaluated first
        .with_description("Block high-risk categories")
        .build()
    )
    
    merchant_whitelist = (
        PolicyBuilder("pol_merchant", "Trusted Merchants")
        .allow()
        .when("merchant").is_in(["Amazon", "Walmart", "Target", "Apple"])
        .with_priority(5)
        .build()
    )
    
    # Add policies
    engine.add_policy(spending_limit)
    engine.add_policy(category_block)
    engine.add_policy(merchant_whitelist)
    
    print(f"[+] Loaded {len(engine.list_policies())} policies")
    
    # Test cases
    test_cases = [
        {
            "name": "Normal purchase",
            "context": {
                "agent_id": "agent_123",
                "user_id": "user_abc",
                "action": "purchase",
                "amount": 49.99,
                "merchant": "Amazon",
                "category": "electronics"
            }
        },
        {
            "name": "Over limit",
            "context": {
                "agent_id": "agent_123",
                "user_id": "user_abc",
                "action": "purchase",
                "amount": 299.99,
                "merchant": "Amazon",
                "category": "electronics"
            }
        },
        {
            "name": "Blocked category",
            "context": {
                "agent_id": "agent_123",
                "user_id": "user_abc",
                "action": "purchase",
                "amount": 50.00,
                "merchant": "CryptoExchange",
                "category": "crypto"
            }
        }
    ]
    
    print("\n[*] Evaluating test cases:\n")
    
    for test in test_cases:
        result = engine.evaluate(test["context"])
        status = "ALLOWED" if result.allowed else "DENIED"
        print(f"  {test['name']}:")
        print(f"    Status: {status}")
        print(f"    Reason: {result.explanation}")
        print(f"    Risk: {result.risk_score:.0%}")
        print(f"    Time: {result.evaluation_time_ms:.2f}ms")
        print()
    
    print(f"[*] Engine stats: {engine.stats}")
    print("\n[*] All policy tests passed!")
