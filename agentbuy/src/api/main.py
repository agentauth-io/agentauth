"""
AgentBuy - FastAPI Application

REST API for the Universal AI Purchase Agent.
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

from ..agent.orchestrator import AgentOrchestrator, ExecutionResult
from ..connectors.starbucks import StarbucksConnector

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global instances
orchestrator: Optional[AgentOrchestrator] = None


class DemoOrchestrator:
    """
    Demo orchestrator that works without OpenAI.
    Uses simple keyword matching for intent parsing.
    """
    
    def __init__(self, agentauth_client, connectors):
        self.agentauth = agentauth_client
        self.connectors = connectors
        self.pending_orders = {}
    
    async def execute_command(self, text: str, user_id: str, delegation_token: str):
        """Demo command execution with keyword matching."""
        text_lower = text.lower()
        
        # Simple keyword-based platform detection
        platform = "starbucks" if "starbucks" in text_lower or "coffee" in text_lower or "latte" in text_lower else None
        
        if not platform:
            return ExecutionResult(
                success=False,
                message="Demo mode: mention 'Starbucks', 'coffee', or 'latte' to try the demo",
                error="platform_not_detected"
            )
        
        connector = self.connectors.get(platform)
        if not connector:
            return ExecutionResult(
                success=False,
                message=f"Platform {platform} not available",
                error="no_connector"
            )
        
        # Extract size (simple keyword match)
        size = "grande"  # default
        for s in ["tall", "grande", "venti", "trenta"]:
            if s in text_lower:
                size = s
                break
        
        # Create demo item
        items = [{"name": "Iced Latte (Demo)", "size": size, "quantity": 1}]
        
        # Estimate price and authorize
        estimated_price = await connector.estimate_price(items)
        auth = await self.agentauth.authorize(
            delegation_token=delegation_token,
            amount=estimated_price,
            currency="USD",
            merchant_id=platform
        )
        
        if auth.decision != "ALLOW":
            return ExecutionResult(
                success=False,
                message=f"Not authorized: {auth.reason}",
                error="auth_denied"
            )
        
        # Create order
        order = await connector.create_order(
            items=items,
            authorization_code=auth.authorization_code,
            delivery=False,
            location="Demo Store"
        )
        
        self.pending_orders[order.order_id] = order
        
        return ExecutionResult(
            success=True,
            order=order,
            message=f"Demo order placed! {order.summary}",
            authorization_code=auth.authorization_code
        )
    
    async def get_order_status(self, order_id: str):
        order = self.pending_orders.get(order_id)
        if not order:
            return None
        connector = self.connectors.get(order.platform)
        return await connector.get_order_status(order_id) if connector else None
    
    async def cancel_order(self, order_id: str):
        order = self.pending_orders.get(order_id)
        if not order:
            return False
        connector = self.connectors.get(order.platform)
        if connector and await connector.cancel_order(order_id):
            del self.pending_orders[order_id]
            return True
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global orchestrator
    
    # Initialize OpenAI client (optional - for demo mode)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = AsyncOpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized")
    else:
        openai_client = None
        logger.warning("OPENAI_API_KEY not set - running in demo mode with mock parser")
    
    # Initialize connectors
    starbucks = StarbucksConnector()
    connectors = {"starbucks": starbucks}
    
    # Mock AgentAuth client for now (will use real SDK in production)
    class MockAgentAuth:
        async def authorize(self, delegation_token, amount, currency, merchant_id):
            class AuthResponse:
                decision = "ALLOW"
                authorization_code = f"auth_{os.urandom(8).hex()}"
                reason = None
            return AuthResponse()
    
    agentauth_client = MockAgentAuth()
    
    # Create orchestrator (with optional OpenAI)
    if openai_client:
        orchestrator = AgentOrchestrator(
            openai_client=openai_client,
            agentauth_client=agentauth_client,
            connectors=connectors
        )
    else:
        # Demo mode - create mock orchestrator
        orchestrator = DemoOrchestrator(
            agentauth_client=agentauth_client,
            connectors=connectors
        )
    
    logger.info("AgentBuy API initialized")
    yield
    
    # Cleanup
    await starbucks.close()
    logger.info("AgentBuy API shutdown")


app = FastAPI(
    title="AgentBuy API",
    description="Universal AI Purchase Agent - Voice/text-first autonomous purchasing",
    version="0.1.0",
    lifespan=lifespan
)

# CORS - Restricted origins
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "https://agentbuy.ai,https://www.agentbuy.ai").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ============== REQUEST/RESPONSE MODELS ==============

class CommandRequest(BaseModel):
    """Text command request."""
    text: str
    user_id: str
    delegation_token: Optional[str] = "mock_token"


class CommandResponse(BaseModel):
    """Command execution response."""
    success: bool
    message: str
    order_id: Optional[str] = None
    total_price: Optional[float] = None
    platform: Optional[str] = None
    estimated_ready: Optional[str] = None


class OrderStatusResponse(BaseModel):
    """Order status response."""
    order_id: str
    status: str
    message: str
    estimated_ready: Optional[str] = None


# ============== ENDPOINTS ==============

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "service": "agentbuy"}


@app.post("/v1/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    Execute a text command.
    
    Example:
        "Buy me a grande iced latte from Starbucks"
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await orchestrator.execute_command(
        text=request.text,
        user_id=request.user_id,
        delegation_token=request.delegation_token
    )
    
    return CommandResponse(
        success=result.success,
        message=result.message,
        order_id=result.order.order_id if result.order else None,
        total_price=result.order.total_price if result.order else None,
        platform=result.order.platform if result.order else None,
        estimated_ready=result.order.estimated_ready.isoformat() if result.order and result.order.estimated_ready else None
    )


@app.post("/v1/voice", response_model=CommandResponse)
async def execute_voice_command(
    audio: UploadFile = File(...),
    user_id: str = "anonymous",
    delegation_token: str = "mock_token"
):
    """
    Execute a voice command.
    
    Upload audio file (wav, mp3, webm) to transcribe and execute.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Read audio file
    audio_bytes = await audio.read()
    
    # Transcribe using OpenAI Whisper
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Save temporarily for API
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    
    try:
        with open(temp_path, "rb") as audio_file:
            transcript = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        logger.info(f"Transcribed: {transcript.text}")
        
        # Execute the transcribed command
        result = await orchestrator.execute_command(
            text=transcript.text,
            user_id=user_id,
            delegation_token=delegation_token
        )
        
        return CommandResponse(
            success=result.success,
            message=result.message,
            order_id=result.order.order_id if result.order else None,
            total_price=result.order.total_price if result.order else None,
            platform=result.order.platform if result.order else None,
            estimated_ready=result.order.estimated_ready.isoformat() if result.order and result.order.estimated_ready else None
        )
    finally:
        import os as os_module
        os_module.unlink(temp_path)


@app.get("/v1/orders/{order_id}", response_model=OrderStatusResponse)
async def get_order_status(order_id: str):
    """Get status of an order."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    status = await orchestrator.get_order_status(order_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderStatusResponse(
        order_id=status.order_id,
        status=status.status.value,
        message=status.message,
        estimated_ready=status.estimated_ready.isoformat() if status.estimated_ready else None
    )


@app.delete("/v1/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    success = await orchestrator.cancel_order(order_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Could not cancel order")
    
    return {"success": True, "message": "Order cancelled"}


def run():
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))


if __name__ == "__main__":
    run()
