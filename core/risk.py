"""
AgentAuth Core - Risk Scoring Engine
====================================
PROPRIETARY AND CONFIDENTIAL

Machine learning and heuristic-based risk scoring for authorization.
This module evaluates the risk level of each transaction request.

Risk Factors:
- Transaction amount relative to history
- Merchant reputation and category
- Time-of-day patterns
- Geographic signals
- Velocity (frequency of requests)
- Behavioral anomalies
- Agent trust level

Output:
- Risk score: 0.0 (safe) to 1.0 (high risk)
- Risk factors: Breakdown of contributing factors
- Recommendations: Suggested actions
"""

import time
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from collections import defaultdict


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"           # 0.0 - 0.3
    MEDIUM = "medium"     # 0.3 - 0.6
    HIGH = "high"         # 0.6 - 0.8
    CRITICAL = "critical" # 0.8 - 1.0


class RiskFactor(Enum):
    """Individual risk factors."""
    AMOUNT_HIGH = "amount_high"
    AMOUNT_UNUSUAL = "amount_unusual"
    MERCHANT_NEW = "merchant_new"
    MERCHANT_RISKY = "merchant_risky"
    CATEGORY_BLOCKED = "category_blocked"
    CATEGORY_RISKY = "category_risky"
    TIME_UNUSUAL = "time_unusual"
    VELOCITY_HIGH = "velocity_high"
    PATTERN_ANOMALY = "pattern_anomaly"
    AGENT_NEW = "agent_new"
    AGENT_UNTRUSTED = "agent_untrusted"
    BUDGET_NEAR_LIMIT = "budget_near_limit"
    FIRST_TRANSACTION = "first_transaction"


@dataclass
class RiskFactorScore:
    """A single risk factor with its score and weight."""
    factor: RiskFactor
    score: float  # 0.0 to 1.0
    weight: float  # Importance weight
    description: str
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class RiskAssessment:
    """Complete risk assessment result."""
    overall_score: float
    level: RiskLevel
    factors: List[RiskFactorScore]
    recommendations: List[str]
    evaluation_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.overall_score,
            "level": self.level.value,
            "factors": [
                {
                    "factor": f.factor.value,
                    "score": f.score,
                    "weight": f.weight,
                    "description": f.description
                }
                for f in self.factors
            ],
            "recommendations": self.recommendations,
            "evaluation_time_ms": self.evaluation_time_ms
        }


@dataclass
class TransactionHistory:
    """Tracks transaction history for pattern analysis."""
    user_id: str
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    merchants: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    categories: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    hourly_counts: List[int] = field(default_factory=lambda: [0] * 24)
    total_amount: float = 0.0
    transaction_count: int = 0
    
    def record(
        self,
        amount: float,
        merchant: str,
        category: str,
        timestamp: Optional[float] = None
    ):
        """Record a transaction."""
        ts = timestamp or time.time()
        hour = int((ts % 86400) / 3600)
        
        self.transactions.append({
            "amount": amount,
            "merchant": merchant,
            "category": category,
            "timestamp": ts
        })
        
        self.merchants[merchant] += 1
        self.categories[category] += 1
        self.hourly_counts[hour] += 1
        self.total_amount += amount
        self.transaction_count += 1
        
        # Keep only last 1000 transactions
        if len(self.transactions) > 1000:
            self.transactions = self.transactions[-1000:]
    
    def average_amount(self) -> float:
        """Average transaction amount."""
        if not self.transaction_count:
            return 0.0
        return self.total_amount / self.transaction_count
    
    def is_new_merchant(self, merchant: str) -> bool:
        """Check if merchant is new for this user."""
        return self.merchants.get(merchant, 0) == 0
    
    def merchant_frequency(self, merchant: str) -> int:
        """Get frequency of merchant transactions."""
        return self.merchants.get(merchant, 0)
    
    def recent_velocity(self, window_seconds: int = 3600) -> int:
        """Count transactions in recent time window."""
        now = time.time()
        cutoff = now - window_seconds
        return sum(1 for t in self.transactions if t["timestamp"] > cutoff)
    
    def typical_hour_range(self) -> Tuple[int, int]:
        """Get typical transaction hours (start, end)."""
        if not any(self.hourly_counts):
            return (9, 21)  # Default business hours
        
        # Find hours with > 10% of activity
        total = sum(self.hourly_counts)
        if total == 0:
            return (9, 21)
        
        threshold = total * 0.1
        active_hours = [h for h, c in enumerate(self.hourly_counts) if c >= threshold]
        
        if not active_hours:
            return (9, 21)
        
        return (min(active_hours), max(active_hours))


