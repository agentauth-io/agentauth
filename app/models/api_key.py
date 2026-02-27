"""
API Key model for persistent key storage.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Index, Integer, String

from app.models.database import Base


class ApiKey(Base):
    """Persistent API key storage."""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_id = Column(String(16), unique=True, nullable=False)
    owner = Column(String(255), nullable=False, index=True)
    permissions = Column(JSON, nullable=False, default=["read", "write"])
    rate_limit = Column(Integer, nullable=False, default=1000)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=90),
    )

    __table_args__ = (
        Index("ix_api_keys_active_hash", "key_hash", "is_active"),
        Index("ix_api_keys_owner_active", "owner", "is_active"),
    )
