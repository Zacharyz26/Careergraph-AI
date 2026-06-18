from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.common import ProcessingStatus
from app.schemas.resume import (
    ResumeProfileParseRequest,
    ResumeProfileParseResponse,
    ResumeRead,
    ResumeUploadResponse,
)
from app.services.document_parser import DocumentParser, DocumentParserError
from app.services.llm_service import LLMResponseError, LLMServiceError, MissingAPIKeyError
from app.services.resume_profile_service import ResumeProfileService
from app.utils.file_utils import safe_filename

router = APIRouter()
document_parser = DocumentParser()
resume_profile_service = ResumeProfileService()


def profile_analysis_error_detail(preferred_language: str, error: Exception) -> str:
    message = str(error)
    if "taking longer" in message.casefold() or "timed out" in message.casefold():
        if preferred_language == "zh":
            return "分析时间较长，请稍后重试。"
        return "The analysis is taking longer than expected. Please try again."
    if preferred_language == "zh":
        return "分析未能完成，请稍后重试。"
    return "The analysis could not be completed. Please try again."


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    response_model_exclude_none=True,
)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    filename = safe_filename(file.filename or "")
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    try:
        content = await file.read()
        parsed = document_parser.parse(filename=filename, content=content)
    except DocumentParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    return ResumeUploadResponse(
        filename=filename,
        file_type=parsed.file_type,
        extracted_text=parsed.extracted_text,
        character_count=len(parsed.extracted_text),
        page_count=parsed.page_count,
    )


@router.post("/parse-profile", response_model=ResumeProfileParseResponse)
async def parse_candidate_profile(
    payload: ResumeProfileParseRequest,
) -> ResumeProfileParseResponse:
    try:
        profile = await resume_profile_service.build_profile(
            payload.extracted_text,
            preferred_language=payload.preferred_language,
        )
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=profile_analysis_error_detail(payload.preferred_language, exc),
        ) from exc
    except LLMResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=profile_analysis_error_detail(payload.preferred_language, exc),
        ) from exc
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=profile_analysis_error_detail(payload.preferred_language, exc),
        ) from exc

    return ResumeProfileParseResponse.model_validate(profile)


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(resume_id: UUID) -> ResumeRead:
    # TODO: Load the authenticated user's resume through ResumeRepository.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Resume lookup is not implemented for {resume_id}.",
    )


@router.get("/{resume_id}/status", response_model=ProcessingStatus)
async def get_resume_status(resume_id: UUID) -> ProcessingStatus:
    # TODO: Read asynchronous parser status from the job store.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Resume processing status is not implemented for {resume_id}.",
    )
