"""
Authorization schemas - request/response models for /v1/authorize
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Transaction details for authorization check."""
    amount: float = Field(
        ...,
        gt=0,
        le=1_000_000,  # Maximum $1M per transaction
        description="Transaction amount (must be positive and <= $1,000,000)",
        examples=[347.00]
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",  # ISO 4217 currency code format
        description="ISO 4217 currency code (uppercase, 3 letters)"
    )
    merchant_id: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Unique merchant identifier (1-255 characters)",
        examples=["delta_airlines"]
    )
    merchant_name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Human-readable merchant name (1-255 characters)",
        examples=["Delta Airlines"]
    )
    merchant_category: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        description="Merchant Category Code (MCC, 1-50 characters)",
        examples=["4511"]
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description="Transaction description (max 1000 characters)"
    )


class AuthorizeRequest(BaseModel):
    """Request body for authorization check."""
    delegation_token: str = Field(
        ...,
        description="JWT delegation token from consent creation"
    )
    action: str = Field(
        default="payment",
        description="Action type being authorized",
        examples=["payment", "search", "compare"]
    )
    transaction: Transaction

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "delegation_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "action": "payment",
                    "transaction": {
                        "amount": 347.00,
                        "currency": "USD",
                        "merchant_id": "delta_airlines",
                        "merchant_name": "Delta Airlines"
                    }
                }
            ]
        }
    }


class AuthorizeResponse(BaseModel):
    """Response from authorization check."""
    decision: Literal["ALLOW", "DENY", "STEP_UP"] = Field(
        ...,
        description="Authorization decision"
    )
    authorization_code: str | None = Field(
        None,
        description="One-time code for merchant to verify (only if ALLOW)"
    )
    expires_at: datetime | None = Field(
        None,
        description="When the authorization code expires"
    )
    consent_id: str | None = Field(
        None,
        description="Reference to the original consent"
    )
    reason: str | None = Field(
        None,
        description="Reason code for denial",
        examples=["amount_exceeded", "currency_mismatch", "merchant_not_allowed"]
    )
    message: str | None = Field(
        None,
        description="Human-readable explanation"
    )
    step_up_url: str | None = Field(
        None,
        description="URL for user confirmation (only if STEP_UP)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "decision": "ALLOW",
                    "authorization_code": "authz_xyz789abc",
                    "expires_at": "2026-01-11T15:05:00Z",
                    "consent_id": "cons_abc123xyz"
                },
                {
                    "decision": "DENY",
                    "reason": "amount_exceeded",
                    "message": "Transaction amount $600 exceeds consent limit of $500"
                }
            ]
        }
    }
