"""
AgentAuth Velocity Checks Engine

5 core fraud detection rules targeting 80% fraud catch rate:
1. Transaction amount spike (3x normal)
2. Frequency limit (>10 txns/min)
3. New merchant first-time high value
4. Geographic anomaly
5. Time-of-day anomaly
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class VelocityRuleResult(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class VelocityCheckResult:
    """Result of velocity check."""
    allowed: bool
    rule_triggered: str | None = None
    risk_score: float = 0.0
    details: dict[str, Any] = None
    recommendation: str = "allow"

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class VelocityRules:
    """
    Core velocity rules for fraud detection.

    Each rule returns:
    - PASS: No issue detected
    - WARN: Suspicious, additional verification recommended
    - BLOCK: High risk, decline transaction
    """

    # Thresholds (configurable)
    AMOUNT_SPIKE_MULTIPLIER = 3.0  # 3x normal = suspicious
    MAX_TRANSACTIONS_PER_MINUTE = 10
    MAX_TRANSACTIONS_PER_HOUR = 50
    NEW_MERCHANT_HIGH_VALUE_THRESHOLD = 500.0  # USD
    SUSPICIOUS_HOURS = {0, 1, 2, 3, 4}  # Midnight to 4 AM

    @staticmethod
    async def check_amount_spike(
        amount: float,
        user_id: str,
        historical_avg: float | None = None
    ) -> tuple[VelocityRuleResult, dict]:
        """
        Rule 1: Transaction amount spike detection.
        Flags transactions 3x higher than user's average.
        """
        if historical_avg is None:
            # Get from cache/DB
            historical_avg = await VelocityService.get_user_avg_transaction(user_id)

        if historical_avg == 0 or historical_avg is None:
            # First transaction, can't determine spike
            if amount > 1000:
                return VelocityRuleResult.WARN, {
                    "reason": "first_transaction_high_value",
                    "amount": amount
                }
            return VelocityRuleResult.PASS, {}

        spike_ratio = amount / historical_avg

        if spike_ratio >= VelocityRules.AMOUNT_SPIKE_MULTIPLIER * 2:
            return VelocityRuleResult.BLOCK, {
                "reason": "extreme_amount_spike",
                "spike_ratio": round(spike_ratio, 2),
                "historical_avg": historical_avg
            }
        elif spike_ratio >= VelocityRules.AMOUNT_SPIKE_MULTIPLIER:
            return VelocityRuleResult.WARN, {
                "reason": "amount_spike",
                "spike_ratio": round(spike_ratio, 2),
                "historical_avg": historical_avg
            }

        return VelocityRuleResult.PASS, {}

    @staticmethod
    async def check_frequency(
        user_id: str,
        recent_txn_count: int | None = None
    ) -> tuple[VelocityRuleResult, dict]:
        """
        Rule 2: Transaction frequency limit.
        Blocks if >10 transactions per minute.
        """
        if recent_txn_count is None:
            recent_txn_count = await VelocityService.get_recent_transaction_count(
                user_id, window_minutes=1
            )

        if recent_txn_count >= VelocityRules.MAX_TRANSACTIONS_PER_MINUTE:
            return VelocityRuleResult.BLOCK, {
                "reason": "frequency_limit_exceeded",
                "count": recent_txn_count,
                "limit": VelocityRules.MAX_TRANSACTIONS_PER_MINUTE,
                "window": "1 minute"
            }
        elif recent_txn_count >= VelocityRules.MAX_TRANSACTIONS_PER_MINUTE * 0.7:
            return VelocityRuleResult.WARN, {
                "reason": "approaching_frequency_limit",
                "count": recent_txn_count
            }

        return VelocityRuleResult.PASS, {}

    @staticmethod
    async def check_new_merchant_high_value(
        user_id: str,
        merchant_id: str,
        amount: float
    ) -> tuple[VelocityRuleResult, dict]:
        """
        Rule 3: New merchant + high value = suspicious.
        First-time transactions with new merchants over $500 flagged.
        """
        is_first_time = await VelocityService.is_first_merchant_transaction(
            user_id, merchant_id
        )

        if not is_first_time:
            return VelocityRuleResult.PASS, {}

        if amount >= VelocityRules.NEW_MERCHANT_HIGH_VALUE_THRESHOLD * 2:
            return VelocityRuleResult.BLOCK, {
                "reason": "new_merchant_extreme_value",
                "merchant_id": merchant_id,
                "amount": amount,
                "threshold": VelocityRules.NEW_MERCHANT_HIGH_VALUE_THRESHOLD
            }
        elif amount >= VelocityRules.NEW_MERCHANT_HIGH_VALUE_THRESHOLD:
            return VelocityRuleResult.WARN, {
                "reason": "new_merchant_high_value",
                "merchant_id": merchant_id,
                "amount": amount
            }

        return VelocityRuleResult.PASS, {}

    @staticmethod
    async def check_geographic_anomaly(
        user_id: str,
        current_location: str | None = None,
        ip_address: str | None = None
    ) -> tuple[VelocityRuleResult, dict]:
        """
        Rule 4: Geographic anomaly detection.
        Detects impossible travel or location mismatches.
        """
        if not current_location and not ip_address:
            return VelocityRuleResult.PASS, {}

        last_location = await VelocityService.get_last_transaction_location(user_id)

        if last_location is None:
            # First transaction with location, record it
            return VelocityRuleResult.PASS, {"first_location": True}

        # Simple country-level check (production would use precise geolocation)
        if current_location and last_location.get("country"):
            if current_location != last_location.get("country"):
                time_since_last = await VelocityService.get_time_since_last_transaction(user_id)

                # Impossible travel: different country within 2 hours
                if time_since_last and time_since_last.total_seconds() < 7200:
                    return VelocityRuleResult.BLOCK, {
                        "reason": "impossible_travel",
                        "last_location": last_location.get("country"),
                        "current_location": current_location,
                        "time_since_last_minutes": int(time_since_last.total_seconds() / 60)
                    }
                else:
                    return VelocityRuleResult.WARN, {
                        "reason": "location_change",
                        "last_location": last_location.get("country"),
                        "current_location": current_location
                    }

        return VelocityRuleResult.PASS, {}

    @staticmethod
    async def check_time_anomaly(
        user_id: str,
        transaction_time: datetime | None = None
    ) -> tuple[VelocityRuleResult, dict]:
        """
        Rule 5: Time-of-day anomaly.
        Transactions during unusual hours (midnight-4AM) flagged.
        """
        if transaction_time is None:
            transaction_time = datetime.now(timezone.utc)

        hour = transaction_time.hour

        # Get user's typical transaction hours
        typical_hours = await VelocityService.get_user_typical_hours(user_id)

        if hour in VelocityRules.SUSPICIOUS_HOURS:
            # Check if user typically transacts at this hour
            if typical_hours and hour in typical_hours:
                return VelocityRuleResult.PASS, {"known_pattern": True}

            return VelocityRuleResult.WARN, {
                "reason": "unusual_hour",
                "hour": hour,
                "typical_hours": list(typical_hours) if typical_hours else []
            }

        return VelocityRuleResult.PASS, {}


class VelocityService:
    """
    Velocity checks service for fraud detection.

    Runs all 5 rules and aggregates results into risk score.
    """

    # Risk score weights
    WEIGHTS = {
        "amount_spike": 30,
        "frequency": 25,
        "new_merchant": 20,
        "geographic": 15,
        "time_anomaly": 10,
    }

    @staticmethod
    async def check_velocity(
        user_id: str,
        amount: float,
        merchant_id: str,
        location: str | None = None,
        ip_address: str | None = None,
        transaction_time: datetime | None = None
    ) -> VelocityCheckResult:
        """
        Run all velocity checks and return aggregated result.

        Returns:
            VelocityCheckResult with:
            - allowed: True if transaction should proceed
            - risk_score: 0-100 score
            - rule_triggered: Name of blocking rule if any
            - recommendation: "allow", "verify", or "decline"
        """
        results: list[tuple[str, VelocityRuleResult, dict]] = []

        # Run all 5 rules
        rule1 = await VelocityRules.check_amount_spike(amount, user_id)
        results.append(("amount_spike", rule1[0], rule1[1]))

        rule2 = await VelocityRules.check_frequency(user_id)
        results.append(("frequency", rule2[0], rule2[1]))

        rule3 = await VelocityRules.check_new_merchant_high_value(user_id, merchant_id, amount)
        results.append(("new_merchant", rule3[0], rule3[1]))

        rule4 = await VelocityRules.check_geographic_anomaly(user_id, location, ip_address)
        results.append(("geographic", rule4[0], rule4[1]))

        rule5 = await VelocityRules.check_time_anomaly(user_id, transaction_time)
        results.append(("time_anomaly", rule5[0], rule5[1]))

        # Calculate risk score
        risk_score = 0.0
        blocking_rule = None
        all_details = {}

        for rule_name, result, details in results:
            all_details[rule_name] = {"result": result.value, **details}

            if result == VelocityRuleResult.BLOCK:
                risk_score += VelocityService.WEIGHTS[rule_name]
                if blocking_rule is None:
                    blocking_rule = rule_name
            elif result == VelocityRuleResult.WARN:
                risk_score += VelocityService.WEIGHTS[rule_name] * 0.5

        # Determine recommendation
        if risk_score >= 50:
            recommendation = "decline"
            allowed = False
        elif risk_score >= 25:
            recommendation = "verify"
            allowed = True  # Allow but flag for review
        else:
            recommendation = "allow"
            allowed = True

        return VelocityCheckResult(
            allowed=allowed,
            rule_triggered=blocking_rule,
            risk_score=min(100, risk_score),
            details=all_details,
            recommendation=recommendation
        )

    # ==================== Data Access Methods ====================
    # These would connect to cache/database in production

    @staticmethod
    async def get_user_avg_transaction(user_id: str) -> float | None:
        """Get user's historical average transaction amount."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:avg_amount"
            cached = await cache.get(key)
            return cached
        except Exception:
            return None

    @staticmethod
    async def set_user_avg_transaction(user_id: str, avg: float) -> None:
        """Update user's average transaction amount."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:avg_amount"
            await cache.set(key, avg, ttl=86400)  # 24 hours
        except Exception:
            pass

    @staticmethod
    async def get_recent_transaction_count(
        user_id: str,
        window_minutes: int = 1
    ) -> int:
        """Get count of recent transactions in time window."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()
            key = f"velocity:user:{user_id}:txn_count:{window_minutes}m"
            count = await client.get(key)
            return int(count) if count else 0
        except Exception:
            return 0

    @staticmethod
    async def increment_transaction_count(user_id: str) -> None:
        """Increment user's transaction count."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()
            # 1-minute window
            key1 = f"velocity:user:{user_id}:txn_count:1m"
            pipe = client.pipeline()
            pipe.incr(key1)
            pipe.expire(key1, 60)
            await pipe.execute()
        except Exception:
            pass

    @staticmethod
    async def is_first_merchant_transaction(user_id: str, merchant_id: str) -> bool:
        """Check if this is user's first transaction with merchant."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:merchants"
            merchants = await cache.get(key)
            if merchants and merchant_id in merchants:
                return False
            return True
        except Exception:
            return True  # Assume first time if can't check

    @staticmethod
    async def record_merchant_transaction(user_id: str, merchant_id: str) -> None:
        """Record that user has transacted with merchant."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()
            key = f"velocity:user:{user_id}:merchants"
            await client.sadd(key, merchant_id)
            await client.expire(key, 86400 * 30)  # 30 days
        except Exception:
            pass

    @staticmethod
    async def get_last_transaction_location(user_id: str) -> dict | None:
        """Get location of user's last transaction."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:last_location"
            return await cache.get(key)
        except Exception:
            return None

    @staticmethod
    async def set_transaction_location(user_id: str, location: dict) -> None:
        """Record transaction location."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:last_location"
            await cache.set(key, location, ttl=86400)
        except Exception:
            pass

    @staticmethod
    async def get_time_since_last_transaction(user_id: str) -> timedelta | None:
        """Get time since user's last transaction."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:last_txn_time"
            last_time = await cache.get(key)
            if last_time:
                last_dt = datetime.fromisoformat(last_time)
                return datetime.now(timezone.utc) - last_dt
            return None
        except Exception:
            return None

    @staticmethod
    async def record_transaction_time(user_id: str) -> None:
        """Record transaction timestamp."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:last_txn_time"
            await cache.set(key, datetime.now(timezone.utc).isoformat(), ttl=86400)
        except Exception:
            pass

    @staticmethod
    async def get_user_typical_hours(user_id: str) -> set | None:
        """Get hours when user typically transacts."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            key = f"velocity:user:{user_id}:typical_hours"
            hours = await cache.get(key)
            return set(hours) if hours else None
        except Exception:
            return None


# Convenience function for quick velocity check
async def check_transaction_velocity(
    user_id: str,
    amount: float,
    merchant_id: str,
    **kwargs
) -> VelocityCheckResult:
    """
    Quick velocity check for a transaction.

    Usage:
        result = await check_transaction_velocity(
            user_id="user_123",
            amount=499.99,
            merchant_id="merchant_abc"
        )
        if not result.allowed:
            raise HTTPException(403, detail=result.details)
    """
    return await VelocityService.check_velocity(
        user_id=user_id,
        amount=amount,
        merchant_id=merchant_id,
        **kwargs
    )
