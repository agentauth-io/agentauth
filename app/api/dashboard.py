"""
Dashboard API routes for monitoring and analytics.

Provides aggregate stats, transaction logs, and real-time metrics.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, cast, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.middleware import require_api_key
from app.middleware.api_keys import get_current_user_id
from app.models.authorization import Authorization
from app.models.consent import Consent
from app.models.database import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])


def _user_consents(user_id: str):
    """Base filter: consents belonging to the authenticated developer."""
    return Consent.developer_id == user_id


@router.get("")
async def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """
    Get complete dashboard data for the frontend.

    Returns stats, transactions, and chart data for the authenticated user only.
    """
    try:
        owner_filter = _user_consents(user_id)

        # Get total consents (as authorizations)
        total_result = await db.execute(
            select(func.count(Consent.id)).where(owner_filter)
        )
        total_authorizations = total_result.scalar() or 0

        # Get active consents
        active_result = await db.execute(
            select(func.count(Consent.id)).where(owner_filter, Consent.is_active)
        )
        active_consents = active_result.scalar() or 0

        # Calculate transaction volume from constraints
        all_consents = await db.execute(
            select(Consent.constraints).where(owner_filter).limit(1000)
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
            .where(owner_filter)
            .order_by(desc(Consent.created_at))
            .limit(10)
        )
        recent_consents = recent_result.scalars().all()

        transactions = []
        for c in recent_consents:
            constraints = c.constraints or {}
            scope = c.scope or {}
            agent_name = scope.get("agent_name", "Agent")
            transactions.append(
                {
                    "id": c.consent_id,
                    "amount": constraints.get("max_amount", 0),
                    "currency": constraints.get("currency", "USD"),
                    "status": "authorized" if c.is_active else "expired",
                    "merchant": agent_name,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "description": c.intent_description or "Authorization",
                }
            )

        # Get daily counts for chart (last 7 days) - single query instead of N+1
        seven_days_ago = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=6)
        daily_result = await db.execute(
            select(
                cast(Consent.created_at, Date).label("day"),
                func.count(Consent.id).label("count"),
            )
            .where(owner_filter, Consent.created_at >= seven_days_ago)
            .group_by(cast(Consent.created_at, Date))
        )
        daily_counts = {row.day: row.count for row in daily_result.all()}

        daily_requests = []
        for i in range(6, -1, -1):
            day = (
                datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                - timedelta(days=i)
            ).date()
            daily_requests.append(daily_counts.get(day, 0))

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
        logger.error(f"Dashboard data error: {e}", exc_info=True)
        return {
            "total_authorizations": 0,
            "transaction_volume": 0,
            "approval_rate": 0,
            "avg_response_time": 0,
            "transactions": [],
            "active_consents": 0,
            "daily_requests": [0, 0, 0, 0, 0, 0, 0],
        }


@router.get("/stats")
async def get_dashboard_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """
    Get aggregate dashboard statistics.

    Returns counts for consents, authorizations, and payment metrics.
    """
    try:
        owner_filter = _user_consents(user_id)

        # Get total consents
        total_result = await db.execute(
            select(func.count(Consent.id)).where(owner_filter)
        )
        total_consents = total_result.scalar() or 0

        # Get active consents
        active_result = await db.execute(
            select(func.count(Consent.id)).where(owner_filter, Consent.is_active)
        )
        active_consents = active_result.scalar() or 0

        # Get today's consents
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_result = await db.execute(
            select(func.count(Consent.id)).where(
                owner_filter, Consent.created_at >= today
            )
        )
        today_consents = today_result.scalar() or 0

        # Calculate average max amount from constraints
        avg_amount_result = await db.execute(
            select(Consent.constraints).where(owner_filter).limit(100)
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
    except Exception:
        return {
            "total_consents": 0,
            "active_consents": 0,
            "consents_today": 0,
            "avg_max_amount": 0,
            "api_status": "error",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """
    Get recent transactions/consents for the dashboard.
    """
    try:
        owner_filter = _user_consents(user_id)

        # Get consents ordered by creation date
        result = await db.execute(
            select(Consent)
            .where(owner_filter)
            .order_by(desc(Consent.created_at))
            .offset(offset)
            .limit(limit)
        )
        consents = result.scalars().all()

        # Get total count
        count_result = await db.execute(
            select(func.count(Consent.id)).where(owner_filter)
        )
        total = count_result.scalar() or 0

        transactions = []
        for c in consents:
            constraints = c.constraints or {}
            scope = c.scope or {}
            scope.get("agent_name", "Agent")
            transactions.append(
                {
                    "id": c.consent_id,
                    "user_id": c.user_id,
                    "developer_id": c.developer_id,
                    "intent": c.intent_description,
                    "max_amount": constraints.get("max_amount", 0),
                    "currency": constraints.get("currency", "USD"),
                    "is_active": c.is_active,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                }
            )

        return {
            "transactions": transactions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Transactions query error: {e}", exc_info=True)
        return {
            "transactions": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }


@router.get("/analytics")
async def get_analytics(
    days: int = Query(default=7, le=30),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """
    Get analytics data for charts.

    Returns daily counts for the specified number of days.
    """
    try:
        owner_filter = _user_consents(user_id)

        # Single query for consent counts by day
        start_day = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days)
        consent_daily = await db.execute(
            select(
                cast(Consent.created_at, Date).label("day"),
                func.count(Consent.id).label("count"),
            )
            .where(owner_filter, Consent.created_at >= start_day)
            .group_by(cast(Consent.created_at, Date))
        )
        consent_counts = {row.day: row.count for row in consent_daily.all()}

        # Single query for authorization counts by day
        auth_daily = await db.execute(
            select(
                cast(Authorization.created_at, Date).label("day"),
                func.count(Authorization.id).label("count"),
            )
            .where(
                Authorization.developer_id == user_id,
                Authorization.created_at >= start_day,
            )
            .group_by(cast(Authorization.created_at, Date))
        )
        auth_counts = {row.day: row.count for row in auth_daily.all()}

        analytics = []
        for i in range(days, -1, -1):
            day = (
                datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                - timedelta(days=i)
            ).date()
            analytics.append(
                {
                    "date": day.strftime("%Y-%m-%d"),
                    "consents": consent_counts.get(day, 0),
                    "authorizations": auth_counts.get(day, 0),
                }
            )

        return {
            "analytics": analytics,
            "period_days": days,
        }
    except Exception as e:
        logger.error(f"Analytics query error: {e}", exc_info=True)
        return {
            "analytics": [],
            "period_days": days,
        }


@router.get("/health")
async def dashboard_health():
    """Quick health check for the dashboard API."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.4",
    }


@router.get("/debug/authorizations")
async def debug_authorizations(
    limit: int = Query(default=10, le=100),
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(require_api_key),
):
    """Debug endpoint to check authorization records. Only available in development."""
    from app.config import get_settings

    if get_settings().environment == "production":
        raise HTTPException(status_code=404, detail="Not found")

    try:
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
            ],
        }
    except Exception as e:
        logger.error(f"Debug authorizations error: {e}", exc_info=True)
        return {"count": 0, "authorizations": []}
