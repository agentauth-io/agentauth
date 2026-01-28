"""
Consent Service - CRUD operations for user consents
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import Consent
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentConstraints
from app.services.token_service import token_service
from app.config import get_settings

settings = get_settings()


def generate_consent_id() -> str:
    """Generate a unique consent ID."""
    return f"cons_{secrets.token_urlsafe(16)}"


def hash_intent(intent: str) -> str:
    """Create SHA-256 hash of intent for integrity."""
    return hashlib.sha256(intent.encode()).hexdigest()


class ConsentService:
    """
    Consent Service - manages user consents.
    
    Consents are the root of trust in AgentAuth.
    Everything flows from user consent.
    """
    
    async def create_consent(
        self,
        db: AsyncSession,
        consent_data: ConsentCreate
    ) -> ConsentResponse:
        """
        Create a new consent and generate a delegation token.
        
        This is the first step in the AgentAuth flow:
        1. User expresses intent ("buy flight under $500")
        2. We capture and store the consent
        3. We generate a delegation token for the agent
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(
            seconds=consent_data.options.expires_in_seconds
        )
        
        consent_id = generate_consent_id()
        intent_hash = hash_intent(consent_data.intent.description)
        
        # Build constraints dict
        constraints = {
            "max_amount": consent_data.constraints.max_amount,
            "currency": consent_data.constraints.currency,
        }
        if consent_data.constraints.allowed_merchants:
            constraints["allowed_merchants"] = consent_data.constraints.allowed_merchants
        if consent_data.constraints.allowed_categories:
            constraints["allowed_categories"] = consent_data.constraints.allowed_categories
        
        # Build scope dict
        scope = {
            "single_use": consent_data.options.single_use,
            "requires_confirmation": consent_data.options.requires_confirmation,
        }
        
        # Create database record
        consent = Consent(
            consent_id=consent_id,
            user_id=consent_data.user_id,
            intent_description=consent_data.intent.description,
            intent_hash=intent_hash,
            constraints=constraints,
            scope=scope,
            signature=consent_data.signature,
            public_key=consent_data.public_key,
            expires_at=expires_at,
            is_active=True,
        )
        
        db.add(consent)
        await db.flush()  # Get the ID without committing
        
        # PRE-WARM the authorization cache so first auth is instant
        from app.services.auth_service import _consent_cache
        cache_data = {
            "consent_id": consent_id,
            "user_id": consent_data.user_id,
            "is_active": True,
            "revoked_at": None,
            "expires_at": str(expires_at),
            "constraints": constraints,
        }
        _consent_cache[consent_id] = (cache_data, datetime.now(timezone.utc))
        
        # Generate delegation token
        delegation_token = token_service.create_delegation_token(
            consent_id=consent_id,
            user_id=consent_data.user_id,
            intent_description=consent_data.intent.description,
            max_amount=consent_data.constraints.max_amount,
            currency=consent_data.constraints.currency,
            allowed_merchants=consent_data.constraints.allowed_merchants,
            allowed_categories=consent_data.constraints.allowed_categories,
            expires_at=expires_at,
            single_use=consent_data.options.single_use,
        )
        
        return ConsentResponse(
            consent_id=consent_id,
            delegation_token=delegation_token,
            expires_at=expires_at,
            constraints=ConsentConstraints(
                max_amount=consent_data.constraints.max_amount,
                currency=consent_data.constraints.currency,
                allowed_merchants=consent_data.constraints.allowed_merchants,
                allowed_categories=consent_data.constraints.allowed_categories,
            )
        )
    
    async def get_consent(
        self,
        db: AsyncSession,
        consent_id: str
    ) -> Optional[Consent]:
        """Get a consent by ID."""
        result = await db.execute(
            select(Consent).where(Consent.consent_id == consent_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_consent(
        self,
        db: AsyncSession,
        consent_id: str
    ) -> Optional[Consent]:
        """Get an active (not expired, not revoked) consent."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Consent).where(
                Consent.consent_id == consent_id,
                Consent.is_active == True,
                Consent.revoked_at == None,
                Consent.expires_at > now
            )
        )
        return result.scalar_one_or_none()
    
    async def revoke_consent(
        self,
        db: AsyncSession,
        consent_id: str
    ) -> bool:
        """Revoke a consent."""
        consent = await self.get_consent(db, consent_id)
        if consent is None:
            return False
        
        consent.revoked_at = datetime.now(timezone.utc)
        consent.is_active = False
        await db.flush()
        return True


# Singleton instance
consent_service = ConsentService()
