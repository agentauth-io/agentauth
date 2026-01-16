"""
Dashboard API routes for monitoring and analytics.

Provides aggregate stats, transaction logs, and real-time metrics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import Optional

from app.config import get_settings
from app.models.database import get_db
from app.models.consent import Consent

settings = get_settings()

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregate dashboard statistics.
    
    Returns counts for consents, authorizations, and payment metrics.
    """
    try:
        # Get total consents
        total_result = await db.execute(select(func.count(Consent.id)))
        total_consents = total_result.scalar() or 0
        
        # Get active consents
        active_result = await db.execute(
            select(func.count(Consent.id)).where(Consent.is_active == True)
        )
        active_consents = active_result.scalar() or 0
        
        # Get today's consents
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await db.execute(
            select(func.count(Consent.id)).where(Consent.created_at >= today)
        )
        today_consents = today_result.scalar() or 0
        
        # Calculate average max amount from constraints
        # This is a simplified version - in production you'd want proper aggregation
        avg_amount_result = await db.execute(
            select(Consent.constraints).limit(100)
        )
        constraints_list = avg_amount_result.scalars().all()
        
        total_amount = 0
        amount_count = 0
        for constraints in constraints_list:
            if constraints and isinstance(constraints, dict):
                max_amount = constraints.get("max_amount", 0)
                if max_amount:
                    total_amount += max_amount
                    amount_count += 1
        
        avg_max_amount = total_amount / amount_count if amount_count > 0 else 0
        
        return {
            "total_consents": total_consents,
            "active_consents": active_consents,
            "consents_today": today_consents,
            "avg_max_amount": round(avg_max_amount, 2),
            "api_status": "healthy",
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "total_consents": 0,
            "active_consents": 0,
            "consents_today": 0,
            "avg_max_amount": 0,
            "api_status": "error",
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat(),
        }


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent transactions/consents for the dashboard.
    """
    try:
        # Get consents ordered by creation date
        result = await db.execute(
            select(Consent)
            .order_by(desc(Consent.created_at))
            .offset(offset)
            .limit(limit)
        )
        consents = result.scalars().all()
        
        # Get total count
        count_result = await db.execute(select(func.count(Consent.id)))
        total = count_result.scalar() or 0
        
        transactions = []
        for c in consents:
            constraints = c.constraints or {}
            transactions.append({
                "id": c.consent_id,
                "user_id": c.user_id,
                "agent_id": c.agent_id,
                "intent": c.intent_description,
                "max_amount": constraints.get("max_amount", 0),
                "currency": constraints.get("currency", "USD"),
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            })
        
        return {
            "transactions": transactions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        return {
            "transactions": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e),
        }


@router.get("/analytics")
async def get_analytics(
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics data for charts.
    
    Returns daily counts for the specified number of days.
    """
    try:
        analytics = []
        
        for i in range(days, -1, -1):
            day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            next_day = day + timedelta(days=1)
            
            # Count consents for this day
            result = await db.execute(
                select(func.count(Consent.id)).where(
                    Consent.created_at >= day,
                    Consent.created_at < next_day
                )
            )
            count = result.scalar() or 0
            
            analytics.append({
                "date": day.strftime("%Y-%m-%d"),
                "consents": count,
                "authorizations": 0,  # TODO: Add when authorization tracking is implemented
            })
        
        return {
            "analytics": analytics,
            "period_days": days,
        }
    except Exception as e:
        return {
            "analytics": [],
            "period_days": days,
            "error": str(e),
        }


@router.get("/health")
async def dashboard_health():
    """Quick health check for the dashboard API."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
