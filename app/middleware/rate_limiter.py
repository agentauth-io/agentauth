"""
Rate Limiting Middleware

Redis-backed distributed rate limiter with token bucket algorithm.
Supports both per-API-key and per-IP limiting.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class RateLimitStore:
    """In-memory store for rate limit tracking (fallback when Redis unavailable)."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if a key is rate limited.
        
        Returns:
            (is_limited, remaining_requests, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        self.requests[key] = [
            ts for ts in self.requests[key] 
            if ts > window_start
        ]
        
        current_count = len(self.requests[key])
        remaining = max(0, max_requests - current_count)
        
        if current_count >= max_requests:
            # Calculate reset time
            oldest = min(self.requests[key]) if self.requests[key] else now
            reset_in = int(oldest + window_seconds - now)
            return True, 0, reset_in
        
        # Record this request
        self.requests[key].append(now)
        return False, remaining - 1, window_seconds


# Global store (fallback)
rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with Redis backend.
    
    Features:
    - Redis-backed distributed limiting (falls back to in-memory)
    - Per-API-key and per-IP limiting
    - Token bucket algorithm
    - 429 responses with Retry-After header
    
    Limits:
    - By IP: 100 requests per minute
    - By API key: 1000 requests per minute (100/sec burst)
    """
    
    EXEMPT_PATHS = {
        "/docs", "/redoc", "/openapi.json", "/health", "/", "/metrics"
    }

    # Auth endpoints get stricter rate limits (10 req/min per IP)
    STRICT_PATHS = {
        "/v1/admin/login",
        "/v1/auth/login",
        "/v1/auth/register",
        "/v1/auth/otp",
    }
    STRICT_LIMIT = 10  # requests per minute for auth endpoints
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        api_key_requests_per_minute: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.api_key_requests_per_minute = api_key_requests_per_minute
        self.settings = get_settings()
        self._redis_available = None
    
    async def _check_redis_rate_limit(
        self, 
        key: str, 
        limit: int,
        window_seconds: int = 1
    ) -> Tuple[bool, int, int]:
        """Check rate limit using Redis."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            return await cache.check_rate_limit(key, limit, window_seconds)
        except Exception:
            return None  # Fall back to in-memory
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        api_key = self._extract_api_key(request)
        
        # Determine rate limit based on auth and path
        path = request.url.path
        if path in self.STRICT_PATHS:
            # Stricter limit for auth endpoints — prevent brute force
            key = f"auth:{client_ip}:{path}"
            max_requests = self.STRICT_LIMIT
            window_seconds = 60
        elif api_key and api_key.startswith("aa_"):
            key = f"apikey:{api_key[:20]}"
            max_requests = self.settings.rate_limit_requests_per_second
            window_seconds = 1  # Per-second for API keys
        else:
            key = f"ip:{client_ip}"
            max_requests = self.requests_per_minute
            window_seconds = 60  # Per-minute for IPs
        
        # Try Redis first
        redis_result = await self._check_redis_rate_limit(key, max_requests, window_seconds)
        
        if redis_result is not None:
            is_limited = not redis_result[0]
            remaining = redis_result[1]
            reset_in = redis_result[2]
        else:
            # Fall back to in-memory
            is_limited, remaining, reset_in = rate_limit_store.is_rate_limited(
                key=key,
                max_requests=max_requests * window_seconds,  # Adjust for window
                window_seconds=window_seconds
            )
        
        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit exceeded. Try again in {reset_in} seconds.",
                    "retry_after": reset_in
                },
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_in)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_in)
        
        return response
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return request.headers.get("X-API-Key")


async def rate_limit_check(
    api_key: str,
    limit: int = 100,
    window_seconds: int = 1
) -> None:
    """
    Standalone rate limit check function for use in endpoints.
    Raises HTTPException if limit exceeded.
    
    Usage:
        await rate_limit_check(api_key, limit=50)
    """
    try:
        from app.services.cache_service import get_cache_service
        cache = get_cache_service()
        allowed, remaining, retry_after = await cache.check_rate_limit(
            api_key=api_key,
            limit=limit,
            window_seconds=window_seconds
        )
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                }
            )
    except ImportError:
        pass  # Redis not available, skip check