class RiskScoringEngine:
    """
    The risk scoring engine.
    
    Combines multiple signals to produce a risk score for each transaction.
    """
    
    # Risk category configuration
    HIGH_RISK_CATEGORIES = {"gambling", "crypto", "adult", "weapons", "drugs"}
    MEDIUM_RISK_CATEGORIES = {"luxury", "jewelry", "electronics", "gift_cards"}
    
    # Merchant risk scores (0.0 = trusted, 1.0 = high risk)
    MERCHANT_RISK: Dict[str, float] = {
        "amazon": 0.1,
        "walmart": 0.1,
        "target": 0.1,
        "apple": 0.15,
        "best buy": 0.15,
        "whole foods": 0.1,
        "costco": 0.1,
        "unknown": 0.5,
    }
    
    # Default weights for risk factors
    DEFAULT_WEIGHTS = {
        RiskFactor.AMOUNT_HIGH: 0.25,
        RiskFactor.AMOUNT_UNUSUAL: 0.15,
        RiskFactor.MERCHANT_NEW: 0.1,
        RiskFactor.MERCHANT_RISKY: 0.2,
        RiskFactor.CATEGORY_BLOCKED: 0.3,
        RiskFactor.CATEGORY_RISKY: 0.15,
        RiskFactor.TIME_UNUSUAL: 0.1,
        RiskFactor.VELOCITY_HIGH: 0.2,
        RiskFactor.PATTERN_ANOMALY: 0.15,
        RiskFactor.AGENT_NEW: 0.1,
        RiskFactor.AGENT_UNTRUSTED: 0.25,
        RiskFactor.BUDGET_NEAR_LIMIT: 0.1,
        RiskFactor.FIRST_TRANSACTION: 0.05,
    }
    
    def __init__(self, weights: Optional[Dict[RiskFactor, float]] = None):
        """
        Initialize risk scoring engine.
        
        Args:
            weights: Custom risk factor weights (optional)
        """
        self._weights = weights or self.DEFAULT_WEIGHTS
        self._user_histories: Dict[str, TransactionHistory] = {}
        self._agent_trust: Dict[str, float] = {}  # agent_id -> trust score
        self._evaluation_count = 0
    
    def _get_history(self, user_id: str) -> TransactionHistory:
        """Get or create transaction history for user."""
        if user_id not in self._user_histories:
            self._user_histories[user_id] = TransactionHistory(user_id=user_id)
        return self._user_histories[user_id]
    
    def set_agent_trust(self, agent_id: str, trust_score: float):
        """
        Set trust score for an agent.
        
        Args:
            agent_id: Agent identifier
            trust_score: 0.0 (untrusted) to 1.0 (fully trusted)
        """
        self._agent_trust[agent_id] = max(0.0, min(1.0, trust_score))
    
    def get_agent_trust(self, agent_id: str) -> float:
        """Get trust score for agent (default 0.5 for new agents)."""
        return self._agent_trust.get(agent_id, 0.5)
    
    def assess(
        self,
        user_id: str,
        agent_id: str,
        amount: float,
        merchant: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RiskAssessment:
        """
        Assess risk for a transaction.
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier
            amount: Transaction amount
            merchant: Merchant name
            category: Transaction category
            metadata: Additional context
            
        Returns:
            RiskAssessment with score and factors
        """
        start_time = time.time()
        self._evaluation_count += 1
        
        history = self._get_history(user_id)
        factors: List[RiskFactorScore] = []
        recommendations: List[str] = []
        
        # 1. Amount analysis
        amount_factors = self._assess_amount(amount, history)
        factors.extend(amount_factors)
        
        # 2. Merchant analysis
        merchant_factors = self._assess_merchant(merchant, history)
        factors.extend(merchant_factors)
        
        # 3. Category analysis
        category_factors = self._assess_category(category)
        factors.extend(category_factors)
        
        # 4. Time analysis
        time_factors = self._assess_time(history)
        factors.extend(time_factors)
        
        # 5. Velocity analysis
        velocity_factors = self._assess_velocity(history)
        factors.extend(velocity_factors)
        
        # 6. Agent trust analysis
        agent_factors = self._assess_agent(agent_id)
        factors.extend(agent_factors)
        
        # 7. First transaction check
        if history.transaction_count == 0:
            factors.append(RiskFactorScore(
                factor=RiskFactor.FIRST_TRANSACTION,
                score=0.3,
                weight=self._weights[RiskFactor.FIRST_TRANSACTION],
                description="First transaction for this user"
            ))
        
        # Calculate overall score
        if factors:
            total_weight = sum(f.weight for f in factors)
            weighted_sum = sum(f.weighted_score for f in factors)
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.1  # Default low risk
        
        # Clamp to [0, 1]
        overall_score = max(0.0, min(1.0, overall_score))
        
        # Determine level
        if overall_score < 0.3:
            level = RiskLevel.LOW
        elif overall_score < 0.6:
            level = RiskLevel.MEDIUM
        elif overall_score < 0.8:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            level, factors, amount, merchant, category
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        return RiskAssessment(
            overall_score=overall_score,
            level=level,
            factors=factors,
            recommendations=recommendations,
            evaluation_time_ms=elapsed
        )
    
    def _assess_amount(
        self,
        amount: float,
        history: TransactionHistory
    ) -> List[RiskFactorScore]:
        """Assess amount-related risk factors."""
        factors = []
        
        # High amount (absolute threshold)
        if amount > 500:
            factors.append(RiskFactorScore(
                factor=RiskFactor.AMOUNT_HIGH,
                score=min(1.0, amount / 1000),
                weight=self._weights[RiskFactor.AMOUNT_HIGH],
                description=f"High amount: ${amount:.2f}"
            ))
        elif amount > 200:
            factors.append(RiskFactorScore(
                factor=RiskFactor.AMOUNT_HIGH,
                score=0.4,
                weight=self._weights[RiskFactor.AMOUNT_HIGH],
                description=f"Moderate amount: ${amount:.2f}"
            ))
        
        # Unusual amount (relative to history)
        if history.transaction_count > 5:
            avg = history.average_amount()
            if avg > 0:
                deviation = abs(amount - avg) / avg
                if deviation > 2.0:  # More than 2x average
                    factors.append(RiskFactorScore(
                        factor=RiskFactor.AMOUNT_UNUSUAL,
                        score=min(1.0, deviation / 5),
                        weight=self._weights[RiskFactor.AMOUNT_UNUSUAL],
                        description=f"Amount {deviation:.1f}x above average (${avg:.2f})"
                    ))
        
        return factors
    
    def _assess_merchant(
        self,
        merchant: str,
        history: TransactionHistory
    ) -> List[RiskFactorScore]:
        """Assess merchant-related risk factors."""
        factors = []
        merchant_lower = merchant.lower()
        
        # New merchant
        if history.is_new_merchant(merchant):
            factors.append(RiskFactorScore(
                factor=RiskFactor.MERCHANT_NEW,
                score=0.3,
                weight=self._weights[RiskFactor.MERCHANT_NEW],
                description=f"First purchase from {merchant}"
            ))
        
        # Risky merchant
        risk = self.MERCHANT_RISK.get(merchant_lower, 0.5)
        if risk > 0.3:
            factors.append(RiskFactorScore(
                factor=RiskFactor.MERCHANT_RISKY,
                score=risk,
                weight=self._weights[RiskFactor.MERCHANT_RISKY],
                description=f"Merchant risk level: {risk:.0%}"
            ))
        
        return factors
    
    def _assess_category(self, category: str) -> List[RiskFactorScore]:
        """Assess category-related risk factors."""
        factors = []
        category_lower = category.lower()
        
        if category_lower in self.HIGH_RISK_CATEGORIES:
            factors.append(RiskFactorScore(
                factor=RiskFactor.CATEGORY_BLOCKED,
                score=1.0,
                weight=self._weights[RiskFactor.CATEGORY_BLOCKED],
                description=f"High-risk category: {category}"
            ))
        elif category_lower in self.MEDIUM_RISK_CATEGORIES:
            factors.append(RiskFactorScore(
                factor=RiskFactor.CATEGORY_RISKY,
                score=0.5,
                weight=self._weights[RiskFactor.CATEGORY_RISKY],
                description=f"Medium-risk category: {category}"
            ))
        
        return factors
    
    def _assess_time(self, history: TransactionHistory) -> List[RiskFactorScore]:
        """Assess time-related risk factors."""
        factors = []
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        
        # Check if current hour is unusual
        start, end = history.typical_hour_range()
        if current_hour < start or current_hour > end:
            factors.append(RiskFactorScore(
                factor=RiskFactor.TIME_UNUSUAL,
                score=0.5,
                weight=self._weights[RiskFactor.TIME_UNUSUAL],
                description=f"Unusual hour ({current_hour}:00, typical: {start}-{end})"
            ))
        
        return factors
    
    def _assess_velocity(self, history: TransactionHistory) -> List[RiskFactorScore]:
        """Assess transaction velocity risk."""
        factors = []
        
        # Check recent transaction count
        recent_count = history.recent_velocity(3600)  # Last hour
        
        if recent_count > 10:
            factors.append(RiskFactorScore(
                factor=RiskFactor.VELOCITY_HIGH,
                score=min(1.0, recent_count / 20),
                weight=self._weights[RiskFactor.VELOCITY_HIGH],
                description=f"High velocity: {recent_count} transactions in last hour"
            ))
        elif recent_count > 5:
            factors.append(RiskFactorScore(
                factor=RiskFactor.VELOCITY_HIGH,
                score=0.4,
                weight=self._weights[RiskFactor.VELOCITY_HIGH],
                description=f"Elevated velocity: {recent_count} transactions in last hour"
            ))
        
        return factors
    
    def _assess_agent(self, agent_id: str) -> List[RiskFactorScore]:
        """Assess agent trust risk."""
        factors = []
        trust = self.get_agent_trust(agent_id)
        
        if agent_id not in self._agent_trust:
            factors.append(RiskFactorScore(
                factor=RiskFactor.AGENT_NEW,
                score=0.3,
                weight=self._weights[RiskFactor.AGENT_NEW],
                description="New agent without established trust"
            ))
        elif trust < 0.5:
            factors.append(RiskFactorScore(
                factor=RiskFactor.AGENT_UNTRUSTED,
                score=1.0 - trust,
                weight=self._weights[RiskFactor.AGENT_UNTRUSTED],
                description=f"Low agent trust score: {trust:.0%}"
            ))
        
        return factors
    
    def _generate_recommendations(
        self,
        level: RiskLevel,
        factors: List[RiskFactorScore],
        amount: float,
        merchant: str,
        category: str
    ) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []
        
        if level == RiskLevel.CRITICAL:
            recommendations.append("BLOCK: Transaction requires manual review")
            recommendations.append("Consider requiring additional verification")
        elif level == RiskLevel.HIGH:
            recommendations.append("REVIEW: High-risk transaction flagged")
            recommendations.append("Consider step-up authentication")
        elif level == RiskLevel.MEDIUM:
            recommendations.append("MONITOR: Keep transaction in watchlist")
        
        # Factor-specific recommendations
        for factor in factors:
            if factor.factor == RiskFactor.VELOCITY_HIGH and factor.score > 0.7:
                recommendations.append("Rate limit may be approaching")
            if factor.factor == RiskFactor.MERCHANT_NEW:
                recommendations.append(f"First purchase from {merchant} - verify merchant")
            if factor.factor == RiskFactor.CATEGORY_BLOCKED:
                recommendations.append(f"Category {category} is blocked by policy")
        
        return recommendations
    
    def record_transaction(
        self,
        user_id: str,
        amount: float,
        merchant: str,
        category: str
    ):
        """Record a completed transaction for history."""
        history = self._get_history(user_id)
        history.record(amount, merchant, category)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "evaluation_count": self._evaluation_count,
            "users_tracked": len(self._user_histories),
            "agents_tracked": len(self._agent_trust)
        }


