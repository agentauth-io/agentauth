"""
Token Service - JWT token generation and verification

This is the heart of AgentAuth. Tokens encode consent constraints
and allow offline verification without database lookups.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

settings = get_settings()


@dataclass
class TokenPayload:
    """Decoded token payload."""
    consent_id: str
    user_id: str
    max_amount: float
    currency: str
    allowed_merchants: list[str] | None
    allowed_categories: list[str] | None
    intent_description: str
    issued_at: datetime
    expires_at: datetime
    single_use: bool


@dataclass
class TokenVerificationResult:
    """Result of token verification."""
    valid: bool
    payload: TokenPayload | None = None
    reason: str | None = None
    message: str | None = None


class TokenService:
    """
    JWT Token Service for delegation tokens.

    Creates tokens that:
    - Encode consent constraints (max_amount, currency, merchants)
    - Are cryptographically signed
    - Can be verified without database lookup
    """

    def __init__(self, secret_key: str = None, algorithm: str = None):
        self.secret_key = secret_key or settings.secret_key
        self.algorithm = algorithm or settings.jwt_algorithm

    def create_delegation_token(
        self,
        consent_id: str,
        user_id: str,
        intent_description: str,
        max_amount: float,
        currency: str,
        allowed_merchants: list[str] | None = None,
        allowed_categories: list[str] | None = None,
        expires_at: datetime = None,
        single_use: bool = True,
    ) -> str:
        """
        Create a delegation token with embedded constraints.

        The token itself contains all constraints needed for authorization
        decisions, enabling offline verification.
        """
        now = datetime.now(timezone.utc)

        if expires_at is None:
            expires_at = now + timedelta(seconds=settings.token_expiry_seconds)

        payload = {
            # Standard JWT claims
            "iat": now,
            "exp": expires_at,
            "iss": "agentauth",
            "sub": user_id,

            # AgentAuth claims
            "consent_id": consent_id,
            "intent": intent_description,

            # Constraints (the key part)
            "constraints": {
                "max_amount": max_amount,
                "currency": currency,
                "allowed_merchants": allowed_merchants,
                "allowed_categories": allowed_categories,
            },

            # Options
            "single_use": single_use,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(
        self,
        token: str,
        request_amount: float | None = None,
        request_currency: str | None = None,
        request_merchant_id: str | None = None,
        request_merchant_category: str | None = None,
    ) -> TokenVerificationResult:
        """
        Verify a delegation token and optionally check against a transaction.

        This is where the magic happens:
        1. Verify JWT signature (is it from us?)
        2. Check expiration (is it still valid?)
        3. Check constraints (is the transaction allowed?)
        """
        try:
            # Decode and verify signature
            decoded = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer="agentauth"
            )
        except jwt.ExpiredSignatureError:
            return TokenVerificationResult(
                valid=False,
                reason="token_expired",
                message="Delegation token has expired"
            )
        except jwt.InvalidTokenError as e:
            return TokenVerificationResult(
                valid=False,
                reason="invalid_token",
                message=f"Invalid token: {str(e)}"
            )

        # Extract constraints
        constraints = decoded.get("constraints", {})
        max_amount = constraints.get("max_amount")
        currency = constraints.get("currency")
        allowed_merchants = constraints.get("allowed_merchants")
        allowed_categories = constraints.get("allowed_categories")

        # Create payload object
        payload = TokenPayload(
            consent_id=decoded.get("consent_id"),
            user_id=decoded.get("sub"),
            max_amount=max_amount,
            currency=currency,
            allowed_merchants=allowed_merchants,
            allowed_categories=allowed_categories,
            intent_description=decoded.get("intent"),
            issued_at=datetime.fromtimestamp(decoded.get("iat")),
            expires_at=datetime.fromtimestamp(decoded.get("exp")),
            single_use=decoded.get("single_use", True),
        )

        # If no transaction provided, just validate the token itself
        if request_amount is None:
            return TokenVerificationResult(valid=True, payload=payload)

        # Check amount constraint
        if max_amount is not None and request_amount > max_amount:
            return TokenVerificationResult(
                valid=False,
                payload=payload,
                reason="amount_exceeded",
                message=f"Transaction amount ${request_amount} exceeds consent limit of ${max_amount}"
            )

        # Check currency constraint
        if currency is not None and request_currency and request_currency != currency:
            return TokenVerificationResult(
                valid=False,
                payload=payload,
                reason="currency_mismatch",
                message=f"Transaction currency {request_currency} does not match consent currency {currency}"
            )

        # Check merchant constraint
        if allowed_merchants and request_merchant_id:
            if request_merchant_id not in allowed_merchants:
                return TokenVerificationResult(
                    valid=False,
                    payload=payload,
                    reason="merchant_not_allowed",
                    message=f"Merchant {request_merchant_id} is not in the allowed list"
                )

        # Check category constraint
        if allowed_categories and request_merchant_category:
            if request_merchant_category not in allowed_categories:
                return TokenVerificationResult(
                    valid=False,
                    payload=payload,
                    reason="category_not_allowed",
                    message=f"Merchant category {request_merchant_category} is not in the allowed list"
                )

        # All checks passed
        return TokenVerificationResult(valid=True, payload=payload)

    def create_proof_token(
        self,
        consent_id: str,
        authorization_code: str,
        user_intent: str,
        max_amount: float,
        actual_amount: float,
        currency: str,
        verified_at: datetime,
    ) -> str:
        """
        Create a proof token for merchant chargeback defense.

        This token proves that:
        - User consented to this type of purchase
        - The amount was within limits
        - AgentAuth verified the authorization
        """
        payload = {
            "iat": verified_at,
            "iss": "agentauth",
            "type": "consent_proof",
            "consent_id": consent_id,
            "authorization_code": authorization_code,
            "user_intent": user_intent,
            "max_authorized_amount": max_amount,
            "actual_amount": actual_amount,
            "currency": currency,
            "verified_at": verified_at.isoformat(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


# Singleton instance
token_service = TokenService()
