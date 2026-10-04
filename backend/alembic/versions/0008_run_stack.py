"""The founder's stack choices for a new project (`runs.stack`, `projects.stack`).

Revision ID: 0008_run_stack
Revises: 0007_run_deployment
Create Date: 2026-10-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008_run_stack"
down_revision: str | Sequence[str] | None = "0007_run_deployment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("stack", postgresql.JSONB(), nullable=True))
    op.add_column("projects", sa.Column("stack", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "stack")
    op.drop_column("runs", "stack")
