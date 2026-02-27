"""
Log redaction utilities for sensitive data.

Provides functions to redact sensitive information from logs.
"""

import re
from typing import Any

# Patterns for sensitive data
SENSITIVE_PATTERNS = [
    # API keys
    (r"aa_live_[a-zA-Z0-9_-]{32,}", "aa_live_***REDACTED***"),
    (r"aa_test_[a-zA-Z0-9_-]{32,}", "aa_test_***REDACTED***"),
    # JWT tokens
    (r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "***JWT_REDACTED***"),
    # Authorization codes
    (r"authz_[a-zA-Z0-9_-]{20,}", "authz_***REDACTED***"),
    # Consent IDs
    (r"cons_[a-zA-Z0-9_-]{20,}", "cons_***REDACTED***"),
    # Credit card numbers (basic pattern)
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "****-****-****-****"),
    # Email addresses
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***@***.***"),
    # Passwords in query params or JSON
    (r'["\']?password["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', "password=***REDACTED***"),
    (r'["\']?secret["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', "secret=***REDACTED***"),
    (r'["\']?api_key["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', "api_key=***REDACTED***"),
    (r'["\']?token["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?', "token=***REDACTED***"),
]


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive data from text.

    Args:
        text: Input text that may contain sensitive data

    Returns:
        Text with sensitive data redacted
    """
    if not text:
        return text

    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def redact_dict(
    data: dict[str, Any], keys_to_redact: set[str] | None = None
) -> dict[str, Any]:
    """
    Redact sensitive values from a dictionary.

    Args:
        data: Input dictionary
        keys_to_redict: Set of keys to redact (if None, uses default sensitive keys)

    Returns:
        Dictionary with sensitive values redacted
    """
    if keys_to_redact is None:
        keys_to_redact = {
            "password",
            "secret",
            "api_key",
            "token",
            "authorization",
            "credit_card",
            "ssn",
            "social_security_number",
            "pin",
            "cvv",
            "cvc",
            "auth_code",
            "delegation_token",
            "signature",
        }

    result = {}
    for key, value in data.items():
        if key.lower() in keys_to_redact:
            result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = redact_dict(value, keys_to_redact)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item, keys_to_redact) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str):
            result[key] = redact_sensitive_data(value)
        else:
            result[key] = value

    return result


def safe_log_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Safely log a dictionary by redacting sensitive data.

    This is a convenience wrapper around redact_dict for logging.

    Args:
        data: Dictionary to log

    Returns:
        Dictionary with sensitive data redacted
    """
    return redact_dict(data)
