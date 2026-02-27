"""
Pydantic schemas for payment-related requests and responses.
"""

from pydantic import BaseModel, EmailStr


class CreatePaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""
    amount: int  # Amount in cents
    currency: str = "usd"
    customer_email: EmailStr | None = None
    metadata: dict | None = None


class CreatePaymentIntentResponse(BaseModel):
    """Response with payment intent details."""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str


class CreateSubscriptionRequest(BaseModel):
    """Request to create a subscription."""
    email: EmailStr
    name: str | None = None
    price_id: str
    payment_method_id: str | None = None


class CreateSubscriptionResponse(BaseModel):
    """Response with subscription details."""
    subscription_id: str
    customer_id: str
    client_secret: str | None
    status: str
    current_period_end: int


class SubscriptionStatusResponse(BaseModel):
    """Response with subscription status."""
    subscription_id: str
    status: str
    current_period_start: int
    current_period_end: int
    cancel_at_period_end: bool


class CancelSubscriptionResponse(BaseModel):
    """Response when canceling a subscription."""
    subscription_id: str
    status: str
    canceled_at: int | None


class PricingTier(BaseModel):
    """Pricing tier information."""
    id: str
    name: str
    price: int  # Monthly price in cents
    api_calls: str
    features: list[str]


class PricingResponse(BaseModel):
    """Available pricing tiers."""
    tiers: list[PricingTier]
