"""pgvector extension and the append-only events table.

Revision ID: 0001_events
Revises:
Create Date: 2026-10-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_events"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Embeddings for project memory later; created here so every database has it.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_id", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(40), nullable=False),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_events_run_id_id", "events", ["run_id", "id"])

    # Append-only, enforced by the database: an audit trail nobody can quietly rewrite.
    op.execute(
        """
        CREATE FUNCTION events_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'events are append-only: % is not allowed', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER events_no_update_or_delete
        BEFORE UPDATE OR DELETE ON events
        FOR EACH ROW EXECUTE FUNCTION events_append_only();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS events_no_update_or_delete ON events")
    op.execute("DROP FUNCTION IF EXISTS events_append_only()")
    op.drop_index("ix_events_run_id_id", table_name="events")
    op.drop_table("events")
