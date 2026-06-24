import asyncio

import httpx
import pytest

from app.main import app
from app.schemas.candidate import CandidateProfile, InferredTargetRole
from app.schemas.career_direction import (
    CareerDirectionRecommendation,
    CareerDirectionResponse,
    DirectionEvidence,
)
from app.schemas.analysis_job import AnalysisJobCreateRequest
from app.schemas.suggestion import SuggestionResponse
from app.services.analysis_job_service import AnalysisJobService
from app.schemas.workspace import StoredAnalysis, StoredAnalysisDetail, StoredResume, utc_now
from app.services.workspace_store import WorkspaceRecordNotFoundError


def profile() -> CandidateProfile:
    return CandidateProfile(
        strengths=["Python API development"],
        inferred_target_roles=[
            InferredTargetRole(
                role=role,
                role_family="Software Engineering",
                seniority_level="Entry-level",
                confidence=confidence,
                rationale="Supported by backend API evidence.",
                evidence=["Built REST APIs with Python"],
            )
            for role, confidence in (
                ("Backend Engineer", 0.9),
                ("Software Engineer", 0.82),
                ("API Developer", 0.76),
            )
        ],
    )


def directions() -> CareerDirectionResponse:
    return CareerDirectionResponse(
        directions=[
            CareerDirectionRecommendation(
                rank=1,
                direction="Backend Engineering",
                role_family="Software Engineering",
                seniority_level="Entry-level",
                fit_type="primary",
                score_range_low=75,
                score_range_high=85,
                score_midpoint=80,
                confidence_level="High",
                matched_evidence=[
                    DirectionEvidence(
                        evidence_id="E001",
                        source_type="work",
                        text="Built REST APIs with Python",
                        evidence_strength=1,
                    )
                ],
            )
        ]
    )


class FakeProfileService:
    async def build_profile(
        self,
        extracted_text: str,
        preferred_language: str = "en",
    ) -> CandidateProfile:
        return profile()


class FailingThenPassingProfileService:
    def __init__(self) -> None:
        self.calls = 0

    async def build_profile(
        self,
        extracted_text: str,
        preferred_language: str = "en",
    ) -> CandidateProfile:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("provider stack trace should stay in logs")
        return profile()


class FakeDirectionService:
    async def recommend(
        self,
        candidate: CandidateProfile,
        preferred_language: str = "en",
    ) -> CareerDirectionResponse:
        return directions()


class FakeSuggestionService:
    async def generate(self, request) -> SuggestionResponse:
        return SuggestionResponse(overall_summary="Use backend API evidence.")


class FakeWorkspaceStore:
    async def save_analysis(self, response, request, user=None):
        return None

    async def get_analysis(self, job_id, user=None):
        raise WorkspaceRecordNotFoundError(str(job_id))


class RecoverableWorkspaceStore:
    def __init__(self) -> None:
        self.response = None
        self.request = None

    async def save_analysis(self, response, request, user=None):
        self.response = response
        self.request = request
        return None

    async def get_analysis(self, job_id, user=None):
        if not self.response or not self.request:
            raise WorkspaceRecordNotFoundError(str(job_id))
        now = utc_now()
        return StoredAnalysisDetail(
            analysis=StoredAnalysis(
                analysis_id=self.response.job_id,
                status=self.response.status,
                preferred_language=self.response.preferred_language,
                analysis_job=self.response,
                created_at=self.response.created_at,
                updated_at=self.response.updated_at,
            ),
            resume=StoredResume(
                resume_id=self.request.resume_id or self.response.job_id,
                filename="resume.docx",
                file_type="docx",
                extracted_text=self.request.extracted_text,
                character_count=len(self.request.extracted_text),
                created_at=now,
                updated_at=now,
            ),
        )


async def wait_for_terminal(client: httpx.AsyncClient, job_id: str) -> dict:
    for _ in range(20):
        response = await client.get(f"/api/v1/analysis-jobs/{job_id}")
        body = response.json()
        if body["status"] in {"succeeded", "failed"}:
            return body
        await asyncio.sleep(0.01)
    raise AssertionError("analysis job did not finish")


