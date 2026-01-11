"""
API Key Authentication

Simple API key management for MVP.
"""
import secrets
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader


# Simple in-memory API key store (use database in production)
# Format: {key_hash: {owner, created_at, permissions}}
API_KEY_STORE = {}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key(owner: str = "default") -> dict:
    """
    Generate a new API key.
    
    Returns:
        {key: "aa_live_xxx", key_id: "xxx", owner: "..."}
    """
    # Generate random key
    raw_key = secrets.token_urlsafe(32)
    key_id = secrets.token_urlsafe(8)
    full_key = f"aa_live_{raw_key}"
    
    # Hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Store
    API_KEY_STORE[key_hash] = {
        "key_id": key_id,
        "owner": owner,
        "created_at": datetime.utcnow().isoformat(),
        "permissions": ["read", "write"],
        "rate_limit": 1000,  # requests per minute
    }
    
    return {
        "key": full_key,
        "key_id": key_id,
        "owner": owner,
        "created_at": API_KEY_STORE[key_hash]["created_at"],
    }


def verify_api_key(api_key: str) -> Optional[dict]:
    """Verify an API key and return its metadata."""
    if not api_key:
        return None
    
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return API_KEY_STORE.get(key_hash)


async def get_api_key_optional(
    api_key: Optional[str] = Depends(api_key_header),
    request: Request = None,
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
        return verify_api_key(api_key)
    return None


async def require_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    request: Request = None,
) -> dict:
    """
    Required API key dependency.
    Raises 401 if key is missing or invalid.
    """
    key_data = await get_api_key_optional(api_key, request)
    
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


# Pre-generate a demo key for testing
try:
    DEMO_KEY = generate_api_key("demo_user")
    print(f"🔑 Demo API Key: {DEMO_KEY['key']}")
except Exception as e:
    print(f"Warning: Could not generate demo key: {e}")
    DEMO_KEY = {"key": "demo_unavailable", "key_id": "n/a"}

