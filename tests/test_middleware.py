"""
Tests for middleware components.

Mix of unit tests and integration tests.
"""

import time

import pytest

from app.middleware import generate_api_key_sync, verify_api_key
from app.middleware.idempotency import (
    generate_idempotency_key,
    validate_idempotency_key,
)
from app.middleware.rate_limiter import RateLimitStore


class TestRateLimitStore:
    def test_not_rate_limited_within_limit(self):
        store = RateLimitStore()
        limited, remaining, reset = store.is_rate_limited(
            "key1", max_requests=10, window_seconds=60
        )
        assert limited is False
        assert remaining >= 0

    def test_rate_limited_at_limit(self):
        store = RateLimitStore()
        # Exhaust the limit
        for _ in range(10):
            store.is_rate_limited("key2", max_requests=10, window_seconds=60)
        limited, remaining, reset = store.is_rate_limited(
            "key2", max_requests=10, window_seconds=60
        )
        assert limited is True
        assert remaining == 0

    def test_different_keys_independent(self):
        store = RateLimitStore()
        for _ in range(10):
            store.is_rate_limited("key_a", max_requests=10, window_seconds=60)
        limited_a, _, _ = store.is_rate_limited(
            "key_a", max_requests=10, window_seconds=60
        )
        limited_b, _, _ = store.is_rate_limited(
            "key_b", max_requests=10, window_seconds=60
        )
        assert limited_a is True
        assert limited_b is False

    def test_cleanup_stale_keys(self):
        store = RateLimitStore()
        store.requests["old_key"] = [time.time() - 300]  # 5 min old
        store._last_cleanup = time.time() - 120  # Force cleanup
        store._cleanup_stale_keys(time.time())
        assert "old_key" not in store.requests

    def test_cleanup_skips_if_recent(self):
        store = RateLimitStore()
        store.requests["old_key"] = [time.time() - 300]
        store._last_cleanup = time.time()  # Just cleaned up
        store._cleanup_stale_keys(time.time())
        # Should NOT clean up because last cleanup was too recent
        assert "old_key" in store.requests


class TestIdempotency:
    def test_generate_idempotency_key(self):
        key = generate_idempotency_key()
        assert isinstance(key, str)
        assert len(key) == 36  # UUID format

    def test_generate_unique_keys(self):
        k1 = generate_idempotency_key()
        k2 = generate_idempotency_key()
        assert k1 != k2

    def test_validate_valid_key(self):
        key = generate_idempotency_key()
        assert validate_idempotency_key(key) is True

    def test_validate_custom_key(self):
        assert validate_idempotency_key("my-custom-key-12345") is True

    def test_validate_short_key(self):
        assert validate_idempotency_key("short") is False

    def test_validate_empty_key(self):
        assert validate_idempotency_key("") is False

    def test_validate_none_key(self):
        assert validate_idempotency_key(None) is False


class TestAPIKeys:
    def test_generate_api_key_sync(self):
        key_data = generate_api_key_sync(owner="test_user")
        assert "key" in key_data
        assert "key_id" in key_data
        assert key_data["key"].startswith("aa_live_")
        assert key_data["owner"] == "test_user"

    def test_generate_api_key_unique(self):
        k1 = generate_api_key_sync(owner="u1")
        k2 = generate_api_key_sync(owner="u2")
        assert k1["key"] != k2["key"]
        assert k1["key_id"] != k2["key_id"]

    @pytest.mark.asyncio
    async def test_verify_api_key_returns_data(self):
        key_data = generate_api_key_sync(owner="verifier")
        result = await verify_api_key(key_data["key"])
        assert result is not None
        assert result["owner"] == "verifier"

    @pytest.mark.asyncio
    async def test_verify_api_key_unknown(self):
        result = await verify_api_key("aa_live_unknown_key_12345")
        assert result is None


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        response = await client.get("/health")
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers


class TestRateLimitingIntegration:
    @pytest.mark.asyncio
    async def test_health_not_rate_limited(self, client):
        # Health endpoint should be exempt from rate limiting
        for _ in range(5):
            response = await client.get("/health")
            assert response.status_code == 200


class TestCORSHeaders:
    @pytest.mark.asyncio
    async def test_cors_preflight(self, client):
        response = await client.options(
            "/v1/consents",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Should not be 405 (Method Not Allowed)
        assert response.status_code in (200, 204, 400)
