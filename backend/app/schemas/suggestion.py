from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.candidate import CandidateProfile
from app.schemas.career_direction import CareerDirectionRecommendation
from app.schemas.common import APIModel
from app.schemas.job import JobProfile
from app.schemas.match import MatchResult


class SuggestionStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"
    REGENERATE_REQUESTED = "regenerate_requested"
    INCLUDED_IN_VERSION = "included_in_version"


class SuggestionAction(StrEnum):
    ACCEPT = "accept"
    EDIT = "edit"
    REJECT = "reject"
    REGENERATE = "regenerate"


SuggestionMode = Literal["career_direction", "job_specific", "general"]
SuggestionType = Literal[
    "bullet_rewrite",
    "section_reorder",
    "skill_grouping",
    "project_emphasis",
    "experience_emphasis",
    "headline_summary",
    "gap_disclosure",
    "evidence_strengthening",
]
SuggestionRisk = Literal["low", "medium", "high"]


class SuggestionGenerateRequest(APIModel):
    candidate_profile: CandidateProfile
    target_direction: str | None = None
    career_direction_result: CareerDirectionRecommendation | None = None
    job_profile: JobProfile | None = None
    match_result: MatchResult | None = None
    suggestion_mode: SuggestionMode = "general"

    @model_validator(mode="after")
    def validate_mode_context(self) -> "SuggestionGenerateRequest":
        if self.suggestion_mode == "general":
            if self.job_profile and self.match_result:
                self.suggestion_mode = "job_specific"
            elif self.target_direction or self.career_direction_result:
                self.suggestion_mode = "career_direction"
        if self.suggestion_mode == "career_direction" and not (
            self.target_direction or self.career_direction_result
        ):
            raise ValueError(
                "career_direction mode requires target_direction or "
                "career_direction_result"
            )
        if self.suggestion_mode == "job_specific" and not (
            self.job_profile and self.match_result
        ):
            raise ValueError(
                "job_specific mode requires job_profile and match_result"
            )
        return self


class SuggestionItem(APIModel):
    suggestion_type: SuggestionType
    target_section: str
    original_text: str | None = None
    suggested_text: str
    reason: str
    source_evidence_ids: list[str] = Field(default_factory=list)
    source_evidence_text: list[str] = Field(default_factory=list)
    related_requirement_or_direction: str | None = None
    risk_level: SuggestionRisk
    requires_user_review: Literal[True] = True
    should_add_to_resume: bool


class SuggestionResponse(APIModel):
    overall_summary: str
    suggestions: list[SuggestionItem] = Field(default_factory=list)
    missing_but_not_addable: list[str] = Field(default_factory=list)
    suggested_resume_focus: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SuggestionActionRequest(APIModel):
    action: SuggestionAction
    edited_text: str | None = None

    @model_validator(mode="after")
    def require_text_for_edit(self) -> "SuggestionActionRequest":
        if self.action == SuggestionAction.EDIT and not self.edited_text:
            raise ValueError("edited_text is required when action is edit")
        return self


class SuggestionRead(APIModel):
    id: UUID
    resume_id: UUID
    job_id: UUID
    original_text: str
    suggested_text: str
    source_fact_ids: list[str] = Field(min_length=1)
    reason: str
    risk_level: str
    requires_user_confirmation: bool
    status: SuggestionStatus
    created_at: datetime
