from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resumes.id"),
        nullable=True,
        index=True,
    )
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[str] = mapped_column(String(40), index=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    candidate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    top_direction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_job_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    career_directions_json: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    suggestions_json: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
