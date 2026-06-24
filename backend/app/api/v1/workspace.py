from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import WorkspaceUser, current_workspace_user
from app.schemas.workspace import (
    AnalysisHistoryResponse,
    StoredAnalysisDetail,
    StoredSuggestionReview,
    SuggestionReviewUpdateRequest,
)
from app.services.workspace_store import (
    WorkspaceRecordNotFoundError,
    WorkspaceStore,
)

router = APIRouter()
workspace_store = WorkspaceStore()


@router.get("/analyses", response_model=AnalysisHistoryResponse)
async def list_analyses(
    current_user: WorkspaceUser = Depends(current_workspace_user),
) -> AnalysisHistoryResponse:
    return await workspace_store.list_analyses(current_user)


@router.get("/analyses/{analysis_id}", response_model=StoredAnalysisDetail)
async def get_analysis(
    analysis_id: UUID,
    current_user: WorkspaceUser = Depends(current_workspace_user),
) -> StoredAnalysisDetail:
    try:
        return await workspace_store.get_analysis(analysis_id, current_user)
    except WorkspaceRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis was not found.",
        ) from exc


@router.patch(
    "/analyses/{analysis_id}/suggestions/{review_id}",
    response_model=StoredSuggestionReview,
)
async def update_suggestion_review(
    analysis_id: UUID,
    review_id: str,
    payload: SuggestionReviewUpdateRequest,
    current_user: WorkspaceUser = Depends(current_workspace_user),
) -> StoredSuggestionReview:
    try:
        return await workspace_store.update_suggestion_review(
            analysis_id,
            review_id,
            payload,
            current_user,
        )
    except WorkspaceRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion review item was not found.",
        ) from exc
