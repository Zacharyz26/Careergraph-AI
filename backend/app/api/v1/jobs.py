from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.job import JobCreate, JobParseRequest, JobProfile, JobRead
from app.services.job_parser_service import JobParserService
from app.services.llm_service import LLMResponseError, LLMServiceError, MissingAPIKeyError

router = APIRouter()
job_parser_service = JobParserService()


@router.post("/parse", response_model=JobProfile)
async def parse_job_description(payload: JobParseRequest) -> JobProfile:
    try:
        return await job_parser_service.parse(payload.raw_job_description)
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except LLMResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_job(payload: JobCreate) -> JobRead:
    # TODO: Parse and persist pasted job descriptions.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Job parsing is not implemented for '{payload.title or 'untitled job'}'.",
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: UUID) -> JobRead:
    # TODO: Load the authenticated user's job through JobRepository.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Job lookup is not implemented for {job_id}.",
    )
