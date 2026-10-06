"""The plan Lekha writes before a build, for the founder to read and approve (`blueprints`).

Revision ID: 0013_blueprints
Revises: 0012_model_settings
Create Date: 2026-10-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0013_blueprints"
down_revision: str | Sequence[str] | None = "0012_model_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blueprints",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("brief", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("docs", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("comments", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("progress", sa.String(200), nullable=False, server_default=""),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("run_id", sa.String(32), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_blueprints_company_id", "blueprints", ["company_id"])
    op.create_index("ix_blueprints_status", "blueprints", ["status"])
    op.create_index("ix_blueprints_run_id", "blueprints", ["run_id"])


def downgrade() -> None:
    op.drop_table("blueprints")
