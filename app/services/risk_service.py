"""
Risk Service - Unified Risk Orchestration

Integrates fraud detection, anomaly detection, and risk scoring
into the authorization flow for real-time risk assessment.
"""
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.ml.anomaly_detection import AnomalyResult, get_anomaly_service
from app.ml.fraud_model import FraudPrediction, get_fraud_service

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Overall risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskDecision(Enum):
    """Risk-based authorization decision."""
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"  # Requires manual review


@dataclass
class RiskAssessment:
    """
    Complete risk assessment result combining all risk signals.
    """
    # Overall assessment
    risk_level: RiskLevel
    risk_score: float  # 0.0 - 1.0
    decision: RiskDecision
    
    # Individual components
    fraud_prediction: FraudPrediction | None = None
    anomaly_result: AnomalyResult | None = None
    
    # Detailed breakdown
    factors: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    
    # Metadata
    assessment_time_ms: float = 0.0
    cache_hit: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "risk_level": self.risk_level.value,
            "risk_score": round(self.risk_score, 4),
            "decision": self.decision.value,
            "factors": self.factors,
            "recommendations": self.recommendations,
            "assessment_time_ms": round(self.assessment_time_ms, 2),
            "cache_hit": self.cache_hit,
        }
        
        if self.fraud_prediction:
            result["fraud_detection"] = {
                "is_fraud": self.fraud_prediction.is_fraud,
                "fraud_score": round(self.fraud_prediction.fraud_score, 4),
                "risk_level": self.fraud_prediction.risk_level,
                "top_risk_factors": self.fraud_prediction.top_risk_factors,
            }
        
        if self.anomaly_result:
            result["anomaly_detection"] = {
                "is_anomaly": self.anomaly_result.is_anomaly,
                "anomaly_score": round(self.anomaly_result.anomaly_score, 4),
                "method": self.anomaly_result.method,
            }
        
        return result


# Risk thresholds configuration
RISK_THRESHOLDS = {
    "fraud_threshold": 0.5,        # Block if fraud score >= 0.5
    "anomaly_threshold": 0.6,       # Block if anomaly score >= 0.6
    "combined_block": 0.7,          # Block if combined risk >= 0.7
    "review_threshold": 0.4,       # Review if combined risk >= 0.4
}


