"""
Common validation utilities and base schemas for AgentAuth.

Provides shared validation logic across all schemas.
"""
import hashlib
import re

from pydantic import BaseModel, Field, model_validator
from pydantic.types import constr

# =============================================================================
# COMMON CONSTRAINTS
# =============================================================================

# Identifier patterns
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
MERCHANT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
CONSENT_ID_PATTERN = re.compile(r'^cons_[a-zA-Z0-9_-]{16,64}$')
TRANSACTION_ID_PATTERN = re.compile(r'^txn_[a-zA-Z0-9_-]{16,64}$')

# Currency codes (ISO 4217)
VALID_CURRENCIES = {
    'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD',
    'MXN', 'SGD', 'HKD', 'NOK', 'KRW', 'TRY', 'RUB', 'INR', 'BRL', 'ZAR'
}

# Valid action types
VALID_ACTIONS = {'payment', 'search', 'compare', 'subscribe', 'transfer'}

# Maximum values
MAX_AMOUNT = 1_000_000  # $1M max transaction
MAX_STRING_LENGTH = 1000
MAX_LIST_LENGTH = 100


# =============================================================================
# COMMON VALIDATORS
# =============================================================================

def validate_identifier(value: str, pattern, field_name: str) -> str:
    """Validate identifier format."""
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if not pattern.match(value):
        raise ValueError(
            f"Invalid {field_name} format. Must be 1-64 alphanumeric characters, hyphens, or underscores"
        )
    return value


def validate_amount(amount: float, max_amount: float = MAX_AMOUNT) -> float:
    """Validate transaction amount."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if amount > max_amount:
        raise ValueError(f"Amount exceeds maximum allowed: ${max_amount}")
    # Check for reasonable decimal places
    if round(amount, 2) != amount:
        raise ValueError("Amount cannot have more than 2 decimal places")
    return amount


def validate_currency(currency: str) -> str:
    """Validate currency code."""
    currency = currency.upper()
    if currency not in VALID_CURRENCIES:
        raise ValueError(f"Invalid currency code. Must be one of: {', '.join(sorted(VALID_CURRENCIES))}")
    return currency


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Sanitize string input."""
    if not value:
        return value

    # Strip whitespace
    value = value.strip()

    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]

    return value


def compute_input_hash(value: str) -> str:
    """Compute SHA-256 hash of input for logging (not storing)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class AgentAuthBaseModel(BaseModel):
    """
    Base model for all AgentAuth schemas.

    Provides common validation and configuration.
    """

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid",  # Reject unknown fields
    }


class PaginationParams(AgentAuthBaseModel):
    """Standard pagination parameters."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DateRangeParams(AgentAuthBaseModel):
    """Date range filtering parameters."""
    start_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")
        return self


# =============================================================================
# CUSTOM CONSTR FOR VALIDATED STRINGS
# =============================================================================

# User ID: alphanumeric, hyphens, underscores, 1-64 chars
UserId = constr(pattern=USER_ID_PATTERN, min_length=1, max_length=64)

# Merchant ID: same as user ID
MerchantId = constr(pattern=MERCHANT_ID_PATTERN, min_length=1, max_length=64)

# Consent ID: starts with cons_
ConsentId = constr(pattern=CONSENT_ID_PATTERN, min_length=20, max_length=64)

# Currency: 3 uppercase letters
CurrencyCode = constr(pattern=r'^[A-Z]{3}$', min_length=3, max_length=3)

# Amount: positive number with max 2 decimal places
PositiveAmount = Field(..., gt=0, le=MAX_AMOUNT)


# =============================================================================
# ERROR RESPONSES
# =============================================================================

class ErrorDetail(AgentAuthBaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable message")
    field: str | None = Field(default=None, description="Field that caused the error")
    details: dict | None = Field(default=None, description="Additional error details")


class ErrorResponse(AgentAuthBaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: list[ErrorDetail] | None = Field(default=None, description="Detailed errors")
    request_id: str | None = Field(default=None, description="Request ID for debugging")

    @classmethod
    def from_exception(cls, error: Exception, request_id: str | None = None) -> "ErrorResponse":
        """Create error response from exception."""
        return cls(
            error=error.__class__.__name__,
            message=str(error),
            request_id=request_id
        )


class ValidationErrorResponse(ErrorResponse):
    """Validation error response."""
    error: str = "validation_error"

    @classmethod
    def from_validation_errors(
        cls,
        errors: list[dict],
        request_id: str | None = None
    ) -> "ValidationErrorResponse":
        """Create validation error response from Pydantic errors."""
        details = []
        for error in errors:
            loc = error.get("loc", [])
            field = ".".join(str(l) for l in loc[1:]) if loc else None

            details.append(ErrorDetail(
                code=error.get("type", "invalid"),
                message=error.get("msg", "Validation failed"),
                field=field,
            ))

        return cls(
            error="validation_error",
            message="Request validation failed",
            details=details,
            request_id=request_id
        )
