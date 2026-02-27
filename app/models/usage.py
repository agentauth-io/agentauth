"""
Usage tracking model for API metering.

Records individual API calls for billing and analytics.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from app.models.database import Base


class UsageRecord(Base):
    """
    Individual API usage record.

    Tracks each API call for metering, billing, and analytics.
    Designed for high-volume inserts with efficient querying by user and date.
    """

    __tablename__ = "usage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)

    # API call details
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    status_code = Column(Integer, nullable=True)

    # Timing
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds

    # Billing period reference (YYYY-MM format for easy grouping)
    billing_period = Column(String(7), nullable=False, index=True)  # e.g., "2026-01"

    # Optional metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_usage_user_period", "user_id", "billing_period"),
        Index("ix_usage_user_endpoint", "user_id", "endpoint"),
    )

    def __repr__(self):
        return f"<UsageRecord {self.user_id} {self.endpoint} {self.timestamp}>"


class UsageSummary(Base):
    """
    Aggregated usage summary per user per billing period.

    Pre-aggregated data for fast billing queries.
    Updated incrementally as usage is recorded.
    """

    __tablename__ = "usage_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    billing_period = Column(String(7), nullable=False, index=True)  # e.g., "2026-01"

    # Aggregated counts
    total_api_calls = Column(Integer, default=0, nullable=False)
    consents_created = Column(Integer, default=0, nullable=False)
    authorizations_created = Column(Integer, default=0, nullable=False)
    verifications_performed = Column(Integer, default=0, nullable=False)

    # Performance stats
    avg_response_time_ms = Column(Integer, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    first_call_at = Column(DateTime, nullable=True)
    last_call_at = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Unique constraint on user + period
    __table_args__ = (
        Index("ix_summary_user_period", "user_id", "billing_period", unique=True),
    )

    def __repr__(self):
        return f"<UsageSummary {self.user_id} {self.billing_period} calls={self.total_api_calls}>"

    def increment(self, endpoint: str):
        """Increment counters based on endpoint."""
        self.total_api_calls += 1
        self.last_call_at = datetime.now(timezone.utc)

        if self.first_call_at is None:
            self.first_call_at = self.last_call_at

        # Track by endpoint type
        if "/consents" in endpoint:
            self.consents_created += 1
        elif "/authorize" in endpoint:
            self.authorizations_created += 1
        elif "/verify" in endpoint:
            self.verifications_performed += 1
