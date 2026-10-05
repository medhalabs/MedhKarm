"""The CEO inbox: messages between the founder and the team; answers to the PM's questions.

Revision ID: 0010_messages
Revises: 0009_companies_users
Create Date: 2026-10-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010_messages"
down_revision: str | Sequence[str] | None = "0009_companies_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("thread", sa.String(20), nullable=False),
        sa.Column("thread_id", sa.String(100), nullable=False),
        sa.Column("author", sa.String(30), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("to", sa.String(30), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_messages_thread", "messages", ["thread", "thread_id", "id"])
    op.create_index("ix_messages_company", "messages", ["company_id", "id"])
    op.add_column(
        "projects",
        sa.Column("answers", postgresql.JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("projects", "answers")
    op.drop_index("ix_messages_company", table_name="messages")
    op.drop_index("ix_messages_thread", table_name="messages")
    op.drop_table("messages")
