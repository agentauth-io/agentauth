"""
AgentAuth Event Streaming Service

CloudEvents specification compliant event streaming.
Delivers webhooks to subscribers when events occur.

Features:
- CloudEvents 1.0 compliant payloads
- Async webhook delivery with retries
- Event filtering by type
- Delivery confirmation tracking
"""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EventType(str, Enum):
    """CloudEvents event types for AgentAuth."""

    # Consent events
    CONSENT_CREATED = "agentauth.consent.created"
    CONSENT_REVOKED = "agentauth.consent.revoked"
    CONSENT_EXPIRED = "agentauth.consent.expired"

    # Authorization events
    AUTHORIZATION_APPROVED = "agentauth.authorization.approved"
    AUTHORIZATION_DENIED = "agentauth.authorization.denied"
    AUTHORIZATION_USED = "agentauth.authorization.used"

    # Transaction events
    TRANSACTION_COMPLETED = "agentauth.transaction.completed"
    TRANSACTION_FAILED = "agentauth.transaction.failed"

    # Security events
    VELOCITY_CHECK_FAILED = "agentauth.security.velocity_check_failed"
    RATE_LIMIT_EXCEEDED = "agentauth.security.rate_limit_exceeded"

    # Limit events
    SPENDING_LIMIT_REACHED = "agentauth.limits.spending_limit_reached"
    SPENDING_LIMIT_WARNING = "agentauth.limits.spending_limit_warning"


@dataclass
class CloudEvent:
    """
    CloudEvents 1.0 specification compliant event.

    See: https://cloudevents.io/
    """

    # Required attributes
    specversion: str = "1.0"
    type: str = ""
    source: str = "https://api.agentauth.in"
    id: str = ""

    # Optional attributes
    time: str = ""
    datacontenttype: str = "application/json"
    subject: str | None = None

    # Extension attributes
    developer_id: str | None = None
    trace_id: str | None = None

    # Event data
    data: dict[str, Any] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"evt_{uuid.uuid4().hex[:16]}"
        if not self.time:
            self.time = datetime.now(timezone.utc).isoformat()
        if self.data is None:
            self.data = {}

    def to_dict(self) -> dict:
        """Convert to CloudEvents JSON format."""
        result = {
            "specversion": self.specversion,
            "type": self.type,
            "source": self.source,
            "id": self.id,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": self.data,
        }

        if self.subject:
            result["subject"] = self.subject
        if self.developer_id:
            result["developerid"] = self.developer_id
        if self.trace_id:
            result["traceid"] = self.trace_id

        return result

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())


