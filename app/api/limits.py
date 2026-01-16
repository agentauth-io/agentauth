"""
Spending Limits API

API endpoints for managing spending limits and viewing usage.
"""
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.limits import SpendingLimit, UsageTracking


router = APIRouter(prefix="/v1/limits", tags=["Spending Limits"])


# Schemas

class SpendingLimitsResponse(BaseModel):
    """Response with current spending limits."""
    daily_limit: Decimal
    monthly_limit: Decimal
    per_transaction_limit: Decimal
    require_approval_above: Optional[Decimal] = None
    is_active: bool


class SpendingLimitsUpdate(BaseModel):
    """Request to update spending limits."""
    daily_limit: Optional[Decimal] = Field(None, ge=0, description="Maximum daily spending")
    monthly_limit: Optional[Decimal] = Field(None, ge=0, description="Maximum monthly spending")
    per_transaction_limit: Optional[Decimal] = Field(None, ge=0, description="Maximum per transaction")
    require_approval_above: Optional[Decimal] = Field(None, ge=0, description="Require human approval above this amount")


class UsageResponse(BaseModel):
    """Response with current usage statistics."""
    daily_spent: Decimal
    monthly_spent: Decimal
    daily_transaction_count: int
    monthly_transaction_count: int
    daily_limit: Decimal
    monthly_limit: Decimal
    daily_remaining: Decimal
    monthly_remaining: Decimal


# Endpoints

@router.get("", response_model=SpendingLimitsResponse)
async def get_limits(
    user_id: str = "default",  # In production, get from auth
    db: AsyncSession = Depends(get_db)
):
    """
    Get current spending limits.
    
    Returns the configured limits for the authenticated user.
    """
    result = await db.execute(
        select(SpendingLimit).where(
            SpendingLimit.user_id == user_id,
            SpendingLimit.is_active == True
        )
    )
    limits = result.scalar_one_or_none()
    
    if not limits:
        # Return default limits
        return SpendingLimitsResponse(
            daily_limit=Decimal("1000.00"),
            monthly_limit=Decimal("10000.00"),
            per_transaction_limit=Decimal("500.00"),
            require_approval_above=Decimal("100.00"),
            is_active=True
        )
    
    return SpendingLimitsResponse(
        daily_limit=limits.daily_limit,
        monthly_limit=limits.monthly_limit,
        per_transaction_limit=limits.per_transaction_limit,
        require_approval_above=limits.require_approval_above,
        is_active=limits.is_active
    )


@router.put("", response_model=SpendingLimitsResponse)
async def update_limits(
    update: SpendingLimitsUpdate,
    user_id: str = "default",  # In production, get from auth
    db: AsyncSession = Depends(get_db)
):
    """
    Update spending limits.
    
    Only provided fields will be updated.
    """
    result = await db.execute(
        select(SpendingLimit).where(
            SpendingLimit.user_id == user_id
        )
    )
    limits = result.scalar_one_or_none()
    
    if not limits:
        # Create new limits
        limits = SpendingLimit(user_id=user_id)
        db.add(limits)
    
    # Update provided fields
    if update.daily_limit is not None:
        limits.daily_limit = update.daily_limit
    if update.monthly_limit is not None:
        limits.monthly_limit = update.monthly_limit
    if update.per_transaction_limit is not None:
        limits.per_transaction_limit = update.per_transaction_limit
    if update.require_approval_above is not None:
        limits.require_approval_above = update.require_approval_above
    
    await db.commit()
    await db.refresh(limits)
    
    return SpendingLimitsResponse(
        daily_limit=limits.daily_limit,
        monthly_limit=limits.monthly_limit,
        per_transaction_limit=limits.per_transaction_limit,
        require_approval_above=limits.require_approval_above,
        is_active=limits.is_active
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    user_id: str = "default",  # In production, get from auth
    db: AsyncSession = Depends(get_db)
):
    """
    Get current usage against limits.
    
    Shows how much has been spent today/this month and remaining budget.
    """
    # Get limits
    limits_result = await db.execute(
        select(SpendingLimit).where(
            SpendingLimit.user_id == user_id,
            SpendingLimit.is_active == True
        )
    )
    limits = limits_result.scalar_one_or_none()
    
    daily_limit = limits.daily_limit if limits else Decimal("1000.00")
    monthly_limit = limits.monthly_limit if limits else Decimal("10000.00")
    
    # Get usage
    usage_result = await db.execute(
        select(UsageTracking).where(UsageTracking.user_id == user_id)
    )
    usage = usage_result.scalar_one_or_none()
    
    if not usage:
        return UsageResponse(
            daily_spent=Decimal("0.00"),
            monthly_spent=Decimal("0.00"),
            daily_transaction_count=0,
            monthly_transaction_count=0,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            daily_remaining=daily_limit,
            monthly_remaining=monthly_limit
        )
    
    return UsageResponse(
        daily_spent=usage.daily_spent,
        monthly_spent=usage.monthly_spent,
        daily_transaction_count=usage.daily_transaction_count,
        monthly_transaction_count=usage.monthly_transaction_count,
        daily_limit=daily_limit,
        monthly_limit=monthly_limit,
        daily_remaining=max(Decimal("0.00"), daily_limit - usage.daily_spent),
        monthly_remaining=max(Decimal("0.00"), monthly_limit - usage.monthly_spent)
    )


@router.post("/reset")
async def reset_usage(
    reset_type: str = "daily",  # "daily" or "monthly"
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Manually reset usage counters.
    
    Use with caution - this is typically automated.
    """
    result = await db.execute(
        select(UsageTracking).where(UsageTracking.user_id == user_id)
    )
    usage = result.scalar_one_or_none()
    
    if not usage:
        raise HTTPException(status_code=404, detail="No usage tracking found")
    
    from datetime import date
    
    if reset_type == "daily":
        usage.daily_spent = Decimal("0.00")
        usage.daily_transaction_count = 0
        usage.last_daily_reset = date.today()
    elif reset_type == "monthly":
        usage.monthly_spent = Decimal("0.00")
        usage.monthly_transaction_count = 0
        usage.last_monthly_reset = date.today()
    else:
        raise HTTPException(status_code=400, detail="reset_type must be 'daily' or 'monthly'")
    
    await db.commit()
    
    return {"status": "success", "message": f"{reset_type} usage reset"}
