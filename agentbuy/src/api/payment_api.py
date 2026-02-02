"""
AgentBuy - Voice Payment Demo API

Simplified API for the voice-to-payment demo.
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global payment agent
payment_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize payment agent."""
    global payment_agent
    from src.agent.payment_demo import PaymentDemoAgent
    
    payment_agent = PaymentDemoAgent()
    logger.info("Payment Demo API initialized")
    yield
    logger.info("Payment Demo API shutdown")


app = FastAPI(
    title="AgentBuy Payment Demo",
    description="Voice-to-Payment Demo showcasing AgentAuth + Stripe",
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


# Request/Response models
class PaymentRequest(BaseModel):
    text: str
    user_id: str = "demo_user"


class PaymentResponse(BaseModel):
    success: bool
    message: str
    amount: Optional[float] = None
    merchant: Optional[str] = None
    authorization_code: Optional[str] = None
    payment_id: Optional[str] = None
    steps: Optional[list] = None
    error: Optional[str] = None


# Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agentbuy-payment-demo"}


@app.post("/v1/pay", response_model=PaymentResponse)
async def process_payment(request: PaymentRequest):
    """
    Process a text payment command.
    
    Example: "Pay $10 for my Notion subscription"
    """
    if not payment_agent:
        raise HTTPException(503, "Service not initialized")
    
    result = await payment_agent.process_voice_command(
        text=request.text,
        user_id=request.user_id
    )
    
    return PaymentResponse(
        success=result.get("success", False),
        message=result.get("message", result.get("error", "Unknown error")),
        amount=result.get("amount"),
        merchant=result.get("merchant"),
        authorization_code=result.get("authorization_code"),
        payment_id=result.get("payment_id"),
        steps=result.get("steps"),
        error=result.get("error")
    )


@app.post("/v1/voice-pay", response_model=PaymentResponse)
async def process_voice_payment(
    audio: UploadFile = File(...),
    user_id: str = Form("demo_user")
):
    """
    Process a voice payment command.
    Upload audio file to transcribe and execute payment.
    """
    if not payment_agent:
        raise HTTPException(503, "Service not initialized")
    
    audio_bytes = await audio.read()
    
    result = await payment_agent.process_voice_command(
        audio_bytes=audio_bytes,
        user_id=user_id
    )
    
    return PaymentResponse(
        success=result.get("success", False),
        message=result.get("message", result.get("error", "Unknown error")),
        amount=result.get("amount"),
        merchant=result.get("merchant"),
        authorization_code=result.get("authorization_code"),
        payment_id=result.get("payment_id"),
        steps=result.get("steps"),
        error=result.get("error")
    )


@app.get("/v1/demo-scenarios")
async def get_demo_scenarios():
    """Get pre-defined demo scenarios to try."""
    return {
        "scenarios": [
            {
                "name": "SaaS Subscription",
                "command": "Pay $10 for my Notion subscription",
                "expected": "APPROVED"
            },
            {
                "name": "Cloud Hosting",
                "command": "Pay $24 for DigitalOcean hosting",
                "expected": "APPROVED"
            },
            {
                "name": "Food Delivery",
                "command": "Pay $25 for DoorDash lunch order",
                "expected": "APPROVED"
            },
            {
                "name": "Over Budget",
                "command": "Pay $500 for expensive software",
                "expected": "DENIED - Over spending limit"
            }
        ]
    }


def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))


if __name__ == "__main__":
    run()