class RiskService:
    """
    Unified Risk Orchestration Service
    
    Combines multiple risk signals:
    1. Fraud detection model
    2. Anomaly detection
    3. Rule-based heuristics
    
    Target: <100ms total assessment time
    """

    # In-memory cache for risk assessments (per session)
    _risk_cache: dict[str, tuple[RiskAssessment, float]] = {}
    CACHE_TTL_SECONDS = 60  # 1 minute cache

    def __init__(self, thresholds: dict[str, float] | None = None):
        self.thresholds = thresholds or RISK_THRESHOLDS
        
        # Initialize ML services
        self._fraud_service = None
        self._anomaly_service = None
        
        # Statistics
        self._stats = {
            "total_assessments": 0,
            "blocks": 0,
            "reviews": 0,
            "allows": 0,
            "cache_hits": 0,
        }

    def _get_fraud_service(self):
        """Lazy load fraud detection service."""
        if self._fraud_service is None:
            self._fraud_service = get_fraud_service()
        return self._fraud_service

    def _get_anomaly_service(self):
        """Lazy load anomaly detection service."""
        if self._anomaly_service is None:
            self._anomaly_service = get_anomaly_service()
        return self._anomaly_service

    def _get_cache_key(
        self,
        user_id: str,
        amount: float,
        merchant_id: str,
    ) -> str:
        """Generate cache key for risk assessment."""
        return f"{user_id}:{amount}:{merchant_id}"

    def _get_cached_assessment(self, cache_key: str) -> RiskAssessment | None:
        """Get cached risk assessment if not expired."""
        if cache_key in self._risk_cache:
            assessment, cached_at = self._risk_cache[cache_key]
            age = time.time() - cached_at
            if age < self.CACHE_TTL_SECONDS:
                self._stats["cache_hits"] += 1
                assessment.cache_hit = True
                return assessment
            else:
                del self._risk_cache[cache_key]
        return None

    def _cache_assessment(self, cache_key: str, assessment: RiskAssessment):
        """Cache risk assessment."""
        self._risk_cache[cache_key] = (assessment, time.time())
        
        # Limit cache size
        if len(self._risk_cache) > 10000:
            oldest_keys = sorted(
                self._risk_cache.keys(),
                key=lambda k: self._risk_cache[k][1]
            )[:5000]
            for key in oldest_keys:
                del self._risk_cache[key]

    async def assess(
        self,
        user_id: str,
        amount: float,
        merchant_id: str,
        category_code: str = "",
        country: str = "",
        consent_max_amount: float | None = None,
        transaction_history: list[dict] | None = None,
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment.
        
        Args:
            user_id: User identifier
            amount: Transaction amount
            merchant_id: Merchant identifier
            category_code: Merchant category code
            country: Transaction country
            consent_max_amount: Maximum amount allowed by consent
            transaction_history: Recent transaction history (optional)
            
        Returns:
            RiskAssessment with decision and details
        """
        start_time = time.time()
        self._stats["total_assessments"] += 1
        
        # Check cache
        cache_key = self._get_cache_key(user_id, amount, merchant_id)
        cached = self._get_cached_assessment(cache_key)
        if cached:
            return cached
        
        fraud_prediction: FraudPrediction | None = None
        anomaly_result: AnomalyResult | None = None
        factors: dict[str, Any] = {}
        
        # 1. Run fraud detection model
        try:
            fraud_service = self._get_fraud_service()
            fraud_prediction = await fraud_service.detect_fraud(
                user_id=user_id,
                amount=amount,
                merchant_id=merchant_id,
                category_code=category_code,
                country=country,
            )
            factors["fraud_score"] = fraud_prediction.fraud_score
            factors["fraud_risk_level"] = fraud_prediction.risk_level
        except Exception as e:
            logger.warning(f"Fraud detection failed: {e}")
            # Continue with other checks
        
        # 2. Run anomaly detection
        try:
            # Build feature dict for anomaly detection
            feature_dict = {
                "amount_normalized": min(amount / 1000, 1.0),
                "txn_count_1h": len(transaction_history) if transaction_history else 0,
                "hour_of_day": 12,  # Default
            }
            
            # Use fraud service features if available
            if fraud_prediction:
                feature_dict["is_new_merchant"] = 0.5
                feature_dict["is_night"] = 0.5
                feature_dict["txn_velocity_1h"] = 0.01
            
            # Get feature names from anomaly service
            anomaly_service = self._get_anomaly_service()
            feature_array = [feature_dict.get(f, 0.0) for f in anomaly_service.feature_names]
            
            anomaly_result = anomaly_service.detect(feature_array, feature_dict)
            factors["anomaly_score"] = anomaly_result.anomaly_score
            factors["is_anomaly"] = anomaly_result.is_anomaly
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            # Continue with other checks
        
        # 3. Rule-based risk factors
        rule_factors = self._evaluate_rule_factors(
            amount=amount,
            merchant_id=merchant_id,
            consent_max_amount=consent_max_amount,
            transaction_history=transaction_history,
        )
        factors.update(rule_factors)
        
        # 4. Calculate combined risk score
        combined_score = self._calculate_combined_score(
            fraud_prediction=fraud_prediction,
            anomaly_result=anomaly_result,
            rule_factors=rule_factors,
        )
        
        # 5. Make decision
        decision = self._make_decision(
            combined_score=combined_score,
            fraud_prediction=fraud_prediction,
            anomaly_result=anomaly_result,
        )
        
        # 6. Determine risk level
        risk_level = self._get_risk_level(combined_score)
        
        # 7. Generate recommendations
        recommendations = self._generate_recommendations(
            fraud_prediction=fraud_prediction,
            anomaly_result=anomaly_result,
            decision=decision,
        )
        
        assessment_time = (time.time() - start_time) * 1000
        
        # Build assessment
        assessment = RiskAssessment(
            risk_level=risk_level,
            risk_score=combined_score,
            decision=decision,
            fraud_prediction=fraud_prediction,
            anomaly_result=anomaly_result,
            factors=factors,
            recommendations=recommendations,
            assessment_time_ms=assessment_time,
            cache_hit=False,
        )
        
        # Cache the assessment
        self._cache_assessment(cache_key, assessment)
        
        # Update stats
        if decision == RiskDecision.BLOCK:
            self._stats["blocks"] += 1
        elif decision == RiskDecision.REVIEW:
            self._stats["reviews"] += 1
        else:
            self._stats["allows"] += 1
        
        return assessment

    def _evaluate_rule_factors(
        self,
        amount: float,
        merchant_id: str,
        consent_max_amount: float | None,
        transaction_history: list[dict] | None,
    ) -> dict[str, Any]:
        """Evaluate rule-based risk factors."""
        factors = {}
        
        # Amount relative to consent limit
        if consent_max_amount:
            amount_ratio = amount / consent_max_amount
            factors["consent_limit_ratio"] = amount_ratio
            if amount_ratio > 0.9:
                factors["near_limit"] = True
            if amount_ratio > 1.0:
                factors["exceeds_limit"] = True
        
        # Transaction velocity
        if transaction_history:
            recent_count = len(transaction_history)
            factors["recent_txn_count"] = recent_count
            
            if recent_count > 10:
                factors["high_velocity"] = True
            
            # Check for similar amounts in recent history
            amounts = [t.get("amount", 0) for t in transaction_history]
            if amounts:
                avg_amount = sum(amounts) / len(amounts)
                if avg_amount > 0:
                    amount_deviation = abs(amount - avg_amount) / avg_amount
                    factors["amount_deviation"] = amount_deviation
                    if amount_deviation > 3.0:
                        factors["unusual_amount"] = True
        
        # Known high-risk patterns
        high_risk_merchants = {"unknown", "unverified", "suspicious"}
        if merchant_id.lower() in high_risk_merchants:
            factors["high_risk_merchant"] = True
        
        return factors

    def _calculate_combined_score(
        self,
        fraud_prediction: FraudPrediction | None,
        anomaly_result: AnomalyResult | None,
        rule_factors: dict[str, Any],
    ) -> float:
        """Calculate combined risk score from all sources."""
        scores = []
        weights = []
        
        # Fraud detection (highest weight)
        if fraud_prediction:
            scores.append(fraud_prediction.fraud_score)
            weights.append(0.5)
        
        # Anomaly detection
        if anomaly_result:
            scores.append(anomaly_result.anomaly_score)
            weights.append(0.3)
        
        # Rule-based factors
        rule_score = 0.0
        rule_count = 0
        
        if rule_factors.get("high_risk_merchant"):
            rule_score += 0.5
            rule_count += 1
        if rule_factors.get("high_velocity"):
            rule_score += 0.3
            rule_count += 1
        if rule_factors.get("unusual_amount"):
            rule_score += 0.3
            rule_count += 1
        if rule_factors.get("exceeds_limit"):
            rule_score += 0.4
            rule_count += 1
        
        if rule_count > 0:
            scores.append(rule_score / rule_count)
            weights.append(0.2)
        
        # Weighted average
        if scores and weights:
            total_weight = sum(weights)
            return sum(s * w for s, w in zip(scores, weights)) / total_weight
        
        return 0.1  # Default low risk

    def _make_decision(
        self,
        combined_score: float,
        fraud_prediction: FraudPrediction | None,
        anomaly_result: AnomalyResult | None,
    ) -> RiskDecision:
        """Make risk-based authorization decision."""
        # Block if fraud model says fraud
        if fraud_prediction and fraud_prediction.is_fraud:
            return RiskDecision.BLOCK
        
        # Block if anomaly detected
        if anomaly_result and anomaly_result.is_anomaly:
            return RiskDecision.BLOCK
        
        # Block if combined score very high
        if combined_score >= self.thresholds["combined_block"]:
            return RiskDecision.BLOCK
        
        # Review if medium-high risk
        if combined_score >= self.thresholds["review_threshold"]:
            return RiskDecision.REVIEW
        
        return RiskDecision.ALLOW

    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert score to risk level."""
        if score < 0.2:
            return RiskLevel.LOW
        elif score < 0.4:
            return RiskLevel.MEDIUM
        elif score < 0.7:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _generate_recommendations(
        self,
        fraud_prediction: FraudPrediction | None,
        anomaly_result: AnomalyResult | None,
        decision: RiskDecision,
    ) -> list[str]:
        """Generate human-readable recommendations."""
        recommendations = []
        
        if decision == RiskDecision.BLOCK:
            recommendations.append("Transaction blocked due to high risk")
            
            if fraud_prediction and fraud_prediction.top_risk_factors:
                top = fraud_prediction.top_risk_factors[0]
                recommendations.append(f"Primary risk factor: {top.get('factor', 'unknown')}")
        
        elif decision == RiskDecision.REVIEW:
            recommendations.append("Transaction requires manual review")
            recommendations.append("Contact user for additional verification")
        
        else:
            recommendations.append("Transaction approved")
        
        return recommendations

    def get_stats(self) -> dict[str, Any]:
        """Get risk service statistics."""
        return {
            **self._stats,
            "cache_size": len(self._risk_cache),
        }

    def clear_cache(self):
        """Clear risk assessment cache."""
        self._risk_cache.clear()


# Singleton instance
_risk_service: RiskService | None = None


def get_risk_service() -> RiskService:
    """Get singleton risk service."""
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskService()
    return _risk_service


# Convenience function
async def assess_risk(
    user_id: str,
    amount: float,
    merchant_id: str,
    **kwargs
) -> RiskAssessment:
    """
    Quick risk assessment.
    
    Usage:
        result = await assess_risk(
            user_id="user_123",
            amount=499.99,
            merchant_id="merchant_abc"
        )
        if result.decision == RiskDecision.BLOCK:
            return {"decision": "DENY", "reason": "high_risk"}
    """
    service = get_risk_service()
    return await service.assess(user_id, amount, merchant_id, **kwargs)
