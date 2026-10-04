"""Where a released run's app is live (`runs.deployment`).

Revision ID: 0007_run_deployment
Revises: 0006_projects_backlog
Create Date: 2026-10-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_run_deployment"
down_revision: str | Sequence[str] | None = "0006_projects_backlog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("deployment", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "deployment")
