"""
Spending Limits and Rules Models

Database models for the rules engine that controls AI agent spending.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.models.database import Base


class RuleAction(str, enum.Enum):
    """Action to take when rule matches."""
    ALLOW = "allow"
    BLOCK = "block"


class SpendingLimit(Base):
    """
    Spending limits configuration for a user/developer.
    
    Defines maximum spending thresholds that the rules engine
    checks before approving any authorization request.
    """
    __tablename__ = "spending_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Spending caps
    daily_limit: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("1000.00")
    )
    monthly_limit: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("10000.00")
    )
    per_transaction_limit: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("500.00")
    )
    
    # Human approval threshold
    require_approval_above: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), default=Decimal("100.00"), nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UsageTracking(Base):
    """
    Tracks actual spending usage against limits.
    
    Automatically resets daily/monthly counters.
    """
    __tablename__ = "usage_tracking"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Current usage
    daily_spent: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    monthly_spent: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    
    # Transaction counts
    daily_transaction_count: Mapped[int] = mapped_column(default=0)
    monthly_transaction_count: Mapped[int] = mapped_column(default=0)
    
    # Reset tracking
    last_daily_reset: Mapped[date] = mapped_column(Date, default=date.today)
    last_monthly_reset: Mapped[date] = mapped_column(Date, default=date.today)
    
    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MerchantRule(Base):
    """
    Whitelist/blacklist rules for specific merchants.
    
    Supports pattern matching (e.g., "*.amazon.com").
    """
    __tablename__ = "merchant_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Rule definition
    merchant_pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[RuleAction] = mapped_column(
        SQLEnum(RuleAction), default=RuleAction.ALLOW
    )
    
    # Optional metadata
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class CategoryRule(Base):
    """
    Allow/block rules for spending categories.
    
    Categories: saas, ecommerce, travel, entertainment, gambling, crypto, etc.
    """
    __tablename__ = "category_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Rule definition
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[RuleAction] = mapped_column(
        SQLEnum(RuleAction), default=RuleAction.ALLOW
    )
    
    # Optional: set custom limit for this category
    category_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class AuthorizationLog(Base):
    """
    Log of all authorization requests for analytics.
    
    Captures full context of each decision.
    """
    __tablename__ = "authorization_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Request details
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Decision
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # approved/denied
    denial_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Processing info
    processing_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    rules_evaluated: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
