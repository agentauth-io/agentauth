"""
API Key Authentication

Database-backed API key management with in-memory LRU cache.
"""
import secrets
import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db

logger = logging.getLogger(__name__)

# In-memory cache for verified keys (write-through)
# Format: {key_hash: (key_data_dict, cached_at_timestamp)}
_KEY_CACHE: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 300  # 5 minutes
_CACHE_MAX_SIZE = 1000

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _evict_cache():
    """Remove expired or excess entries from the key cache."""
    now = time.time()
    # Remove expired
    expired = [k for k, (_, ts) in _KEY_CACHE.items() if now - ts > _CACHE_TTL]
    for k in expired:
        del _KEY_CACHE[k]
    # If still over max, remove oldest
    if len(_KEY_CACHE) > _CACHE_MAX_SIZE:
        sorted_keys = sorted(_KEY_CACHE, key=lambda k: _KEY_CACHE[k][1])
        for k in sorted_keys[:len(_KEY_CACHE) - _CACHE_MAX_SIZE]:
            del _KEY_CACHE[k]


async def generate_api_key(db: AsyncSession, owner: str = "default") -> dict:
    """
    Generate a new API key and persist to database.

    Returns:
        {key: "aa_live_xxx", key_id: "xxx", owner: "..."}
    """
    from app.models.api_key import ApiKey

    raw_key = secrets.token_urlsafe(32)
    key_id = secrets.token_urlsafe(8)
    full_key = f"aa_live_{raw_key}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    api_key = ApiKey(
        key_hash=key_hash,
        key_id=key_id,
        owner=owner,
        permissions=["read", "write"],
        rate_limit=1000,
    )
    db.add(api_key)
    await db.flush()

    key_data = {
        "key_id": key_id,
        "owner": owner,
        "created_at": api_key.created_at.isoformat() if api_key.created_at else datetime.now(timezone.utc).isoformat(),
        "permissions": ["read", "write"],
        "rate_limit": 1000,
    }

    # Write-through to cache
    _KEY_CACHE[key_hash] = (key_data, time.time())

    return {
        "key": full_key,
        "key_id": key_id,
        "owner": owner,
        "created_at": key_data["created_at"],
    }


def generate_api_key_sync(owner: str = "default") -> dict:
    """
    Generate an API key synchronously (for testing only).

    Stores in cache only — does not persist to database.
    """
    raw_key = secrets.token_urlsafe(32)
    key_id = secrets.token_urlsafe(8)
    full_key = f"aa_live_{raw_key}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    key_data = {
        "key_id": key_id,
        "owner": owner,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "permissions": ["read", "write"],
        "rate_limit": 1000,
    }
    _KEY_CACHE[key_hash] = (key_data, time.time())

    return {
        "key": full_key,
        "key_id": key_id,
        "owner": owner,
        "created_at": key_data["created_at"],
    }


async def verify_api_key(api_key: str, db: Optional[AsyncSession] = None) -> Optional[dict]:
    """Verify an API key against cache first, then database."""
    if not api_key:
        return None

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Check cache first
    if key_hash in _KEY_CACHE:
        data, cached_at = _KEY_CACHE[key_hash]
        if time.time() - cached_at < _CACHE_TTL:
            return data

    # Cache miss — check database
    if db is not None:
        from app.models.api_key import ApiKey
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            # Check expiry (DB stores naive UTC datetimes)
            now_naive = datetime.utcnow()
            if row.expires_at and row.expires_at < now_naive:
                return None
            key_data = {
                "key_id": row.key_id,
                "owner": row.owner,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "permissions": row.permissions or ["read", "write"],
                "rate_limit": row.rate_limit or 1000,
            }
            # Update cache
            _KEY_CACHE[key_hash] = (key_data, time.time())
            _evict_cache()
            # Update last_used_at (fire-and-forget, don't block)
            row.last_used_at = datetime.now(timezone.utc)
            return key_data

    return None


async def get_api_key_optional(
    api_key: Optional[str] = Depends(api_key_header),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> Optional[dict]:
    """
    Optional API key dependency.
    Returns key metadata if valid, None otherwise.
    """
    if not api_key:
        # Check Authorization header as fallback
        auth_header = request.headers.get("Authorization", "") if request else ""
        if auth_header.startswith("Bearer aa_"):
            api_key = auth_header.replace("Bearer ", "")

    if api_key:
        return await verify_api_key(api_key, db)
    return None


async def require_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Required API key dependency.
    Raises 401 if key is missing or invalid.
    """
    key_data = await get_api_key_optional(api_key, request, db)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Valid API key required. Get one at /v1/api-keys"
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key_data


async def get_current_user_id(
    api_key: dict = Depends(require_api_key),
) -> str:
    """
    Extract the authenticated user's ID from the API key.
    Use this instead of accepting user_id as a query parameter.
    """
    return api_key["owner"]


# Generate a demo key for testing (sync, cache-only)
try:
    DEMO_KEY = generate_api_key_sync("demo_user")
    logger.info(f"Demo API Key generated: {DEMO_KEY['key_id']}")
except Exception as e:
    logger.warning(f"Could not generate demo key: {e}")
    DEMO_KEY = {"key": "demo_unavailable", "key_id": "n/a"}
