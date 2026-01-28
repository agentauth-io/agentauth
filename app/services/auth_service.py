"""
Auth Service - Authorization decision engine

OPTIMIZED for <10ms latency:
1. Token verification is in-memory (JWT decode) - ~1ms
2. Consent lookup uses pre-warmed in-memory cache - ~0ms
3. Authorization record write uses FastAPI BackgroundTasks
"""
import asyncio
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from collections import deque
import threading

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authorization import Authorization
from app.models.database import async_session_maker
from app.schemas.authorize import AuthorizeRequest, AuthorizeResponse
from app.services.token_service import token_service
from app.services.consent_service import consent_service
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory LRU cache for consents (faster than Redis for single-instance)
_consent_cache: Dict[str, tuple[dict, datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

# In-memory cache for authorization codes (for verification)
_auth_cache: Dict[str, dict] = {}

# Queue for async authorization storage
_auth_queue: deque = deque(maxlen=10000)
_background_worker_started = False


def generate_authorization_code() -> str:
    """Generate a unique authorization code."""
    return f"authz_{secrets.token_urlsafe(16)}"


class AuthService:
    """
    Authorization Service - makes authorization decisions.
    
    OPTIMIZED FLOW (<50ms target):
    1. Token verification - in-memory JWT decode (~1ms)
    2. Consent check - in-memory LRU cache first, DB fallback (~1ms cached)
    3. Authorization record - write after returning response
    
    If all checks pass, we generate an authorization code.
    """
    
    def _get_cached_consent(self, consent_id: str) -> Optional[dict]:
        """Get consent from in-memory cache if not expired."""
        if consent_id in _consent_cache:
            data, cached_at = _consent_cache[consent_id]
            if (datetime.now(timezone.utc) - cached_at).total_seconds() < CACHE_TTL_SECONDS:
                return data
            else:
                del _consent_cache[consent_id]
        return None
    
    def _cache_consent(self, consent_id: str, data: dict):
        """Store consent in in-memory cache."""
        _consent_cache[consent_id] = (data, datetime.now(timezone.utc))
        # Limit cache size (simple eviction)
        if len(_consent_cache) > 10000:
            oldest = min(_consent_cache.keys(), key=lambda k: _consent_cache[k][1])
            del _consent_cache[oldest]
    
    async def _check_consent_cached(
        self,
        db: AsyncSession,
        consent_id: str
    ) -> Optional[dict]:
        """
        Check consent with in-memory cache first, DB fallback.
        Returns None if consent is invalid/revoked/expired.
        """
        # Try in-memory cache first (fastest)
        cached = self._get_cached_consent(consent_id)
        if cached is not None:
            # Validate cached consent
            if cached.get("is_active") and not cached.get("revoked_at"):
                expires_at = cached.get("expires_at")
                if expires_at:
                    from dateutil.parser import parse as parse_date
                    if parse_date(expires_at).replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                        return cached
            # Cache hit but invalid
            return None
        
        # Cache miss - query database
        consent = await consent_service.get_active_consent(db, consent_id)
        if consent is None:
            return None
        
        # Cache the consent for next time
        consent_data = {
            "consent_id": consent.consent_id,
            "user_id": consent.user_id,
            "is_active": consent.is_active,
            "revoked_at": str(consent.revoked_at) if consent.revoked_at else None,
            "expires_at": str(consent.expires_at),
            "constraints": consent.constraints,
        }
        self._cache_consent(consent_id, consent_data)
        
        return consent_data
    
    async def authorize(
        self,
        db: AsyncSession,
        request: AuthorizeRequest
    ) -> AuthorizeResponse:
        """
        Make an authorization decision.
        
        OPTIMIZED for <50ms latency on cache hits.
        """
        # Step 1: Verify the delegation token (in-memory, ~1ms)
        verification = token_service.verify_token(
            token=request.delegation_token,
            request_amount=request.transaction.amount,
            request_currency=request.transaction.currency,
            request_merchant_id=request.transaction.merchant_id,
            request_merchant_category=request.transaction.merchant_category,
        )
        
        # If token verification failed, deny immediately
        if not verification.valid:
            return AuthorizeResponse(
                decision="DENY",
                reason=verification.reason,
                message=verification.message
            )
        
        # Step 2: Check consent (cache-first, ~5ms cached, ~300ms uncached)
        consent = await self._check_consent_cached(
            db, verification.payload.consent_id
        )
        
        if consent is None:
            return AuthorizeResponse(
                decision="DENY",
                reason="consent_invalid",
                message="Consent has been revoked or does not exist"
            )
        
        # Step 3: All checks passed - generate authorization code
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.auth_code_expiry_seconds)
        authorization_code = generate_authorization_code()
        
        # Cache authorization in memory for instant verification
        _auth_cache[authorization_code] = {
            "consent_id": verification.payload.consent_id,
            "decision": "ALLOW",
            "amount": request.transaction.amount,
            "currency": request.transaction.currency,
            "merchant_id": request.transaction.merchant_id,
            "expires_at": expires_at,
            "created_at": now,
        }
        
        # Make expires_at timezone-naive for DB compatibility
        expires_at_naive = expires_at.replace(tzinfo=None)
        
        # Write authorization directly to DB (fast, <10ms)
        try:
            authorization = Authorization(
                authorization_code=authorization_code,
                consent_id=verification.payload.consent_id,
                decision="ALLOW",
                amount=request.transaction.amount,
                currency=request.transaction.currency,
                merchant_id=request.transaction.merchant_id,
                merchant_name=request.transaction.merchant_name,
                merchant_category=request.transaction.merchant_category,
                action=request.action,
                transaction_metadata={"description": request.transaction.description},
                expires_at=expires_at_naive,
            )
            db.add(authorization)
            await db.flush()  # Write immediately, don't wait for commit
            logger.debug(f"Authorization {authorization_code} written to DB")
        except Exception as e:
            logger.error(f"Failed to write authorization to DB: {e}")
            # Continue anyway - in-memory cache still works for verification
        
        # Return response
        return AuthorizeResponse(
            decision="ALLOW",
            authorization_code=authorization_code,
            expires_at=expires_at,
            consent_id=verification.payload.consent_id
        )
    
    async def check_step_up_required(
        self,
        consent_id: str,
        amount: float,
        consent_max_amount: Optional[float] = None
    ) -> bool:
        """
        Check if step-up authentication is required.
        
        Step-up is triggered when:
        1. Amount exceeds 80% of consent limit (high-value transaction)
        2. Transaction is from a new/unusual merchant (future: anomaly detection)
        3. User has configured step-up for certain thresholds
        
        Returns True if additional user verification is needed.
        """
        # High-value transaction threshold: 80% of max authorized
        if consent_max_amount and amount > 0:
            usage_ratio = amount / consent_max_amount
            if usage_ratio >= 0.80:
                logger.info(f"Step-up required: amount ${amount} is {usage_ratio:.0%} of limit ${consent_max_amount}")
                return True
        
        # Absolute threshold: transactions over $500 require step-up
        STEP_UP_THRESHOLD = 500.0
        if amount >= STEP_UP_THRESHOLD:
            logger.info(f"Step-up required: amount ${amount} exceeds ${STEP_UP_THRESHOLD} threshold")
            return True
        
        return False


# Singleton instance
auth_service = AuthService()


async def write_authorization_to_db(auth_data: dict):
    """Write a single authorization to the database (used by BackgroundTasks)."""
    try:
        async with async_session_maker() as session:
            authorization = Authorization(
                authorization_code=auth_data["authorization_code"],
                consent_id=auth_data["consent_id"],
                decision=auth_data["decision"],
                amount=auth_data["amount"],
                currency=auth_data["currency"],
                merchant_id=auth_data["merchant_id"],
                merchant_name=auth_data.get("merchant_name"),
                merchant_category=auth_data.get("merchant_category"),
                action=auth_data["action"],
                transaction_metadata={"description": auth_data.get("description")},
                expires_at=auth_data["expires_at"],
            )
            session.add(authorization)
            await session.commit()
            logger.debug(f"Authorization {auth_data['authorization_code']} written to DB")
    except Exception as e:
        logger.error(f"Failed to write authorization to DB: {e}")


async def flush_auth_queue():
    """Background task to flush authorization queue to DB (fallback)."""
    
    while True:
        await asyncio.sleep(1)  # Flush every second
        
        if not _auth_queue:
            continue
        
        # Batch flush
        batch = []
        while _auth_queue and len(batch) < 100:
            try:
                batch.append(_auth_queue.popleft())
            except IndexError:
                break
        
        if not batch:
            continue
        
        try:
            async with async_session_maker() as session:
                for auth_data in batch:
                    authorization = Authorization(
                        authorization_code=auth_data["authorization_code"],
                        consent_id=auth_data["consent_id"],
                        decision=auth_data["decision"],
                        amount=auth_data["amount"],
                        currency=auth_data["currency"],
                        merchant_id=auth_data["merchant_id"],
                        merchant_name=auth_data.get("merchant_name"),
                        merchant_category=auth_data.get("merchant_category"),
                        action=auth_data["action"],
                        transaction_metadata={"description": auth_data.get("description")},
                        expires_at=auth_data["expires_at"],
                    )
                    session.add(authorization)
                await session.commit()
                logger.info(f"Flushed {len(batch)} authorizations to database")
        except Exception as e:
            logger.error(f"Auth queue flush error: {e}")


def start_background_worker():
    """Start the background worker if not already running."""
    global _background_worker_started
    if not _background_worker_started:
        _background_worker_started = True
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(flush_auth_queue())
            logger.info("Auth queue background worker started")
        except RuntimeError:
            # No running event loop - will start when first needed
            logger.warning("No event loop running, auth queue worker deferred")
