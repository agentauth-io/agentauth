"""
Analytics Service

Provides analytics and insights from authorization logs.
"""
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.limits import AuthorizationLog, UsageTracking


@dataclass
class DailyStats:
    """Daily authorization statistics."""
    date: date
    total_authorizations: int
    approved: int
    denied: int
    total_amount: Decimal
    approval_rate: float


@dataclass
class AnalyticsSummary:
    """Overall analytics summary for dashboard."""
    # Totals
    total_authorizations: int
    total_approved: int
    total_denied: int
    total_amount: Decimal
    approval_rate: float
    
    # Today
    today_authorizations: int
    today_approved: int
    today_denied: int
    today_amount: Decimal
    
    # This month
    month_authorizations: int
    month_amount: Decimal
    
    # Top merchants
    top_merchants: List[dict]
    
    # Top agents
    top_agents: List[dict]


@dataclass
class TrendData:
    """Time-series trend data."""
    dates: List[str]
    authorizations: List[int]
    amounts: List[float]
    approval_rates: List[float]


class AnalyticsService:
    """
    Analytics service for authorization data.
    
    Provides dashboard stats, trends, and insights.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_summary(self, user_id: str, days: int = 30) -> AnalyticsSummary:
        """Get analytics summary for dashboard."""
        today = date.today()
        start_date = today - timedelta(days=days)
        month_start = today.replace(day=1)
        
        # Total stats (all time)
        total_result = await self.db.execute(
            select(
                func.count(AuthorizationLog.id).label('total'),
                func.count().filter(AuthorizationLog.decision == 'approved').label('approved'),
                func.count().filter(AuthorizationLog.decision == 'denied').label('denied'),
                func.coalesce(func.sum(AuthorizationLog.amount), 0).label('amount')
            ).where(AuthorizationLog.user_id == user_id)
        )
        total_row = total_result.fetchone()
        
        total_auth = total_row.total or 0
        total_approved = total_row.approved or 0
        total_denied = total_row.denied or 0
        total_amount = Decimal(str(total_row.amount or 0))
        approval_rate = (total_approved / total_auth * 100) if total_auth > 0 else 0
        
        # Today's stats
        today_result = await self.db.execute(
            select(
                func.count(AuthorizationLog.id).label('total'),
                func.count().filter(AuthorizationLog.decision == 'approved').label('approved'),
                func.count().filter(AuthorizationLog.decision == 'denied').label('denied'),
                func.coalesce(func.sum(AuthorizationLog.amount), 0).label('amount')
            ).where(
                AuthorizationLog.user_id == user_id,
                func.date(AuthorizationLog.created_at) == today
            )
        )
        today_row = today_result.fetchone()
        
        # This month's stats
        month_result = await self.db.execute(
            select(
                func.count(AuthorizationLog.id).label('total'),
                func.coalesce(func.sum(AuthorizationLog.amount), 0).label('amount')
            ).where(
                AuthorizationLog.user_id == user_id,
                AuthorizationLog.created_at >= month_start
            )
        )
        month_row = month_result.fetchone()
        
        # Top merchants
        top_merchants = await self._get_top_merchants(user_id, limit=5)
        
        # Top agents
        top_agents = await self._get_top_agents(user_id, limit=5)
        
        return AnalyticsSummary(
            total_authorizations=total_auth,
            total_approved=total_approved,
            total_denied=total_denied,
            total_amount=total_amount,
            approval_rate=round(approval_rate, 1),
            today_authorizations=today_row.total or 0,
            today_approved=today_row.approved or 0,
            today_denied=today_row.denied or 0,
            today_amount=Decimal(str(today_row.amount or 0)),
            month_authorizations=month_row.total or 0,
            month_amount=Decimal(str(month_row.amount or 0)),
            top_merchants=top_merchants,
            top_agents=top_agents
        )
    
    async def get_trends(self, user_id: str, days: int = 30) -> TrendData:
        """Get daily trends for the specified period."""
        today = date.today()
        start_date = today - timedelta(days=days)
        
        # Get daily aggregates
        result = await self.db.execute(
            select(
                func.date(AuthorizationLog.created_at).label('date'),
                func.count(AuthorizationLog.id).label('total'),
                func.count().filter(AuthorizationLog.decision == 'approved').label('approved'),
                func.coalesce(func.sum(AuthorizationLog.amount), 0).label('amount')
            ).where(
                AuthorizationLog.user_id == user_id,
                AuthorizationLog.created_at >= start_date
            ).group_by(
                func.date(AuthorizationLog.created_at)
            ).order_by(
                func.date(AuthorizationLog.created_at)
            )
        )
        rows = result.fetchall()
        
        # Build trend data with all dates (fill gaps with zeros)
        date_map = {row.date: row for row in rows}
        dates = []
        authorizations = []
        amounts = []
        approval_rates = []
        
        for i in range(days + 1):
            d = start_date + timedelta(days=i)
            dates.append(d.isoformat())
            
            if d in date_map:
                row = date_map[d]
                authorizations.append(row.total)
                amounts.append(float(row.amount))
                rate = (row.approved / row.total * 100) if row.total > 0 else 0
                approval_rates.append(round(rate, 1))
            else:
                authorizations.append(0)
                amounts.append(0.0)
                approval_rates.append(0.0)
        
        return TrendData(
            dates=dates,
            authorizations=authorizations,
            amounts=amounts,
            approval_rates=approval_rates
        )
    
    async def get_authorization_logs(
        self, 
        user_id: str, 
        limit: int = 50,
        offset: int = 0,
        decision: Optional[str] = None
    ) -> List[dict]:
        """Get recent authorization logs."""
        query = select(AuthorizationLog).where(
            AuthorizationLog.user_id == user_id
        )
        
        if decision:
            query = query.where(AuthorizationLog.decision == decision)
        
        query = query.order_by(AuthorizationLog.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": str(log.id),
                "agent_id": log.agent_id,
                "merchant": log.merchant,
                "amount": str(log.amount),
                "category": log.category,
                "decision": log.decision,
                "denial_reason": log.denial_reason,
                "processing_time_ms": log.processing_time_ms,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    
    async def _get_top_merchants(self, user_id: str, limit: int = 5) -> List[dict]:
        """Get top merchants by transaction count."""
        result = await self.db.execute(
            select(
                AuthorizationLog.merchant,
                func.count(AuthorizationLog.id).label('count'),
                func.coalesce(func.sum(AuthorizationLog.amount), 0).label('amount')
            ).where(
                AuthorizationLog.user_id == user_id,
                AuthorizationLog.merchant.isnot(None)
            ).group_by(
                AuthorizationLog.merchant
            ).order_by(
                func.count(AuthorizationLog.id).desc()
            ).limit(limit)
        )
        rows = result.fetchall()
        
        return [
            {"merchant": row.merchant, "count": row.count, "amount": str(row.amount)}
            for row in rows
        ]
    
    async def _get_top_agents(self, user_id: str, limit: int = 5) -> List[dict]:
        """Get top agents by transaction count."""
        result = await self.db.execute(
            select(
                AuthorizationLog.agent_id,
                func.count(AuthorizationLog.id).label('count'),
                func.coalesce(func.sum(AuthorizationLog.amount), 0).label('amount')
            ).where(
                AuthorizationLog.user_id == user_id,
                AuthorizationLog.agent_id.isnot(None)
            ).group_by(
                AuthorizationLog.agent_id
            ).order_by(
                func.count(AuthorizationLog.id).desc()
            ).limit(limit)
        )
        rows = result.fetchall()
        
        return [
            {"agent_id": row.agent_id, "count": row.count, "amount": str(row.amount)}
            for row in rows
        ]


# Convenience functions

async def get_analytics_summary(db: AsyncSession, user_id: str) -> AnalyticsSummary:
    """Get analytics summary for a user."""
    service = AnalyticsService(db)
    return await service.get_summary(user_id)


async def get_analytics_trends(db: AsyncSession, user_id: str, days: int = 30) -> TrendData:
    """Get trend data for a user."""
    service = AnalyticsService(db)
    return await service.get_trends(user_id, days)
