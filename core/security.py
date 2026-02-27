"""
AgentAuth Core - Security Configuration
=======================================
PROPRIETARY AND CONFIDENTIAL

This file defines security policies and access controls for the core module.
Modify with extreme caution.

ACCESS LEVELS:
- OWNER: Full access to all operations including master secret export
- ADMIN: Can manage policies and view audit logs
- OPERATOR: Can authorize transactions only
- AUDITOR: Read-only access to audit logs

SECURITY NOTES:
1. Master secret should be stored in HSM in production
2. All key operations should be logged
3. Rotate keys periodically (recommended: 90 days)
4. Keep audit logs for minimum 7 years for compliance
"""

from enum import IntEnum


class AccessLevel(IntEnum):
    """Access levels for core operations."""
    NONE = 0
    AUDITOR = 10      # Read audit logs only
    OPERATOR = 20     # Authorize transactions
    ADMIN = 30        # Manage policies
    OWNER = 100       # Full access


# Operations and required access levels
OPERATION_ACCESS = {
    # Authorization
    "authorize": AccessLevel.OPERATOR,
    "verify_token": AccessLevel.OPERATOR,
    "revoke_token": AccessLevel.ADMIN,

    # Policy management
    "add_policy": AccessLevel.ADMIN,
    "remove_policy": AccessLevel.ADMIN,
    "get_policy": AccessLevel.OPERATOR,
    "list_policies": AccessLevel.OPERATOR,

    # User/Agent management
    "set_user_limits": AccessLevel.ADMIN,
    "set_agent_trust": AccessLevel.ADMIN,
    "get_user_spending": AccessLevel.OPERATOR,

    # Audit
    "get_audit_log": AccessLevel.AUDITOR,
    "verify_audit_chain": AccessLevel.AUDITOR,
    "export_audit": AccessLevel.ADMIN,

    # System (sensitive)
    "export_master_secret": AccessLevel.OWNER,
    "export_public_keys": AccessLevel.ADMIN,
    "get_stats": AccessLevel.OPERATOR,
}


# Security configuration
SECURITY_CONFIG = {
    # Token settings
    "default_token_ttl_seconds": 3600,      # 1 hour
    "max_token_ttl_seconds": 86400,         # 24 hours
    "token_one_time_above_amount": 100.0,   # One-time tokens for high value

    # Rate limiting
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000,
    "rate_limit_per_day": 10000,
    "burst_limit": 10,

    # Spending defaults
    "default_daily_limit": 500.0,
    "default_monthly_limit": 5000.0,
    "default_per_transaction_limit": 200.0,

    # Risk thresholds
    "risk_block_threshold": 0.8,    # Block if risk >= 80%
    "risk_review_threshold": 0.6,   # Require review if risk >= 60%

    # Audit settings
    "audit_retention_days": 2555,   # 7 years
    "audit_export_format": "jsonl",

    # Key rotation
    "key_rotation_days": 90,

    # Categories
    "blocked_categories": [
        "gambling",
        "crypto",
        "adult",
        "weapons",
        "drugs"
    ],

    "high_risk_categories": [
        "luxury",
        "jewelry",
        "gift_cards",
        "money_transfer"
    ],
}


# Trusted merchants (lower risk score)
TRUSTED_MERCHANTS = {
    "amazon",
    "walmart",
    "target",
    "costco",
    "apple",
    "best buy",
    "home depot",
    "whole foods",
    "trader joes",
    "safeway",
    "kroger",
    "uber",
    "lyft",
    "doordash",
    "grubhub",
}


def check_access(operation: str, access_level: AccessLevel) -> bool:
    """
    Check if an access level is sufficient for an operation.

    Args:
        operation: The operation being performed
        access_level: The access level of the caller

    Returns:
        True if access is allowed
    """
    required = OPERATION_ACCESS.get(operation, AccessLevel.OWNER)
    return access_level >= required


def get_required_access(operation: str) -> AccessLevel:
    """Get the required access level for an operation."""
    return OPERATION_ACCESS.get(operation, AccessLevel.OWNER)
