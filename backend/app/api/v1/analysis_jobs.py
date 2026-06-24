from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import WorkspaceUser, current_workspace_user
from app.schemas.analysis_job import AnalysisJobCreateRequest, AnalysisJobResponse
from app.services.analysis_job_service import (
    AnalysisJobNotFoundError,
    AnalysisJobService,
)

router = APIRouter()
analysis_job_service = AnalysisJobService()


@router.post("", response_model=AnalysisJobResponse)
async def create_analysis_job(
    payload: AnalysisJobCreateRequest,
    current_user: WorkspaceUser = Depends(current_workspace_user),
) -> AnalysisJobResponse:
    return await analysis_job_service.create_job(payload, current_user)


@router.get("/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(
    job_id: UUID,
    current_user: WorkspaceUser = Depends(current_workspace_user),
) -> AnalysisJobResponse:
    try:
        return await analysis_job_service.get_job(job_id, current_user)
    except AnalysisJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job was not found.",
        ) from exc


@router.post("/{job_id}/retry", response_model=AnalysisJobResponse)
async def retry_analysis_job(
    job_id: UUID,
    current_user: WorkspaceUser = Depends(current_workspace_user),
) -> AnalysisJobResponse:
    try:
        return await analysis_job_service.retry_job(job_id, current_user)
    except AnalysisJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job was not found.",
        ) from exc
