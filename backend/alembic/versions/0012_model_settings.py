"""Each founder's models and own API keys (`model_settings`).

Revision ID: 0012_model_settings
Revises: 0011_notification_settings
Create Date: 2026-10-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0012_model_settings"
down_revision: str | Sequence[str] | None = "0011_notification_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_settings",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("mode", sa.String(20), nullable=False, server_default="managed"),
        sa.Column("default_model", sa.String(200), nullable=False, server_default=""),
        sa.Column(
            "role_models", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column("local_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("keys", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("model_settings")
