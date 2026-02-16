"""
Admin authentication API.

Provides secure access to the admin dashboard.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import uuid
import jwt
import bcrypt
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models.database import get_db
from app.services.token_revocation import revoke_token, is_revoked

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/v1/admin", tags=["Admin"])


class AdminLoginRequest(BaseModel):
    """Admin login request."""
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response with token."""
    token: str
    expires_at: str
    message: str


class AdminVerifyResponse(BaseModel):
    """Token verification response."""
    valid: bool
    expires_at: Optional[str] = None


def create_admin_token() -> tuple[str, datetime]:
    """Create a JWT token for admin access with a unique JTI for revocation."""
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.admin_token_expiry)
    payload = {
        "type": "admin",
        "jti": str(uuid.uuid4()),
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm="HS256")
    return token, expires


def verify_admin_token(token: str) -> bool:
    """Verify an admin JWT token, checking revocation."""
    try:
        payload = jwt.decode(
            token,
            settings.admin_jwt_secret,
            algorithms=["HS256"]
        )
        if payload.get("type") != "admin":
            return False
        # Check if token has been revoked
        jti = payload.get("jti")
        if jti and is_revoked(jti):
            return False
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    """Extract JWT from Authorization header."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


async def get_admin_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> bool:
    """Dependency to verify admin access."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return True


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """
    Authenticate as admin.

    Returns a JWT token valid for 1 hour.
    """
    # Bcrypt verification (constant-time, salted, slow by design)
    if not bcrypt.checkpw(request.password.encode(), settings.admin_password_bcrypt):
        logger.warning("Failed admin login attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    logger.info("Admin login successful")
    token, expires = create_admin_token()

    return AdminLoginResponse(
        token=token,
        expires_at=expires.isoformat(),
        message="Login successful",
    )


@router.get("/verify", response_model=AdminVerifyResponse)
async def verify_token_endpoint(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Verify if the admin token is valid.
    """
    token = _extract_token(authorization)
    if not token:
        return AdminVerifyResponse(valid=False)

    try:
        payload = jwt.decode(
            token,
            settings.admin_jwt_secret,
            algorithms=["HS256"]
        )
        if payload.get("type") == "admin":
            jti = payload.get("jti")
            if jti and is_revoked(jti):
                return AdminVerifyResponse(valid=False)
            exp = datetime.fromtimestamp(payload["exp"])
            return AdminVerifyResponse(valid=True, expires_at=exp.isoformat())
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")

    return AdminVerifyResponse(valid=False)


@router.post("/logout")
async def admin_logout(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Logout admin session.

    Revokes the JWT token so it can no longer be used.
    """
    token = _extract_token(authorization)
    if token:
        try:
            payload = jwt.decode(
                token,
                settings.admin_jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            if jti:
                exp = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
                revoke_token(jti, exp)
        except jwt.InvalidTokenError:
            pass

    return {"message": "Logout successful", "action": "Token revoked"}


@router.post("/api-keys")
async def admin_create_api_key(
    owner: str = "default",
    is_admin: bool = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key (admin-only).

    Requires valid admin JWT token from POST /v1/admin/login.
    """
    from app.middleware.api_keys import generate_api_key
    key_data = await generate_api_key(db, owner)
    return {
        "key": key_data["key"],
        "key_id": key_data["key_id"],
        "owner": key_data["owner"],
        "created_at": key_data["created_at"],
        "message": "Save this key securely - it won't be shown again!",
    }


@router.get("/api-keys")
async def admin_list_api_keys(
    is_admin: bool = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys (admin-only). Does not expose key hashes."""
    from app.models.api_key import ApiKey
    from sqlalchemy import select, desc

    result = await db.execute(
        select(ApiKey).order_by(desc(ApiKey.created_at)).limit(100)
    )
    keys = result.scalars().all()
    return {
        "keys": [
            {
                "key_id": k.key_id,
                "owner": k.owner,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "rate_limit": k.rate_limit,
            }
            for k in keys
        ],
        "total": len(keys),
    }


@router.post("/api-keys/{key_id}/rotate")
async def admin_rotate_api_key(
    key_id: str,
    is_admin: bool = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate an API key (admin-only).

    Deactivates the old key and generates a new one for the same owner.
    """
    from app.models.api_key import ApiKey
    from app.middleware.api_keys import generate_api_key
    from sqlalchemy import select

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_id == key_id, ApiKey.is_active == True)
    )
    old_key = result.scalar_one_or_none()
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found or already inactive")

    # Deactivate old key
    old_key.is_active = False
    await db.flush()

    # Invalidate cache for old key
    from app.middleware.api_keys import _KEY_CACHE
    to_remove = [h for h, (d, _) in _KEY_CACHE.items() if d.get("key_id") == key_id]
    for h in to_remove:
        del _KEY_CACHE[h]

    # Generate new key for same owner
    new_key_data = await generate_api_key(db, old_key.owner)
    return {
        "old_key_id": key_id,
        "old_key_status": "deactivated",
        "new_key": new_key_data["key"],
        "new_key_id": new_key_data["key_id"],
        "owner": old_key.owner,
        "message": "Old key deactivated. Save the new key securely!",
    }


@router.delete("/api-keys/{key_id}")
async def admin_revoke_api_key(
    key_id: str,
    is_admin: bool = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (deactivate) an API key (admin-only)."""
    from app.models.api_key import ApiKey
    from sqlalchemy import select

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_id == key_id, ApiKey.is_active == True)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found or already inactive")

    key.is_active = False
    await db.flush()

    # Invalidate cache
    from app.middleware.api_keys import _KEY_CACHE
    to_remove = [h for h, (d, _) in _KEY_CACHE.items() if d.get("key_id") == key_id]
    for h in to_remove:
        del _KEY_CACHE[h]

    return {"key_id": key_id, "status": "revoked"}
