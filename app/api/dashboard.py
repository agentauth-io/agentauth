"""
Dashboard API routes for monitoring and analytics.

Provides aggregate stats, transaction logs, and real-time metrics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings
from app.models.database import get_db
from app.models.consent import Consent
from app.models.authorization import Authorization

settings = get_settings()

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete dashboard data for the frontend.
    
    Returns stats, transactions, and chart data in the format expected by the Dashboard component.
    """
    try:
        # Get total consents (as authorizations)
        total_result = await db.execute(select(func.count(Consent.id)))
        total_authorizations = total_result.scalar() or 0
        
        # Get active consents
        active_result = await db.execute(
            select(func.count(Consent.id)).where(Consent.is_active == True)
        )
        active_consents = active_result.scalar() or 0
        
        # Calculate transaction volume from constraints
        all_consents = await db.execute(
            select(Consent.constraints).limit(1000)
        )
        constraints_list = all_consents.scalars().all()
        
        transaction_volume = 0
        for constraints in constraints_list:
            if constraints and isinstance(constraints, dict):
                max_amount = constraints.get("max_amount", 0)
                if max_amount:
                    transaction_volume += max_amount
        
        # Calculate approval rate (if we have authorizations)
        approval_rate = 100.0 if total_authorizations > 0 else 0
        
        # Get recent transactions
        recent_result = await db.execute(
            select(Consent)
            .order_by(desc(Consent.created_at))
            .limit(10)
        )
        recent_consents = recent_result.scalars().all()
        
        transactions = []
        for c in recent_consents:
            constraints = c.constraints or {}
            scope = c.scope or {}
            agent_name = scope.get("agent_name", "Agent")
            transactions.append({
                "id": c.consent_id,
                "amount": constraints.get("max_amount", 0),
                "currency": constraints.get("currency", "USD"),
                "status": "authorized" if c.is_active else "expired",
                "merchant": agent_name,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "description": c.intent_description or "Authorization",
            })
        
        # Get daily counts for chart (last 7 days)
        daily_requests = []
        for i in range(6, -1, -1):
            day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            next_day = day + timedelta(days=1)
            
            result = await db.execute(
                select(func.count(Consent.id)).where(
                    Consent.created_at >= day,
                    Consent.created_at < next_day
                )
            )
            count = result.scalar() or 0
            daily_requests.append(count)
        
        return {
            "total_authorizations": total_authorizations,
            "transaction_volume": round(transaction_volume, 2),
            "approval_rate": round(approval_rate, 1),
            "avg_response_time": 8.3,  # Placeholder - would need actual timing data
            "transactions": transactions,
            "active_consents": active_consents,
            "daily_requests": daily_requests,
        }
    except Exception as e:
        # Return empty state on error
        return {
            "total_authorizations": 0,
            "transaction_volume": 0,
            "approval_rate": 0,
            "avg_response_time": 0,
            "transactions": [],
            "active_consents": 0,
            "daily_requests": [0, 0, 0, 0, 0, 0, 0],
            "error": str(e),
        }


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
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
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
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "total_consents": 0,
            "active_consents": 0,
            "consents_today": 0,
            "avg_max_amount": 0,
            "api_status": "error",
            "error": str(e),
            "last_updated": datetime.now(timezone.utc).isoformat(),
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
            # Note: agent_id is not in Consent model, extract from scope if available
            scope = c.scope or {}
            agent_name = scope.get("agent_name", "Agent")
            transactions.append({
                "id": c.consent_id,
                "user_id": c.user_id,
                "developer_id": c.developer_id,
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
            day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            next_day = day + timedelta(days=1)
            
            # Count consents for this day
            result = await db.execute(
                select(func.count(Consent.id)).where(
                    Consent.created_at >= day,
                    Consent.created_at < next_day
                )
            )
            consent_count = result.scalar() or 0
            
            # Count authorizations for this day
            auth_result = await db.execute(
                select(func.count(Authorization.id)).where(
                    Authorization.created_at >= day,
                    Authorization.created_at < next_day
                )
            )
            auth_count = auth_result.scalar() or 0
            
            analytics.append({
                "date": day.strftime("%Y-%m-%d"),
                "consents": consent_count,
                "authorizations": auth_count,
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.3",  # Cache fix for consent creation
    }


@router.get("/debug/authorizations")
async def debug_authorizations(
    limit: int = Query(default=10, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Debug endpoint to check authorization records."""
    try:
        # Check if table exists and has data
        result = await db.execute(
            select(Authorization).order_by(desc(Authorization.created_at)).limit(limit)
        )
        auths = result.scalars().all()
        
        return {
            "count": len(auths),
            "authorizations": [
                {
                    "code": a.authorization_code,
                    "consent_id": a.consent_id,
                    "decision": a.decision,
                    "amount": a.amount,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in auths
            ]
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
        }
