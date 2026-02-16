"""
Verify API - POST /v1/verify

Merchant verification of authorization codes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.verify import VerifyRequest, VerifyResponse
from app.services.verify_service import verify_service
from app.middleware import require_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Verification"])


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
    api_key: dict = Depends(require_api_key),
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
    except ValueError as e:
        logger.warning(f"Verification validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Verification failed unexpectedly: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )
