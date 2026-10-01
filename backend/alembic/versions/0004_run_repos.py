"""Runs on founders' repositories: the repository (`repo`) and the pull request (`delivery`).

Revision ID: 0004_run_repos
Revises: 0003_jobs_and_runs
Create Date: 2026-10-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_run_repos"
down_revision: str | Sequence[str] | None = "0003_jobs_and_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("repo", postgresql.JSONB(), nullable=True))
    op.add_column("runs", sa.Column("delivery", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "delivery")
    op.drop_column("runs", "repo")
