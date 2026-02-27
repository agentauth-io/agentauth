"""
Verification schemas - request/response models for /v1/verify
"""
from datetime import datetime

from pydantic import BaseModel, Field


class VerifyTransaction(BaseModel):
    """Transaction details for verification."""
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount being verified"
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code"
    )


class VerifyRequest(BaseModel):
    """Request body for merchant verification."""
    authorization_code: str = Field(
        ...,
        description="Authorization code from /authorize response"
    )
    transaction: VerifyTransaction
    merchant_id: str | None = Field(
        None,
        description="Merchant's identifier for additional validation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "authorization_code": "authz_xyz789abc",
                    "transaction": {
                        "amount": 347.00,
                        "currency": "USD"
                    }
                }
            ]
        }
    }


class ConsentProof(BaseModel):
    """Cryptographic proof of user consent for chargeback defense."""
    consent_id: str = Field(
        ...,
        description="Original consent identifier"
    )
    user_authorized_at: datetime = Field(
        ...,
        description="When the user created the consent"
    )
    user_intent: str = Field(
        ...,
        description="User's stated intent"
    )
    max_authorized_amount: float = Field(
        ...,
        description="Maximum amount user authorized"
    )
    actual_amount: float = Field(
        ...,
        description="Actual transaction amount"
    )
    currency: str = Field(
        ...,
        description="Currency of the transaction"
    )
    signature_valid: bool = Field(
        ...,
        description="Whether the user's signature was valid"
    )


class VerifyResponse(BaseModel):
    """Response from merchant verification."""
    valid: bool = Field(
        ...,
        description="Whether the authorization is valid"
    )
    authorization_id: str | None = Field(
        None,
        description="Unique authorization identifier"
    )
    consent_proof: ConsentProof | None = Field(
        None,
        description="Proof of consent for chargeback defense (if valid)"
    )
    verification_timestamp: datetime = Field(
        ...,
        description="When verification was performed"
    )
    proof_token: str | None = Field(
        None,
        description="Signed token containing the proof (store for disputes)"
    )
    error: str | None = Field(
        None,
        description="Error reason if not valid"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "valid": True,
                    "authorization_id": "auth_abc123",
                    "consent_proof": {
                        "consent_id": "cons_abc123xyz",
                        "user_authorized_at": "2026-01-11T14:00:00Z",
                        "user_intent": "Buy cheapest flight to NYC",
                        "max_authorized_amount": 500,
                        "actual_amount": 347,
                        "currency": "USD",
                        "signature_valid": True
                    },
                    "verification_timestamp": "2026-01-11T15:02:00Z",
                    "proof_token": "eyJ..."
                },
                {
                    "valid": False,
                    "verification_timestamp": "2026-01-11T15:02:00Z",
                    "error": "authorization_expired"
                }
            ]
        }
    }
