"""
Rules API

API endpoints for managing merchant and category rules.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.limits import MerchantRule, CategoryRule, RuleAction


router = APIRouter(prefix="/v1/rules", tags=["Rules"])


# Schemas

class MerchantRuleCreate(BaseModel):
    """Request to create a merchant rule."""
    merchant_pattern: str = Field(..., description="Merchant pattern (supports wildcards like *.amazon.com)")
    action: str = Field("block", description="Action: 'allow' or 'block'")
    description: Optional[str] = None


class MerchantRuleResponse(BaseModel):
    """Response with merchant rule details."""
    id: UUID
    merchant_pattern: str
    action: str
    description: Optional[str]
    is_active: bool


class CategoryRuleCreate(BaseModel):
    """Request to create a category rule."""
    category: str = Field(..., description="Category name (e.g., gambling, saas, travel)")
    action: str = Field("block", description="Action: 'allow' or 'block'")


class CategoryRuleResponse(BaseModel):
    """Response with category rule details."""
    id: UUID
    category: str
    action: str
    is_active: bool


# Merchant Rules Endpoints

@router.get("/merchants", response_model=List[MerchantRuleResponse])
async def list_merchant_rules(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    List all merchant rules.
    
    Returns whitelist and blacklist rules for merchants.
    """
    result = await db.execute(
        select(MerchantRule).where(
            MerchantRule.user_id == user_id,
            MerchantRule.is_active == True
        ).order_by(MerchantRule.created_at.desc())
    )
    rules = result.scalars().all()
    
    return [
        MerchantRuleResponse(
            id=rule.id,
            merchant_pattern=rule.merchant_pattern,
            action=rule.action.value,
            description=rule.description,
            is_active=rule.is_active
        )
        for rule in rules
    ]


@router.post("/merchants", response_model=MerchantRuleResponse)
async def create_merchant_rule(
    rule: MerchantRuleCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new merchant rule.
    
    Examples:
    - Block all gambling: merchant_pattern="*.gambling.com", action="block"
    - Only allow Amazon: merchant_pattern="*.amazon.com", action="allow"
    """
    action = RuleAction.ALLOW if rule.action.lower() == "allow" else RuleAction.BLOCK
    
    new_rule = MerchantRule(
        user_id=user_id,
        merchant_pattern=rule.merchant_pattern,
        action=action,
        description=rule.description
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    
    return MerchantRuleResponse(
        id=new_rule.id,
        merchant_pattern=new_rule.merchant_pattern,
        action=new_rule.action.value,
        description=new_rule.description,
        is_active=new_rule.is_active
    )


@router.delete("/merchants/{rule_id}")
async def delete_merchant_rule(
    rule_id: UUID,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a merchant rule.
    
    Soft-deletes by setting is_active=False.
    """
    result = await db.execute(
        select(MerchantRule).where(
            MerchantRule.id == rule_id,
            MerchantRule.user_id == user_id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = False
    await db.commit()
    
    return {"status": "success", "message": "Rule deleted"}


# Category Rules Endpoints

@router.get("/categories", response_model=List[CategoryRuleResponse])
async def list_category_rules(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    List all category rules.
    
    Returns rules for spending categories.
    """
    result = await db.execute(
        select(CategoryRule).where(
            CategoryRule.user_id == user_id,
            CategoryRule.is_active == True
        ).order_by(CategoryRule.created_at.desc())
    )
    rules = result.scalars().all()
    
    return [
        CategoryRuleResponse(
            id=rule.id,
            category=rule.category,
            action=rule.action.value,
            is_active=rule.is_active
        )
        for rule in rules
    ]


@router.post("/categories", response_model=CategoryRuleResponse)
async def create_category_rule(
    rule: CategoryRuleCreate,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new category rule.
    
    Categories: saas, ecommerce, travel, entertainment, gambling, crypto, food, utilities
    """
    action = RuleAction.ALLOW if rule.action.lower() == "allow" else RuleAction.BLOCK
    
    new_rule = CategoryRule(
        user_id=user_id,
        category=rule.category.lower(),
        action=action
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    
    return CategoryRuleResponse(
        id=new_rule.id,
        category=new_rule.category,
        action=new_rule.action.value,
        is_active=new_rule.is_active
    )


@router.delete("/categories/{rule_id}")
async def delete_category_rule(
    rule_id: UUID,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a category rule.
    """
    result = await db.execute(
        select(CategoryRule).where(
            CategoryRule.id == rule_id,
            CategoryRule.user_id == user_id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = False
    await db.commit()
    
    return {"status": "success", "message": "Rule deleted"}


# Predefined categories for reference

@router.get("/categories/available")
async def get_available_categories():
    """
    Get list of available categories.
    
    These are suggested categories - you can use any category name.
    """
    return {
        "categories": [
            {"name": "saas", "description": "Software as a Service subscriptions"},
            {"name": "ecommerce", "description": "Online retail purchases"},
            {"name": "travel", "description": "Travel and accommodation"},
            {"name": "entertainment", "description": "Streaming, gaming, media"},
            {"name": "gambling", "description": "Gambling and betting"},
            {"name": "crypto", "description": "Cryptocurrency purchases"},
            {"name": "food", "description": "Food delivery and dining"},
            {"name": "utilities", "description": "Bills and utilities"},
            {"name": "education", "description": "Courses and learning"},
            {"name": "healthcare", "description": "Health and medical"},
        ]
    }
