"""How much the team does on its own, per company and per project (`autonomy_settings`).

Revision ID: 0015_autonomy_settings
Revises: 0014_run_artifacts
Create Date: 2026-10-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015_autonomy_settings"
down_revision: str | Sequence[str] | None = "0014_run_artifacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "autonomy_settings",
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("project_id", sa.String(32), primary_key=True, server_default=""),
        sa.Column("settings", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("autonomy_settings")
