"""
Auth Service - Authorization decision engine

OPTIMIZED for <10ms latency:
1. Token verification is in-memory (JWT decode) - ~1ms
2. Consent lookup uses pre-warmed in-memory cache - ~0ms
3. Authorization record write uses FastAPI BackgroundTasks
4. Risk assessment via ML models (fraud, anomaly detection)
"""

import asyncio
import logging
import secrets
from collections import deque
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.authorization import Authorization
from app.models.database import async_session_maker
from app.schemas.authorize import (
    AuthorizeRequest,
    AuthorizeResponse,
    RiskAssessmentSchema,
)
from app.services.audit_service import create_audit_entry
from app.services.consent_service import consent_service
from app.services.risk_service import RiskDecision, get_risk_service
from app.services.token_service import token_service

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory LRU cache for consents (faster than Redis for single-instance)
_consent_cache: dict[str, tuple[dict, datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

# In-memory cache for authorization codes (for verification)
# Limited to 50k entries; oldest entries evicted when full
_AUTH_CACHE_MAX_SIZE = 50000
_auth_cache: dict[str, dict] = {}

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

    def _get_cached_consent(self, consent_id: str) -> dict | None:
        """Get consent from in-memory cache if not expired."""
        if consent_id in _consent_cache:
            data, cached_at = _consent_cache[consent_id]
            if (
                datetime.now(timezone.utc) - cached_at
            ).total_seconds() < CACHE_TTL_SECONDS:
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
        self, db: AsyncSession, consent_id: str
    ) -> dict | None:
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
                    parsed = datetime.fromisoformat(str(expires_at))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    if parsed > datetime.now(timezone.utc):
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
        request: AuthorizeRequest,
        client_ip: str | None = None,
        user_agent: str | None = None,
        skip_risk_assessment: bool = False,
    ) -> AuthorizeResponse:
        """
        Make an authorization decision.

        OPTIMIZED for <50ms latency on cache hits.

        Args:
            db: Database session
            request: Authorization request
            client_ip: Client IP for audit logging
            user_agent: User agent for audit logging
            skip_risk_assessment: Skip ML risk assessment (for testing/low-latency needs)
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
            # Log the denial
            await create_audit_entry(
                db=db,
                event_type="authorization_denied",
                actor_id=(
                    verification.payload.user_id if verification.payload else "unknown"
                ),
                actor_type="agent",
                action="authorize",
                outcome="denied",
                resource_id=None,
                resource_type="authorization",
                reason=verification.reason,
                metadata={
                    "transaction_amount": request.transaction.amount,
                    "merchant_id": request.transaction.merchant_id,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )

            return AuthorizeResponse(
                decision="DENY",
                reason=verification.reason,
                message=verification.message,
            )

        # Step 2: Check consent (cache-first, ~5ms cached, ~300ms uncached)
        consent = await self._check_consent_cached(db, verification.payload.consent_id)

        if consent is None:
            # Log the denial
            await create_audit_entry(
                db=db,
                event_type="authorization_denied",
                actor_id=(
                    verification.payload.user_id if verification.payload else "unknown"
                ),
                actor_type="agent",
                action="authorize",
                outcome="denied",
                resource_id=None,
                resource_type="authorization",
                reason="consent_invalid",
                metadata={
                    "consent_id": (
                        verification.payload.consent_id
                        if verification.payload
                        else None
                    ),
                    "transaction_amount": request.transaction.amount,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )

            return AuthorizeResponse(
                decision="DENY",
                reason="consent_invalid",
                message="Consent has been revoked or does not exist",
            )

        # Step 3: Risk Assessment (ML-based fraud & anomaly detection)
        risk_assessment = None
        if not skip_risk_assessment:
            try:
                risk_service = get_risk_service()
                risk = await risk_service.assess(
                    user_id=verification.payload.user_id,
                    amount=request.transaction.amount,
                    merchant_id=request.transaction.merchant_id or "unknown",
                    category_code=request.transaction.merchant_category or "",
                    consent_max_amount=verification.payload.max_amount,
                )

                # Build risk assessment schema for response
                risk_assessment = RiskAssessmentSchema(
                    risk_level=risk.risk_level.value,
                    risk_score=risk.risk_score,
                    decision=risk.decision.value,
                    assessment_time_ms=risk.assessment_time_ms,
                    fraud_detection=(
                        {
                            "is_fraud": (
                                risk.fraud_prediction.is_fraud
                                if risk.fraud_prediction
                                else False
                            ),
                            "fraud_score": (
                                risk.fraud_prediction.fraud_score
                                if risk.fraud_prediction
                                else 0.0
                            ),
                            "risk_level": (
                                risk.fraud_prediction.risk_level
                                if risk.fraud_prediction
                                else "low"
                            ),
                        }
                        if risk.fraud_prediction
                        else None
                    ),
                    anomaly_detection=(
                        {
                            "is_anomaly": (
                                risk.anomaly_result.is_anomaly
                                if risk.anomaly_result
                                else False
                            ),
                            "anomaly_score": (
                                risk.anomaly_result.anomaly_score
                                if risk.anomaly_result
                                else 0.0
                            ),
                        }
                        if risk.anomaly_result
                        else None
                    ),
                    factors=risk.factors,
                    recommendations=risk.recommendations,
                )

                # Handle risk-based decisions
                if risk.decision == RiskDecision.BLOCK:
                    await create_audit_entry(
                        db=db,
                        event_type="authorization_denied",
                        actor_id=verification.payload.user_id,
                        actor_type="agent",
                        action="authorize",
                        outcome="denied",
                        resource_id=None,
                        resource_type="authorization",
                        reason="risk_blocked",
                        metadata={
                            "consent_id": verification.payload.consent_id,
                            "transaction_amount": request.transaction.amount,
                            "risk_score": risk.risk_score,
                            "risk_level": risk.risk_level.value,
                        },
                        ip_address=client_ip,
                        user_agent=user_agent,
                    )

                    return AuthorizeResponse(
                        decision="DENY",
                        reason="risk_blocked",
                        message=f"Transaction blocked due to high risk (score: {risk.risk_score:.2f})",
                        risk_assessment=risk_assessment,
                    )

                # STEP_UP for review cases
                if risk.decision == RiskDecision.REVIEW:
                    # Log for review but still allow with warning
                    logger.warning(
                        f"Transaction flagged for review: user={verification.payload.user_id}, "
                        f"amount={request.transaction.amount}, risk={risk.risk_score:.2f}"
                    )

            except Exception as e:
                logger.error(f"Risk assessment failed: {e}")
                # Continue without risk assessment if it fails

        # Step 4: All checks passed - generate authorization code
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.auth_code_expiry_seconds)
        authorization_code = generate_authorization_code()

        # Cache authorization in memory for instant verification
        # Evict expired entries if cache is getting large
        if len(_auth_cache) > _AUTH_CACHE_MAX_SIZE:
            cutoff = datetime.now(timezone.utc)
            expired_keys = [
                k
                for k, v in _auth_cache.items()
                if v.get("expires_at", cutoff) < cutoff
            ]
            for k in expired_keys:
                del _auth_cache[k]
            # If still too large, remove oldest entries
            if len(_auth_cache) > _AUTH_CACHE_MAX_SIZE:
                oldest = sorted(
                    _auth_cache.keys(),
                    key=lambda k: _auth_cache[k].get("created_at", cutoff),
                )
                for k in oldest[: len(_auth_cache) - _AUTH_CACHE_MAX_SIZE + 1000]:
                    del _auth_cache[k]

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

            # Log the successful authorization
            await create_audit_entry(
                db=db,
                event_type="authorization_allowed",
                actor_id=verification.payload.user_id,
                actor_type="agent",
                action="authorize",
                outcome="success",
                resource_id=authorization_code,
                resource_type="authorization",
                metadata={
                    "consent_id": verification.payload.consent_id,
                    "transaction_amount": request.transaction.amount,
                    "merchant_id": request.transaction.merchant_id,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"Failed to write authorization to DB: {e}")
            # Continue anyway - in-memory cache still works for verification

        # Return response
        return AuthorizeResponse(
            decision="ALLOW",
            authorization_code=authorization_code,
            expires_at=expires_at,
            consent_id=verification.payload.consent_id,
            risk_assessment=risk_assessment,
        )

    async def check_step_up_required(
        self, consent_id: str, amount: float, consent_max_amount: float | None = None
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
                logger.info(
                    f"Step-up required: amount ${amount} is {usage_ratio:.0%} of limit ${consent_max_amount}"
                )
                return True

        # Absolute threshold: transactions over $500 require step-up
        STEP_UP_THRESHOLD = 500.0
        if amount >= STEP_UP_THRESHOLD:
            logger.info(
                f"Step-up required: amount ${amount} exceeds ${STEP_UP_THRESHOLD} threshold"
            )
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
            logger.debug(
                f"Authorization {auth_data['authorization_code']} written to DB"
            )
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
                        transaction_metadata={
                            "description": auth_data.get("description")
                        },
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
