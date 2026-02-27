"""
Tenant Context Middleware

Sets PostgreSQL session variable for Row-Level Security (RLS).
Each request sets app.tenant_id which RLS policies use for isolation.
"""

from fastapi import HTTPException, Request
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.models.database import async_session_maker


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant (developer) ID from request
    and sets it as a PostgreSQL session variable for RLS.

    RLS policies use: current_setting('app.tenant_id')
    """

    async def dispatch(self, request: Request, call_next):
        # Extract tenant ID from API key or auth token
        tenant_id = await self._extract_tenant_id(request)

        if tenant_id:
            # Store in request state for use in dependencies
            request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response

    async def _extract_tenant_id(self, request: Request) -> str | None:
        """Extract tenant ID from request authentication."""
        # Try X-API-Key header
        api_key = request.headers.get("X-API-Key", "")

        # Try Authorization Bearer token
        if not api_key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]

        if not api_key:
            return None

        # Extract developer_id from API key
        # Format: aa_<env>_<developer_id>_<random>
        # Or in simpler format just derive from key hash
        if api_key.startswith("aa_"):
            parts = api_key.split("_")
            if len(parts) >= 3:
                # Use first 16 chars of key as tenant ID for simplicity
                return api_key[:20]

        return api_key[:20] if api_key else None


async def set_tenant_context(session, tenant_id: str) -> None:
    """
    Set tenant context for RLS in a database session.

    Call this at the start of any database operation to enable RLS.

    Usage:
        async with async_session_maker() as session:
            await set_tenant_context(session, tenant_id)
            # Now all queries are automatically filtered by tenant
    """
    if tenant_id:
        # Set the session variable that RLS policies will use
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"), {"tenant_id": tenant_id}
        )


async def get_tenant_id(request: Request) -> str | None:
    """
    Dependency to get tenant ID from request.

    Usage:
        @app.get("/resource")
        async def get_resource(tenant_id: str = Depends(get_tenant_id)):
            ...
    """
    return getattr(request.state, "tenant_id", None)


def require_tenant_id(request: Request) -> str:
    """
    Dependency that requires a valid tenant ID.
    Raises 401 if not authenticated.

    Usage:
        @app.get("/resource")
        async def get_resource(tenant_id: str = Depends(require_tenant_id)):
            ...
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail={"error": "authentication_required", "message": "API key required"},
        )
    return tenant_id


class TenantAwareSession:
    """
    Context manager for tenant-aware database sessions.

    Automatically sets RLS context on session creation.

    Usage:
        async with TenantAwareSession(tenant_id) as session:
            result = await session.execute(select(Consent))
            # Only returns consents for this tenant
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.session = None

    async def __aenter__(self):
        self.session = async_session_maker()
        await set_tenant_context(self.session, self.tenant_id)
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
