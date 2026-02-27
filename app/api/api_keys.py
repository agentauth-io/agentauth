"""
API Key Management API

Endpoints for managing API keys including rotation and revocation.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware import get_current_user_id
from app.models.api_key import ApiKey
from app.models.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/api-keys", tags=["API Keys"])


class RotateKeyRequest(BaseModel):
    """Request to rotate an API key."""
    ttl_days: int = Field(default=90, ge=1, le=365, description="New key TTL in days")


class RotateKeyResponse(BaseModel):
    """Response after key rotation."""
    key_id: str
    new_key: str
    old_key_expires_at: str
    new_key_expires_at: str
    message: str


class RevokeKeyResponse(BaseModel):
    """Response after key revocation."""
    key_id: str
    revoked_at: str
    message: str


@router.post("/{key_id}/rotate", response_model=RotateKeyResponse)
async def rotate_api_key(
    key_id: str,
    request: RotateKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Rotate an API key.

    Creates a new key and marks the old one as expiring in 24 hours.
    This allows for graceful transition without service interruption.
    """
    # Find the existing key
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.key_id == key_id,
                ApiKey.owner == current_user_id,
                ApiKey.is_active
            )
        )
    )
    existing_key = result.scalar_one_or_none()

    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or you don't have permission to rotate it"
        )

    # Check if key is already expired
    if existing_key.expires_at and existing_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rotate an expired key. Generate a new one instead."
        )

    # Set old key to expire in 24 hours
    old_key_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    existing_key.expires_at = old_key_expires_at

    # Generate new key
    raw_key = secrets.token_urlsafe(32)
    new_key_id = secrets.token_urlsafe(8)
    full_key = f"aa_live_{raw_key}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    new_key_expires_at = datetime.now(timezone.utc) + timedelta(days=request.ttl_days)

    new_api_key = ApiKey(
        key_hash=key_hash,
        key_id=new_key_id,
        owner=current_user_id,
        permissions=existing_key.permissions,
        rate_limit=existing_key.rate_limit,
        expires_at=new_key_expires_at,
    )

    db.add(new_api_key)
    await db.commit()

    logger.info(f"API key rotated: {key_id} -> {new_key_id} for user {current_user_id}")

    return RotateKeyResponse(
        key_id=new_key_id,
        new_key=full_key,
        old_key_expires_at=old_key_expires_at.isoformat(),
        new_key_expires_at=new_key_expires_at.isoformat(),
        message="Key rotated successfully. Old key will expire in 24 hours. Save the new key securely."
    )


@router.post("/{key_id}/revoke", response_model=RevokeKeyResponse)
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Revoke an API key immediately.

    This action cannot be undone. The key will stop working immediately.
    """
    # Find the key
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.key_id == key_id,
                ApiKey.owner == current_user_id,
                ApiKey.is_active
            )
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or you don't have permission to revoke it"
        )

    # Revoke the key
    api_key.is_active = False
    revoked_at = datetime.now(timezone.utc)
    api_key.expires_at = revoked_at  # Set expiry to now

    await db.commit()

    # Clear from cache
    from app.middleware.api_keys import _KEY_CACHE
    key_hash = hashlib.sha256(api_key.key_hash.encode()).hexdigest()
    _KEY_CACHE.pop(key_hash, None)

    logger.info(f"API key revoked: {key_id} for user {current_user_id}")

    return RevokeKeyResponse(
        key_id=key_id,
        revoked_at=revoked_at.isoformat(),
        message="Key revoked successfully. It will no longer work."
    )


@router.get("/")
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    List all API keys for the authenticated user.
    """
    result = await db.execute(
        select(ApiKey).where(
            and_(
                ApiKey.owner == current_user_id,
                ApiKey.is_active
            )
        )
    )
    keys = result.scalars().all()

    return {
        "keys": [
            {
                "key_id": key.key_id,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "permissions": key.permissions,
                "rate_limit": key.rate_limit,
            }
            for key in keys
        ],
        "total": len(keys)
    }
