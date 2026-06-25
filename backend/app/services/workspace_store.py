from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from uuid import UUID
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import BACKEND_DIR, settings
from app.core.security import WorkspaceUser
from app.db.session import AsyncSessionFactory
from app.models.analysis import Analysis
from app.models.resume import CandidateProfile as CandidateProfileModel
from app.models.resume import Resume
from app.models.suggestion import Suggestion
from app.models.user import User
from app.schemas.analysis_job import AnalysisJobCreateRequest, AnalysisJobResponse
from app.schemas.resume import ResumeUploadResponse
from app.schemas.workspace import (
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    StoredAnalysis,
    StoredAnalysisDetail,
    StoredResume,
    StoredSuggestionReview,
    SuggestionReviewStatus,
    SuggestionReviewUpdateRequest,
    utc_now,
)

logger = logging.getLogger(__name__)


class WorkspaceRecordNotFoundError(KeyError):
    pass


def default_workspace_user() -> WorkspaceUser:
    return WorkspaceUser(
        email=settings.workspace_default_user_email,
        name="CareerGraph Workspace",
        auth_provider="local",
    )


def owner_key(user: WorkspaceUser | None) -> str:
    return (user or default_workspace_user()).email.casefold()


def record_belongs_to_user(
    record: dict[str, object],
    user: WorkspaceUser | None,
) -> bool:
    user_email = owner_key(user)
    record_email = record.get("user_email")
    if isinstance(record_email, str):
        return record_email.casefold() == user_email
    return user_email == settings.workspace_default_user_email.casefold()


def build_initial_suggestion_reviews(
    response: AnalysisJobResponse,
) -> list[StoredSuggestionReview]:
    if not response.suggestions:
        return []
    now = utc_now()
    sections = [
        ("resume_ready_improvements", response.suggestions.resume_ready_improvements),
        ("positioning_advice", response.suggestions.positioning_advice),
        ("evidence_gaps", response.suggestions.evidence_gaps),
        ("recommended_next_actions", response.suggestions.recommended_next_actions),
    ]
    reviews: list[StoredSuggestionReview] = []
    for section, items in sections:
        for index, item in enumerate(items):
            original_text = (
                getattr(item, "suggested_text", None)
                or getattr(item, "advice", None)
                or getattr(item, "gap", None)
                or getattr(item, "action", None)
            )
            reviews.append(
                StoredSuggestionReview(
                    review_id=f"{section}:{index}",
                    section=section,
                    item_index=index,
                    original_text=original_text,
                    updated_at=now,
                )
            )
    return reviews


