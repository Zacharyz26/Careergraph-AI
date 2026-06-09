from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.match import MatchCreate, MatchRead, MatchResult, MatchScoreRequest
from app.services.matching_service import MatchingService

router = APIRouter()
matching_service = MatchingService()


@router.post("/score", response_model=MatchResult)
async def score_match(payload: MatchScoreRequest) -> MatchResult:
    return await matching_service.score(
        payload.candidate_profile,
        payload.job_profile,
    )


@router.post("", response_model=MatchRead, status_code=status.HTTP_202_ACCEPTED)
async def create_match(payload: MatchCreate) -> MatchRead:
    # TODO: Enqueue the deterministic and semantic match-scoring pipeline.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Matching is not implemented for resume {payload.resume_id} and job {payload.job_id}.",
    )


@router.get("/{match_id}", response_model=MatchRead)
async def get_match(match_id: UUID) -> MatchRead:
    # TODO: Load a persisted match result with evidence.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Match lookup is not implemented for {match_id}.",
    )
