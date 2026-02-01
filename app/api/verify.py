"""
Verify API - POST /v1/verify

Merchant verification of authorization codes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.verify import VerifyRequest, VerifyResponse
from app.services.verify_service import verify_service
from app.middleware.api_keys import require_api_key

router = APIRouter(prefix="/v1", tags=["Verification"], dependencies=[Depends(require_api_key)])


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify an authorization code",
    description="""
    Verify an authorization code and get consent proof.
    
    This endpoint is for merchants to:
    1. Confirm the authorization code is valid
    2. Get cryptographic proof of user consent
    3. Store proof for chargeback defense
    
    The authorization code can only be used once.
    """,
)
async def verify(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """
    Verify authorization and return consent proof.
    
    This is the merchant-facing endpoint. The merchant receives
    an authorization code from the agent and calls this to:
    1. Confirm it's valid
    2. Get proof for chargeback defense
    3. Mark it as used (one-time use)
    """
    try:
        response = await verify_service.verify(db, request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )
