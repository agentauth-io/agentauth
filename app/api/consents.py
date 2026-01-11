"""
Consents API - POST /v1/consents

Create user consents and get delegation tokens.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db
from app.models.consent import Consent
from app.schemas.consent import ConsentCreate, ConsentResponse
from app.services.consent_service import consent_service

router = APIRouter(prefix="/v1/consents", tags=["Consents"])


@router.get(
    "",
    summary="List all consents",
    description="List all active consents (for dashboard monitoring).",
)
async def list_consents(
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all consents for dashboard monitoring."""
    try:
        result = await db.execute(
            select(Consent).order_by(Consent.created_at.desc()).limit(limit)
        )
        consents = result.scalars().all()
        
        return {
            "consents": [
                {
                    "id": c.consent_id,
                    "user_id": c.user_id,
                    "agent_id": c.agent_id,
                    "intent": c.intent_description,
                    "constraints": c.constraints,
                    "is_active": c.is_active,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in consents
            ],
            "total": len(consents),
        }
    except Exception as e:
        return {"consents": [], "total": 0, "error": str(e)}


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
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    """
    Create a new consent.
    
    This is the first step in the AgentAuth flow.
    User expresses intent → We issue delegation token.
    """
    try:
        response = await consent_service.create_consent(db, consent_data)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consent: {str(e)}"
        )


@router.get(
    "/{consent_id}",
    summary="Get consent details",
    description="Retrieve details of an existing consent.",
)
async def get_consent(
    consent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get consent by ID."""
    consent = await consent_service.get_consent(db, consent_id)
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
    description="Revoke a consent, invalidating any associated tokens.",
)
async def revoke_consent(
    consent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Revoke a consent."""
    success = await consent_service.revoke_consent(db, consent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found"
        )
    return None
