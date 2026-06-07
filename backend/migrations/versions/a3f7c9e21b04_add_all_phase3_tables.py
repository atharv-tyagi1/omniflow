"""add_all_phase3_tables

Revision ID: a3f7c9e21b04
Revises: 8d9d412d6fcb
Create Date: 2026-06-02 14:16:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "a3f7c9e21b04"
down_revision: Union[str, Sequence[str], None] = "8d9d412d6fcb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add vector extension if postgresql
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── customers ──────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("telegram_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_customers_workspace", "customers", ["workspace_id"])
    op.create_index("idx_customers_email", "customers", ["email"])
    op.create_index("idx_customers_telegram", "customers", ["telegram_id"])

    # ── conversations ──────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("customer_id", UUID(), nullable=False),
        sa.Column("current_agent", sa.String(50), nullable=True),
        sa.Column("channel", sa.String(50), server_default="web", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_conversations_workspace", "conversations", ["workspace_id"])
    op.create_index("idx_conversations_customer", "conversations", ["customer_id"])
    op.create_index("idx_conversations_channel", "conversations", ["channel"])

    # ── messages ───────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("sender_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(50), server_default="text", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_messages_conversation", "messages", ["conversation_id"])
    op.create_index("idx_messages_created", "messages", ["created_at"])

    # ── handoffs ───────────────────────────────────────────
    op.create_table(
        "handoffs",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("from_agent", sa.String(50), nullable=False),
        sa.Column("to_agent", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_handoffs_conversation", "handoffs", ["conversation_id"])

    # ── documents ──────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("uploaded_by", UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_documents_workspace", "documents", ["workspace_id"])
    op.create_index("idx_documents_status", "documents", ["status"])

    # ── document_chunks (with pgvector) ────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("document_id", UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Add vector column via raw SQL (pgvector type not natively supported by Alembic)
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(768)")
    op.create_index("idx_chunks_document", "document_chunks", ["document_id"])

    # ── tickets ────────────────────────────────────────────
    op.create_table(
        "tickets",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("customer_id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), server_default="medium", nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("assigned_to", UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tickets_workspace", "tickets", ["workspace_id"])
    op.create_index("idx_tickets_status", "tickets", ["status"])
    op.create_index("idx_tickets_priority", "tickets", ["priority"])

    # ── sentiments ─────────────────────────────────────────
    op.create_table(
        "sentiments",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("label", sa.String(20), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sentiments_label", "sentiments", ["label"])

    # ── topics ─────────────────────────────────────────────
    op.create_table(
        "topics",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_topics_name", "topics", ["topic_name"])

    # ── analytics_reports ──────────────────────────────────
    op.create_table(
        "analytics_reports",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("report_json", JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_reports_workspace", "analytics_reports", ["workspace_id"])

    # ── datasets ───────────────────────────────────────────
    op.create_table(
        "datasets",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_datasets_workspace", "datasets", ["workspace_id"])

    # ── dataset_queries ────────────────────────────────────
    op.create_table(
        "dataset_queries",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("dataset_id", UUID(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("chart_config", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_dataset_queries_dataset", "dataset_queries", ["dataset_id"])

    # ── workflows ──────────────────────────────────────────
    op.create_table(
        "workflows",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workflows_workspace", "workflows", ["workspace_id"])

    # ── workflow_runs ──────────────────────────────────────
    op.create_table(
        "workflow_runs",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workflow_id", UUID(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("execution_log", JSONB(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workflow_runs_workflow", "workflow_runs", ["workflow_id"])

    # ── voice_interactions ─────────────────────────────────
    op.create_table(
        "voice_interactions",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("conversation_id", UUID(), nullable=False),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_voice_conversation", "voice_interactions", ["conversation_id"])

    # ── notifications ──────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("type", sa.String(50), server_default="info", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_workspace", "notifications", ["workspace_id"])
    op.create_index("idx_notifications_read", "notifications", ["is_read"])

    # ── audit_logs ─────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("workspace_id", UUID(), nullable=False),
        sa.Column("user_id", UUID(), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", UUID(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_workspace", "audit_logs", ["workspace_id"])
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("idx_audit_user", table_name="audit_logs")
    op.drop_index("idx_audit_workspace", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("idx_notifications_read", table_name="notifications")
    op.drop_index("idx_notifications_workspace", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("idx_voice_conversation", table_name="voice_interactions")
    op.drop_table("voice_interactions")

    op.drop_index("idx_workflow_runs_workflow", table_name="workflow_runs")
    op.drop_table("workflow_runs")

    op.drop_index("idx_workflows_workspace", table_name="workflows")
    op.drop_table("workflows")

    op.drop_index("idx_dataset_queries_dataset", table_name="dataset_queries")
    op.drop_table("dataset_queries")

    op.drop_index("idx_datasets_workspace", table_name="datasets")
    op.drop_table("datasets")

    op.drop_index("idx_reports_workspace", table_name="analytics_reports")
    op.drop_table("analytics_reports")

    op.drop_index("idx_topics_name", table_name="topics")
    op.drop_table("topics")

    op.drop_index("idx_sentiments_label", table_name="sentiments")
    op.drop_table("sentiments")

    op.drop_index("idx_tickets_priority", table_name="tickets")
    op.drop_index("idx_tickets_status", table_name="tickets")
    op.drop_index("idx_tickets_workspace", table_name="tickets")
    op.drop_table("tickets")

    op.drop_index("idx_chunks_document", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("idx_documents_status", table_name="documents")
    op.drop_index("idx_documents_workspace", table_name="documents")
    op.drop_table("documents")

    op.drop_index("idx_handoffs_conversation", table_name="handoffs")
    op.drop_table("handoffs")

    op.drop_index("idx_messages_created", table_name="messages")
    op.drop_index("idx_messages_conversation", table_name="messages")
    op.drop_table("messages")

    op.drop_index("idx_conversations_channel", table_name="conversations")
    op.drop_index("idx_conversations_customer", table_name="conversations")
    op.drop_index("idx_conversations_workspace", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("idx_customers_telegram", table_name="customers")
    op.drop_index("idx_customers_email", table_name="customers")
    op.drop_index("idx_customers_workspace", table_name="customers")
    op.drop_table("customers")

    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
