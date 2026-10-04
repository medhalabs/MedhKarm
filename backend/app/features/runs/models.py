"""The `runs` table: one row per build run (migration 0003). Detail lives in the event log
and the LangGraph checkpoint; this row is the run's current status for lists and approvals."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    request: Mapped[str] = mapped_column(Text, nullable=False)
    test_command: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    repo: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_repo: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    gate: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    delivery: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    deployment: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_runs_created_at", "created_at"),)
