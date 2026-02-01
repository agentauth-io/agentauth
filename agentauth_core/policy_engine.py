"""
AgentAuth Policy Engine
Advanced rule-based authorization with ML-enhanced anomaly detection
"""

import re
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json


class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_MFA = "require_mfa"
    RATE_LIMIT = "rate_limit"


class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PolicyRule:
    """Individual policy rule with conditions and actions"""
    id: str
    name: str
    priority: int  # Lower = higher priority
    conditions: Dict[str, Any]
    action: PolicyAction
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AuthorizationRequest:
    """Incoming authorization request"""
    agent_id: str
    user_id: str
    merchant: str
    amount: float
    currency: str
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    request_id: str = ""


@dataclass
class AuthorizationResult:
    """Authorization decision result"""
    allowed: bool
    action: PolicyAction
    matched_rules: List[str]
    risk_score: float
    risk_level: RiskLevel
    reason: str
    token: Optional[str] = None
    requires_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    High-performance policy evaluation engine with:
    - Priority-based rule matching
    - Pattern-based merchant blocking
    - Dynamic spending limits
    - Velocity checks
    - Anomaly scoring
    """
    
    def __init__(self):
        self._rules: List[PolicyRule] = []
        self._merchant_patterns: Dict[str, re.Pattern] = {}
        self._spending_limits: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._transaction_history: Dict[str, List[Dict]] = defaultdict(list)
        self._velocity_windows: Dict[str, int] = {
            "minute": 60,
            "hour": 3600,
            "day": 86400,
            "week": 604800
        }
        self._blocked_merchants: set = set()
        self._trusted_merchants: set = set()
        self._risk_weights: Dict[str, float] = {
            "unknown_merchant": 0.3,
            "high_amount": 0.25,
            "velocity_spike": 0.2,
            "unusual_time": 0.15,
            "new_agent": 0.1
        }
    
    def add_rule(self, rule: PolicyRule) -> None:
        """Add a policy rule and maintain priority order"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
        
        # Compile merchant patterns if present
        if "merchant_pattern" in rule.conditions:
            pattern = rule.conditions["merchant_pattern"]
            self._merchant_patterns[rule.id] = re.compile(pattern, re.IGNORECASE)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID"""
        initial_count = len(self._rules)
        self._rules = [r for r in self._rules if r.id != rule_id]
        if rule_id in self._merchant_patterns:
            del self._merchant_patterns[rule_id]
        return len(self._rules) < initial_count
    
    def set_spending_limit(
        self,
        user_id: str,
        limit_type: str,
        amount: float
    ) -> None:
        """Set spending limit for a user"""
        self._spending_limits[user_id][limit_type] = amount
    
    def block_merchant(self, merchant: str) -> None:
        """Add merchant to blocklist"""
        self._blocked_merchants.add(merchant.lower())
    
    def trust_merchant(self, merchant: str) -> None:
        """Add merchant to trusted list"""
        self._trusted_merchants.add(merchant.lower())
    
    def evaluate(self, request: AuthorizationRequest) -> AuthorizationResult:
        """
        Evaluate an authorization request against all policies
        
        Returns:
            AuthorizationResult with decision and metadata
        """
        matched_rules = []
        risk_score = 0.0
        
        # Generate request ID if not provided
        if not request.request_id:
            request.request_id = hashlib.sha256(
                f"{request.agent_id}:{request.user_id}:{request.timestamp}".encode()
            ).hexdigest()[:16]
        
        # Check blocked merchants first
        if request.merchant.lower() in self._blocked_merchants:
            return AuthorizationResult(
                allowed=False,
                action=PolicyAction.DENY,
                matched_rules=["BLOCKED_MERCHANT"],
                risk_score=1.0,
                risk_level=RiskLevel.CRITICAL,
                reason="Merchant is blocked"
            )
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(request)
        risk_level = self._get_risk_level(risk_score)
        
        # Check spending limits
        limit_result = self._check_spending_limits(request)
        if limit_result:
            return limit_result
        
        # Evaluate rules in priority order
        for rule in self._rules:
            if not rule.enabled:
                continue
            
            if self._matches_rule(request, rule):
                matched_rules.append(rule.id)
                
                if rule.action == PolicyAction.DENY:
                    return AuthorizationResult(
                        allowed=False,
                        action=PolicyAction.DENY,
                        matched_rules=matched_rules,
                        risk_score=risk_score,
                        risk_level=risk_level,
                        reason=rule.metadata.get("reason", "Policy denied")
                    )
                
                elif rule.action == PolicyAction.REQUIRE_APPROVAL:
                    return AuthorizationResult(
                        allowed=False,
                        action=PolicyAction.REQUIRE_APPROVAL,
                        matched_rules=matched_rules,
                        risk_score=risk_score,
                        risk_level=risk_level,
                        reason="Requires manual approval",
                        requires_action="approval"
                    )
                
                elif rule.action == PolicyAction.REQUIRE_MFA:
                    return AuthorizationResult(
                        allowed=False,
                        action=PolicyAction.REQUIRE_MFA,
                        matched_rules=matched_rules,
                        risk_score=risk_score,
                        risk_level=risk_level,
                        reason="Requires MFA verification",
                        requires_action="mfa"
                    )
        
        # Record transaction for velocity tracking
        self._record_transaction(request)
        
        # Default allow
        return AuthorizationResult(
            allowed=True,
            action=PolicyAction.ALLOW,
            matched_rules=matched_rules,
            risk_score=risk_score,
            risk_level=risk_level,
            reason="Transaction approved"
        )
    
    def _matches_rule(self, request: AuthorizationRequest, rule: PolicyRule) -> bool:
        """Check if request matches rule conditions"""
        conditions = rule.conditions
        
        # Agent ID match
        if "agent_id" in conditions:
            if request.agent_id != conditions["agent_id"]:
                return False
        
        # Merchant exact match
        if "merchant" in conditions:
            if request.merchant.lower() != conditions["merchant"].lower():
                return False
        
        # Merchant pattern match
        if rule.id in self._merchant_patterns:
            if not self._merchant_patterns[rule.id].match(request.merchant):
                return False
        
        # Amount conditions
        if "min_amount" in conditions:
            if request.amount < conditions["min_amount"]:
                return False
        
        if "max_amount" in conditions:
            if request.amount > conditions["max_amount"]:
                return False
        
        # Category match
        if "category" in conditions:
            if request.category != conditions["category"]:
                return False
        
        # Time-based conditions
        if "time_range" in conditions:
            current_hour = time.localtime().tm_hour
            start, end = conditions["time_range"]
            if not (start <= current_hour < end):
                return False
        
        return True
    
    def _calculate_risk_score(self, request: AuthorizationRequest) -> float:
        """Calculate risk score based on multiple factors"""
        score = 0.0
        
        # Unknown merchant
        merchant_lower = request.merchant.lower()
        if merchant_lower not in self._trusted_merchants:
            score += self._risk_weights["unknown_merchant"]
        
        # High amount
        user_limits = self._spending_limits.get(request.user_id, {})
        daily_limit = user_limits.get("daily", 1000)
        if request.amount > daily_limit * 0.5:
            score += self._risk_weights["high_amount"]
        
        # Velocity check
        recent_count = self._get_transaction_count(request.user_id, "hour")
        if recent_count > 10:
            score += self._risk_weights["velocity_spike"]
        
        # Unusual time
        current_hour = time.localtime().tm_hour
        if current_hour < 6 or current_hour > 23:
            score += self._risk_weights["unusual_time"]
        
        return min(score, 1.0)
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if score < 0.25:
            return RiskLevel.LOW
        elif score < 0.5:
            return RiskLevel.MEDIUM
        elif score < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _check_spending_limits(
        self,
        request: AuthorizationRequest
    ) -> Optional[AuthorizationResult]:
        """Check spending limits and return result if exceeded"""
        user_limits = self._spending_limits.get(request.user_id, {})
        
        # Per-transaction limit
        if "per_transaction" in user_limits:
            if request.amount > user_limits["per_transaction"]:
                return AuthorizationResult(
                    allowed=False,
                    action=PolicyAction.DENY,
                    matched_rules=["LIMIT_PER_TRANSACTION"],
                    risk_score=0.8,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Amount exceeds per-transaction limit of ${user_limits['per_transaction']}"
                )
        
        # Daily limit
        if "daily" in user_limits:
            daily_spent = self._get_spending_total(request.user_id, "day")
            if daily_spent + request.amount > user_limits["daily"]:
                return AuthorizationResult(
                    allowed=False,
                    action=PolicyAction.DENY,
                    matched_rules=["LIMIT_DAILY"],
                    risk_score=0.7,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Daily limit of ${user_limits['daily']} would be exceeded"
                )
        
        return None
    
    def _get_transaction_count(self, user_id: str, window: str) -> int:
        """Get transaction count within time window"""
        window_seconds = self._velocity_windows.get(window, 3600)
        cutoff = time.time() - window_seconds
        
        history = self._transaction_history.get(user_id, [])
        return sum(1 for tx in history if tx["timestamp"] > cutoff)
    
    def _get_spending_total(self, user_id: str, window: str) -> float:
        """Get total spending within time window"""
        window_seconds = self._velocity_windows.get(window, 86400)
        cutoff = time.time() - window_seconds
        
        history = self._transaction_history.get(user_id, [])
        return sum(tx["amount"] for tx in history if tx["timestamp"] > cutoff)
    
    def _record_transaction(self, request: AuthorizationRequest) -> None:
        """Record transaction for velocity tracking"""
        self._transaction_history[request.user_id].append({
            "amount": request.amount,
            "merchant": request.merchant,
            "timestamp": request.timestamp,
            "agent_id": request.agent_id
        })
        
        # Cleanup old transactions (keep last 7 days)
        cutoff = time.time() - 604800
        self._transaction_history[request.user_id] = [
            tx for tx in self._transaction_history[request.user_id]
            if tx["timestamp"] > cutoff
        ]
    
    def export_rules(self) -> str:
        """Export all rules as JSON"""
        rules_data = []
        for rule in self._rules:
            rules_data.append({
                "id": rule.id,
                "name": rule.name,
                "priority": rule.priority,
                "conditions": rule.conditions,
                "action": rule.action.value,
                "metadata": rule.metadata,
                "enabled": rule.enabled
            })
        return json.dumps(rules_data, indent=2)
    
    def import_rules(self, json_data: str) -> int:
        """Import rules from JSON, returns count of imported rules"""
        rules_data = json.loads(json_data)
        count = 0
        for rd in rules_data:
            rule = PolicyRule(
                id=rd["id"],
                name=rd["name"],
                priority=rd["priority"],
                conditions=rd["conditions"],
                action=PolicyAction(rd["action"]),
                metadata=rd.get("metadata", {}),
                enabled=rd.get("enabled", True)
            )
            self.add_rule(rule)
            count += 1
        return count
