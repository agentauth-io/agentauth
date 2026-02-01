"""
Stripe Connect API routes for connected accounts management.

Handles account linking, onboarding, and transaction tracking.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.database import get_db
from app.services import stripe_service
from app.config import get_settings
from app.middleware import require_api_key

settings = get_settings()

router = APIRouter(prefix="/v1/connect", tags=["Stripe Connect"])


# --- Request/Response Schemas ---

class CreateConnectAccountRequest(BaseModel):
    """Request to create a Stripe Connect account."""
    email: str
    country: str = "US"


class CreateConnectAccountResponse(BaseModel):
    """Response with Connect account details."""
    account_id: str
    onboarding_url: str


class ConnectAccountStatus(BaseModel):
    """Status of a connected account."""
    account_id: str
    details_submitted: bool
    charges_enabled: bool
    payouts_enabled: bool
    status: str  # 'pending', 'active', 'restricted'


class ConnectedAccountTransaction(BaseModel):
    """A transaction from a connected account."""
    id: str
    amount: float
    currency: str
    status: str
    description: str
    created_at: int
    merchant: str


class ConnectBalanceResponse(BaseModel):
    """Balance for a connected account."""
    available: List[dict]
    pending: List[dict]


# --- Endpoints ---

@router.post("/accounts", response_model=CreateConnectAccountResponse)
async def create_connect_account(
    request: CreateConnectAccountRequest,
    user_id: str = Query(..., description="User ID"),
    api_key: dict = Depends(require_api_key),
):
    """
    Create a new Stripe Connect account for a user.
    
    Returns an onboarding URL to complete account setup.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        # Create the Connect account
        account = await stripe_service.create_connect_account(
            user_id=user_id,
            email=request.email,
            country=request.country,
        )
        
        # Generate onboarding link
        base_url = "https://agentauth.in"
        onboarding_url = await stripe_service.create_connect_onboarding_link(
            account_id=account.account_id,
            return_url=f"{base_url}/nucleus?connect=success&account_id={account.account_id}",
            refresh_url=f"{base_url}/nucleus?connect=refresh",
        )
        
        return CreateConnectAccountResponse(
            account_id=account.account_id,
            onboarding_url=onboarding_url,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}", response_model=ConnectAccountStatus)
async def get_connect_account_status(
    account_id: str,
    api_key: dict = Depends(require_api_key),
):
    """
    Get the status of a connected Stripe account.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        account = await stripe_service.get_connect_account(account_id)
        
        # Determine overall status
        if account.charges_enabled and account.payouts_enabled:
            status = "active"
        elif account.details_submitted:
            status = "pending"
        else:
            status = "incomplete"
        
        return ConnectAccountStatus(
            account_id=account.account_id,
            details_submitted=account.details_submitted,
            charges_enabled=account.charges_enabled,
            payouts_enabled=account.payouts_enabled,
            status=status,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/{account_id}/onboarding-link")
async def refresh_onboarding_link(
    account_id: str,
    api_key: dict = Depends(require_api_key),
):
    """
    Generate a new onboarding link for an incomplete account.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        base_url = "https://agentauth.in"
        onboarding_url = await stripe_service.create_connect_onboarding_link(
            account_id=account_id,
            return_url=f"{base_url}/nucleus?connect=success&account_id={account_id}",
            refresh_url=f"{base_url}/nucleus?connect=refresh",
        )
        
        return {"onboarding_url": onboarding_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/dashboard-link")
async def get_dashboard_link(
    account_id: str,
    api_key: dict = Depends(require_api_key),
):
    """
    Get a login link to the connected account's Stripe dashboard.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        login_url = await stripe_service.create_connect_login_link(account_id)
        return {"dashboard_url": login_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/transactions", response_model=List[ConnectedAccountTransaction])
async def list_connect_transactions(
    account_id: str,
    limit: int = Query(20, ge=1, le=100),
    api_key: dict = Depends(require_api_key),
):
    """
    List recent transactions for a connected account.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        transactions = await stripe_service.list_connect_transactions(
            account_id=account_id,
            limit=limit,
        )
        return [ConnectedAccountTransaction(**tx) for tx in transactions]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/balance", response_model=ConnectBalanceResponse)
async def get_connect_balance(
    account_id: str,
    api_key: dict = Depends(require_api_key),
):
    """
    Get the balance for a connected account.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    try:
        balance = await stripe_service.get_connect_balance(account_id)
        return ConnectBalanceResponse(**balance)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
