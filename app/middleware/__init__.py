"""
AgentAuth Middleware Package
"""

from app.middleware.api_keys import (
    DEMO_KEY,
    generate_api_key,
    generate_api_key_sync,
    get_api_key_optional,
    get_current_user_id,
    require_api_key,
    verify_api_key,
)
from app.middleware.idempotency import (
    IdempotencyMiddleware,
    generate_idempotency_key,
    get_idempotency_key,
    require_idempotency_key,
)
from app.middleware.rate_limiter import (
    RateLimitMiddleware,
    rate_limit_check,
    rate_limit_store,
)
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.tenant_context import (
    TenantAwareSession,
    TenantContextMiddleware,
    get_tenant_id,
    require_tenant_id,
    set_tenant_context,
)

__all__ = [
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "rate_limit_store",
    "rate_limit_check",
    "generate_api_key",
    "generate_api_key_sync",
    "verify_api_key",
    "get_api_key_optional",
    "require_api_key",
    "get_current_user_id",
    "DEMO_KEY",
    "IdempotencyMiddleware",
    "generate_idempotency_key",
    "get_idempotency_key",
    "require_idempotency_key",
    "TenantContextMiddleware",
    "set_tenant_context",
    "get_tenant_id",
    "require_tenant_id",
    "TenantAwareSession",
]
