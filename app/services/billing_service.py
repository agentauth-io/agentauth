"""
Billing service for subscription and usage management.

Handles plan limits, usage tracking, and Stripe synchronization.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.models.subscription import Subscription, PlanType, SubscriptionStatus, PLAN_LIMITS
from app.models.usage import UsageRecord, UsageSummary
from app.services import stripe_service
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


async def get_or_create_subscription(db: AsyncSession, user_id: str) -> Subscription:
    """
    Get user's subscription or create a free one if none exists.
    """
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        # Create free subscription for new user
        subscription = Subscription(
            user_id=user_id,
            plan=PlanType.FREE,
            status=SubscriptionStatus.ACTIVE,
            api_calls_limit=PLAN_LIMITS[PlanType.FREE]["api_calls_monthly"],
            current_period_start=datetime.now(timezone.utc),
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
    
    return subscription


async def check_usage_limit(db: AsyncSession, user_id: str) -> dict:
    """
    Check if user can make another API call.
    
    Returns:
        dict with 'allowed', 'remaining', 'limit', 'used'
    """
    subscription = await get_or_create_subscription(db, user_id)
    
    limit = subscription.api_calls_limit
    used = subscription.api_calls_used
    
    # Unlimited plan
    if limit == -1:
        return {
            "allowed": True,
            "remaining": -1,
            "limit": -1,
            "used": used,
            "plan": subscription.plan.value,
        }
    
    remaining = max(0, limit - used)
    allowed = remaining > 0
    
    return {
        "allowed": allowed,
        "remaining": remaining,
        "limit": limit,
        "used": used,
        "plan": subscription.plan.value,
    }


async def record_api_usage(
    db: AsyncSession,
    user_id: str,
    endpoint: str,
    method: str = "POST",
    status_code: int = 200,
    response_time_ms: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> bool:
    """
    Record an API call and increment usage counter.
    
    Returns:
        True if recorded successfully, False if limit exceeded
    """
    subscription = await get_or_create_subscription(db, user_id)
    
    # Check limit (unless unlimited)
    if subscription.api_calls_limit != -1:
        if subscription.api_calls_used >= subscription.api_calls_limit:
            return False
    
    # Increment subscription usage
    subscription.api_calls_used += 1
    
    # Get current billing period
    billing_period = datetime.now(timezone.utc).strftime("%Y-%m")
    
    # Record individual usage
    usage_record = UsageRecord(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        billing_period=billing_period,
        ip_address=ip_address,
    )
    db.add(usage_record)
    
    # Update or create usage summary
    result = await db.execute(
        select(UsageSummary).where(
            UsageSummary.user_id == user_id,
            UsageSummary.billing_period == billing_period
        )
    )
    summary = result.scalar_one_or_none()
    
    if summary:
        summary.increment(endpoint)
        if status_code >= 400:
            summary.error_count += 1
    else:
        summary = UsageSummary(
            user_id=user_id,
            billing_period=billing_period,
            total_api_calls=1,
            first_call_at=datetime.now(timezone.utc),
            last_call_at=datetime.now(timezone.utc),
        )
        if "/consents" in endpoint:
            summary.consents_created = 1
        elif "/authorize" in endpoint:
            summary.authorizations_created = 1
        elif "/verify" in endpoint:
            summary.verifications_performed = 1
        if status_code >= 400:
            summary.error_count = 1
        db.add(summary)
    
    await db.commit()
    return True


async def get_usage_stats(db: AsyncSession, user_id: str) -> dict:
    """
    Get usage statistics for a user.
    """
    subscription = await get_or_create_subscription(db, user_id)
    billing_period = datetime.now(timezone.utc).strftime("%Y-%m")
    
    result = await db.execute(
        select(UsageSummary).where(
            UsageSummary.user_id == user_id,
            UsageSummary.billing_period == billing_period
        )
    )
    summary = result.scalar_one_or_none()
    
    return {
        "plan": subscription.plan.value,
        "status": subscription.status.value,
        "billing_period": billing_period,
        "api_calls": {
            "used": subscription.api_calls_used,
            "limit": subscription.api_calls_limit,
            "remaining": max(0, subscription.api_calls_limit - subscription.api_calls_used) 
                        if subscription.api_calls_limit != -1 else -1,
        },
        "breakdown": {
            "consents": summary.consents_created if summary else 0,
            "authorizations": summary.authorizations_created if summary else 0,
            "verifications": summary.verifications_performed if summary else 0,
            "errors": summary.error_count if summary else 0,
        },
        "period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    }


async def upgrade_subscription(
    db: AsyncSession,
    user_id: str,
    plan: PlanType,
    stripe_subscription_id: str,
    stripe_customer_id: str,
    stripe_price_id: str,
    period_end: Optional[datetime] = None,
) -> Subscription:
    """
    Upgrade a user's subscription after successful Stripe payment.
    """
    subscription = await get_or_create_subscription(db, user_id)
    
    subscription.plan = plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.stripe_subscription_id = stripe_subscription_id
    subscription.stripe_customer_id = stripe_customer_id
    subscription.stripe_price_id = stripe_price_id
    subscription.api_calls_limit = PLAN_LIMITS[plan]["api_calls_monthly"]
    subscription.current_period_start = datetime.now(timezone.utc)
    subscription.current_period_end = period_end
    
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def cancel_subscription(db: AsyncSession, user_id: str) -> Subscription:
    """
    Cancel a user's subscription (downgrade to free).
    """
    subscription = await get_or_create_subscription(db, user_id)
    
    # Cancel in Stripe if exists
    if subscription.stripe_subscription_id:
        try:
            await stripe_service.cancel_subscription(subscription.stripe_subscription_id)
        except Exception as e:
            logger.error(f"Stripe cancel error: {e}", exc_info=True)
    
    subscription.status = SubscriptionStatus.CANCELED
    subscription.canceled_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def sync_stripe_webhook(db: AsyncSession, event: dict) -> None:
    """
    Sync subscription data from Stripe webhook event.
    """
    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})
    
    if event_type == "customer.subscription.updated":
        stripe_sub_id = data.get("id")
        status = data.get("status")
        
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            # Map Stripe status to our status
            status_map = {
                "active": SubscriptionStatus.ACTIVE,
                "past_due": SubscriptionStatus.PAST_DUE,
                "canceled": SubscriptionStatus.CANCELED,
                "unpaid": SubscriptionStatus.UNPAID,
                "trialing": SubscriptionStatus.TRIALING,
                "incomplete": SubscriptionStatus.INCOMPLETE,
            }
            subscription.status = status_map.get(status, SubscriptionStatus.ACTIVE)
            subscription.current_period_end = datetime.fromtimestamp(
                data.get("current_period_end", 0)
            ) if data.get("current_period_end") else None
            
            await db.commit()
    
    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data.get("id")
        
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now(timezone.utc)
            await db.commit()
    
    elif event_type == "invoice.payment_succeeded":
        # Reset usage on successful payment (new billing period)
        stripe_sub_id = data.get("subscription")
        
        if stripe_sub_id:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_sub_id
                )
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.reset_usage()
                await db.commit()
