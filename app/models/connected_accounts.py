"""
Connected Accounts Model

Stores user-linked financial accounts (Stripe Connect, etc.)
"""
import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, String

from app.models.database import Base


class AccountProvider(str, enum.Enum):
    """Supported account providers."""
    STRIPE = "stripe"
    STRIPE_CONNECT = "stripe_connect"
    PAYPAL = "paypal"
    PLAID = "plaid"
    SQUARE = "square"


class AccountStatus(str, enum.Enum):
    """Account connection status."""
    PENDING = "pending"       # Onboarding not complete
    ACTIVE = "active"         # Fully connected and operational
    RESTRICTED = "restricted"  # Some limitations
    DISCONNECTED = "disconnected"


class ConnectedAccount(Base):
    """
    A financial account connected by a user.

    This stores the link between AgentAuth users and their
    external financial accounts (Stripe Connect, bank accounts, etc.)
    """
    __tablename__ = "connected_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)

    # Provider details
    provider = Column(Enum(AccountProvider), nullable=False)
    provider_account_id = Column(String(255), nullable=False, unique=True)  # e.g., acct_xxx for Stripe

    # Account info
    account_name = Column(String(255), nullable=True)  # Display name
    account_email = Column(String(255), nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    currency = Column(String(3), nullable=True)  # Default currency

    # Status
    status = Column(Enum(AccountStatus), default=AccountStatus.PENDING, nullable=False)
    details_submitted = Column(Boolean, default=False)
    charges_enabled = Column(Boolean, default=False)
    payouts_enabled = Column(Boolean, default=False)

    # Capabilities and metadata
    capabilities = Column(JSON, nullable=True)  # Provider-specific capabilities
    account_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    connected_at = Column(DateTime, nullable=True)  # When fully connected
    disconnected_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ConnectedAccount {self.provider.value}:{self.provider_account_id} ({self.status.value})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider.value,
            "provider_account_id": self.provider_account_id,
            "account_name": self.account_name,
            "account_email": self.account_email,
            "country": self.country,
            "currency": self.currency,
            "status": self.status.value,
            "details_submitted": self.details_submitted,
            "charges_enabled": self.charges_enabled,
            "payouts_enabled": self.payouts_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
        }


class AgentTransaction(Base):
    """
    Transactions made by AI agents.

    Tracks both authorized purchases via AgentAuth and
    actual payment outcomes from connected accounts.
    """
    __tablename__ = "agent_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)

    # Link to AgentAuth authorization
    authorization_id = Column(String(36), ForeignKey("authorizations.id"), nullable=True)
    consent_id = Column(String(36), ForeignKey("consents.id"), nullable=True)

    # Link to connected account
    connected_account_id = Column(String(36), ForeignKey("connected_accounts.id"), nullable=True)

    # Transaction details
    agent_id = Column(String(255), nullable=True, index=True)
    agent_name = Column(String(255), nullable=True)

    # Payment provider reference
    provider = Column(Enum(AccountProvider), nullable=True)
    provider_transaction_id = Column(String(255), nullable=True, index=True)  # e.g., pi_xxx for Stripe
    provider_charge_id = Column(String(255), nullable=True)

    # Amount
    amount = Column(String(50), nullable=False)  # Store as string for precision
    currency = Column(String(3), default="USD", nullable=False)

    # Merchant info
    merchant_id = Column(String(255), nullable=True)
    merchant_name = Column(String(255), nullable=True)
    merchant_category = Column(String(100), nullable=True)

    # Status
    authorization_status = Column(String(20), nullable=True)  # ALLOW, DENY, PENDING
    payment_status = Column(String(20), nullable=True)  # succeeded, failed, pending, refunded

    # Description and metadata
    description = Column(String(500), nullable=True)
    transaction_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    authorized_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AgentTransaction {self.id[:8]} ${self.amount} {self.payment_status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "amount": float(self.amount) if self.amount else 0,
            "currency": self.currency,
            "merchant_name": self.merchant_name,
            "merchant_category": self.merchant_category,
            "authorization_status": self.authorization_status,
            "payment_status": self.payment_status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
