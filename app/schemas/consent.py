"""
Consent schemas - request/response models for /v1/consents
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ConsentIntent(BaseModel):
    """User's intent - what they want to accomplish."""

    description: str = Field(
        ...,
        description="Human-readable description of intent",
        examples=["Buy cheapest flight to NYC"],
    )
    raw_input: str | None = Field(None, description="Original user input (voice/text)")


class ConsentConstraints(BaseModel):
    """Spending and merchant constraints."""

    max_amount: float = Field(
        ...,
        gt=0,
        le=10_000_000,  # Maximum $10M per consent
        description="Maximum amount in the specified currency (must be positive and <= $10,000,000)",
        examples=[500.0],
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",  # ISO 4217 currency code format
        description="ISO 4217 currency code (uppercase, 3 letters)",
        examples=["USD", "EUR", "GBP"],
    )
    allowed_merchants: list[str] | None = Field(
        None,
        max_length=100,  # Maximum 100 merchants in whitelist
        description="List of allowed merchant IDs (if restricted, max 100)",
    )
    allowed_categories: list[str] | None = Field(
        None,
        max_length=50,  # Maximum 50 categories
        description="List of allowed merchant category codes (MCCs, max 50)",
    )


class ConsentOptions(BaseModel):
    """Optional consent configuration."""

    expires_in_seconds: int = Field(
        default=3600,
        gt=0,
        le=86400 * 7,  # Max 7 days
        description="How long the consent is valid (seconds)",
    )
    single_use: bool = Field(
        default=True, description="Whether consent is consumed after one use"
    )
    requires_confirmation: bool = Field(
        default=False, description="Require step-up confirmation for final purchase"
    )


class ConsentCreate(BaseModel):
    """Request body for creating a new consent."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the user",
        examples=["user_123"],
    )
    intent: ConsentIntent
    constraints: ConsentConstraints
    options: ConsentOptions | None = Field(default_factory=ConsentOptions)
    signature: str = Field(
        ..., description="Digital signature over intent + constraints"
    )
    public_key: str = Field(..., description="User's public key for verification")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user_123",
                    "intent": {"description": "Buy cheapest flight to NYC"},
                    "constraints": {"max_amount": 500, "currency": "USD"},
                    "options": {"expires_in_seconds": 3600},
                    "signature": "base64_signature",
                    "public_key": "base64_public_key",
                }
            ]
        }
    }


class ConsentResponse(BaseModel):
    """Response after creating a consent."""

    consent_id: str = Field(..., description="Unique consent identifier")
    delegation_token: str = Field(..., description="JWT token for agent to use")
    expires_at: datetime = Field(..., description="When the consent expires")
    constraints: ConsentConstraints = Field(
        ..., description="The constraints that were set"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "consent_id": "cons_abc123xyz",
                    "delegation_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",  # nosec: B105 - Example JWT token, not a password
                    "expires_at": "2026-01-11T15:00:00Z",
                    "constraints": {"max_amount": 500, "currency": "USD"},
                }
            ]
        }
    }
