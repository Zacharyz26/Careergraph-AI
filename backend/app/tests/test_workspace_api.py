import httpx
import pytest

from app.main import app
from app.schemas.analysis_job import AnalysisJobCreateRequest, AnalysisJobResponse
from app.schemas.workspace import (
    AnalysisHistoryResponse,
    StoredAnalysis,
    StoredAnalysisDetail,
    StoredSuggestionReview,
    utc_now,
)
from app.services.workspace_store import WorkspaceRecordNotFoundError
from app.tests.test_analysis_jobs_api import directions, profile


class FakeWorkspaceStore:
    def __init__(self) -> None:
        self.records = {}

    async def save_analysis(self, response, request, user=None):
        now = utc_now()
        record = StoredAnalysis(
            analysis_id=response.job_id,
            resume_id=request.resume_id,
            filename=None,
            preferred_language=response.preferred_language,
            status=response.status,
            analysis_job=response,
            suggestion_reviews=[
                StoredSuggestionReview(
                    review_id="resume_ready_improvements:0",
                    section="resume_ready_improvements",
                    item_index=0,
                    original_text="Built REST APIs with Python",
                    updated_at=now,
                )
            ],
            created_at=now,
            updated_at=now,
        )
        self.records[str(response.job_id)] = record
        return record

    async def list_analyses(self, user=None):
        return AnalysisHistoryResponse(
            analyses=[
                {
                    "analysis_id": item.analysis_id,
                    "resume_id": item.resume_id,
                    "filename": item.filename,
                    "preferred_language": item.preferred_language,
                    "status": item.status,
                    "candidate_name": item.analysis_job.profile.basic_info.full_name
                    if item.analysis_job.profile
                    else None,
                    "top_direction": item.analysis_job.career_directions.directions[0].direction
                    if item.analysis_job.career_directions
                    and item.analysis_job.career_directions.directions
                    else None,
                    "suggestion_count": 0,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in self.records.values()
            ]
        )

    async def get_analysis(self, analysis_id, user=None):
        try:
            return StoredAnalysisDetail(
                analysis=self.records[str(analysis_id)],
                resume=None,
            )
        except KeyError as exc:
            raise WorkspaceRecordNotFoundError(str(analysis_id)) from exc

    async def update_suggestion_review(self, analysis_id, review_id, request, user=None):
        detail = await self.get_analysis(analysis_id)
        for review in detail.analysis.suggestion_reviews:
            if review.review_id == review_id:
                review.status = request.status
                review.edited_text = request.edited_text
                review.note = request.note
                review.updated_at = utc_now()
                return review
        raise WorkspaceRecordNotFoundError(review_id)


@pytest.mark.asyncio
async def test_workspace_lists_and_returns_stored_analysis(
    monkeypatch,
) -> None:
    from app.api.v1 import workspace

    store = FakeWorkspaceStore()
    response = AnalysisJobResponse(
        job_id="11111111-1111-4111-8111-111111111111",
        status="succeeded",
        steps=[],
        preferred_language="en",
        profile=profile(),
        career_directions=directions(),
        selected_direction=directions().directions[0],
        created_at="2026-06-18T00:00:00Z",
        updated_at="2026-06-18T00:01:00Z",
    )
    await store.save_analysis(
        response,
        AnalysisJobCreateRequest(extracted_text="Built REST APIs with Python"),
    )
    monkeypatch.setattr(workspace, "workspace_store", store)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        list_response = await client.get("/api/v1/workspace/analyses")
        detail_response = await client.get(
            "/api/v1/workspace/analyses/11111111-1111-4111-8111-111111111111"
        )

    assert list_response.status_code == 200
    history = AnalysisHistoryResponse.model_validate(list_response.json())
    assert history.analyses[0].top_direction == "Backend Engineering"
    assert detail_response.status_code == 200
    assert detail_response.json()["analysis"]["analysis_job"]["profile"]["strengths"] == [
        "Python API development"
    ]


@pytest.mark.asyncio
async def test_workspace_returns_404_for_missing_analysis(monkeypatch) -> None:
    from app.api.v1 import workspace

    monkeypatch.setattr(
        workspace,
        "workspace_store",
        FakeWorkspaceStore(),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/workspace/analyses/11111111-1111-4111-8111-111111111111"
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_workspace_updates_suggestion_review(monkeypatch) -> None:
    from app.api.v1 import workspace

    store = FakeWorkspaceStore()
    response = AnalysisJobResponse(
        job_id="11111111-1111-4111-8111-111111111111",
        status="succeeded",
        steps=[],
        preferred_language="en",
        profile=profile(),
        career_directions=directions(),
        selected_direction=directions().directions[0],
        created_at="2026-06-18T00:00:00Z",
        updated_at="2026-06-18T00:01:00Z",
    )
    await store.save_analysis(
        response,
        AnalysisJobCreateRequest(extracted_text="Built REST APIs with Python"),
    )
    monkeypatch.setattr(workspace, "workspace_store", store)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        patch_response = await client.patch(
            "/api/v1/workspace/analyses/11111111-1111-4111-8111-111111111111/suggestions/resume_ready_improvements%3A0",
            json={
                "status": "edited",
                "edited_text": "Built Python REST APIs for backend services",
            },
        )

    assert patch_response.status_code == 200
    body = patch_response.json()
    assert body["status"] == "edited"
    assert body["edited_text"] == "Built Python REST APIs for backend services"
