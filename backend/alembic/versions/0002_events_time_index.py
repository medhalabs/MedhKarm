"""Index events by time, for the daily standup (which runs were active in a window).

Revision ID: 0002_events_time_index
Revises: 0001_events
Create Date: 2026-10-01

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_events_time_index"
down_revision: str | Sequence[str] | None = "0001_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_events_occurred_at", table_name="events")
