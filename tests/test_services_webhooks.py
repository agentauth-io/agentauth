"""
Tests for Webhooks service.

Requires database fixtures + httpx mocking.
"""

import hashlib
import hmac
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.webhooks import WEBHOOK_EVENTS
from app.services.webhooks import WebhooksService, emit_authorization_event


class TestWebhooksServiceCRUD:
    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self, db_session):
        service = WebhooksService(db_session)
        result = await service.list_webhooks("user_1")
        assert result == []

    @pytest.mark.asyncio
    async def test_create_webhook(self, db_session):
        service = WebhooksService(db_session)
        webhook = await service.create_webhook(
            user_id="user_1",
            url="https://example.com/hook",
            events=["authorization.approved", "authorization.denied"],
        )
        assert webhook.user_id == "user_1"
        assert webhook.url == "https://example.com/hook"
        assert "authorization.approved" in webhook.get_events_list()
        assert webhook.secret is not None
        assert webhook.is_active is True

    @pytest.mark.asyncio
    async def test_create_webhook_with_description(self, db_session):
        service = WebhooksService(db_session)
        webhook = await service.create_webhook(
            user_id="user_1",
            url="https://example.com/hook",
            events=["authorization.approved"],
            description="Test webhook",
        )
        assert webhook.description == "Test webhook"

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_events_fallback(self, db_session):
        service = WebhooksService(db_session)
        webhook = await service.create_webhook(
            user_id="user_1",
            url="https://example.com/hook",
            events=["invalid.event"],
        )
        events = webhook.get_events_list()
        assert "authorization.approved" in events
        assert "authorization.denied" in events

    @pytest.mark.asyncio
    async def test_list_webhooks(self, db_session):
        service = WebhooksService(db_session)
        await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        await service.create_webhook(
            "user_1", "https://b.com/hook", ["authorization.denied"]
        )
        result = await service.list_webhooks("user_1")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_webhooks_user_isolation(self, db_session):
        service = WebhooksService(db_session)
        await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        await service.create_webhook(
            "user_2", "https://b.com/hook", ["authorization.approved"]
        )
        result = await service.list_webhooks("user_1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_webhook(self, db_session):
        service = WebhooksService(db_session)
        created = await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        found = await service.get_webhook(created.id, "user_1")
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_webhook_wrong_user(self, db_session):
        service = WebhooksService(db_session)
        created = await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        found = await service.get_webhook(created.id, "user_2")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_webhook_nonexistent(self, db_session):
        service = WebhooksService(db_session)
        found = await service.get_webhook(uuid4(), "user_1")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_webhook_url(self, db_session):
        service = WebhooksService(db_session)
        created = await service.create_webhook(
            "user_1", "https://old.com/hook", ["authorization.approved"]
        )
        updated = await service.update_webhook(
            created.id, "user_1", url="https://new.com/hook"
        )
        assert updated.url == "https://new.com/hook"

    @pytest.mark.asyncio
    async def test_update_webhook_events(self, db_session):
        service = WebhooksService(db_session)
        created = await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        updated = await service.update_webhook(
            created.id, "user_1", events=["authorization.denied", "limit.exceeded"]
        )
        events = updated.get_events_list()
        assert "authorization.denied" in events
        assert "limit.exceeded" in events

    @pytest.mark.asyncio
    async def test_update_webhook_is_active(self, db_session):
        service = WebhooksService(db_session)
        created = await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        updated = await service.update_webhook(created.id, "user_1", is_active=False)
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_update_webhook_nonexistent(self, db_session):
        service = WebhooksService(db_session)
        result = await service.update_webhook(uuid4(), "user_1", url="https://new.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_webhook(self, db_session):
        service = WebhooksService(db_session)
        created = await service.create_webhook(
            "user_1", "https://a.com/hook", ["authorization.approved"]
        )
        deleted = await service.delete_webhook(created.id, "user_1")
        assert deleted is True
        # Should not appear in list (soft delete)
        result = await service.list_webhooks("user_1")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_delete_webhook_nonexistent(self, db_session):
        service = WebhooksService(db_session)
        result = await service.delete_webhook(uuid4(), "user_1")
        assert result is False


class TestWebhooksServiceSignature:
    def test_generate_signature(self):
        service = WebhooksService.__new__(WebhooksService)
        payload = '{"event": "test"}'
        secret = "test_secret"
        sig = service._generate_signature(payload, secret)
        expected = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        assert sig == expected

    def test_verify_signature_valid(self):
        payload = '{"event": "test"}'
        secret = "test_secret"
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        assert WebhooksService.verify_signature(payload, sig, secret) is True

    def test_verify_signature_invalid(self):
        assert (
            WebhooksService.verify_signature('{"a":1}', "wrong_sig", "secret") is False
        )


class TestWebhooksServiceDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_event_creates_delivery(self, db_session):
        service = WebhooksService(db_session)
        webhook = await service.create_webhook(
            "user_1", "https://example.com/hook", ["authorization.approved"]
        )

        # Mock the HTTP delivery
        with patch.object(service, "_deliver_webhook", new_callable=AsyncMock):
            await service.dispatch_event(
                "user_1", "authorization.approved", {"amount": 50.0}
            )

    @pytest.mark.asyncio
    async def test_dispatch_event_filters_by_subscription(self, db_session):
        service = WebhooksService(db_session)
        await service.create_webhook(
            "user_1", "https://a.com", ["authorization.approved"]
        )
        await service.create_webhook(
            "user_1", "https://b.com", ["authorization.denied"]
        )

        deliver_calls = []
        original_deliver = service._deliver_webhook

        async def mock_deliver(*args, **kwargs):
            deliver_calls.append(kwargs.get("event_type") or args)

        with patch.object(service, "_deliver_webhook", side_effect=mock_deliver):
            await service.dispatch_event(
                "user_1", "authorization.approved", {"amount": 50.0}
            )
        # Only the first webhook subscribed to authorization.approved
        assert len(deliver_calls) == 1


class TestEmitAuthorizationEvent:
    @pytest.mark.asyncio
    async def test_emit_authorization_approved(self, db_session):
        # Create a webhook first
        service = WebhooksService(db_session)
        await service.create_webhook(
            "user_1", "https://example.com/hook", ["authorization.approved"]
        )

        with patch(
            "app.services.webhooks.WebhooksService._deliver_webhook",
            new_callable=AsyncMock,
        ):
            await emit_authorization_event(
                db_session, "user_1", "approved", amount=49.99, merchant="amazon"
            )


class TestWebhookEvents:
    def test_webhook_events_list(self):
        assert "authorization.requested" in WEBHOOK_EVENTS
        assert "authorization.approved" in WEBHOOK_EVENTS
        assert "authorization.denied" in WEBHOOK_EVENTS
        assert "authorization.expired" in WEBHOOK_EVENTS
        assert "limit.exceeded" in WEBHOOK_EVENTS
        assert "rule.triggered" in WEBHOOK_EVENTS
