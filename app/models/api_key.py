"""
API Key model for persistent key storage.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, Index
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
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_api_keys_active_hash", "key_hash", "is_active"),
    )
