"""The `model_settings` table (migration 0012): one row per company."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class ModelSettingsRow(Base):
    __tablename__ = "model_settings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False, server_default="managed")
    default_model: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
    role_models: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    local_url: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    # provider -> {"sealed": Fernet token, "hint": "…a1b2"}; the plain key is never stored
    keys: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
