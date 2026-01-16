"""
Stripe service for payment processing.

Handles payment intents, subscriptions, and webhook events.
"""
import stripe
from typing import Optional
from pydantic import BaseModel
from app.config import get_settings

settings = get_settings()

# Initialize Stripe with API key
stripe.api_key = settings.stripe_secret_key


class PaymentIntentResponse(BaseModel):
    """Payment intent creation response."""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str


class SubscriptionResponse(BaseModel):
    """Subscription creation response."""
    subscription_id: str
    client_secret: Optional[str]
    status: str
    current_period_end: int


async def create_payment_intent(
    amount: int,
    currency: str = "usd",
    customer_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> PaymentIntentResponse:
    """
    Create a payment intent for one-time payment.
    
    Args:
        amount: Amount in cents (e.g., 4999 for $49.99)
        currency: Currency code (default: usd)
        customer_id: Optional Stripe customer ID
        metadata: Optional metadata dict
    
    Returns:
        PaymentIntentResponse with client_secret for frontend
    """
    intent_params = {
        "amount": amount,
        "currency": currency,
        "automatic_payment_methods": {"enabled": True},
    }
    
    if customer_id:
        intent_params["customer"] = customer_id
    if metadata:
        intent_params["metadata"] = metadata
    
    intent = stripe.PaymentIntent.create(**intent_params)
    
    return PaymentIntentResponse(
        client_secret=intent.client_secret,
        payment_intent_id=intent.id,
        amount=intent.amount,
        currency=intent.currency,
    )


async def create_customer(
    email: str,
    name: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> str:
    """
    Create a Stripe customer.
    
    Returns:
        Stripe customer ID
    """
    customer_params = {"email": email}
    if name:
        customer_params["name"] = name
    if metadata:
        customer_params["metadata"] = metadata
    
    customer = stripe.Customer.create(**customer_params)
    return customer.id


async def create_subscription(
    customer_id: str,
    price_id: str,
    payment_method_id: Optional[str] = None,
) -> SubscriptionResponse:
    """
    Create a subscription for a customer.
    
    Args:
        customer_id: Stripe customer ID
        price_id: Stripe price ID (e.g., price_xxxxx)
        payment_method_id: Optional payment method to attach
    
    Returns:
        SubscriptionResponse with subscription details
    """
    subscription_params = {
        "customer": customer_id,
        "items": [{"price": price_id}],
        "payment_behavior": "default_incomplete",
        "payment_settings": {"save_default_payment_method": "on_subscription"},
        "expand": ["latest_invoice.payment_intent"],
    }
    
    if payment_method_id:
        # Attach payment method to customer first
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id},
        )
    
    subscription = stripe.Subscription.create(**subscription_params)
    
    # Get client secret for incomplete subscriptions
    client_secret = None
    if subscription.latest_invoice and subscription.latest_invoice.payment_intent:
        client_secret = subscription.latest_invoice.payment_intent.client_secret
    
    return SubscriptionResponse(
        subscription_id=subscription.id,
        client_secret=client_secret,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
    )


async def cancel_subscription(subscription_id: str) -> dict:
    """Cancel a subscription immediately."""
    subscription = stripe.Subscription.delete(subscription_id)
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "canceled_at": subscription.canceled_at,
    }


async def get_subscription(subscription_id: str) -> dict:
    """Get subscription details."""
    subscription = stripe.Subscription.retrieve(subscription_id)
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
    }


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """
    Verify Stripe webhook signature.
    
    Args:
        payload: Raw request body
        sig_header: Stripe-Signature header value
    
    Returns:
        Parsed event object
    
    Raises:
        ValueError: If signature verification fails
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        return event
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid webhook signature")
