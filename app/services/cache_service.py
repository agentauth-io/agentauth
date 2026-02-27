"""
AgentAuth Redis Cache Service

Provides distributed caching with Redis for:
- Consent lookups (most frequent query)
- Authorization rules caching
- Session/token validation caching
- Rate limiting data

Target: 75%+ cache hit ratio, <10ms authorization latency
"""

import hashlib
import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.config import get_settings

T = TypeVar('T')

# Global connection pool
_pool: ConnectionPool | None = None
_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get Redis client with connection pooling."""
    global _pool, _client

    if _client is None:
        settings = get_settings()

        # Parse Redis URL and create connection pool
        _pool = ConnectionPool.from_url(
            settings.redis_url,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            decode_responses=True,
            max_connections=50,
        )
        _client = redis.Redis(connection_pool=_pool)

    return _client


async def close_redis():
    """Close Redis connection pool."""
    global _pool, _client
    if _client:
        await _client.close()
        _client = None
    if _pool:
        await _pool.disconnect()
        _pool = None


class CacheService:
    """
    Distributed cache service with Redis backend.

    Features:
    - Automatic serialization/deserialization
    - Key prefixing for namespace isolation
    - TTL management
    - Cache invalidation patterns
    - Metrics tracking
    """

    PREFIX = "agentauth:"

    # Cache key patterns
    CONSENT_KEY = "consent:{consent_id}"
    CONSENT_TOKEN_KEY = "consent:token:{token}"
    USER_CONSENTS_KEY = "user:{user_id}:consents"
    RULES_KEY = "rules:{developer_id}"
    RATE_LIMIT_KEY = "ratelimit:{api_key}:{window}"
    IDEMPOTENCY_KEY = "idem:{key}"

    def __init__(self):
        self.settings = get_settings()
        self._hits = 0
        self._misses = 0

    async def _get_client(self) -> redis.Redis:
        return await get_redis()

    def _make_key(self, pattern: str, **kwargs) -> str:
        """Generate cache key from pattern."""
        return self.PREFIX + pattern.format(**kwargs)

    # ==================== Core Cache Operations ====================

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        client = await self._get_client()
        try:
            value = await client.get(key)
            if value is not None:
                self._hits += 1
                return json.loads(value)
            self._misses += 1
            return None
        except Exception:
            self._misses += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        client = await self._get_client()
        ttl = ttl or self.settings.cache_ttl_seconds
        try:
            await client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await self._get_client()
        try:
            await client.delete(key)
            return True
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        client = await self._get_client()
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await client.scan(cursor, match=self.PREFIX + pattern)
                if keys:
                    await client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            return deleted
        except Exception:
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = await self._get_client()
        try:
            return await client.exists(key) > 0
        except Exception:
            return False

    # ==================== Consent Caching ====================

    async def get_consent(self, consent_id: str) -> dict | None:
        """Get cached consent by ID."""
        key = self._make_key(self.CONSENT_KEY, consent_id=consent_id)
        return await self.get(key)

    async def set_consent(self, consent_id: str, consent_data: dict) -> bool:
        """Cache consent data."""
        key = self._make_key(self.CONSENT_KEY, consent_id=consent_id)
        return await self.set(key, consent_data, self.settings.cache_consent_ttl)

    async def get_consent_by_token(self, token: str) -> dict | None:
        """Get cached consent by delegation token."""
        # Hash the token for the key (tokens can be long)
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
        key = self._make_key(self.CONSENT_TOKEN_KEY, token=token_hash)
        return await self.get(key)

    async def set_consent_by_token(self, token: str, consent_data: dict) -> bool:
        """Cache consent by delegation token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
        key = self._make_key(self.CONSENT_TOKEN_KEY, token=token_hash)
        return await self.set(key, consent_data, self.settings.cache_consent_ttl)

    async def invalidate_consent(self, consent_id: str, token: str | None = None):
        """Invalidate consent cache entries."""
        key = self._make_key(self.CONSENT_KEY, consent_id=consent_id)
        await self.delete(key)

        if token:
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
            token_key = self._make_key(self.CONSENT_TOKEN_KEY, token=token_hash)
            await self.delete(token_key)

    # ==================== Rate Limiting ====================

    async def check_rate_limit(
        self,
        api_key: str,
        limit: int = 100,
        window_seconds: int = 1
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using sliding window.

        Returns:
            (allowed, remaining, retry_after_seconds)
        """
        client = await self._get_client()
        import time

        now = int(time.time())
        window = now // window_seconds
        key = self._make_key(self.RATE_LIMIT_KEY, api_key=api_key[:16], window=window)

        try:
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds * 2)
            results = await pipe.execute()

            current = results[0]
            remaining = max(0, limit - current)

            if current > limit:
                retry_after = window_seconds - (now % window_seconds)
                return False, 0, retry_after

            return True, remaining, 0
        except Exception:
            # Fail open on Redis errors
            return True, limit, 0

    # ==================== Idempotency ====================

    async def check_idempotency(self, key: str) -> dict | None:
        """Check if idempotency key exists, return cached response if so."""
        cache_key = self._make_key(self.IDEMPOTENCY_KEY, key=key)
        return await self.get(cache_key)

    async def set_idempotency(
        self,
        key: str,
        response: dict,
        ttl_hours: int = 24
    ) -> bool:
        """Store idempotency response with 24-hour TTL."""
        cache_key = self._make_key(self.IDEMPOTENCY_KEY, key=key)
        return await self.set(cache_key, response, ttl_hours * 3600)

    # ==================== Metrics ====================

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        client = await self._get_client()
        try:
            info = await client.info("stats")
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(self.hit_ratio * 100, 2),
                "redis_hits": info.get("keyspace_hits", 0),
                "redis_misses": info.get("keyspace_misses", 0),
            }
        except Exception:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(self.hit_ratio * 100, 2),
            }


# Singleton instance
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# ==================== Decorator for caching ====================

def cached(
    key_pattern: str,
    ttl: int | None = None,
    key_builder: Callable[..., dict] | None = None
):
    """
    Decorator for caching function results.

    Usage:
        @cached("user:{user_id}:profile", ttl=300)
        async def get_user_profile(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Build cache key
            if key_builder:
                key_params = key_builder(*args, **kwargs)
            else:
                key_params = kwargs

            cache_key = cache._make_key(key_pattern, **key_params)

            # Try cache first
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
