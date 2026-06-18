from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.schemas.analysis_job import (
    AnalysisJobCreateRequest,
    AnalysisJobResponse,
    AnalysisJobStatus,
    AnalysisStepKey,
    AnalysisStepState,
    AnalysisStepStatus,
    utc_now,
)
from app.schemas.candidate import CandidateProfile
from app.schemas.career_direction import (
    CareerDirectionRecommendation,
    CareerDirectionResponse,
)
from app.schemas.suggestion import SuggestionGenerateRequest, SuggestionResponse
from app.services.career_direction_service import CareerDirectionService
from app.services.resume_profile_service import ResumeProfileService
from app.services.suggestion_service import SuggestionService

logger = logging.getLogger(__name__)


STEP_LABELS = {
    AnalysisStepKey.PROFILE_PARSING: "Profile Parsing",
    AnalysisStepKey.CAREER_DIRECTIONS: "Career Directions",
    AnalysisStepKey.ADVISOR_SUGGESTIONS: "Advisor/Suggestions",
    AnalysisStepKey.JOB_MATCHING: "Job Matching",
}


@dataclass
class AnalysisJobRecord:
    request: AnalysisJobCreateRequest
    response: AnalysisJobResponse


class AnalysisJobNotFoundError(KeyError):
    pass


class AnalysisJobService:
    def __init__(
        self,
        *,
        resume_profile_service: ResumeProfileService | None = None,
        career_direction_service: CareerDirectionService | None = None,
        suggestion_service: SuggestionService | None = None,
    ) -> None:
        self.resume_profile_service = (
            resume_profile_service or ResumeProfileService()
        )
        self.career_direction_service = (
            career_direction_service or CareerDirectionService()
        )
        self.suggestion_service = suggestion_service or SuggestionService()
        self._jobs: dict[UUID, AnalysisJobRecord] = {}
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        request: AnalysisJobCreateRequest,
    ) -> AnalysisJobResponse:
        job_id = uuid4()
        now = utc_now()
        record = AnalysisJobRecord(
            request=request,
            response=AnalysisJobResponse(
                job_id=job_id,
                status=AnalysisJobStatus.QUEUED,
                steps=self._initial_steps(),
                preferred_language=request.preferred_language,
                created_at=now,
                updated_at=now,
            ),
        )
        async with self._lock:
            self._jobs[job_id] = record
            self._tasks[job_id] = asyncio.create_task(self._run_job(job_id))
            return record.response.model_copy(deep=True)

    async def get_job(self, job_id: UUID) -> AnalysisJobResponse:
        async with self._lock:
            return self._record_for(job_id).response.model_copy(deep=True)

    async def retry_job(self, job_id: UUID) -> AnalysisJobResponse:
        async with self._lock:
            record = self._record_for(job_id)
            task = self._tasks.get(job_id)
            if task and not task.done():
                task.cancel()
            now = utc_now()
            record.response = AnalysisJobResponse(
                job_id=job_id,
                status=AnalysisJobStatus.QUEUED,
                steps=self._initial_steps(),
                preferred_language=record.request.preferred_language,
                created_at=record.response.created_at,
                updated_at=now,
            )
            self._tasks[job_id] = asyncio.create_task(self._run_job(job_id))
            return record.response.model_copy(deep=True)

    async def _run_job(self, job_id: UUID) -> None:
        profile: CandidateProfile | None = None
        directions = CareerDirectionResponse()
        selected_direction: CareerDirectionRecommendation | None = None
        suggestions: SuggestionResponse | None = None

        try:
            async with self._lock:
                record = self._record_for(job_id)
                self._set_job_running(record)

            async with self._lock:
                record = self._record_for(job_id)
                self._start_step(record, AnalysisStepKey.PROFILE_PARSING)
            profile = await self.resume_profile_service.build_profile(
                record.request.extracted_text,
                preferred_language=record.request.preferred_language,
            )
            async with self._lock:
                record = self._record_for(job_id)
                record.response.profile = profile
                self._finish_step(record, AnalysisStepKey.PROFILE_PARSING)

            async with self._lock:
                record = self._record_for(job_id)
                self._start_step(record, AnalysisStepKey.CAREER_DIRECTIONS)
            directions = await self.career_direction_service.recommend(
                profile,
                preferred_language=record.request.preferred_language,
            )
            selected_direction = directions.directions[0] if directions.directions else None
            async with self._lock:
                record = self._record_for(job_id)
                record.response.career_directions = directions
                record.response.selected_direction = selected_direction
                self._finish_step(record, AnalysisStepKey.CAREER_DIRECTIONS)

            if selected_direction:
                async with self._lock:
                    record = self._record_for(job_id)
                    self._start_step(record, AnalysisStepKey.ADVISOR_SUGGESTIONS)
                suggestions = await self.suggestion_service.generate(
                    SuggestionGenerateRequest(
                        candidate_profile=profile,
                        career_direction_result=selected_direction,
                        target_direction=selected_direction.direction,
                        suggestion_mode="career_direction",
                        preferred_language=record.request.preferred_language,
                    )
                )
                async with self._lock:
                    record = self._record_for(job_id)
                    record.response.suggestions = suggestions
                    self._finish_step(record, AnalysisStepKey.ADVISOR_SUGGESTIONS)
            else:
                async with self._lock:
                    record = self._record_for(job_id)
                    self._skip_step(record, AnalysisStepKey.ADVISOR_SUGGESTIONS)

            async with self._lock:
                record = self._record_for(job_id)
                self._skip_step(record, AnalysisStepKey.JOB_MATCHING)
                record.response.status = AnalysisJobStatus.SUCCEEDED
                record.response.current_step = None
                record.response.updated_at = utc_now()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception(
                "Analysis job failed: job_id=%s step=%s error_type=%s",
                job_id,
                await self._current_step_for_log(job_id),
                type(exc).__name__,
            )
            async with self._lock:
                record = self._record_for(job_id)
                self._fail_current_step(record)

    async def _current_step_for_log(self, job_id: UUID) -> str | None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return None
            return record.response.current_step

    def _record_for(self, job_id: UUID) -> AnalysisJobRecord:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise AnalysisJobNotFoundError(str(job_id)) from exc

    def _initial_steps(self) -> list[AnalysisStepState]:
        return [
            AnalysisStepState(key=step, label=STEP_LABELS[step])
            for step in AnalysisStepKey
        ]

    def _set_job_running(self, record: AnalysisJobRecord) -> None:
        record.response.status = AnalysisJobStatus.RUNNING
        record.response.updated_at = utc_now()

    def _start_step(
        self,
        record: AnalysisJobRecord,
        step: AnalysisStepKey,
    ) -> None:
        state = self._step(record, step)
        state.status = AnalysisStepStatus.RUNNING
        state.started_at = utc_now()
        state.completed_at = None
        state.message = None
        record.response.status = AnalysisJobStatus.RUNNING
        record.response.current_step = step
        record.response.error_message = None
        record.response.updated_at = utc_now()

    def _finish_step(
        self,
        record: AnalysisJobRecord,
        step: AnalysisStepKey,
    ) -> None:
        state = self._step(record, step)
        state.status = AnalysisStepStatus.SUCCEEDED
        state.completed_at = utc_now()
        record.response.updated_at = utc_now()

    def _skip_step(
        self,
        record: AnalysisJobRecord,
        step: AnalysisStepKey,
    ) -> None:
        state = self._step(record, step)
        state.status = AnalysisStepStatus.SKIPPED
        state.completed_at = utc_now()
        record.response.updated_at = utc_now()

    def _fail_current_step(self, record: AnalysisJobRecord) -> None:
        message = self._friendly_error(record.request.preferred_language)
        if record.response.current_step:
            state = self._step(record, record.response.current_step)
            state.status = AnalysisStepStatus.FAILED
            state.message = message
            state.completed_at = utc_now()
        record.response.status = AnalysisJobStatus.FAILED
        record.response.error_message = message
        record.response.updated_at = utc_now()

    def _step(
        self,
        record: AnalysisJobRecord,
        step: AnalysisStepKey,
    ) -> AnalysisStepState:
        return next(item for item in record.response.steps if item.key == step)

    def _friendly_error(self, preferred_language: str) -> str:
        if preferred_language == "zh":
            return "分析未能完成，请稍后重试。"
        return "The analysis could not be completed. Please try again."
