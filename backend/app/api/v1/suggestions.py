from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.suggestion import (
    SuggestionActionRequest,
    SuggestionGenerateRequest,
    SuggestionRead,
)

router = APIRouter()


@router.post("/generate", response_model=list[SuggestionRead], status_code=status.HTTP_202_ACCEPTED)
async def generate_suggestions(payload: SuggestionGenerateRequest) -> list[SuggestionRead]:
    # TODO: Generate only suggestions grounded in verified source facts.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Suggestion generation is not implemented for match {payload.match_id}.",
    )


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
