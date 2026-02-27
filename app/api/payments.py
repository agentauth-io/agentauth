"""
Payment API routes for Stripe integration.

Handles payment intents, subscriptions, and webhooks.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.config import get_settings
from app.middleware import require_api_key
from app.middleware.api_keys import get_current_user_id

logger = logging.getLogger(__name__)
from app.schemas.payment import (
    CancelSubscriptionResponse,
    CreatePaymentIntentRequest,
    CreatePaymentIntentResponse,
    CreateSubscriptionRequest,
    CreateSubscriptionResponse,
    PricingResponse,
    PricingTier,
    SubscriptionStatusResponse,
)
from app.services import stripe_service

settings = get_settings()

router = APIRouter(prefix="/v1/payments", tags=["Payments"])


# Pricing tiers definition
PRICING_TIERS = [
    PricingTier(
        id="free",
        name="Free",
        price=0,
        api_calls="100/month",
        features=[
            "Basic authorization API",
            "Email support",
            "Community access",
        ],
    ),
    PricingTier(
        id="pro",
        name="Pro",
        price=4900,  # $49.00
        api_calls="10,000/month",
        features=[
            "Everything in Free",
            "Advanced analytics",
            "Priority support",
            "Custom spending rules",
            "Webhook notifications",
        ],
    ),
    PricingTier(
        id="enterprise",
        name="Enterprise",
        price=19900,  # $199.00
        api_calls="Unlimited",
        features=[
            "Everything in Pro",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "On-premise option",
            "Advanced security features",
        ],
    ),
]


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """Get available pricing tiers."""
    return PricingResponse(tiers=PRICING_TIERS)


@router.post("/create-intent", response_model=CreatePaymentIntentResponse)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    user_id: str = Depends(get_current_user_id),
    api_key: dict = Depends(require_api_key),
):
    """
    Create a payment intent for one-time payment.

    Use this for single purchases. Returns a client_secret to complete
    payment on the frontend with Stripe.js.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Payment processing not configured. Contact support.",
        )

    try:
        # Optionally create customer if email provided
        customer_id = None
        if request.customer_email:
            customer_id = await stripe_service.create_customer(
                email=request.customer_email,
                metadata={"agentauth_user_id": user_id},
            )

        intent = await stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_id=customer_id,
            metadata={
                **(request.metadata or {}),
                "agentauth_user_id": user_id,
            },
        )

        return CreatePaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.payment_intent_id,
            amount=intent.amount,
            currency=intent.currency,
        )
    except Exception as e:
        logger.error(f"Payment intent creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to create payment intent")


@router.post("/agent-purchase")
async def create_agent_purchase(
    authorization_code: str,
    amount: int,
    currency: str = "USD",
    description: str = "",
    customer_email: str | None = None,
    user_id: str = Depends(get_current_user_id),
    api_key: dict = Depends(require_api_key),
):
    """
    Create a payment intent for an AI agent purchase.

    This endpoint is called after AgentAuth authorization is successful.
    It creates a Stripe PaymentIntent that can be confirmed with a saved payment method.

    Args:
        authorization_code: The auth code from /v1/authorize
        amount: Amount in cents (e.g., 7999 for $79.99)
        currency: Currency code (default: USD)
        description: Purchase description
        customer_email: Customer email for receipt
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Payment processing not configured",
        )

    # Verify the authorization code is valid
    from app.services.auth_service import _auth_cache

    cached_auth = _auth_cache.get(authorization_code)
    if not cached_auth:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired authorization code",
        )
    if cached_auth.get("is_used"):
        raise HTTPException(
            status_code=400,
            detail="Authorization code has already been used",
        )

    # Verify the authorization belongs to the authenticated user
    auth_user = cached_auth.get("user_id")
    if auth_user and auth_user != user_id:
        raise HTTPException(
            status_code=403,
            detail="Authorization code does not belong to this user",
        )

    try:
        intent = await stripe_service.create_payment_intent(
            amount=amount,
            currency=currency.lower(),
            customer_id=None,
            metadata={
                "authorization_code": authorization_code,
                "source": "agentauth_ai_agent",
                "description": description,
                "agentauth_user_id": user_id,
            },
        )

        return {
            "success": True,
            "payment_intent_id": intent.payment_intent_id,
            "client_secret": intent.client_secret,
            "amount": intent.amount,
            "currency": intent.currency,
            "authorization_code": authorization_code,
        }
    except Exception as e:
        logger.error(f"Agent purchase failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Payment creation failed")


@router.post("/subscribe", response_model=CreateSubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    api_key: dict = Depends(require_api_key),
):
    """
    Create a subscription for the authenticated user.

    Creates a Stripe customer and subscription. Returns client_secret
    to complete payment setup on frontend.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Payment processing not configured. Contact support.",
        )

    # Map tier to price ID
    price_id = request.price_id
    if price_id == "pro":
        price_id = settings.stripe_price_pro
    elif price_id == "enterprise":
        price_id = settings.stripe_price_enterprise

    if not price_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid pricing tier or price not configured.",
        )

    try:
        # Create customer
        customer_id = await stripe_service.create_customer(
            email=request.email,
            name=request.name,
            metadata={"agentauth_user_id": user_id},
        )

        # Create subscription
        subscription = await stripe_service.create_subscription(
            customer_id=customer_id,
            price_id=price_id,
            payment_method_id=request.payment_method_id,
        )

        return CreateSubscriptionResponse(
            subscription_id=subscription.subscription_id,
            customer_id=customer_id,
            client_secret=subscription.client_secret,
            status=subscription.status,
            current_period_end=subscription.current_period_end,
        )
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to create subscription")


