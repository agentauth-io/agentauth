"""
AgentAuth - Main Application Entry Point

The authorization layer for AI agent purchases.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.logging_config import setup_logging, api_logger

__version__ = "0.2.0"
from app.api import consents_router, authorize_router, verify_router, payments_router, dashboard_router, admin_router, limits_router, rules_router, analytics_router, webhooks_router, billing_router
from app.api.connect import router as connect_router
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import init_db, get_db
from app.middleware import RateLimitMiddleware, IdempotencyMiddleware, TenantContextMiddleware, SecurityHeadersMiddleware, generate_api_key, generate_api_key_sync, DEMO_KEY
from app.services.cache_service import close_redis, get_cache_service

settings = get_settings()

# Initialize logging first
setup_logging(
    level=settings.log_level,
    json_format=settings.log_json or settings.environment == "production"
)

# Initialize Sentry for error tracking (optional)
if settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,  # 10% of transactions
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
        )
        api_logger.info("Sentry error tracking initialized")
    except ImportError:
        api_logger.warning("sentry-sdk not installed, error tracking disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown."""
    api_logger.info("Starting AgentAuth API...")
    
    # Startup: Initialize database tables
    # Note: In production, use Alembic migrations instead
    try:
        if settings.debug:
            await init_db()
            api_logger.info("Database tables initialized")
    except Exception as e:
        api_logger.warning(f"Database init failed: {e}")
        # Continue anyway - API will work but DB operations will fail
    
    # Initialize Redis connection (optional - will fail gracefully if unavailable)
    try:
        cache = get_cache_service()
        api_logger.info("Redis cache service initialized")
    except Exception as e:
        api_logger.warning(f"Redis init failed (using in-memory fallback): {e}")
    
    # Initialize OpenTelemetry tracing (optional)
    try:
        from app.tracing import init_tracing
        init_tracing(app, service_name="agentauth")
        api_logger.info("OpenTelemetry tracing initialized")
    except Exception as e:
        api_logger.debug(f"Tracing init skipped: {e}")
    
    # Start background worker for async auth queue flushing
    try:
        from app.services.auth_service import start_background_worker
        start_background_worker()
        api_logger.info("Authorization background worker started")
    except Exception as e:
        api_logger.warning(f"Background worker failed: {e}")
    
    api_logger.info("AgentAuth API started successfully")
    yield
    
    # Shutdown
    api_logger.info("Shutting down AgentAuth API...")
    try:
        await close_redis()
        api_logger.info("Redis connection closed")
    except Exception:
        pass
    api_logger.info("AgentAuth API shutdown complete")



# Create FastAPI application
app = FastAPI(
    title="AgentAuth",
    description="""
    ## The Authorization Layer for AI Agent Purchases
    
    AgentAuth provides cryptographic proof that a human authorized an AI agent's purchase.
    
    ### Core Flows
    
    1. **Consent** (`POST /v1/consents`)
       - User authorizes agent with spending limits
       - Returns delegation token for agent
    
    2. **Authorize** (`POST /v1/authorize`)
       - Agent requests permission for specific transaction
       - Returns ALLOW/DENY decision
    
    3. **Verify** (`POST /v1/verify`)
       - Merchant verifies authorization code
       - Returns consent proof for chargeback defense
    
    ### Spending Controls
    
    4. **Limits** (`/v1/limits`)
       - Set daily, monthly, per-transaction limits
       - View current usage
    
    5. **Rules** (`/v1/rules`)
       - Merchant whitelists/blacklists
       - Category controls
    
    ### Authentication
    
    Use `X-API-Key` header or `Authorization: Bearer aa_live_xxx` for authenticated requests.
    Get an API key from `POST /v1/api-keys`.
    """,
    version=__version__,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan,
)


# Add request ID middleware (outermost, runs first)
import uuid as _uuid
from starlette.middleware.base import BaseHTTPMiddleware as _BaseMiddleware

class RequestIDMiddleware(_BaseMiddleware):
    """Adds X-Request-ID header to all responses for tracing."""
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(_uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware (before CORS)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,
    api_key_requests_per_minute=1000,
)

# Add idempotency middleware for transaction safety
app.add_middleware(IdempotencyMiddleware)

# Add tenant context middleware for RLS
app.add_middleware(TenantContextMiddleware)

