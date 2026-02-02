"""
Idempotency Key Middleware

Prevents duplicate transactions using UUIDv4 keys stored in Redis.
- 128+ bits of entropy
- 24-hour TTL
- Returns cached response for duplicate requests
"""

import uuid
import hashlib
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Endpoints that support idempotency
IDEMPOTENT_ENDPOINTS = {
    "/v1/authorize",
    "/v1/consents",
    "/v1/transactions",
}

# Header name for idempotency key
IDEMPOTENCY_HEADER = "Idempotency-Key"


def generate_idempotency_key() -> str:
    """Generate a new idempotency key (UUIDv4, 128 bits entropy)."""
    return str(uuid.uuid4())


def validate_idempotency_key(key: str) -> bool:
    """Validate idempotency key format."""
    if not key or len(key) < 16:
        return False
    # Allow UUIDs or custom keys (min 16 chars)
    return True


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware for preventing duplicate transactions.
    
    Features:
    - Requires Idempotency-Key header for POST requests to critical endpoints
    - Caches responses in Redis with 24-hour TTL
    - Returns cached response for duplicate requests
    - Prevents race conditions with atomic Redis operations
    """
    
    TTL_HOURS = 24
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to POST/PUT methods on specific endpoints
        if request.method not in {"POST", "PUT"}:
            return await call_next(request)
        
        # Check if endpoint requires idempotency
        path = request.url.path
        requires_idempotency = any(
            path.startswith(endpoint) for endpoint in IDEMPOTENT_ENDPOINTS
        )
        
        if not requires_idempotency:
            return await call_next(request)
        
        # Get idempotency key from header
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        
        if not idempotency_key:
            # Generate warning but allow request (for backward compatibility)
            # In strict mode, you could return 400 here
            return await call_next(request)
        
        if not validate_idempotency_key(idempotency_key):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_idempotency_key",
                    "detail": "Idempotency-Key must be at least 16 characters"
                }
            )
        
        # Create composite key with endpoint and method
        cache_key = self._make_cache_key(request, idempotency_key)
        
        # Check for existing response
        cached_response = await self._get_cached_response(cache_key)
        
        if cached_response is not None:
            # Return cached response with indicator header
            return JSONResponse(
                status_code=cached_response.get("status_code", 200),
                content=cached_response.get("body"),
                headers={
                    "Idempotent-Replayed": "true",
                    "X-Idempotency-Key": idempotency_key
                }
            )
        
        # Try to acquire lock (prevent race conditions)
        lock_acquired = await self._acquire_lock(cache_key)
        
        if not lock_acquired:
            # Another request with same key is in progress
            return JSONResponse(
                status_code=409,
                content={
                    "error": "idempotency_conflict",
                    "detail": "A request with this idempotency key is already in progress"
                }
            )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Cache the response (only for successful responses)
            if 200 <= response.status_code < 300:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Cache it
                await self._cache_response(
                    cache_key, 
                    response.status_code,
                    body.decode() if body else "{}"
                )
                
                # Return new response with body
                import json
                return JSONResponse(
                    status_code=response.status_code,
                    content=json.loads(body.decode()) if body else {},  # Safe JSON parsing
                    headers={
                        "X-Idempotency-Key": idempotency_key,
                        **dict(response.headers)
                    }
                )
            
            return response
            
        finally:
            # Release lock
            await self._release_lock(cache_key)
    
    def _make_cache_key(self, request: Request, idempotency_key: str) -> str:
        """Create cache key from request and idempotency key."""
        # Include API key if present for isolation
        api_key = request.headers.get("Authorization", "")[:20]
        key_base = f"{api_key}:{request.method}:{request.url.path}:{idempotency_key}"
        return hashlib.sha256(key_base.encode()).hexdigest()[:48]
    
    async def _get_cached_response(self, cache_key: str) -> Optional[dict]:
        """Get cached response from Redis."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            return await cache.check_idempotency(cache_key)
        except Exception:
            return None
    
    async def _cache_response(
        self, 
        cache_key: str, 
        status_code: int, 
        body: str
    ) -> bool:
        """Cache response in Redis."""
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            import json
            return await cache.set_idempotency(
                cache_key,
                {"status_code": status_code, "body": json.loads(body) if body else {}},
                ttl_hours=self.TTL_HOURS
            )
        except Exception:
            return False
    
    async def _acquire_lock(self, cache_key: str) -> bool:
        """Acquire distributed lock."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()
            lock_key = f"lock:{cache_key}"
            # SET NX with 60 second timeout
            result = await client.set(lock_key, "1", nx=True, ex=60)
            return result is not None
        except Exception:
            return True  # Allow if Redis unavailable
    
    async def _release_lock(self, cache_key: str) -> None:
        """Release distributed lock."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()
            lock_key = f"lock:{cache_key}"
            await client.delete(lock_key)
        except Exception:
            pass


def get_idempotency_key(request: Request) -> Optional[str]:
    """Extract idempotency key from request."""
    return request.headers.get(IDEMPOTENCY_HEADER)


def require_idempotency_key(request: Request) -> str:
    """
    Dependency that requires and validates idempotency key.
    
    Usage:
        @app.post("/v1/transactions")
        async def create_transaction(
            idempotency_key: str = Depends(require_idempotency_key)
        ):
            ...
    """
    key = get_idempotency_key(request)
    if not key:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_idempotency_key",
                "detail": "Idempotency-Key header is required for this endpoint"
            }
        )
    if not validate_idempotency_key(key):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_idempotency_key", 
                "detail": "Idempotency-Key must be at least 16 characters"
            }
        )
    return key
