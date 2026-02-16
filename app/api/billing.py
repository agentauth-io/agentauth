"""
Billing API routes for subscription and usage management.

Handles subscription CRUD, usage stats, and Stripe checkout.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.database import get_db
from app.models.subscription import PlanType, PLAN_LIMITS
from app.services import billing_service, stripe_service
from app.config import get_settings
from app.middleware import require_api_key
from app.middleware.api_keys import get_current_user_id

settings = get_settings()

router = APIRouter(
    prefix="/v1/billing",
    tags=["Billing"],
    dependencies=[Depends(require_api_key)],
)


# --- Request/Response Schemas ---

class SubscriptionResponse(BaseModel):
    """Subscription details response."""
    plan: str
    status: str
    api_calls_used: int
    api_calls_limit: int
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    stripe_customer_id: Optional[str]


class UsageResponse(BaseModel):
    """Usage statistics response."""
    plan: str
    status: str
    billing_period: str
    api_calls: dict
    breakdown: dict
    period_start: Optional[str]
    period_end: Optional[str]


class CheckoutRequest(BaseModel):
    """Checkout session request."""
    plan: str  # startup, pro, enterprise
    success_url: str = "https://agentauth.in/portal?checkout=success"
    cancel_url: str = "https://agentauth.in/portal?checkout=canceled"


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


class PlanLimitsResponse(BaseModel):
    """Plan limits for all tiers."""
    plans: dict


# --- Endpoints ---

@router.get("/subscription")
async def get_subscription(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """
    Get current subscription details for the authenticated user.
    """
    subscription = await billing_service.get_or_create_subscription(db, user_id)

    return SubscriptionResponse(
        plan=subscription.plan.value,
        status=subscription.status.value,
        api_calls_used=subscription.api_calls_used,
        api_calls_limit=subscription.api_calls_limit,
        current_period_start=subscription.current_period_start.isoformat()
            if subscription.current_period_start else None,
        current_period_end=subscription.current_period_end.isoformat()
            if subscription.current_period_end else None,
        stripe_customer_id=subscription.stripe_customer_id,
    )


@router.get("/usage")
async def get_usage(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    """
    Get usage statistics for the current billing period.
    """
    stats = await billing_service.get_usage_stats(db, user_id)
    return UsageResponse(**stats)


@router.get("/check-limit")
async def check_limit(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Check if user can make another API call.

    Returns allowed status and remaining calls.
    """
    return await billing_service.check_usage_limit(db, user_id)


@router.get("/plans")
async def get_plans() -> PlanLimitsResponse:
    """
    Get available plans and their limits.
    """
    plans = {}
    for plan_type, limits in PLAN_LIMITS.items():
        plans[plan_type.value] = {
            "name": plan_type.value.title(),
            "api_calls_monthly": limits["api_calls_monthly"],
            "tenants": limits["tenants"],
            "audit_log_days": limits["audit_log_days"],
            "environments": limits["environments"],
        }
    return PlanLimitsResponse(plans=plans)


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    email: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """
    Create a Stripe Checkout session for subscription upgrade.

    Returns checkout URL to redirect user to Stripe.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    # Map plan to Stripe price ID
    plan_to_price = {
        "startup": settings.stripe_price_pro,  # Using same price for now
        "pro": settings.stripe_price_pro,
        "enterprise": settings.stripe_price_enterprise,
    }

    price_id = plan_to_price.get(request.plan.lower())
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}")

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        # Get or create Stripe customer
        subscription = await billing_service.get_or_create_subscription(db, user_id)

        if not subscription.stripe_customer_id:
            customer_id = await stripe_service.create_customer(email, metadata={"user_id": user_id})
            subscription.stripe_customer_id = customer_id
            await db.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": user_id,
                "plan": request.plan,
            },
        )

        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Operation failed")


@router.post("/portal")
async def create_billing_portal(
    user_id: str = Depends(get_current_user_id),
    return_url: str = "https://agentauth.in/portal",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a Stripe Billing Portal session for subscription management.

    Allows users to update payment methods, view invoices, cancel subscription.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    subscription = await billing_service.get_or_create_subscription(db, user_id)

    if not subscription.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key

        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url,
        )

        return {"portal_url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Operation failed")


@router.post("/cancel")
async def cancel_subscription(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cancel user's subscription.

    Downgrades to free plan at end of billing period.
    """
    subscription = await billing_service.cancel_subscription(db, user_id)
    return {
        "status": "canceled",
        "canceled_at": subscription.canceled_at.isoformat() if subscription.canceled_at else None,
        "message": "Subscription canceled. You'll retain access until the end of your billing period.",
    }


@router.post("/webhook/stripe")
async def stripe_billing_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events for billing.

    Processes subscription updates, payment failures, etc.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe_service.verify_webhook_signature(payload, sig_header)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Process the event
    await billing_service.sync_stripe_webhook(db, event)

    return {"received": True}