@pytest.mark.asyncio
async def test_analysis_job_runs_steps_and_returns_results(monkeypatch) -> None:
    from app.api.v1 import analysis_jobs

    monkeypatch.setattr(
        analysis_jobs,
        "analysis_job_service",
        AnalysisJobService(
            resume_profile_service=FakeProfileService(),
            career_direction_service=FakeDirectionService(),
            suggestion_service=FakeSuggestionService(),
            workspace_store=FakeWorkspaceStore(),
        ),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/analysis-jobs",
            json={"extracted_text": "Built REST APIs with Python"},
        )
        assert create_response.status_code == 200
        assert create_response.json()["job_id"]

        body = await wait_for_terminal(client, create_response.json()["job_id"])

    assert body["status"] == "succeeded"
    assert body["profile"]["strengths"] == ["Python API development"]
    assert body["career_directions"]["directions"][0]["direction"] == (
        "Backend Engineering"
    )
    assert body["suggestions"]["overall_summary"] == "Use backend API evidence."
    step_statuses = {step["key"]: step["status"] for step in body["steps"]}
    assert step_statuses == {
        "profile_parsing": "succeeded",
        "career_directions": "succeeded",
        "advisor_suggestions": "succeeded",
        "job_matching": "skipped",
    }


@pytest.mark.asyncio
async def test_analysis_job_failure_uses_friendly_localized_error(monkeypatch) -> None:
    from app.api.v1 import analysis_jobs

    monkeypatch.setattr(
        analysis_jobs,
        "analysis_job_service",
        AnalysisJobService(
            resume_profile_service=FailingThenPassingProfileService(),
            career_direction_service=FakeDirectionService(),
            suggestion_service=FakeSuggestionService(),
            workspace_store=FakeWorkspaceStore(),
        ),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/analysis-jobs",
            json={
                "extracted_text": "Built REST APIs with Python",
                "preferred_language": "zh",
            },
        )
        body = await wait_for_terminal(client, create_response.json()["job_id"])

    assert body["status"] == "failed"
    assert body["error_message"] == "分析未能完成，请稍后重试。"
    assert "provider stack trace" not in body["error_message"]
    failed_steps = [step for step in body["steps"] if step["status"] == "failed"]
    assert failed_steps[0]["key"] == "profile_parsing"


@pytest.mark.asyncio
async def test_analysis_job_retry_restarts_failed_job(monkeypatch) -> None:
    from app.api.v1 import analysis_jobs

    monkeypatch.setattr(
        analysis_jobs,
        "analysis_job_service",
        AnalysisJobService(
            resume_profile_service=FailingThenPassingProfileService(),
            career_direction_service=FakeDirectionService(),
            suggestion_service=FakeSuggestionService(),
            workspace_store=FakeWorkspaceStore(),
        ),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/analysis-jobs",
            json={"extracted_text": "Built REST APIs with Python"},
        )
        job_id = create_response.json()["job_id"]
        failed = await wait_for_terminal(client, job_id)
        assert failed["status"] == "failed"

        retry_response = await client.post(f"/api/v1/analysis-jobs/{job_id}/retry")
        assert retry_response.status_code == 200
        succeeded = await wait_for_terminal(client, job_id)

    assert succeeded["status"] == "succeeded"
    assert succeeded["error_message"] is None


@pytest.mark.asyncio
async def test_analysis_job_get_recovers_saved_terminal_job() -> None:
    store = RecoverableWorkspaceStore()
    first_service = AnalysisJobService(
        resume_profile_service=FakeProfileService(),
        career_direction_service=FakeDirectionService(),
        suggestion_service=FakeSuggestionService(),
        workspace_store=store,
    )
    created = await first_service.create_job(
        AnalysisJobCreateRequest(extracted_text="Built REST APIs with Python")
    )

    for _ in range(20):
        terminal = await first_service.get_job(created.job_id)
        if terminal.status == "succeeded":
            break
        await asyncio.sleep(0.01)
    else:
        raise AssertionError("analysis job did not finish")

    restarted_service = AnalysisJobService(
        resume_profile_service=FakeProfileService(),
        career_direction_service=FakeDirectionService(),
        suggestion_service=FakeSuggestionService(),
        workspace_store=store,
    )

    recovered = await restarted_service.get_job(created.job_id)

    assert recovered.status == "succeeded"
    assert recovered.profile
    assert recovered.career_directions
