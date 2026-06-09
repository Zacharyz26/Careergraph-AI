from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="pasted")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_description: Mapped[str] = mapped_column(Text)
    parsed_job_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    processing_state: Mapped[str] = mapped_column(String(30), default="pending", index=True)
