"""Public share links for finished builds (`run_shares`).

Revision ID: 0016_run_shares
Revises: 0015_autonomy_settings
Create Date: 2026-10-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016_run_shares"
down_revision: str | Sequence[str] | None = "0015_autonomy_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "run_shares",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(32), nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_run_shares_run_id", "run_shares", ["run_id"])
    op.create_index("ix_run_shares_company_id", "run_shares", ["company_id"])


def downgrade() -> None:
    op.drop_table("run_shares")
