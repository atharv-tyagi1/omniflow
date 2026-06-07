import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Text, UniqueConstraint, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.models.base import Base

class PublicApiKey(Base):
    """
    Represents a public API key for an external client.
    Key material is NEVER stored in plaintext.
    """
    __tablename__ = "public_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # securely hashed key material
    prefix = Column(String(8), nullable=False)  # prefix for UI identification (e.g. "of_live_...")
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_public_api_keys_workspace_id", "workspace_id"),
        Index("ix_public_api_keys_prefix", "prefix"),  # useful for initial candidate lookup
    )


class PublicApiKeyScope(Base):
    """
    Normalized mapping of scopes assigned to a PublicApiKey.
    """
    __tablename__ = "public_api_key_scopes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("public_api_keys.id", ondelete="CASCADE"), nullable=False)
    scope_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("api_key_id", "scope_name", name="uq_public_api_key_scope"),
        Index("ix_public_api_key_scopes_key_id", "api_key_id"),
    )


class PublicApiKeyRotation(Base):
    """
    Audit trail for API key rotations. Never stores secret material.
    """
    __tablename__ = "public_api_key_rotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("public_api_keys.id", ondelete="CASCADE"), nullable=False)
    old_key_prefix = Column(String(8), nullable=False)
    new_key_prefix = Column(String(8), nullable=False)
    rotated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rotated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_public_api_key_rotations_api_key_id", "api_key_id"),
        Index("ix_public_api_key_rotations_workspace_id", "workspace_id"),
    )


class IdempotencyKey(Base):
    """
    Stores requests to guarantee safe retries for mutating operations.
    """
    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    idempotency_key = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status = Column(String, nullable=False)  # "in_progress", "completed", "failed"
    response_body = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # used for background cleanup

    __table_args__ = (
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_workspace_idempotency_key"),
        Index("ix_idempotency_keys_expires_at", "expires_at"),
    )


class PublicWebhook(Base):
    """
    Configuration for an external webhook source.
    """
    __tablename__ = "public_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False)  # e.g. "shopify", "internal_crm"
    url = Column(String, nullable=True)  # Optional URL if we dispatch TO them, or null if they dispatch TO us
    secret_hash = Column(String, nullable=False)  # Hashed or securely encrypted verification secret
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("workspace_id", "source", name="uq_workspace_webhook_source"),
    )


class PublicAsyncJob(Base):
    """
    Durable execution record for async API behaviors (e.g. async chat processing).
    """
    __tablename__ = "public_async_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String, nullable=False)  # e.g., "chat_message"
    status = Column(String, nullable=False, default="pending")  # "pending", "completed", "failed"
    result_payload = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_public_async_jobs_workspace_id_status", "workspace_id", "status"),
        Index("ix_public_async_jobs_status_attempts", "status", "attempts"),
    )