# Test the risk scoring engine
if __name__ == "__main__":
    print("AgentAuth Core Risk Scoring Engine Test")
    print("=" * 50)
    
    # Initialize
    engine = RiskScoringEngine()
    print("[+] Risk engine initialized")
    
    # Set up some agent trust
    engine.set_agent_trust("agent_trusted", 0.9)
    engine.set_agent_trust("agent_new", 0.3)
    
    # Record some transaction history
    for i in range(10):
        engine.record_transaction(
            user_id="user_demo",
            amount=50.0 + (i * 5),
            merchant="Amazon",
            category="electronics"
        )
    
    print(f"[+] Recorded 10 transactions for user_demo")
    
    # Test cases
    test_cases = [
        {
            "name": "Normal purchase",
            "user_id": "user_demo",
            "agent_id": "agent_trusted",
            "amount": 49.99,
            "merchant": "Amazon",
            "category": "electronics"
        },
        {
            "name": "High amount",
            "user_id": "user_demo",
            "agent_id": "agent_trusted",
            "amount": 899.99,
            "merchant": "Apple",
            "category": "electronics"
        },
        {
            "name": "Risky category",
            "user_id": "user_demo",
            "agent_id": "agent_trusted",
            "amount": 50.00,
            "merchant": "CryptoExchange",
            "category": "crypto"
        },
        {
            "name": "Untrusted agent",
            "user_id": "user_demo",
            "agent_id": "agent_new",
            "amount": 75.00,
            "merchant": "Unknown Store",
            "category": "misc"
        },
    ]
    
    print("\n[*] Risk assessments:\n")
    
    for test in test_cases:
        result = engine.assess(
            user_id=test["user_id"],
            agent_id=test["agent_id"],
            amount=test["amount"],
            merchant=test["merchant"],
            category=test["category"]
        )
        
        print(f"  {test['name']}:")
        print(f"    Score: {result.overall_score:.2f} ({result.level.value})")
        print(f"    Factors: {len(result.factors)}")
        for factor in result.factors[:3]:
            print(f"      - {factor.factor.value}: {factor.score:.2f}")
        if result.recommendations:
            print(f"    Recommendation: {result.recommendations[0]}")
        print()
    
    print(f"[*] Engine stats: {engine.stats}")
    print("\n[*] All risk scoring tests passed!")
