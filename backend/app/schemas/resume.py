from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import APIModel, ProcessingState
from app.schemas.candidate import CandidateProfile


class ResumeRead(APIModel):
    id: UUID
    user_id: UUID
    filename: str
    content_type: str
    processing_state: ProcessingState
    created_at: datetime


class ResumeBlock(APIModel):
    section_type: str
    text: str
    page: int | None = Field(default=None, ge=1)
    order_index: int = Field(ge=0)
    layout_meta: dict[str, object] = Field(default_factory=dict)


class VerifiedFact(APIModel):
    fact_id: str
    fact_type: str
    section: str
    text: str
    source_block_id: UUID | None = None
    verified_by_user: bool = False
    confidence: float = Field(ge=0, le=1)


class ResumeUploadResponse(APIModel):
    filename: str
    file_type: Literal["pdf", "docx"]
    extracted_text: str = Field(min_length=1)
    character_count: int = Field(ge=1)
    page_count: int | None = Field(default=None, ge=1)


class ResumeProfileParseRequest(APIModel):
    extracted_text: str = Field(min_length=1, max_length=100_000)

    @field_validator("extracted_text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("extracted_text must contain non-whitespace characters")
        return stripped


class ResumeProfileParseResponse(CandidateProfile):
    pass
