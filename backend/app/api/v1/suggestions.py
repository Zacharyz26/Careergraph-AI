from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.suggestion import (
    SuggestionActionRequest,
    SuggestionGenerateRequest,
    SuggestionRead,
    SuggestionResponse,
)
from app.services.suggestion_service import SuggestionService

router = APIRouter()
suggestion_service = SuggestionService()


@router.post("/generate", response_model=SuggestionResponse)
async def generate_suggestions(
    payload: SuggestionGenerateRequest,
) -> SuggestionResponse:
    return await suggestion_service.generate(payload)


@router.patch("/{suggestion_id}", response_model=SuggestionRead)
async def review_suggestion(
    suggestion_id: UUID,
    payload: SuggestionActionRequest,
) -> SuggestionRead:
    # TODO: Apply the human review state machine and record the reviewer action.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Suggestion review is not implemented for {suggestion_id} ({payload.action}).",
    )
