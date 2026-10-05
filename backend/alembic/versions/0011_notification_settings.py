"""Where each founder's standup and weekly report go (`notification_settings`).

Revision ID: 0011_notification_settings
Revises: 0010_messages
Create Date: 2026-10-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011_notification_settings"
down_revision: str | Sequence[str] | None = "0010_messages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_settings",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("email", sa.String(254), nullable=False, server_default=""),
        sa.Column("whatsapp", sa.String(20), nullable=False, server_default=""),
        sa.Column("standup_on", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("standup_hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("weekly_on", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
