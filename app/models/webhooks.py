"""
Webhook Models

Database models for webhook endpoints and delivery tracking.
"""

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Webhook(Base):
    """
    Webhook endpoint configuration.

    Stores user-defined webhook URLs and event subscriptions.
    """

    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # Endpoint configuration
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Event subscriptions (stored as comma-separated string for simplicity)
    events: Mapped[str] = mapped_column(
        String(1000), default="authorization.approved,authorization.denied"
    )

    # Security
    secret: Mapped[str] = mapped_column(
        String(64), default=lambda: secrets.token_hex(32)
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Delivery tracking
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status_code: Mapped[int | None] = mapped_column(nullable=True)
    failure_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def get_events_list(self) -> list[str]:
        """Get events as a list."""
        return [e.strip() for e in self.events.split(",") if e.strip()]

    def set_events_list(self, events: list[str]):
        """Set events from a list."""
        self.events = ",".join(events)


class WebhookDelivery(Base):
    """
    Webhook delivery log.

    Tracks each attempt to deliver a webhook.
    """

    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    webhook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    # Delivery status
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, success, failed
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Timing
    attempts: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# Available webhook events
WEBHOOK_EVENTS = [
    "authorization.requested",
    "authorization.approved",
    "authorization.denied",
    "authorization.expired",
    "limit.exceeded",
    "rule.triggered",
]
