"""
Tests for CloudEvents event streaming service.

Pure Python tests with httpx mocking.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.event_service import (
    CloudEvent,
    EventService,
    EventType,
    emit_authorization_approved,
    emit_authorization_denied,
    emit_consent_created,
    get_event_service,
)


class TestEventType:
    def test_all_event_types_exist(self):
        assert EventType.CONSENT_CREATED == "agentauth.consent.created"
        assert EventType.CONSENT_REVOKED == "agentauth.consent.revoked"
        assert EventType.CONSENT_EXPIRED == "agentauth.consent.expired"
        assert EventType.AUTHORIZATION_APPROVED == "agentauth.authorization.approved"
        assert EventType.AUTHORIZATION_DENIED == "agentauth.authorization.denied"
        assert EventType.AUTHORIZATION_USED == "agentauth.authorization.used"
        assert EventType.TRANSACTION_COMPLETED == "agentauth.transaction.completed"
        assert EventType.TRANSACTION_FAILED == "agentauth.transaction.failed"
        assert EventType.VELOCITY_CHECK_FAILED == "agentauth.security.velocity_check_failed"
        assert EventType.RATE_LIMIT_EXCEEDED == "agentauth.security.rate_limit_exceeded"
        assert EventType.SPENDING_LIMIT_REACHED == "agentauth.limits.spending_limit_reached"
        assert EventType.SPENDING_LIMIT_WARNING == "agentauth.limits.spending_limit_warning"

    def test_event_type_count(self):
        assert len(EventType) == 12


class TestCloudEvent:
    def test_post_init_generates_id(self):
        event = CloudEvent(type="test.event")
        assert event.id.startswith("evt_")
        assert len(event.id) > 4

    def test_post_init_sets_time(self):
        event = CloudEvent(type="test.event")
        assert event.time != ""
        assert "T" in event.time  # ISO format

    def test_post_init_empty_data(self):
        event = CloudEvent(type="test.event")
        assert event.data == {}

    def test_to_dict_required_fields(self):
        event = CloudEvent(type="test.event", data={"key": "val"})
        d = event.to_dict()
        assert d["specversion"] == "1.0"
        assert d["type"] == "test.event"
        assert d["source"] == "https://api.agentauth.in"
        assert d["id"].startswith("evt_")
        assert "time" in d
        assert d["datacontenttype"] == "application/json"
        assert d["data"] == {"key": "val"}

    def test_to_dict_optional_fields(self):
        event = CloudEvent(
            type="test.event",
            subject="sub_123",
            developer_id="dev_1",
            trace_id="trace_abc",
        )
        d = event.to_dict()
        assert d["subject"] == "sub_123"
        assert d["developerid"] == "dev_1"
        assert d["traceid"] == "trace_abc"

    def test_to_dict_omits_none_optional(self):
        event = CloudEvent(type="test.event")
        d = event.to_dict()
        assert "subject" not in d
        assert "developerid" not in d
        assert "traceid" not in d

    def test_to_json(self):
        event = CloudEvent(type="test.event", data={"k": "v"})
        j = event.to_json()
        parsed = json.loads(j)
        assert parsed["type"] == "test.event"
        assert parsed["data"] == {"k": "v"}

    def test_custom_id(self):
        event = CloudEvent(type="test.event", id="custom_id")
        assert event.id == "custom_id"


class TestEventService:
    @pytest.mark.asyncio
    async def test_emit_returns_cloud_event(self):
        service = EventService()
        with patch.object(service, "_cache_event", new_callable=AsyncMock):
            event = await service.emit(
                EventType.AUTHORIZATION_APPROVED,
                {"amount": 50.0},
            )
        assert isinstance(event, CloudEvent)
        assert event.type == "agentauth.authorization.approved"
        assert event.data["amount"] == 50.0

    @pytest.mark.asyncio
    async def test_emit_appends_to_pending(self):
        service = EventService()
        with patch.object(service, "_cache_event", new_callable=AsyncMock):
            await service.emit(EventType.CONSENT_CREATED, {"id": "c1"})
            await service.emit(EventType.CONSENT_REVOKED, {"id": "c2"})
        assert len(service._pending_events) == 2

    @pytest.mark.asyncio
    async def test_emit_with_developer_id(self):
        service = EventService()
        with patch.object(service, "_cache_event", new_callable=AsyncMock):
            event = await service.emit(
                EventType.AUTHORIZATION_APPROVED,
                {"amount": 50.0},
                developer_id="dev_123",
            )
        assert event.developer_id == "dev_123"

    def test_register_webhook(self):
        service = EventService()
        service.register_webhook("dev_1", "https://example.com/webhook")
        assert "dev_1" in service._subscribers
        assert "https://example.com/webhook" in service._subscribers["dev_1"]

    def test_register_webhook_no_duplicates(self):
        service = EventService()
        service.register_webhook("dev_1", "https://example.com/webhook")
        service.register_webhook("dev_1", "https://example.com/webhook")
        assert len(service._subscribers["dev_1"]) == 1

    def test_register_webhook_multiple_urls(self):
        service = EventService()
        service.register_webhook("dev_1", "https://a.com/hook")
        service.register_webhook("dev_1", "https://b.com/hook")
        assert len(service._subscribers["dev_1"]) == 2

    @pytest.mark.asyncio
    async def test_deliver_to_webhook_success(self):
        service = EventService()
        event = CloudEvent(type="test.event", data={"k": "v"})

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.event_service.httpx.AsyncClient", return_value=mock_client):
            result = await service._deliver_to_webhook(event, "https://example.com/hook")
        assert result is True

    @pytest.mark.asyncio
    async def test_deliver_to_webhook_server_error_retries(self):
        service = EventService()
        service.RETRY_DELAYS = [0, 0, 0]  # No actual delay in tests
        event = CloudEvent(type="test.event", data={})

        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200

        call_count = 0
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return mock_response_500
            return mock_response_200

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.event_service.httpx.AsyncClient", return_value=mock_client):
            result = await service._deliver_to_webhook(event, "https://example.com/hook")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_recent_events_returns_empty_without_redis(self):
        service = EventService()
        events = await service.get_recent_events("dev_1")
        assert events == []


class TestGetEventService:
    def test_singleton(self):
        import app.services.event_service as emod
        emod._event_service = None
        s1 = get_event_service()
        s2 = get_event_service()
        assert s1 is s2
        emod._event_service = None


class TestConvenienceFunctions:
    @pytest.mark.asyncio
    async def test_emit_authorization_approved(self):
        import app.services.event_service as emod
        emod._event_service = None

        service = get_event_service()
        with patch.object(service, "_cache_event", new_callable=AsyncMock):
            event = await emit_authorization_approved(
                consent_id="c_1",
                authorization_code="authz_1",
                amount=99.99,
                merchant_id="m_1",
            )
        assert event.type == "agentauth.authorization.approved"
        assert event.data["amount"] == 99.99
        emod._event_service = None

    @pytest.mark.asyncio
    async def test_emit_authorization_denied(self):
        import app.services.event_service as emod
        emod._event_service = None

        service = get_event_service()
        with patch.object(service, "_cache_event", new_callable=AsyncMock):
            event = await emit_authorization_denied(
                consent_id="c_1",
                reason="limit exceeded",
                amount=999.99,
                merchant_id="m_1",
            )
        assert event.type == "agentauth.authorization.denied"
        assert event.data["reason"] == "limit exceeded"
        emod._event_service = None

    @pytest.mark.asyncio
    async def test_emit_consent_created(self):
        import app.services.event_service as emod
        emod._event_service = None

        service = get_event_service()
        with patch.object(service, "_cache_event", new_callable=AsyncMock):
            event = await emit_consent_created(
                consent_id="c_1",
                user_id="u_1",
                max_amount=500.0,
                expires_at="2025-01-01T00:00:00Z",
            )
        assert event.type == "agentauth.consent.created"
        assert event.data["user_id"] == "u_1"
        emod._event_service = None
