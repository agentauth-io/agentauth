"""
Payment API routes for Stripe integration.

Handles payment intents, subscriptions, and webhooks.
"""
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional

from app.config import get_settings
from app.schemas.payment import (
    CreatePaymentIntentRequest,
    CreatePaymentIntentResponse,
    CreateSubscriptionRequest,
    CreateSubscriptionResponse,
    SubscriptionStatusResponse,
    CancelSubscriptionResponse,
    PricingTier,
    PricingResponse,
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
async def create_payment_intent(request: CreatePaymentIntentRequest):
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
                email=request.customer_email
            )
        
        intent = await stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_id=customer_id,
            metadata=request.metadata,
        )
        
        return CreatePaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.payment_intent_id,
            amount=intent.amount,
            currency=intent.currency,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agent-purchase")
async def create_agent_purchase(
    authorization_code: str,
    amount: int,
    currency: str = "USD",
    description: str = "",
    customer_email: Optional[str] = None,
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
    
    try:
        # Create payment intent with metadata
        intent = await stripe_service.create_payment_intent(
            amount=amount,
            currency=currency.lower(),
            customer_id=None,
            metadata={
                "authorization_code": authorization_code,
                "source": "agentauth_ai_agent",
                "description": description,
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
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscribe", response_model=CreateSubscriptionResponse)
async def create_subscription(request: CreateSubscriptionRequest):
    """
    Create a subscription for a customer.
    
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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionStatusResponse)
async def get_subscription_status(subscription_id: str):
    """Get the status of a subscription."""
    try:
        subscription = await stripe_service.get_subscription(subscription_id)
        return SubscriptionStatusResponse(**subscription)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/subscriptions/{subscription_id}", response_model=CancelSubscriptionResponse)
async def cancel_subscription(subscription_id: str):
    """Cancel a subscription immediately."""
    try:
        result = await stripe_service.cancel_subscription(subscription_id)
        return CancelSubscriptionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.
    
    Processes payment and subscription events from Stripe.
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
        # Payment completed successfully
        payment_intent = event["data"]["object"]
        print(f"Payment succeeded: {payment_intent['id']}")
        # TODO: Update order status, send confirmation email, etc.
        
    elif event_type == "payment_intent.payment_failed":
        # Payment failed
        payment_intent = event["data"]["object"]
        print(f"Payment failed: {payment_intent['id']}")
        # TODO: Notify user, update order status
        
    elif event_type == "customer.subscription.created":
        subscription = event["data"]["object"]
        print(f"Subscription created: {subscription['id']}")
        # TODO: Grant access to user
        
    elif event_type == "customer.subscription.updated":
        subscription = event["data"]["object"]
        print(f"Subscription updated: {subscription['id']}")
        # TODO: Update user access level
        
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        print(f"Subscription canceled: {subscription['id']}")
        # TODO: Revoke access
        
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        print(f"Invoice paid: {invoice['id']}")
        # TODO: Send receipt
        
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        print(f"Invoice payment failed: {invoice['id']}")
        # TODO: Notify user, retry payment
    
    return {"received": True}
