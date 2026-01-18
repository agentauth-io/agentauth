"""
AgentAuth ML Feature Store

Real-time feature store backed by Redis for ML model inference.
Targets <100ms latency for fraud detection.

Features:
- User behavior vectors
- Transaction history aggregates
- Real-time feature computation
- Feature versioning
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import json
import hashlib
import asyncio

from app.config import get_settings

settings = get_settings()


@dataclass
class FeatureVector:
    """A feature vector for ML inference."""
    
    entity_id: str  # user_id, agent_id, etc.
    entity_type: str  # "user", "agent", "merchant"
    features: Dict[str, float]
    computed_at: str = ""
    version: str = "v1"
    
    def __post_init__(self):
        if not self.computed_at:
            self.computed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "features": self.features,
            "computed_at": self.computed_at,
            "version": self.version,
        }
    
    def to_array(self, feature_names: List[str]) -> List[float]:
        """Convert to ordered array for model input."""
        return [self.features.get(name, 0.0) for name in feature_names]


@dataclass
class TransactionFeatures:
    """Features computed from a single transaction."""
    
    # Amount features
    amount: float = 0.0
    amount_log: float = 0.0
    amount_normalized: float = 0.0
    
    # Time features
    hour_of_day: int = 0
    day_of_week: int = 0
    is_weekend: bool = False
    is_night: bool = False  # 10pm - 6am
    
    # Merchant features
    merchant_category_code: str = ""
    is_new_merchant: bool = False
    
    # Geographic features
    country_code: str = ""
    is_cross_border: bool = False
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "amount": self.amount,
            "amount_log": self.amount_log,
            "amount_normalized": self.amount_normalized,
            "hour_of_day": float(self.hour_of_day),
            "day_of_week": float(self.day_of_week),
            "is_weekend": 1.0 if self.is_weekend else 0.0,
            "is_night": 1.0 if self.is_night else 0.0,
            "is_new_merchant": 1.0 if self.is_new_merchant else 0.0,
            "is_cross_border": 1.0 if self.is_cross_border else 0.0,
        }


@dataclass
class UserBehaviorFeatures:
    """Aggregated user behavior features."""
    
    # Transaction count features
    txn_count_1h: int = 0
    txn_count_24h: int = 0
    txn_count_7d: int = 0
    txn_count_30d: int = 0
    
    # Amount features
    avg_amount_7d: float = 0.0
    max_amount_7d: float = 0.0
    total_amount_24h: float = 0.0
    total_amount_7d: float = 0.0
    
    # Velocity features
    txn_velocity_1h: float = 0.0  # txns per minute
    amount_velocity_1h: float = 0.0  # spend per minute
    
    # Pattern features
    unique_merchants_7d: int = 0
    unique_categories_7d: int = 0
    pct_new_merchants_7d: float = 0.0
    
    # Risk indicators
    declined_count_24h: int = 0
    velocity_check_failures_24h: int = 0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "txn_count_1h": float(self.txn_count_1h),
            "txn_count_24h": float(self.txn_count_24h),
            "txn_count_7d": float(self.txn_count_7d),
            "txn_count_30d": float(self.txn_count_30d),
            "avg_amount_7d": self.avg_amount_7d,
            "max_amount_7d": self.max_amount_7d,
            "total_amount_24h": self.total_amount_24h,
            "total_amount_7d": self.total_amount_7d,
            "txn_velocity_1h": self.txn_velocity_1h,
            "amount_velocity_1h": self.amount_velocity_1h,
            "unique_merchants_7d": float(self.unique_merchants_7d),
            "unique_categories_7d": float(self.unique_categories_7d),
            "pct_new_merchants_7d": self.pct_new_merchants_7d,
            "declined_count_24h": float(self.declined_count_24h),
            "velocity_check_failures_24h": float(self.velocity_check_failures_24h),
        }


class FeatureStore:
    """
    Redis-backed feature store for real-time ML inference.
    
    Target: <10ms feature retrieval, <100ms total inference
    """
    
    # Feature key patterns
    USER_FEATURES_KEY = "features:user:{user_id}:v{version}"
    AGENT_FEATURES_KEY = "features:agent:{agent_id}:v{version}"
    TXN_HISTORY_KEY = "history:user:{user_id}:txns"
    MERCHANT_SET_KEY = "history:user:{user_id}:merchants"
    
    # Feature TTLs
    USER_FEATURES_TTL = 300  # 5 minutes
    TXN_HISTORY_TTL = 86400 * 7  # 7 days
    
    # Current feature version
    VERSION = "1"
    
    def __init__(self):
        self._feature_names = [
            # Transaction features
            "amount", "amount_log", "amount_normalized",
            "hour_of_day", "day_of_week", "is_weekend", "is_night",
            "is_new_merchant", "is_cross_border",
            # User behavior features
            "txn_count_1h", "txn_count_24h", "txn_count_7d",
            "avg_amount_7d", "max_amount_7d",
            "total_amount_24h", "total_amount_7d",
            "txn_velocity_1h", "amount_velocity_1h",
            "unique_merchants_7d", "pct_new_merchants_7d",
            "declined_count_24h", "velocity_check_failures_24h",
        ]
    
    @property
    def feature_names(self) -> List[str]:
        """Get ordered list of feature names."""
        return self._feature_names
    
    async def _get_redis(self):
        """Get Redis client."""
        from app.services.cache_service import get_redis
        return await get_redis()
    
    # ==================== Feature Retrieval ====================
    
    async def get_user_features(self, user_id: str) -> Optional[FeatureVector]:
        """Get cached user features (fast path)."""
        try:
            client = await self._get_redis()
            key = self.USER_FEATURES_KEY.format(user_id=user_id, version=self.VERSION)
            
            data = await client.get(key)
            if data:
                features = json.loads(data)
                return FeatureVector(
                    entity_id=user_id,
                    entity_type="user",
                    features=features["features"],
                    computed_at=features["computed_at"],
                    version=self.VERSION,
                )
            return None
        except Exception:
            return None
    
    async def set_user_features(self, user_id: str, features: Dict[str, float]) -> bool:
        """Cache computed user features."""
        try:
            client = await self._get_redis()
            key = self.USER_FEATURES_KEY.format(user_id=user_id, version=self.VERSION)
            
            data = {
                "features": features,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await client.setex(key, self.USER_FEATURES_TTL, json.dumps(data))
            return True
        except Exception:
            return False
    
    # ==================== Feature Computation ====================
    
    async def compute_user_features(self, user_id: str) -> UserBehaviorFeatures:
        """Compute user behavior features from transaction history."""
        try:
            client = await self._get_redis()
            
            # Get transaction history
            history_key = self.TXN_HISTORY_KEY.format(user_id=user_id)
            txns = await client.zrange(history_key, 0, -1, withscores=True)
            
            now = datetime.now(timezone.utc).timestamp()
            one_hour_ago = now - 3600
            one_day_ago = now - 86400
            seven_days_ago = now - 86400 * 7
            thirty_days_ago = now - 86400 * 30
            
            features = UserBehaviorFeatures()
            
            amounts_7d = []
            merchants_7d = set()
            
            for txn_data, timestamp in txns:
                txn = json.loads(txn_data)
                amount = txn.get("amount", 0)
                merchant = txn.get("merchant_id", "")
                
                if timestamp >= one_hour_ago:
                    features.txn_count_1h += 1
                    features.total_amount_24h += amount
                
                if timestamp >= one_day_ago:
                    features.txn_count_24h += 1
                    features.total_amount_24h += amount
                
                if timestamp >= seven_days_ago:
                    features.txn_count_7d += 1
                    features.total_amount_7d += amount
                    amounts_7d.append(amount)
                    if merchant:
                        merchants_7d.add(merchant)
                
                if timestamp >= thirty_days_ago:
                    features.txn_count_30d += 1
            
            # Compute aggregates
            if amounts_7d:
                features.avg_amount_7d = sum(amounts_7d) / len(amounts_7d)
                features.max_amount_7d = max(amounts_7d)
            
            features.unique_merchants_7d = len(merchants_7d)
            
            # Velocity (per minute)
            if features.txn_count_1h > 0:
                features.txn_velocity_1h = features.txn_count_1h / 60
                features.amount_velocity_1h = features.total_amount_24h / 60
            
            return features
            
        except Exception:
            return UserBehaviorFeatures()
    
    async def compute_transaction_features(
        self,
        user_id: str,
        amount: float,
        merchant_id: str,
        category_code: str = "",
        country: str = ""
    ) -> TransactionFeatures:
        """Compute features for a specific transaction."""
        import math
        
        now = datetime.now(timezone.utc)
        
        features = TransactionFeatures(
            amount=amount,
            amount_log=math.log(amount + 1),
            amount_normalized=min(amount / 1000, 1.0),  # Normalize to 0-1
            hour_of_day=now.hour,
            day_of_week=now.weekday(),
            is_weekend=now.weekday() >= 5,
            is_night=now.hour < 6 or now.hour >= 22,
            merchant_category_code=category_code,
            country_code=country,
        )
        
        # Check if new merchant
        try:
            client = await self._get_redis()
            merchant_key = self.MERCHANT_SET_KEY.format(user_id=user_id)
            features.is_new_merchant = not await client.sismember(merchant_key, merchant_id)
        except Exception:
            pass
        
        return features
    
    # ==================== Transaction Recording ====================
    
    async def record_transaction(
        self,
        user_id: str,
        amount: float,
        merchant_id: str,
        category_code: str = "",
        decision: str = "ALLOW"
    ) -> None:
        """Record a transaction for feature computation."""
        try:
            client = await self._get_redis()
            
            # Add to transaction history
            history_key = self.TXN_HISTORY_KEY.format(user_id=user_id)
            txn = {
                "amount": amount,
                "merchant_id": merchant_id,
                "category": category_code,
                "decision": decision,
            }
            timestamp = datetime.now(timezone.utc).timestamp()
            await client.zadd(history_key, {json.dumps(txn): timestamp})
            await client.expire(history_key, self.TXN_HISTORY_TTL)
            
            # Add to merchant set
            if decision == "ALLOW":
                merchant_key = self.MERCHANT_SET_KEY.format(user_id=user_id)
                await client.sadd(merchant_key, merchant_id)
                await client.expire(merchant_key, self.TXN_HISTORY_TTL)
            
            # Invalidate cached features
            feature_key = self.USER_FEATURES_KEY.format(user_id=user_id, version=self.VERSION)
            await client.delete(feature_key)
            
        except Exception:
            pass
    
    # ==================== Combined Feature Vector ====================
    
    async def get_inference_features(
        self,
        user_id: str,
        amount: float,
        merchant_id: str,
        category_code: str = "",
        country: str = ""
    ) -> Tuple[List[float], Dict[str, float]]:
        """
        Get complete feature vector for ML inference.
        
        Returns:
            (feature_array, feature_dict)
        """
        # Get cached user features or compute
        cached = await self.get_user_features(user_id)
        
        if cached:
            user_features = cached.features
        else:
            behavior = await self.compute_user_features(user_id)
            user_features = behavior.to_dict()
            await self.set_user_features(user_id, user_features)
        
        # Compute transaction-specific features
        txn_features = await self.compute_transaction_features(
            user_id, amount, merchant_id, category_code, country
        )
        
        # Merge features
        all_features = {**txn_features.to_dict(), **user_features}
        
        # Convert to ordered array
        feature_array = [all_features.get(name, 0.0) for name in self.feature_names]
        
        return feature_array, all_features


# Singleton instance
_feature_store: Optional[FeatureStore] = None


def get_feature_store() -> FeatureStore:
    """Get singleton feature store."""
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store


# Convenience functions
async def get_fraud_features(
    user_id: str,
    amount: float,
    merchant_id: str,
    **kwargs
) -> Tuple[List[float], Dict[str, float]]:
    """Get features for fraud detection."""
    store = get_feature_store()
    return await store.get_inference_features(user_id, amount, merchant_id, **kwargs)


async def record_transaction(
    user_id: str,
    amount: float,
    merchant_id: str,
    decision: str = "ALLOW"
) -> None:
    """Record transaction for feature computation."""
    store = get_feature_store()
    await store.record_transaction(user_id, amount, merchant_id, decision=decision)
