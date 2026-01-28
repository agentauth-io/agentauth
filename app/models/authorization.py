"""
Authorization model - stores authorization decisions and codes
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, JSON, Boolean, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Authorization(Base):
    """
    Authorization table - records each authorization decision.
    
    When an agent requests to perform an action, we create an authorization
    record with the decision (ALLOW/DENY) and generate an authorization code
    for approved requests.
    """
    __tablename__ = "authorizations"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Authorization code (external facing, for merchants to verify)
    authorization_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )
    
    # Link to consent
    consent_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("consents.consent_id"),
        nullable=False,
        index=True
    )
    
    # Developer/Tenant identification (for RLS)
    developer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Decision
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # ALLOW, DENY, STEP_UP
    
    denial_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Transaction details (what was authorized)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    merchant_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Action type
    action: Mapped[str] = mapped_column(String(50), nullable=False, default="payment")
    
    # Additional transaction metadata
    transaction_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Usage tracking
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Verification details (filled when merchant verifies)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Authorization {self.authorization_code} decision={self.decision}>"
    
    @property
    def is_valid(self) -> bool:
        """Check if authorization is still valid (not expired, not used)."""
        now = datetime.now(timezone.utc)
        return (
            self.decision == "ALLOW"
            and not self.is_used
            and self.expires_at > now
        )
    
    @property
    def was_allowed(self) -> bool:
        """Check if this was an ALLOW decision."""
        return self.decision == "ALLOW"
