from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.schemas.analysis_job import AnalysisJobResponse, AnalysisJobStatus
from app.schemas.common import APIModel, PreferredLanguage
from app.schemas.resume import ResumeUploadResponse


class SuggestionReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class StoredResume(APIModel):
    resume_id: UUID
    user_email: str | None = None
    filename: str
    file_type: str
    extracted_text: str
    character_count: int = Field(ge=1)
    page_count: int | None = None
    created_at: datetime
    updated_at: datetime

    def to_upload_response(self) -> ResumeUploadResponse:
        return ResumeUploadResponse(
            resume_id=self.resume_id,
            filename=self.filename,
            file_type=self.file_type,  # type: ignore[arg-type]
            extracted_text=self.extracted_text,
            character_count=self.character_count,
            page_count=self.page_count,
        )


class StoredSuggestionReview(APIModel):
    review_id: str
    section: str
    item_index: int = Field(ge=0)
    status: SuggestionReviewStatus = SuggestionReviewStatus.PENDING_REVIEW
    original_text: str | None = None
    edited_text: str | None = None
    note: str | None = None
    updated_at: datetime


class SuggestionReviewUpdateRequest(APIModel):
    status: SuggestionReviewStatus
    edited_text: str | None = None
    note: str | None = None


class StoredAnalysis(APIModel):
    analysis_id: UUID
    user_email: str | None = None
    resume_id: UUID | None = None
    filename: str | None = None
    preferred_language: PreferredLanguage = "en"
    status: AnalysisJobStatus
    analysis_job: AnalysisJobResponse
    suggestion_reviews: list[StoredSuggestionReview] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AnalysisHistoryItem(APIModel):
    analysis_id: UUID
    resume_id: UUID | None = None
    filename: str | None = None
    preferred_language: PreferredLanguage
    status: AnalysisJobStatus
    candidate_name: str | None = None
    top_direction: str | None = None
    suggestion_count: int = 0
    created_at: datetime
    updated_at: datetime


class AnalysisHistoryResponse(APIModel):
    analyses: list[AnalysisHistoryItem] = Field(default_factory=list)


class StoredAnalysisDetail(APIModel):
    analysis: StoredAnalysis
    resume: StoredResume | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
