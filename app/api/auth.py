"""
Auth validation endpoint.

Provides API key validation for CLI integration tests.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.api_keys import require_api_key

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class AuthValidateResponse(BaseModel):
    """Response for API key validation."""
    valid: bool
    key_id: str
    owner: str
    permissions: list[str]


@router.get("/validate", response_model=AuthValidateResponse)
async def validate_api_key(
    api_key: dict = Depends(require_api_key),
):
    """
    Validate the current API key.
    
    Returns key metadata if the key is valid.
    Used by CLI `agentauth test` for the Authentication check.
    """
    return AuthValidateResponse(
        valid=True,
        key_id=api_key.get("key_id", "unknown"),
        owner=api_key.get("owner", "default"),
        permissions=api_key.get("permissions", ["read", "write"]),
    )