class JsonWorkspaceStore:
    def __init__(self, path: Path | None = None) -> None:
        store_path = path or settings.workspace_fallback_store_path
        self.path = store_path if store_path.is_absolute() else BACKEND_DIR / store_path
        self._lock = threading.Lock()

    async def save_uploaded_resume(
        self,
        upload: ResumeUploadResponse,
        user: WorkspaceUser | None = None,
    ) -> StoredResume:
        now = utc_now()
        resume_id = upload.resume_id or uuid4()
        record = StoredResume(
            resume_id=resume_id,
            user_email=owner_key(user),
            filename=upload.filename,
            file_type=upload.file_type,
            extracted_text=upload.extracted_text,
            character_count=upload.character_count,
            page_count=upload.page_count,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            data = self._read()
            data["resumes"][str(resume_id)] = record.model_dump(mode="json")
            self._write(data)
        return record

    async def get_resume(self, resume_id: UUID) -> StoredResume:
        return await self.get_resume_for_user(resume_id, None)

    async def get_resume_for_user(
        self,
        resume_id: UUID,
        user: WorkspaceUser | None = None,
    ) -> StoredResume:
        with self._lock:
            raw_resume = self._read()["resumes"].get(str(resume_id))
        if not raw_resume or not record_belongs_to_user(raw_resume, user):
            raise WorkspaceRecordNotFoundError(str(resume_id))
        return StoredResume.model_validate(raw_resume)

    async def save_analysis(
        self,
        response: AnalysisJobResponse,
        request: AnalysisJobCreateRequest,
        user: WorkspaceUser | None = None,
    ) -> StoredAnalysis:
        now = utc_now()
        user_email = owner_key(user)
        with self._lock:
            data = self._read()
            raw_resume = (
                data["resumes"].get(str(request.resume_id))
                if request.resume_id
                else None
            )
            if raw_resume and not record_belongs_to_user(raw_resume, user):
                raise WorkspaceRecordNotFoundError(str(request.resume_id))
            resume = StoredResume.model_validate(raw_resume) if raw_resume else None
            existing = data["analyses"].get(str(response.job_id))
            if existing and not record_belongs_to_user(existing, user):
                raise WorkspaceRecordNotFoundError(str(response.job_id))
            created_at = existing.get("created_at") if existing else now
            reviews = (
                existing.get("suggestion_reviews", [])
                if existing
                else build_initial_suggestion_reviews(response)
            )
            if not reviews and response.suggestions:
                reviews = build_initial_suggestion_reviews(response)
            record = StoredAnalysis(
                analysis_id=response.job_id,
                user_email=user_email,
                resume_id=request.resume_id,
                filename=resume.filename if resume else None,
                preferred_language=response.preferred_language,
                status=response.status,
                analysis_job=response,
                suggestion_reviews=reviews,
                created_at=created_at,
                updated_at=now,
            )
            data["analyses"][str(response.job_id)] = record.model_dump(mode="json")
            self._write(data)
        return record

    async def list_analyses(
        self,
        user: WorkspaceUser | None = None,
    ) -> AnalysisHistoryResponse:
        user_email = owner_key(user)
        with self._lock:
            records = [
                record
                for record in self._read()["analyses"].values()
                if record_belongs_to_user(record, user)
            ]
        analyses = [
            StoredAnalysis.model_validate(record)
            for record in records
        ]
        analyses.sort(key=lambda item: item.updated_at, reverse=True)
        return AnalysisHistoryResponse(
            analyses=[
                AnalysisHistoryItem(
                    analysis_id=analysis.analysis_id,
                    resume_id=analysis.resume_id,
                    filename=analysis.filename,
                    preferred_language=analysis.preferred_language,
                    status=analysis.status,
                    candidate_name=analysis.analysis_job.profile.basic_info.full_name
                    if analysis.analysis_job.profile
                    else None,
                    top_direction=analysis.analysis_job.career_directions.directions[0].direction
                    if analysis.analysis_job.career_directions
                    and analysis.analysis_job.career_directions.directions
                    else None,
                    suggestion_count=len(analysis.suggestion_reviews),
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at,
                )
                for analysis in analyses
            ]
        )

    async def get_analysis(
        self,
        analysis_id: UUID,
        user: WorkspaceUser | None = None,
    ) -> StoredAnalysisDetail:
        user_email = owner_key(user)
        with self._lock:
            data = self._read()
            raw_analysis = data["analyses"].get(str(analysis_id))
            if not raw_analysis or not record_belongs_to_user(raw_analysis, user):
                raise WorkspaceRecordNotFoundError(str(analysis_id))
            analysis = StoredAnalysis.model_validate(raw_analysis)
            raw_resume = (
                data["resumes"].get(str(analysis.resume_id))
                if analysis.resume_id
                else None
            )
        if raw_resume and not record_belongs_to_user(raw_resume, user):
            raise WorkspaceRecordNotFoundError(str(analysis.resume_id))
        return StoredAnalysisDetail(
            analysis=analysis,
            resume=StoredResume.model_validate(raw_resume) if raw_resume else None,
        )

    async def update_suggestion_review(
        self,
        analysis_id: UUID,
        review_id: str,
        request: SuggestionReviewUpdateRequest,
        user: WorkspaceUser | None = None,
    ) -> StoredSuggestionReview:
        user_email = owner_key(user)
        with self._lock:
            data = self._read()
            raw_analysis = data["analyses"].get(str(analysis_id))
            if not raw_analysis or not record_belongs_to_user(raw_analysis, user):
                raise WorkspaceRecordNotFoundError(str(analysis_id))
            analysis = StoredAnalysis.model_validate(raw_analysis)
            review = self._review_by_id(analysis.suggestion_reviews, review_id)
            self._apply_review_update(review, request)
            analysis.updated_at = utc_now()
            data["analyses"][str(analysis_id)] = analysis.model_dump(mode="json")
            self._write(data)
            return review

    def _read(self) -> dict[str, dict[str, object]]:
        if not self.path.exists():
            return {"resumes": {}, "analyses": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.exception("Workspace fallback store is invalid JSON: path=%s", self.path)
            return {"resumes": {}, "analyses": {}}
        if not isinstance(data, dict):
            return {"resumes": {}, "analyses": {}}
        resumes = data.get("resumes")
        analyses = data.get("analyses")
        return {
            "resumes": resumes if isinstance(resumes, dict) else {},
            "analyses": analyses if isinstance(analyses, dict) else {},
        }

    def _write(self, data: dict[str, dict[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _review_by_id(
        self,
        reviews: list[StoredSuggestionReview],
        review_id: str,
    ) -> StoredSuggestionReview:
        for review in reviews:
            if review.review_id == review_id:
                return review
        raise WorkspaceRecordNotFoundError(review_id)

    def _apply_review_update(
        self,
        review: StoredSuggestionReview,
        request: SuggestionReviewUpdateRequest,
    ) -> None:
        review.status = request.status
        review.note = request.note
        review.edited_text = (
            request.edited_text
            if request.status == SuggestionReviewStatus.EDITED
            else None
        )
        review.updated_at = utc_now()


class DatabaseWorkspaceStore:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.session_factory = session_factory or AsyncSessionFactory

    async def save_uploaded_resume(
        self,
        upload: ResumeUploadResponse,
        user: WorkspaceUser | None = None,
    ) -> StoredResume:
        async with self.session_factory() as session:
            db_user = await self._user_for_workspace(session, user)
            resume = Resume(
                user_id=db_user.id,
                filename=upload.filename,
                content_type=self._content_type(upload.file_type),
                file_url="",
                raw_text=upload.extracted_text,
                parser_version="document_parser:v1",
                processing_state="completed",
            )
            session.add(resume)
            await session.flush()
            await session.commit()
            await session.refresh(resume)
            return self._stored_resume(resume)

    async def get_resume(self, resume_id: UUID) -> StoredResume:
        return await self.get_resume_for_user(resume_id, None)

    async def get_resume_for_user(
        self,
        resume_id: UUID,
        user: WorkspaceUser | None = None,
    ) -> StoredResume:
        async with self.session_factory() as session:
            db_user = await self._user_for_workspace(session, user)
            resume = await self._resume_for_user(session, resume_id, db_user.id)
            if not resume:
                raise WorkspaceRecordNotFoundError(str(resume_id))
            return self._stored_resume(resume)

    async def save_analysis(
        self,
        response: AnalysisJobResponse,
        request: AnalysisJobCreateRequest,
        user: WorkspaceUser | None = None,
    ) -> StoredAnalysis:
        async with self.session_factory() as session:
            db_user = await self._user_for_workspace(session, user)
            resume = (
                await self._resume_for_user(session, request.resume_id, db_user.id)
                if request.resume_id
                else None
            )
            analysis = await session.get(Analysis, response.job_id)
            if analysis and analysis.user_id != db_user.id:
                raise WorkspaceRecordNotFoundError(str(response.job_id))
            profile = response.profile
            directions = response.career_directions
            suggestions = response.suggestions
            if analysis is None:
                analysis = Analysis(
                    id=response.job_id,
                    user_id=db_user.id,
                    resume_id=resume.id if resume else None,
                    status=response.status,
                    preferred_language=response.preferred_language,
                    filename=resume.filename if resume else None,
                    analysis_job_json=response.model_dump(mode="json"),
                )
                session.add(analysis)

            analysis.status = response.status
            analysis.preferred_language = response.preferred_language
            analysis.resume_id = resume.id if resume else analysis.resume_id
            analysis.filename = resume.filename if resume else analysis.filename
            analysis.candidate_name = (
                profile.basic_info.full_name if profile else analysis.candidate_name
            )
            analysis.top_direction = (
                directions.directions[0].direction
                if directions and directions.directions
                else analysis.top_direction
            )
            analysis.error_message = response.error_message
            analysis.analysis_job_json = response.model_dump(mode="json")
            analysis.career_directions_json = (
                directions.model_dump(mode="json") if directions else None
            )
            analysis.suggestions_json = (
                suggestions.model_dump(mode="json") if suggestions else None
            )

            if profile and resume:
                await self._upsert_candidate_profile(session, db_user.id, resume.id, profile)
            if suggestions:
                await self._replace_suggestions(
                    session,
                    db_user.id,
                    analysis.id,
                    resume.id if resume else None,
                    response,
                )

            await session.commit()
            return await self._stored_analysis(session, analysis.id, db_user.id)

    async def list_analyses(
        self,
        user: WorkspaceUser | None = None,
    ) -> AnalysisHistoryResponse:
        async with self.session_factory() as session:
            db_user = await self._user_for_workspace(session, user)
            result = await session.execute(
                select(Analysis)
                .where(Analysis.user_id == db_user.id)
                .order_by(Analysis.updated_at.desc())
            )
            analyses = result.scalars().all()
            items = [
                AnalysisHistoryItem(
                    analysis_id=analysis.id,
                    resume_id=analysis.resume_id,
                    filename=analysis.filename,
                    preferred_language=analysis.preferred_language,  # type: ignore[arg-type]
                    status=analysis.status,  # type: ignore[arg-type]
                    candidate_name=analysis.candidate_name,
                    top_direction=analysis.top_direction,
                    suggestion_count=await self._suggestion_count(session, analysis.id),
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at,
                )
                for analysis in analyses
            ]
            return AnalysisHistoryResponse(analyses=items)

    async def get_analysis(
        self,
        analysis_id: UUID,
        user: WorkspaceUser | None = None,
    ) -> StoredAnalysisDetail:
        async with self.session_factory() as session:
            db_user = await self._user_for_workspace(session, user)
            analysis = await self._analysis_for_user(session, analysis_id, db_user.id)
            if not analysis:
                raise WorkspaceRecordNotFoundError(str(analysis_id))
            stored_analysis = await self._stored_analysis(session, analysis.id, db_user.id)
            resume = (
                await self._resume_for_user(session, analysis.resume_id, db_user.id)
                if analysis.resume_id
                else None
            )
            return StoredAnalysisDetail(
                analysis=stored_analysis,
                resume=self._stored_resume(resume) if resume else None,
            )

    async def update_suggestion_review(
        self,
        analysis_id: UUID,
        review_id: str,
        request: SuggestionReviewUpdateRequest,
        user: WorkspaceUser | None = None,
    ) -> StoredSuggestionReview:
        section, item_index = self._parse_review_id(review_id)
        async with self.session_factory() as session:
            db_user = await self._user_for_workspace(session, user)
            analysis = await self._analysis_for_user(session, analysis_id, db_user.id)
            if not analysis:
                raise WorkspaceRecordNotFoundError(str(analysis_id))
            result = await session.execute(
                select(Suggestion).where(
                    Suggestion.analysis_id == analysis.id,
                    Suggestion.user_id == db_user.id,
                    Suggestion.section == section,
                    Suggestion.item_index == item_index,
                )
            )
            suggestion = result.scalar_one_or_none()
            if not suggestion:
                raise WorkspaceRecordNotFoundError(review_id)
            suggestion.status = request.status.value
            suggestion.edited_text = (
                request.edited_text
                if request.status == SuggestionReviewStatus.EDITED
                else None
            )
            await session.commit()
            await session.refresh(suggestion)
            return self._stored_suggestion_review(suggestion)

    async def _default_user(self, session: AsyncSession) -> User:
        return await self._user_for_workspace(session, None)

    async def _user_for_workspace(
        self,
        session: AsyncSession,
        workspace_user: WorkspaceUser | None,
    ) -> User:
        owner = workspace_user or default_workspace_user()
        result = await session.execute(
            select(User).where(User.email == owner.email)
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(
            email=owner.email,
            name=owner.name,
            auth_provider=owner.auth_provider,
        )
        session.add(user)
        await session.flush()
        return user

    async def _resume_for_user(
        self,
        session: AsyncSession,
        resume_id: UUID | None,
        user_id: UUID,
    ) -> Resume | None:
        if not resume_id:
            return None
        result = await session.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _analysis_for_user(
        self,
        session: AsyncSession,
        analysis_id: UUID,
        user_id: UUID,
    ) -> Analysis | None:
        result = await session.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _upsert_candidate_profile(
        self,
        session: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        profile,
    ) -> None:
        result = await session.execute(
            select(CandidateProfileModel).where(
                CandidateProfileModel.resume_id == resume_id,
                CandidateProfileModel.user_id == user_id,
            )
        )
        candidate_profile = result.scalar_one_or_none()
        if candidate_profile is None:
            candidate_profile = CandidateProfileModel(
                user_id=user_id,
                resume_id=resume_id,
                profile_json=profile.model_dump(mode="json"),
                confidence_json={},
            )
            session.add(candidate_profile)
        else:
            candidate_profile.profile_json = profile.model_dump(mode="json")

    async def _replace_suggestions(
        self,
        session: AsyncSession,
        user_id: UUID,
        analysis_id: UUID,
        resume_id: UUID | None,
        response: AnalysisJobResponse,
    ) -> None:
        await session.execute(delete(Suggestion).where(Suggestion.analysis_id == analysis_id))
        for review in build_initial_suggestion_reviews(response):
            item_json = {
                "review_id": review.review_id,
                "section": review.section,
                "item_index": review.item_index,
                "original_text": review.original_text,
            }
            session.add(
                Suggestion(
                    user_id=user_id,
                    analysis_id=analysis_id,
                    resume_id=resume_id,
                    job_id=None,
                    section=review.section,
                    item_index=review.item_index,
                    item_json=item_json,
                    original_text=review.original_text,
                    suggested_text=review.original_text,
                    edited_text=review.edited_text,
                    source_fact_ids=[],
                    reason=None,
                    risk_level="low",
                    requires_user_confirmation=True,
                    status=review.status,
                )
            )

    async def _stored_analysis(
        self,
        session: AsyncSession,
        analysis_id: UUID,
        user_id: UUID,
    ) -> StoredAnalysis:
        analysis = await self._analysis_for_user(session, analysis_id, user_id)
        if not analysis:
            raise WorkspaceRecordNotFoundError(str(analysis_id))
        response = AnalysisJobResponse.model_validate(analysis.analysis_job_json)
        reviews = await self._suggestion_reviews(session, analysis.id)
        return StoredAnalysis(
            analysis_id=analysis.id,
            user_email=None,
            resume_id=analysis.resume_id,
            filename=analysis.filename,
            preferred_language=analysis.preferred_language,  # type: ignore[arg-type]
            status=analysis.status,  # type: ignore[arg-type]
            analysis_job=response,
            suggestion_reviews=reviews,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )

    async def _suggestion_reviews(
        self,
        session: AsyncSession,
        analysis_id: UUID,
    ) -> list[StoredSuggestionReview]:
        result = await session.execute(
            select(Suggestion)
            .where(Suggestion.analysis_id == analysis_id)
            .order_by(Suggestion.section, Suggestion.item_index)
        )
        return [
            self._stored_suggestion_review(suggestion)
            for suggestion in result.scalars().all()
        ]

    async def _suggestion_count(
        self,
        session: AsyncSession,
        analysis_id: UUID,
    ) -> int:
        result = await session.execute(
            select(Suggestion).where(Suggestion.analysis_id == analysis_id)
        )
        return len(result.scalars().all())

    def _stored_resume(self, resume: Resume) -> StoredResume:
        file_type = "docx" if resume.filename.lower().endswith(".docx") else "pdf"
        return StoredResume(
            resume_id=resume.id,
            user_email=None,
            filename=resume.filename,
            file_type=file_type,
            extracted_text=resume.raw_text or "",
            character_count=len(resume.raw_text or ""),
            page_count=None,
            created_at=resume.created_at,
            updated_at=resume.updated_at,
        )

    def _content_type(self, file_type: str) -> str:
        if file_type == "pdf":
            return "application/pdf"
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def _stored_suggestion_review(
        self,
        suggestion: Suggestion,
    ) -> StoredSuggestionReview:
        return StoredSuggestionReview(
            review_id=f"{suggestion.section}:{suggestion.item_index}",
            section=suggestion.section,
            item_index=suggestion.item_index,
            status=suggestion.status,  # type: ignore[arg-type]
            original_text=suggestion.original_text,
            edited_text=suggestion.edited_text,
            note=getattr(suggestion, "note", None),
            updated_at=suggestion.updated_at,
        )

    def _parse_review_id(self, review_id: str) -> tuple[str, int]:
        try:
            section, raw_index = review_id.rsplit(":", 1)
            return section, int(raw_index)
        except ValueError as exc:
            raise WorkspaceRecordNotFoundError(review_id) from exc


class WorkspaceStore:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        fallback_store: JsonWorkspaceStore | None = None,
    ) -> None:
        self.primary = DatabaseWorkspaceStore(session_factory)
        self.fallback = fallback_store or JsonWorkspaceStore()
        self._primary_unavailable = False

    async def save_uploaded_resume(
        self,
        upload: ResumeUploadResponse,
        user: WorkspaceUser | None = None,
    ) -> StoredResume:
        if self._primary_unavailable:
            return await self.fallback.save_uploaded_resume(upload, user)
        try:
            return await self.primary.save_uploaded_resume(upload, user)
        except Exception as exc:
            return await self._fallback(
                exc,
                "save uploaded resume",
                self.fallback.save_uploaded_resume,
                upload,
                user,
            )

    async def get_resume(
        self,
        resume_id: UUID,
        user: WorkspaceUser | None = None,
    ) -> StoredResume:
        if self._primary_unavailable:
            return await self.fallback.get_resume_for_user(resume_id, user)
        try:
            return await self.primary.get_resume_for_user(resume_id, user)
        except WorkspaceRecordNotFoundError:
            raise
        except Exception as exc:
            return await self._fallback(
                exc,
                "get resume",
                self.fallback.get_resume_for_user,
                resume_id,
                user,
            )

    async def save_analysis(
        self,
        response: AnalysisJobResponse,
        request: AnalysisJobCreateRequest,
        user: WorkspaceUser | None = None,
    ) -> StoredAnalysis:
        if self._primary_unavailable:
            return await self.fallback.save_analysis(response, request, user)
        try:
            return await self.primary.save_analysis(response, request, user)
        except Exception as exc:
            return await self._fallback(
                exc,
                "save analysis",
                self.fallback.save_analysis,
                response,
                request,
                user,
            )

    async def list_analyses(
        self,
        user: WorkspaceUser | None = None,
    ) -> AnalysisHistoryResponse:
        if self._primary_unavailable:
            return await self.fallback.list_analyses(user)
        try:
            return await self.primary.list_analyses(user)
        except Exception as exc:
            return await self._fallback(
                exc,
                "list analyses",
                self.fallback.list_analyses,
                user,
            )

    async def get_analysis(
        self,
        analysis_id: UUID,
        user: WorkspaceUser | None = None,
    ) -> StoredAnalysisDetail:
        if self._primary_unavailable:
            return await self.fallback.get_analysis(analysis_id, user)
        try:
            return await self.primary.get_analysis(analysis_id, user)
        except WorkspaceRecordNotFoundError:
            raise
        except Exception as exc:
            return await self._fallback(
                exc,
                "get analysis",
                self.fallback.get_analysis,
                analysis_id,
                user,
            )

    async def update_suggestion_review(
        self,
        analysis_id: UUID,
        review_id: str,
        request: SuggestionReviewUpdateRequest,
        user: WorkspaceUser | None = None,
    ) -> StoredSuggestionReview:
        if self._primary_unavailable:
            return await self.fallback.update_suggestion_review(
                analysis_id,
                review_id,
                request,
                user,
            )
        try:
            return await self.primary.update_suggestion_review(
                analysis_id,
                review_id,
                request,
                user,
            )
        except WorkspaceRecordNotFoundError:
            raise
        except Exception as exc:
            return await self._fallback(
                exc,
                "update suggestion review",
                self.fallback.update_suggestion_review,
                analysis_id,
                review_id,
                request,
                user,
            )

    async def _fallback(self, exc: Exception, operation: str, handler, *args):
        if (
            not settings.workspace_enable_json_fallback
            or settings.environment.casefold() == "production"
        ):
            raise exc
        self._primary_unavailable = True
        logger.exception(
            "PostgreSQL workspace %s failed; using JSON fallback store at %s",
            operation,
            self.fallback.path,
        )
        return await handler(*args)
