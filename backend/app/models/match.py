from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matches"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    resume_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), index=True)
    job_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("jobs.id"), index=True)
    state: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    component_scores_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
