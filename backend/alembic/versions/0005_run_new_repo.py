"""Runs on new projects can create a GitHub repository on release (`new_repo`).

Revision ID: 0005_run_new_repo
Revises: 0004_run_repos
Create Date: 2026-10-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_run_new_repo"
down_revision: str | Sequence[str] | None = "0004_run_repos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("new_repo", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "new_repo")
