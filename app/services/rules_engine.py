"""
Rules Engine Service

Evaluates authorization requests against user-defined spending limits,
merchant whitelists/blacklists, and category rules.
"""
import fnmatch
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.limits import (
    SpendingLimit, UsageTracking, MerchantRule, CategoryRule, 
    AuthorizationLog, RuleAction
)


@dataclass
class AuthorizationDecision:
    """Result of authorization evaluation."""
    allowed: bool
    reason: str
    requires_human_approval: bool = False
    rules_evaluated: int = 0
    processing_time_ms: int = 0


@dataclass
class AuthorizationRequest:
    """Incoming authorization request."""
    user_id: str
    amount: Decimal
    merchant: Optional[str] = None
    category: Optional[str] = None
    agent_id: Optional[str] = None


class RulesEngine:
    """
    Evaluates authorization requests against configured rules.
    
    Evaluation order:
    1. Check per-transaction limit
    2. Check merchant rules (whitelist/blacklist)
    3. Check category rules
    4. Check daily spending limit
    5. Check monthly spending limit
    6. Check if human approval required
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision:
        """
        Evaluate an authorization request against all rules.
        
        Returns decision with allow/deny and reason.
        """
        start_time = datetime.utcnow()
        rules_evaluated = 0
        
        # Get user's spending limits
        limits = await self._get_spending_limits(request.user_id)
        if not limits:
            # Create default limits if none exist
            limits = await self._create_default_limits(request.user_id)
        
        # Get current usage
        usage = await self._get_usage_tracking(request.user_id)
        if not usage:
            usage = await self._create_usage_tracking(request.user_id)
        
        # Auto-reset counters if needed
        usage = await self._maybe_reset_counters(usage)
        
        # 1. Check per-transaction limit
        rules_evaluated += 1
        if request.amount > limits.per_transaction_limit:
            return self._decision(
                allowed=False,
                reason=f"Amount ${request.amount} exceeds per-transaction limit of ${limits.per_transaction_limit}",
                rules_evaluated=rules_evaluated,
                start_time=start_time
            )
        
        # 2. Check merchant rules
        if request.merchant:
            rules_evaluated += 1
            merchant_decision = await self._check_merchant_rules(
                request.user_id, request.merchant
            )
            if merchant_decision is not None and not merchant_decision:
                return self._decision(
                    allowed=False,
                    reason=f"Merchant '{request.merchant}' is blocked by merchant rules",
                    rules_evaluated=rules_evaluated,
                    start_time=start_time
                )
        
        # 3. Check category rules
        if request.category:
            rules_evaluated += 1
            category_decision = await self._check_category_rules(
                request.user_id, request.category
            )
            if category_decision is not None and not category_decision:
                return self._decision(
                    allowed=False,
                    reason=f"Category '{request.category}' is blocked by category rules",
                    rules_evaluated=rules_evaluated,
                    start_time=start_time
                )
        
        # 4. Check daily limit
        rules_evaluated += 1
        new_daily_total = usage.daily_spent + request.amount
        if new_daily_total > limits.daily_limit:
            return self._decision(
                allowed=False,
                reason=f"Would exceed daily limit: ${new_daily_total} > ${limits.daily_limit}",
                rules_evaluated=rules_evaluated,
                start_time=start_time
            )
        
        # 5. Check monthly limit
        rules_evaluated += 1
        new_monthly_total = usage.monthly_spent + request.amount
        if new_monthly_total > limits.monthly_limit:
            return self._decision(
                allowed=False,
                reason=f"Would exceed monthly limit: ${new_monthly_total} > ${limits.monthly_limit}",
                rules_evaluated=rules_evaluated,
                start_time=start_time
            )
        
        # 6. Check if human approval required
        requires_approval = False
        if limits.require_approval_above:
            rules_evaluated += 1
            if request.amount > limits.require_approval_above:
                requires_approval = True
        
        return self._decision(
            allowed=True,
            reason="All rules passed",
            requires_human_approval=requires_approval,
            rules_evaluated=rules_evaluated,
            start_time=start_time
        )
    
    async def record_transaction(self, request: AuthorizationRequest, decision: AuthorizationDecision):
        """Record a transaction and update usage counters."""
        # Update usage tracking if approved
        if decision.allowed:
            usage = await self._get_usage_tracking(request.user_id)
            if usage:
                usage.daily_spent += request.amount
                usage.monthly_spent += request.amount
                usage.daily_transaction_count += 1
                usage.monthly_transaction_count += 1
                self.db.add(usage)
        
        # Log the authorization
        log = AuthorizationLog(
            user_id=request.user_id,
            agent_id=request.agent_id,
            merchant=request.merchant,
            amount=request.amount,
            category=request.category,
            decision="approved" if decision.allowed else "denied",
            denial_reason=None if decision.allowed else decision.reason,
            processing_time_ms=decision.processing_time_ms,
            rules_evaluated=decision.rules_evaluated
        )
        self.db.add(log)
        await self.db.commit()
    
    # Private helper methods
    
    async def _get_spending_limits(self, user_id: str) -> Optional[SpendingLimit]:
        """Get spending limits for a user."""
        result = await self.db.execute(
            select(SpendingLimit).where(
                SpendingLimit.user_id == user_id,
                SpendingLimit.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def _create_default_limits(self, user_id: str) -> SpendingLimit:
        """Create default spending limits for a new user."""
        limits = SpendingLimit(user_id=user_id)
        self.db.add(limits)
        await self.db.flush()
        return limits
    
    async def _get_usage_tracking(self, user_id: str) -> Optional[UsageTracking]:
        """Get usage tracking for a user."""
        result = await self.db.execute(
            select(UsageTracking).where(UsageTracking.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_usage_tracking(self, user_id: str) -> UsageTracking:
        """Create usage tracking for a new user."""
        usage = UsageTracking(user_id=user_id)
        self.db.add(usage)
        await self.db.flush()
        return usage
    
    async def _maybe_reset_counters(self, usage: UsageTracking) -> UsageTracking:
        """Reset daily/monthly counters if needed."""
        today = date.today()
        
        # Reset daily counter
        if usage.last_daily_reset < today:
            usage.daily_spent = Decimal("0.00")
            usage.daily_transaction_count = 0
            usage.last_daily_reset = today
        
        # Reset monthly counter
        if usage.last_monthly_reset.month != today.month or usage.last_monthly_reset.year != today.year:
            usage.monthly_spent = Decimal("0.00")
            usage.monthly_transaction_count = 0
            usage.last_monthly_reset = today
        
        self.db.add(usage)
        return usage
    
    async def _check_merchant_rules(self, user_id: str, merchant: str) -> Optional[bool]:
        """
        Check if merchant is allowed.
        
        Returns:
            True if explicitly allowed
            False if explicitly blocked
            None if no matching rule (default allow)
        """
        result = await self.db.execute(
            select(MerchantRule).where(
                MerchantRule.user_id == user_id,
                MerchantRule.is_active == True
            )
        )
        rules = result.scalars().all()
        
        for rule in rules:
            # Use fnmatch for pattern matching (supports *, ?)
            if fnmatch.fnmatch(merchant.lower(), rule.merchant_pattern.lower()):
                return rule.action == RuleAction.ALLOW
        
        return None  # No matching rule
    
    async def _check_category_rules(self, user_id: str, category: str) -> Optional[bool]:
        """
        Check if category is allowed.
        
        Returns:
            True if explicitly allowed
            False if explicitly blocked
            None if no matching rule (default allow)
        """
        result = await self.db.execute(
            select(CategoryRule).where(
                CategoryRule.user_id == user_id,
                CategoryRule.category == category.lower(),
                CategoryRule.is_active == True
            )
        )
        rule = result.scalar_one_or_none()
        
        if rule:
            return rule.action == RuleAction.ALLOW
        
        return None  # No matching rule
    
    def _decision(
        self, 
        allowed: bool, 
        reason: str, 
        requires_human_approval: bool = False,
        rules_evaluated: int = 0,
        start_time: datetime = None
    ) -> AuthorizationDecision:
        """Create a decision object."""
        processing_time = 0
        if start_time:
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AuthorizationDecision(
            allowed=allowed,
            reason=reason,
            requires_human_approval=requires_human_approval,
            rules_evaluated=rules_evaluated,
            processing_time_ms=processing_time
        )


# Convenience functions

async def evaluate_authorization(
    db: AsyncSession,
    user_id: str,
    amount: Decimal,
    merchant: Optional[str] = None,
    category: Optional[str] = None,
    agent_id: Optional[str] = None
) -> AuthorizationDecision:
    """
    Convenience function to evaluate an authorization request.
    
    Usage:
        decision = await evaluate_authorization(db, user_id, amount=49.99, merchant="stripe.com")
        if decision.allowed:
            # Process payment
        else:
            # Return error with decision.reason
    """
    engine = RulesEngine(db)
    request = AuthorizationRequest(
        user_id=user_id,
        amount=Decimal(str(amount)),
        merchant=merchant,
        category=category,
        agent_id=agent_id
    )
    return await engine.evaluate(request)