# Configure CORS with proper origins
allowed_origins = settings.cors_origins
if settings.debug:
    # In development, use specific localhost origins (wildcard + credentials is invalid per CORS spec)
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# Register routers
app.include_router(consents_router)
app.include_router(authorize_router)
app.include_router(verify_router)
app.include_router(payments_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(limits_router)
app.include_router(rules_router)
app.include_router(analytics_router)
app.include_router(webhooks_router)
app.include_router(billing_router)
app.include_router(connect_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AgentAuth",
        "version": __version__,
        "description": "Authorization layer for AI agent purchases",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Basic health check endpoint for load balancers."""
    return {"status": "healthy"}


@app.get("/health/detailed", tags=["Health"])
async def health_detailed():
    """Detailed health check with component status."""
    from app.models.database import async_engine
    from app.services.cache_service import get_cache_service
    from sqlalchemy import text
    import time
    
    checks = {
        "api": {"status": "healthy", "latency_ms": 0},
        "database": {"status": "unknown", "latency_ms": 0},
        "cache": {"status": "unknown", "latency_ms": 0},
    }
    overall_status = "healthy"
    
    # Check database
    try:
        start = time.perf_counter()
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"]["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        checks["database"]["status"] = "healthy"
    except Exception as e:
        checks["database"]["status"] = "unhealthy"
        checks["database"]["error"] = str(e)
        overall_status = "degraded"
    
    # Check Redis cache
    try:
        start = time.perf_counter()
        cache = get_cache_service()
        await cache.ping()
        checks["cache"]["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        checks["cache"]["status"] = "healthy"
    except Exception as e:
        checks["cache"]["status"] = "unavailable"
        checks["cache"]["error"] = str(e)
        # Cache is optional, don't degrade status
    
    return {
        "status": overall_status,
        "version": __version__,
        "environment": settings.environment,
        "checks": checks,
    }


@app.post("/v1/api-keys", tags=["API Keys"])
async def create_api_key_endpoint(
    owner: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key.

    In development: open for testing.
    In production: requires admin authentication (POST /v1/admin/api-keys instead).
    """
    if settings.environment == "production":
        raise HTTPException(
            status_code=403,
            detail="Use POST /v1/admin/login to authenticate, then POST /v1/admin/api-keys to generate keys."
        )
    key_data = await generate_api_key(db, owner)
    return {
        "key": key_data["key"],
        "key_id": key_data["key_id"],
        "owner": key_data["owner"],
        "created_at": key_data["created_at"],
        "message": "Save this key securely - it won't be shown again!",
    }


@app.get("/v1/demo-key", tags=["API Keys"])
async def get_demo_key():
    """Get a demo API key for testing. Only available in development."""
    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "key": DEMO_KEY["key"],
        "key_id": DEMO_KEY["key_id"],
        "message": "Use this key for testing. In production, generate your own.",
    }


@app.post("/v1/test-key", tags=["API Keys"])
async def create_test_key(
    owner: str = "test",
    db: AsyncSession = Depends(get_db),
):
    """Create a test API key. Only available in development."""
    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")
    key_data = await generate_api_key(db, owner)
    return {
        "key": key_data["key"],
        "key_id": key_data["key_id"],
        "owner": owner,
        "message": "Test key created. Development only!",
    }


@app.get("/demo", response_class=HTMLResponse, tags=["Demo"])
async def demo():
    """Serve the demo UI."""
    demo_path = Path(__file__).parent.parent / "demo.html"
    if demo_path.exists():
        return demo_path.read_text()
    return HTMLResponse(
        content="<h1>Demo not found</h1><p>demo.html not available</p>",
        status_code=404
    )


@app.get("/landing", response_class=HTMLResponse, tags=["Landing"])
async def landing():
    """Serve the landing page."""
    landing_path = Path(__file__).parent.parent / "landing.html"
    if landing_path.exists():
        return landing_path.read_text()
    return HTMLResponse(
        content="<h1>Landing page not found</h1>",
        status_code=404
    )


@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Get system metrics including cache stats."""
    try:
        cache = get_cache_service()
        cache_stats = await cache.get_stats()
    except Exception:
        cache_stats = {"status": "unavailable"}
    
    return {
        "cache": cache_stats,
        "infrastructure": {
            "rate_limiting": "enabled",
            "idempotency": "enabled",
            "velocity_checks": "enabled"
        }
    }
