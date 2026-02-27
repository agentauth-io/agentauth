"""
Consents API - POST /v1/consents

Create user consents and get delegation tokens.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware import require_api_key
from app.middleware.api_keys import get_current_user_id
from app.models.consent import Consent
from app.models.database import get_db
from app.schemas.consent import ConsentCreate, ConsentResponse
from app.services.consent_service import consent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/consents", tags=["Consents"])


@router.get(
    "",
    summary="List consents",
    description="List consents belonging to the authenticated developer.",
)
async def list_consents(
    limit: int = Query(default=20, le=100, description="Max consents to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """List consents owned by the authenticated developer with pagination."""
    try:
        owner_filter = Consent.developer_id == user_id

        # Get total count for proper pagination
        count_result = await db.execute(
            select(func.count(Consent.id)).where(owner_filter)
        )
        total = count_result.scalar() or 0

        # Efficient query with pagination - uses index on created_at
        result = await db.execute(
            select(
                Consent.consent_id,
                Consent.user_id,
                Consent.developer_id,
                Consent.intent_description,
                Consent.constraints,
                Consent.scope,
                Consent.is_active,
                Consent.created_at,
                Consent.expires_at
            )
            .where(owner_filter)
            .order_by(Consent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()

        return {
            "consents": [
                {
                    "consent_id": row.consent_id,
                    "user_id": row.user_id,
                    "developer_id": row.developer_id,
                    "intent_description": row.intent_description,
                    "constraints": row.constraints,
                    "scope": row.scope,
                    "is_active": row.is_active,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                }
                for row in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error listing consents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list consents"
        )


@router.post(
    "",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new consent",
    description="""
    Create a new user consent and receive a delegation token.

    The consent captures:
    - **User intent**: What the user wants to accomplish
    - **Constraints**: Spending limits and merchant restrictions
    - **Options**: Expiry, single-use, etc.

    Returns a delegation token that agents use to request authorization.
    """,
)
async def create_consent(
    consent_data: ConsentCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
) -> ConsentResponse:
    """
    Create a new consent.

    This is the first step in the AgentAuth flow.
    User expresses intent -> We issue delegation token.
    The developer_id is automatically set from the authenticated API key.
    """
    try:
        response = await consent_service.create_consent(
            db, consent_data, developer_id=user_id
        )
        return response
    except ValueError as e:
        logger.warning(f"Consent validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid consent data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create consent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create consent. Please try again or contact support."
        )


@router.get(
    "/{consent_id}",
    summary="Get consent details",
    description="Retrieve details of a consent you own.",
)
async def get_consent(
    consent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """Get consent by ID, verifying the caller owns it."""
    consent = await consent_service.get_consent(db, consent_id, developer_id=user_id)
    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found"
        )

    return {
        "consent_id": consent.consent_id,
        "user_id": consent.user_id,
        "intent": consent.intent_description,
        "constraints": consent.constraints,
        "is_active": consent.is_active,
        "expires_at": consent.expires_at,
        "created_at": consent.created_at,
    }


@router.delete(
    "/{consent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a consent",
    description="Revoke a consent you own, invalidating any associated tokens.",
)
async def revoke_consent(
    consent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """Revoke a consent, verifying the caller owns it."""
    success = await consent_service.revoke_consent(db, consent_id, developer_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found"
        )
    return None