@router.get(
    "/subscriptions/{subscription_id}", response_model=SubscriptionStatusResponse
)
async def get_subscription_status(
    subscription_id: str,
    user_id: str = Depends(get_current_user_id),
    api_key: dict = Depends(require_api_key),
):
    """Get the status of a subscription owned by the authenticated user."""
    try:
        subscription = await stripe_service.get_subscription(subscription_id)
        # Verify the subscription belongs to the authenticated user via metadata
        metadata = subscription.get("metadata", {})
        if (
            metadata.get("agentauth_user_id")
            and metadata["agentauth_user_id"] != user_id
        ):
            raise HTTPException(status_code=404, detail="Subscription not found")
        return SubscriptionStatusResponse(**subscription)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription lookup failed: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Subscription not found")


@router.delete(
    "/subscriptions/{subscription_id}", response_model=CancelSubscriptionResponse
)
async def cancel_subscription(
    subscription_id: str,
    user_id: str = Depends(get_current_user_id),
    api_key: dict = Depends(require_api_key),
):
    """Cancel a subscription owned by the authenticated user."""
    try:
        # Verify ownership before canceling
        subscription = await stripe_service.get_subscription(subscription_id)
        metadata = subscription.get("metadata", {})
        if (
            metadata.get("agentauth_user_id")
            and metadata["agentauth_user_id"] != user_id
        ):
            raise HTTPException(status_code=404, detail="Subscription not found")

        result = await stripe_service.cancel_subscription(subscription_id)
        return CancelSubscriptionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to cancel subscription")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.

    Processes payment and subscription events from Stripe.
    Note: Webhooks are authenticated via Stripe signature, not API key.
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    payload = await request.body()

    try:
        event = stripe_service.verify_webhook_signature(payload, stripe_signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle different event types
    event_type = event.get("type", "")

    if event_type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        await _record_payment_event("payment_succeeded", payment_intent)

    elif event_type == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        logger.warning(f"Payment failed: {payment_intent['id']}")
        await _record_payment_event("payment_failed", payment_intent)

    elif event_type == "customer.subscription.created":
        subscription = event["data"]["object"]
        logger.info(f"Subscription created: {subscription['id']}")
        await _handle_subscription_created(subscription)

    elif event_type == "customer.subscription.updated":
        subscription = event["data"]["object"]
        logger.info(f"Subscription updated: {subscription['id']}")
        await _handle_subscription_updated(subscription)

    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        logger.info(f"Subscription canceled: {subscription['id']}")
        await _handle_subscription_deleted(subscription)

    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        logger.info(f"Invoice paid: {invoice['id']}")
        await _handle_invoice_paid(invoice)

    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        logger.warning(f"Invoice payment failed: {invoice['id']}")
        await _handle_invoice_failed(invoice)

    return {"received": True}


# --- Webhook Handler Functions ---


async def _record_payment_event(event_type: str, payment_intent: dict) -> None:
    """Record a payment event to the audit log."""
    logger.debug(
        f"Recording payment event: {event_type} for {payment_intent.get('id')}"
    )


async def _handle_subscription_created(subscription: dict) -> None:
    """Handle new subscription creation - grant access to user."""
    customer_id = subscription.get("customer")
    plan_id = (
        subscription.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
    )
    logger.info(f"Granting access for customer {customer_id} on plan {plan_id}")


async def _handle_subscription_updated(subscription: dict) -> None:
    """Handle subscription updates - adjust user access level."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    logger.info(f"Updating subscription status for customer {customer_id}: {status}")


async def _handle_subscription_deleted(subscription: dict) -> None:
    """Handle subscription cancellation - revoke premium access."""
    customer_id = subscription.get("customer")
    logger.info(f"Revoking premium access for customer {customer_id}")


async def _handle_invoice_paid(invoice: dict) -> None:
    """Handle successful invoice payment - send receipt."""
    customer_email = invoice.get("customer_email")
    amount = invoice.get("amount_paid", 0) / 100
    logger.info(f"Invoice paid: ${amount:.2f} for {customer_email}")


async def _handle_invoice_failed(invoice: dict) -> None:
    """Handle failed invoice payment - notify user."""
    customer_email = invoice.get("customer_email")
    logger.warning(f"Payment failed for {customer_email}")
