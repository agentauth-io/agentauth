"""
Stripe service for payment processing.

Handles payment intents, subscriptions, and webhook events.
"""

import stripe
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

# Initialize Stripe with API key and timeout
stripe.api_key = settings.stripe_secret_key
stripe.max_network_retries = 2
STRIPE_TIMEOUT = 15  # seconds


class PaymentIntentResponse(BaseModel):
    """Payment intent creation response."""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str


class SubscriptionResponse(BaseModel):
    """Subscription creation response."""
    subscription_id: str
    client_secret: str | None
    status: str
    current_period_end: int


async def create_payment_intent(
    amount: int,
    currency: str = "usd",
    customer_id: str | None = None,
    metadata: dict | None = None,
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

    intent = stripe.PaymentIntent.create(**intent_params, timeout=STRIPE_TIMEOUT)

    return PaymentIntentResponse(
        client_secret=intent.client_secret,
        payment_intent_id=intent.id,
        amount=intent.amount,
        currency=intent.currency,
    )


async def create_customer(
    email: str,
    name: str | None = None,
    metadata: dict | None = None,
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

    customer = stripe.Customer.create(**customer_params, timeout=STRIPE_TIMEOUT)
    return customer.id


async def create_subscription(
    customer_id: str,
    price_id: str,
    payment_method_id: str | None = None,
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
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id, timeout=STRIPE_TIMEOUT)
        stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id},
            timeout=STRIPE_TIMEOUT,
        )

    subscription = stripe.Subscription.create(**subscription_params, timeout=STRIPE_TIMEOUT)

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
    subscription = stripe.Subscription.delete(subscription_id, timeout=STRIPE_TIMEOUT)
    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "canceled_at": subscription.canceled_at,
    }


async def get_subscription(subscription_id: str) -> dict:
    """Get subscription details."""
    subscription = stripe.Subscription.retrieve(subscription_id, timeout=STRIPE_TIMEOUT)
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


# ============ Stripe Connect Functions ============

class ConnectAccountResponse(BaseModel):
    """Stripe Connect account response."""
    account_id: str
    onboarding_url: str | None = None
    details_submitted: bool = False
    charges_enabled: bool = False
    payouts_enabled: bool = False


async def create_connect_account(
    user_id: str,
    email: str,
    country: str = "US",
    account_type: str = "express",
) -> ConnectAccountResponse:
    """
    Create a Stripe Connect account for a user.

    Args:
        user_id: Internal user ID
        email: User's email
        country: Two-letter country code
        account_type: 'express', 'standard', or 'custom'

    Returns:
        ConnectAccountResponse with account details
    """
    account = stripe.Account.create(
        type=account_type,
        country=country,
        email=email,
        metadata={"user_id": user_id},
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
    )

    return ConnectAccountResponse(
        account_id=account.id,
        details_submitted=account.details_submitted,
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
    )


async def create_connect_onboarding_link(
    account_id: str,
    return_url: str,
    refresh_url: str,
) -> str:
    """
    Create an onboarding link for a Stripe Connect account.

    Args:
        account_id: Stripe Connect account ID
        return_url: URL to redirect after onboarding
        refresh_url: URL to redirect if link expires

    Returns:
        Onboarding URL
    """
    account_link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return account_link.url


async def get_connect_account(account_id: str) -> ConnectAccountResponse:
    """
    Get details of a Stripe Connect account.

    Args:
        account_id: Stripe Connect account ID

    Returns:
        ConnectAccountResponse with current status
    """
    account = stripe.Account.retrieve(account_id)
    return ConnectAccountResponse(
        account_id=account.id,
        details_submitted=account.details_submitted,
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
    )


async def create_connect_login_link(account_id: str) -> str:
    """
    Create a login link for a connected account's Stripe dashboard.

    Args:
        account_id: Stripe Connect account ID

    Returns:
        Dashboard login URL
    """
    login_link = stripe.Account.create_login_link(account_id)
    return login_link.url


async def list_connect_transactions(
    account_id: str,
    limit: int = 20,
) -> list:
    """
    List recent transactions for a connected account.

    Args:
        account_id: Stripe Connect account ID
        limit: Maximum number of transactions

    Returns:
        List of transaction objects
    """
    charges = stripe.Charge.list(
        limit=limit,
        stripe_account=account_id,
    )

    transactions = []
    for charge in charges.data:
        transactions.append({
            "id": charge.id,
            "amount": charge.amount / 100,  # Convert from cents
            "currency": charge.currency.upper(),
            "status": charge.status,
            "description": charge.description or "No description",
            "created_at": charge.created,
            "merchant": charge.metadata.get("merchant", "Unknown"),
        })

    return transactions


async def get_connect_balance(account_id: str) -> dict:
    """
    Get the balance for a connected account.

    Args:
        account_id: Stripe Connect account ID

    Returns:
        Balance details
    """
    balance = stripe.Balance.retrieve(stripe_account=account_id)

    return {
        "available": [
            {"amount": b.amount / 100, "currency": b.currency}
            for b in balance.available
        ],
        "pending": [
            {"amount": b.amount / 100, "currency": b.currency}
            for b in balance.pending
        ],
    }
