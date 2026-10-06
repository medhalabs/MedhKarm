"""The `blueprints` table (migration 0013)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class BlueprintRow(Base):
    __tablename__ = "blueprints"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    brief: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    docs: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    comments: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    progress: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
    error: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    run_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
