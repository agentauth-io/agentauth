"""
AgentAuth Middleware Package
"""
from app.middleware.rate_limiter import RateLimitMiddleware, rate_limit_store, rate_limit_check
from app.middleware.api_keys import (
    generate_api_key,
    generate_api_key_sync,
    verify_api_key,
    get_api_key_optional,
    require_api_key,
    get_current_user_id,
    DEMO_KEY,
)
from app.middleware.idempotency import (
    IdempotencyMiddleware,
    generate_idempotency_key,
    get_idempotency_key,
    require_idempotency_key,
)
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.tenant_context import (
    TenantContextMiddleware,
    set_tenant_context,
    get_tenant_id,
    require_tenant_id,
    TenantAwareSession,
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
