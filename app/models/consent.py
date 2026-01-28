"""
Consent model - stores user authorization intents
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Consent(Base):
    """
    Consent table - captures user intent and constraints for agent actions.
    
    This is the root of trust - everything flows from user consent.
    """
    __tablename__ = "consents"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Consent identifier (external facing)
    consent_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )
    
    # User identification
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Developer/Tenant identification (for RLS)
    developer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Intent - what the user wants to do
    intent_description: Mapped[str] = mapped_column(Text, nullable=False)
    intent_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    
    # Constraints - spending limits and restrictions
    constraints: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Expected structure:
    # {
    #   "max_amount": 500,
    #   "currency": "USD",
    #   "allowed_merchants": ["merchant_id_1", "merchant_id_2"],
    #   "allowed_categories": ["4511", "5812"]
    # }
    
    # Scope - what actions are allowed
    scope: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Expected structure:
    # {
    #   "allowed_actions": ["search", "compare", "purchase"],
    #   "requires_confirmation": false,
    #   "single_use": true
    # }
    
    # Cryptographic proof
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True  # Index for ORDER BY created_at DESC queries
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Consent {self.consent_id} user={self.user_id}>"
    
    @property
    def is_valid(self) -> bool:
        """Check if consent is still valid (not expired, not revoked)."""
        now = datetime.now(timezone.utc)
        return (
            self.is_active 
            and self.revoked_at is None 
            and self.expires_at > now
        )
    
    @property
    def max_amount(self) -> Optional[float]:
        """Get max amount from constraints."""
        return self.constraints.get("max_amount")
    
    @property
    def currency(self) -> Optional[str]:
        """Get currency from constraints."""
        return self.constraints.get("currency")

    @property
    def agent_id(self) -> Optional[str]:
        """Get agent_id from scope for backward compatibility."""
        if self.scope and isinstance(self.scope, dict):
            return self.scope.get("agent_id") or self.scope.get("agent_name")
        return None
