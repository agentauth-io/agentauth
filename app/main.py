"""
AgentAuth - Main Application Entry Point

The authorization layer for AI agent purchases.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.api import consents_router, authorize_router, verify_router
from app.models.database import init_db
from app.middleware import RateLimitMiddleware, generate_api_key, DEMO_KEY

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown."""
    # Startup: Initialize database tables
    # Note: In production, use Alembic migrations instead
    try:
        if settings.debug:
            await init_db()
    except Exception as e:
        print(f"Warning: Database init failed: {e}")
        # Continue anyway - API will work but DB operations will fail
    yield
    # Shutdown: cleanup if needed



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
    
    ### Authentication
    
    Use `X-API-Key` header or `Authorization: Bearer aa_live_xxx` for authenticated requests.
    Get an API key from `POST /v1/api-keys`.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Add rate limiting middleware (before CORS)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,
    api_key_requests_per_minute=1000,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(consents_router)
app.include_router(authorize_router)
app.include_router(verify_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AgentAuth",
        "version": "0.1.0",
        "description": "Authorization layer for AI agent purchases",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/v1/api-keys", tags=["API Keys"])
async def create_api_key(owner: str = "default"):
    """
    Generate a new API key.
    
    Returns the full API key - save it securely, it won't be shown again.
    """
    key_data = generate_api_key(owner)
    return {
        "key": key_data["key"],
        "key_id": key_data["key_id"],
        "owner": key_data["owner"],
        "created_at": key_data["created_at"],
        "message": "Save this key securely - it won't be shown again!",
    }


@app.get("/v1/demo-key", tags=["API Keys"])
async def get_demo_key():
    """Get a demo API key for testing."""
    return {
        "key": DEMO_KEY["key"],
        "key_id": DEMO_KEY["key_id"],
        "message": "Use this key for testing. In production, generate your own.",
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



