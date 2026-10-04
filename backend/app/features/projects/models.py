"""The `projects` and `backlog_items` tables (migration 0006)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    repo: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    repo_owned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    test_command: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    autopilot: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")
    questions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    error: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BacklogItemRow(Base):
    __tablename__ = "backlog_items"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    acceptance: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    size: Mapped[str] = mapped_column(String(2), nullable=False, server_default="M")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    pull_request_url: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_backlog_items_project_position", "project_id", "position"),
        Index("ix_backlog_items_run_id", "run_id"),
    )
