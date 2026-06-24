from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    file_url: Mapped[str] = mapped_column(Text, default="")
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    processing_state: Mapped[str] = mapped_column(String(30), default="pending", index=True)


class ResumeBlock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_blocks"

    resume_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), index=True)
    section_type: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)
    layout_meta: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    resume_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), unique=True)
    profile_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    confidence_json: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)


class VerifiedFact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "verified_facts"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    resume_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resumes.id"), index=True)
    source_block_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resume_blocks.id"),
        nullable=True,
    )
    fact_type: Mapped[str] = mapped_column(String(100))
    section: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    verified_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float)


class ResumeVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_versions"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    base_resume_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resumes.id"))
    version_name: Mapped[str] = mapped_column(String(200))
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content_json: Mapped[dict[str, object]] = mapped_column(JSONB)
    change_log_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
