"""The `notification_settings` table (migration 0011): one row per company."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base


class NotificationSettingsRow(Base):
    __tablename__ = "notification_settings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False, server_default="")
    whatsapp: Mapped[str] = mapped_column(String(20), nullable=False, server_default="")
    standup_on: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    standup_hour: Mapped[int] = mapped_column(Integer, nullable=False, server_default="9")
    weekly_on: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    nudge_on: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
