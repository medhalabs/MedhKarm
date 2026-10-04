"""Projects and their backlog (`projects`, `backlog_items`).

Revision ID: 0006_projects_backlog
Revises: 0005_run_new_repo
Create Date: 2026-10-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_projects_backlog"
down_revision: str | Sequence[str] | None = "0005_run_new_repo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("repo", postgresql.JSONB(), nullable=True),
        sa.Column("repo_owned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("test_command", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("autopilot", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("daily_limit", sa.Integer(), server_default="2", nullable=False),
        sa.Column("questions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("error", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "backlog_items",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(40),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("acceptance", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("size", sa.String(2), server_default="M", nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("run_id", sa.String(100), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("note", sa.Text(), server_default="", nullable=False),
        sa.Column("pull_request_url", sa.Text(), server_default="", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("done_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_backlog_items_project_position", "backlog_items", ["project_id", "position"]
    )
    op.create_index("ix_backlog_items_run_id", "backlog_items", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_backlog_items_run_id", table_name="backlog_items")
    op.drop_index("ix_backlog_items_project_position", table_name="backlog_items")
    op.drop_table("backlog_items")
    op.drop_table("projects")
