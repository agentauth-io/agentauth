"""
Authorize API - POST /v1/authorize

Real-time authorization decisions for agent actions.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware import require_api_key
from app.models.database import get_db
from app.schemas.authorize import AuthorizeRequest, AuthorizeResponse
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Authorization"])


@router.post(
    "/authorize",
    response_model=AuthorizeResponse,
    summary="Request authorization for an action",
    description="""
    Request authorization for an agent action (typically a payment).

    The request includes:
    - **delegation_token**: JWT token from consent creation
    - **action**: Type of action (e.g., "payment")
    - **transaction**: Details of the proposed transaction

    Returns:
    - **ALLOW**: Authorization granted with authorization_code
    - **DENY**: Authorization denied with reason
    - **STEP_UP**: User confirmation required
    """,
)
async def authorize(
    request: AuthorizeRequest,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
    http_request: Request = None,
) -> AuthorizeResponse:
    """
    Make an authorization decision.

    This is the critical path - called every time an agent
    wants to perform an action.

    The authorization decision is based on:
    1. Token validity (signature, expiry)
    2. Amount constraints (within limit?)
    3. Currency match
    4. Merchant restrictions
    """
    try:
        # Extract client info for audit logging
        client_ip = http_request.client.host if http_request else None
        user_agent = http_request.headers.get("user-agent") if http_request else None

        response = await auth_service.authorize(
            db,
            request,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        return response
    except ValueError as e:
        logger.warning(f"Authorization validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Authorization failed unexpectedly: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization service error"
        )
