from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.candidate import CandidateProfile
from app.schemas.career_direction import (
    CareerDirectionRecommendation,
    CareerDirectionResponse,
)
from app.schemas.common import APIModel, PreferredLanguage
from app.schemas.suggestion import SuggestionResponse


class AnalysisJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AnalysisStepKey(StrEnum):
    PROFILE_PARSING = "profile_parsing"
    CAREER_DIRECTIONS = "career_directions"
    ADVISOR_SUGGESTIONS = "advisor_suggestions"
    JOB_MATCHING = "job_matching"


class AnalysisStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class AnalysisStepState(APIModel):
    key: AnalysisStepKey
    label: str
    status: AnalysisStepStatus = AnalysisStepStatus.PENDING
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AnalysisJobCreateRequest(APIModel):
    extracted_text: str = Field(min_length=1, max_length=100_000)
    preferred_language: PreferredLanguage = "en"

    @field_validator("extracted_text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("extracted_text must contain non-whitespace characters")
        return stripped


class AnalysisJobResponse(APIModel):
    job_id: UUID
    status: AnalysisJobStatus
    current_step: AnalysisStepKey | None = None
    steps: list[AnalysisStepState]
    preferred_language: PreferredLanguage
    error_message: str | None = None
    profile: CandidateProfile | None = None
    career_directions: CareerDirectionResponse | None = None
    selected_direction: CareerDirectionRecommendation | None = None
    suggestions: SuggestionResponse | None = None
    created_at: datetime
    updated_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
