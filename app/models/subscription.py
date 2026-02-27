"""
Subscription model for user billing and plan management.

Tracks Stripe subscription data, plan limits, and usage quotas.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func

from app.models.database import Base


class PlanType(str, enum.Enum):
    """Available subscription plans."""
    FREE = "free"
    STARTUP = "startup"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status values."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    UNPAID = "unpaid"


# Plan limits configuration
PLAN_LIMITS = {
    PlanType.FREE: {
        "api_calls_monthly": 1000,
        "tenants": 1,
        "audit_log_days": 7,
        "environments": 1,
    },
    PlanType.STARTUP: {
        "api_calls_monthly": 10000,
        "tenants": 10,
        "audit_log_days": 30,
        "environments": 3,
    },
    PlanType.PRO: {
        "api_calls_monthly": 50000,
        "tenants": 100,
        "audit_log_days": 90,
        "environments": 10,
    },
    PlanType.ENTERPRISE: {
        "api_calls_monthly": -1,  # Unlimited
        "tenants": -1,  # Unlimited
        "audit_log_days": 365,
        "environments": -1,  # Unlimited
    },
}


class Subscription(Base):
    """
    User subscription model.

    Tracks Stripe subscription data and usage limits for billing.
    """
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, unique=True, index=True)

    # Stripe references
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Plan info
    plan = Column(SQLEnum(PlanType), default=PlanType.FREE, nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)

    # Billing period
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Usage tracking for current period
    api_calls_used = Column(Integer, default=0, nullable=False)
    api_calls_limit = Column(Integer, default=1000, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Subscription {self.user_id} plan={self.plan.value} status={self.status.value}>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is active and usable."""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]

    @property
    def can_make_api_call(self) -> bool:
        """Check if user can make another API call."""
        if self.api_calls_limit == -1:  # Unlimited
            return True
        return self.api_calls_used < self.api_calls_limit

    @property
    def usage_percentage(self) -> float:
        """Get usage percentage for current period."""
        if self.api_calls_limit == -1:
            return 0.0
        if self.api_calls_limit == 0:
            return 100.0
        return (self.api_calls_used / self.api_calls_limit) * 100

    def get_limits(self) -> dict:
        """Get plan limits for this subscription."""
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS[PlanType.FREE])

    def increment_usage(self) -> bool:
        """
        Increment API call usage.
        Returns True if successful, False if limit exceeded.
        """
        if not self.can_make_api_call:
            return False
        self.api_calls_used += 1
        return True

    def reset_usage(self):
        """Reset usage counter for new billing period."""
        self.api_calls_used = 0
        self.current_period_start = datetime.now(timezone.utc)