class EventService:
    """
    Event streaming service with webhook delivery.

    Features:
    - CloudEvents 1.0 specification
    - Async webhook delivery with retries
    - Event persistence for replay
    - Dead letter queue for failed deliveries
    """

    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 5, 30]  # seconds
    TIMEOUT = 10  # seconds

    def __init__(self):
        self._subscribers: dict[str, list[str]] = {}  # developer_id -> [webhook_urls]
        self._pending_events: list[CloudEvent] = []

    async def emit(
        self,
        event_type: EventType,
        data: dict[str, Any],
        developer_id: str | None = None,
        subject: str | None = None,
    ) -> CloudEvent:
        """
        Emit an event.

        Usage:
            await event_service.emit(
                EventType.AUTHORIZATION_APPROVED,
                {"consent_id": "...", "amount": 49.99},
                developer_id="dev_123"
            )
        """
        # Get trace ID if available
        trace_id = None
        try:
            from app.tracing import get_trace_id
            trace_id = get_trace_id()
        except ImportError:
            pass

        event = CloudEvent(
            type=event_type.value,
            data=data,
            developer_id=developer_id,
            subject=subject,
            trace_id=trace_id,
        )

        # Store event
        self._pending_events.append(event)

        # Cache event for replay
        await self._cache_event(event)

        # Deliver to subscribers (async, don't block)
        asyncio.create_task(self._deliver_event(event, developer_id))

        return event

    async def _deliver_event(
        self,
        event: CloudEvent,
        developer_id: str | None
    ) -> None:
        """Deliver event to all subscribers."""
        if not developer_id:
            return

        # Get subscriber webhooks from DB/cache
        webhooks = await self._get_subscriber_webhooks(developer_id)

        for webhook_url in webhooks:
            asyncio.create_task(
                self._deliver_to_webhook(event, webhook_url)
            )

    async def _deliver_to_webhook(
        self,
        event: CloudEvent,
        webhook_url: str,
        attempt: int = 0
    ) -> bool:
        """Deliver event to a single webhook with retries."""
        headers = {
            "Content-Type": "application/cloudevents+json",
            "Ce-Specversion": event.specversion,
            "Ce-Type": event.type,
            "Ce-Source": event.source,
            "Ce-Id": event.id,
            "Ce-Time": event.time,
        }

        if event.trace_id:
            headers["Ce-Traceid"] = event.trace_id

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    webhook_url,
                    json=event.to_dict(),
                    headers=headers
                )

                if response.status_code in (200, 201, 202, 204):
                    return True

                # Retry on server errors
                if response.status_code >= 500 and attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAYS[attempt])
                    return await self._deliver_to_webhook(event, webhook_url, attempt + 1)

                # Log failed delivery
                await self._log_delivery_failure(event, webhook_url, response.status_code)
                return False

        except Exception as e:
            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(self.RETRY_DELAYS[attempt])
                return await self._deliver_to_webhook(event, webhook_url, attempt + 1)

            await self._log_delivery_failure(event, webhook_url, str(e))
            return False

    async def _get_subscriber_webhooks(self, developer_id: str) -> list[str]:
        """Get webhook URLs for a developer."""
        # Try cache first
        try:
            from app.services.cache_service import get_cache_service
            cache = get_cache_service()
            cached = await cache.get(f"webhooks:{developer_id}")
            if cached:
                return cached
        except Exception:
            pass

        # Would query database here
        # For now return empty (webhooks registered via API)
        return self._subscribers.get(developer_id, [])

    async def _cache_event(self, event: CloudEvent) -> None:
        """Cache event for replay capability."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()

            # Store in sorted set by timestamp
            key = f"events:{event.developer_id or 'global'}"
            score = datetime.fromisoformat(event.time.replace("Z", "+00:00")).timestamp()

            await client.zadd(key, {event.to_json(): score})

            # Keep only last 1000 events per developer
            await client.zremrangebyrank(key, 0, -1001)

            # Expire after 7 days
            await client.expire(key, 86400 * 7)
        except Exception:
            pass

    async def _log_delivery_failure(
        self,
        event: CloudEvent,
        webhook_url: str,
        error: Any
    ) -> None:
        """Log failed webhook delivery to dead letter queue."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()

            failure = {
                "event_id": event.id,
                "event_type": event.type,
                "webhook_url": webhook_url,
                "error": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await client.lpush("dlq:webhooks", json.dumps(failure))
            await client.ltrim("dlq:webhooks", 0, 9999)  # Keep last 10k failures
        except Exception:
            pass

    async def get_recent_events(
        self,
        developer_id: str,
        limit: int = 50
    ) -> list[dict]:
        """Get recent events for a developer."""
        try:
            from app.services.cache_service import get_redis
            client = await get_redis()

            key = f"events:{developer_id}"
            events = await client.zrevrange(key, 0, limit - 1)

            return [json.loads(e) for e in events]
        except Exception:
            return []

    def register_webhook(self, developer_id: str, webhook_url: str) -> None:
        """Register a webhook URL for a developer (in-memory, for testing)."""
        if developer_id not in self._subscribers:
            self._subscribers[developer_id] = []
        if webhook_url not in self._subscribers[developer_id]:
            self._subscribers[developer_id].append(webhook_url)


# Singleton instance
_event_service: EventService | None = None


def get_event_service() -> EventService:
    """Get singleton event service instance."""
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service


# Convenience functions
async def emit_event(
    event_type: EventType,
    data: dict[str, Any],
    developer_id: str | None = None,
    subject: str | None = None
) -> CloudEvent:
    """Quick helper to emit an event."""
    return await get_event_service().emit(event_type, data, developer_id, subject)


# Pre-built event emitters for common cases
async def emit_authorization_approved(
    consent_id: str,
    authorization_code: str,
    amount: float,
    merchant_id: str,
    developer_id: str | None = None
) -> CloudEvent:
    """Emit authorization approved event."""
    return await emit_event(
        EventType.AUTHORIZATION_APPROVED,
        {
            "consent_id": consent_id,
            "authorization_code": authorization_code,
            "amount": amount,
            "merchant_id": merchant_id,
        },
        developer_id=developer_id,
        subject=consent_id
    )


async def emit_authorization_denied(
    consent_id: str,
    reason: str,
    amount: float,
    merchant_id: str,
    developer_id: str | None = None
) -> CloudEvent:
    """Emit authorization denied event."""
    return await emit_event(
        EventType.AUTHORIZATION_DENIED,
        {
            "consent_id": consent_id,
            "reason": reason,
            "amount": amount,
            "merchant_id": merchant_id,
        },
        developer_id=developer_id,
        subject=consent_id
    )


async def emit_consent_created(
    consent_id: str,
    user_id: str,
    max_amount: float,
    expires_at: str,
    developer_id: str | None = None
) -> CloudEvent:
    """Emit consent created event."""
    return await emit_event(
        EventType.CONSENT_CREATED,
        {
            "consent_id": consent_id,
            "user_id": user_id,
            "max_amount": max_amount,
            "expires_at": expires_at,
        },
        developer_id=developer_id,
        subject=consent_id
    )
