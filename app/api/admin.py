"""
Admin authentication API.

Provides secure access to the admin dashboard.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import hmac
import logging
from typing import Optional

from app.config import get_settings

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
    """Create a JWT token for admin access."""
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.admin_token_expiry)
    payload = {
        "type": "admin",
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm="HS256")
    return token, expires


def verify_admin_token(token: str) -> bool:
    """Verify an admin JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.admin_jwt_secret, 
            algorithms=["HS256"]
        )
        return payload.get("type") == "admin"
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


async def get_admin_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> bool:
    """Dependency to verify admin access."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = parts[1]
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return True


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """
    Authenticate as admin.
    
    Returns a JWT token valid for 1 hour.
    """
    # Constant-time password comparison to prevent timing attacks
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    expected_hash = hashlib.sha256(settings.admin_password.encode()).hexdigest()
    
    if not hmac.compare_digest(password_hash, expected_hash):
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
async def verify_token(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Verify if the admin token is valid.
    """
    if not authorization:
        return AdminVerifyResponse(valid=False)
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return AdminVerifyResponse(valid=False)
    
    token = parts[1]
    
    try:
        payload = jwt.decode(
            token, 
            settings.admin_jwt_secret, 
            algorithms=["HS256"]
        )
        if payload.get("type") == "admin":
            exp = datetime.fromtimestamp(payload["exp"])
            return AdminVerifyResponse(valid=True, expires_at=exp.isoformat())
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
    
    return AdminVerifyResponse(valid=False)


@router.post("/logout")
async def admin_logout():
    """
    Logout admin session.
    
    Note: With JWT, logout is handled client-side by removing the token.
    This endpoint exists for API completeness.
    """
    return {"message": "Logout successful", "action": "Remove token from client storage"}
