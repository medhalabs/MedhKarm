"""Priya's nudges can be switched off per company (`notification_settings.nudge_on`).

Revision ID: 0018_nudge_setting
Revises: 0017_waitlist
Create Date: 2026-10-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_nudge_setting"
down_revision: str | Sequence[str] | None = "0017_waitlist"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notification_settings",
        sa.Column("nudge_on", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("notification_settings", "nudge_on")
