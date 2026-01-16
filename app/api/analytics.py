"""
Analytics API

API endpoints for viewing authorization analytics and insights.
"""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.analytics import AnalyticsService


router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


# Schemas

class SummaryResponse(BaseModel):
    """Dashboard summary response."""
    total_authorizations: int
    total_approved: int
    total_denied: int
    total_amount: str
    approval_rate: float
    today_authorizations: int
    today_approved: int
    today_denied: int
    today_amount: str
    month_authorizations: int
    month_amount: str
    top_merchants: List[dict]
    top_agents: List[dict]


class TrendResponse(BaseModel):
    """Trend data response."""
    dates: List[str]
    authorizations: List[int]
    amounts: List[float]
    approval_rates: List[float]


class LogEntry(BaseModel):
    """Authorization log entry."""
    id: str
    agent_id: Optional[str]
    merchant: Optional[str]
    amount: str
    category: Optional[str]
    decision: str
    denial_reason: Optional[str]
    processing_time_ms: Optional[int]
    created_at: str


# Endpoints

@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    user_id: str = "default",
    days: int = Query(30, ge=1, le=365, description="Days to include in stats"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics summary for dashboard.
    
    Returns overall stats, today's activity, and top merchants/agents.
    """
    service = AnalyticsService(db)
    summary = await service.get_summary(user_id, days)
    
    return SummaryResponse(
        total_authorizations=summary.total_authorizations,
        total_approved=summary.total_approved,
        total_denied=summary.total_denied,
        total_amount=str(summary.total_amount),
        approval_rate=summary.approval_rate,
        today_authorizations=summary.today_authorizations,
        today_approved=summary.today_approved,
        today_denied=summary.today_denied,
        today_amount=str(summary.today_amount),
        month_authorizations=summary.month_authorizations,
        month_amount=str(summary.month_amount),
        top_merchants=summary.top_merchants,
        top_agents=summary.top_agents
    )


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    user_id: str = "default",
    days: int = Query(30, ge=1, le=365, description="Days to include in trends"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trend data for charts.
    
    Returns daily authorization counts, amounts, and approval rates.
    """
    service = AnalyticsService(db)
    trends = await service.get_trends(user_id, days)
    
    return TrendResponse(
        dates=trends.dates,
        authorizations=trends.authorizations,
        amounts=trends.amounts,
        approval_rates=trends.approval_rates
    )


@router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    user_id: str = "default",
    limit: int = Query(50, ge=1, le=500, description="Maximum logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    decision: Optional[str] = Query(None, description="Filter by decision: approved/denied"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get authorization logs.
    
    Returns recent authorization requests with filtering options.
    """
    service = AnalyticsService(db)
    logs = await service.get_authorization_logs(user_id, limit, offset, decision)
    
    return [LogEntry(**log) for log in logs]


@router.get("/agents")
async def get_agent_stats(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Get per-agent statistics.
    
    Returns breakdown of authorizations by agent.
    """
    service = AnalyticsService(db)
    agents = await service._get_top_agents(user_id, limit=20)
    
    return {"agents": agents}


@router.get("/merchants")
async def get_merchant_stats(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Get per-merchant statistics.
    
    Returns breakdown of authorizations by merchant.
    """
    service = AnalyticsService(db)
    merchants = await service._get_top_merchants(user_id, limit=20)
    
    return {"merchants": merchants}
