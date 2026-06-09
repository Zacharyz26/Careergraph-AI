from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Suggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "suggestions"

    resume_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), index=True)
    job_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("jobs.id"), index=True)
    original_text: Mapped[str] = mapped_column(Text)
    suggested_text: Mapped[str] = mapped_column(Text)
    source_fact_ids: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    reason: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(30), default="low")
    requires_user_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(40), default="pending_review", index=True)
