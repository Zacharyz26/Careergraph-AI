from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import APIModel


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


class SuggestionGenerateRequest(APIModel):
    match_id: UUID


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
