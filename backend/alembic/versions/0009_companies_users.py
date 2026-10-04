"""Sign-in: companies and users; runs and projects belong to a company.

Revision ID: 0009_companies_users
Revises: 0008_run_stack
Create Date: 2026-10-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_companies_users"
down_revision: str | Sequence[str] | None = "0008_run_stack"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False, server_default=""),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])
    for table in ("runs", "projects"):
        op.create_foreign_key(
            f"fk_{table}_company", table, "companies", ["company_id"], ["id"], ondelete="CASCADE"
        )
        op.create_index(f"ix_{table}_company_id", table, ["company_id"])


def downgrade() -> None:
    for table in ("runs", "projects"):
        op.drop_index(f"ix_{table}_company_id", table_name=table)
        op.drop_constraint(f"fk_{table}_company", table, type_="foreignkey")
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_table("users")
    op.drop_table("companies")
