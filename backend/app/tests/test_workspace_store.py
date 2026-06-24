from uuid import UUID

import pytest

from app.schemas.analysis_job import AnalysisJobCreateRequest, AnalysisJobResponse
from app.schemas.resume import ResumeUploadResponse
from app.schemas.suggestion import RecommendedNextActionItem, SuggestionResponse
from app.core.config import settings
from app.core.security import WorkspaceUser
from app.services.workspace_store import JsonWorkspaceStore, WorkspaceStore
from app.tests.test_analysis_jobs_api import directions, profile


class FailingSessionFactory:
    def __call__(self):
        return self

    async def __aenter__(self):
        raise ConnectionError("database is not available")

    async def __aexit__(self, exc_type, exc, traceback):
        return False


@pytest.mark.asyncio
async def test_workspace_store_falls_back_to_json_when_database_is_unavailable(
    tmp_path,
) -> None:
    store = WorkspaceStore(
        session_factory=FailingSessionFactory(),  # type: ignore[arg-type]
        fallback_store=JsonWorkspaceStore(tmp_path / "workspace.json"),
    )
    upload = ResumeUploadResponse(
        filename="resume.docx",
        file_type="docx",
        extracted_text="Built REST APIs with Python",
        character_count=27,
    )

    stored_resume = await store.save_uploaded_resume(upload)
    response = AnalysisJobResponse(
        job_id=UUID("11111111-1111-4111-8111-111111111111"),
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
        AnalysisJobCreateRequest(
            extracted_text=upload.extracted_text,
            resume_id=stored_resume.resume_id,
        ),
    )

    history = await store.list_analyses()
    detail = await store.get_analysis(response.job_id)

    assert history.analyses[0].analysis_id == response.job_id
    assert history.analyses[0].filename == "resume.docx"
    assert detail.resume
    assert detail.resume.resume_id == stored_resume.resume_id
    assert detail.analysis.analysis_job.profile


@pytest.mark.asyncio
async def test_json_workspace_initializes_reviews_after_late_suggestions(
    tmp_path,
) -> None:
    store = JsonWorkspaceStore(tmp_path / "workspace.json")
    request = AnalysisJobCreateRequest(extracted_text="Built REST APIs with Python")
    job_id = UUID("22222222-2222-4222-8222-222222222222")
    queued = AnalysisJobResponse(
        job_id=job_id,
        status="queued",
        steps=[],
        preferred_language="en",
        created_at="2026-06-18T00:00:00Z",
        updated_at="2026-06-18T00:00:00Z",
    )
    succeeded = AnalysisJobResponse(
        job_id=job_id,
        status="succeeded",
        steps=[],
        preferred_language="en",
        suggestions=SuggestionResponse(
            overall_summary="Use backend API evidence.",
            recommended_next_actions=[
                RecommendedNextActionItem(
                    action="Publish a backend API project demo.",
                    rationale="A demo strengthens deployment evidence.",
                    priority="high",
                )
            ],
        ),
        created_at="2026-06-18T00:00:00Z",
        updated_at="2026-06-18T00:01:00Z",
    )

    await store.save_analysis(queued, request)
    await store.save_analysis(succeeded, request)

    detail = await store.get_analysis(job_id)

    assert len(detail.analysis.suggestion_reviews) == 1
    assert detail.analysis.suggestion_reviews[0].review_id == (
        "recommended_next_actions:0"
    )


@pytest.mark.asyncio
async def test_json_workspace_filters_records_by_user(tmp_path) -> None:
    store = JsonWorkspaceStore(tmp_path / "workspace.json")
    upload = ResumeUploadResponse(
        filename="resume.docx",
        file_type="docx",
        extracted_text="Built REST APIs with Python",
        character_count=27,
    )
    user_a = WorkspaceUser(email="a@example.com")
    user_b = WorkspaceUser(email="b@example.com")
    resume_a = await store.save_uploaded_resume(upload, user_a)
    resume_b = await store.save_uploaded_resume(upload, user_b)

    response_a = AnalysisJobResponse(
        job_id=UUID("33333333-3333-4333-8333-333333333333"),
        status="succeeded",
        steps=[],
        preferred_language="en",
        profile=profile(),
        career_directions=directions(),
        created_at="2026-06-18T00:00:00Z",
        updated_at="2026-06-18T00:01:00Z",
    )
    response_b = response_a.model_copy(
        update={"job_id": UUID("44444444-4444-4444-8444-444444444444")},
    )
    await store.save_analysis(
        response_a,
        AnalysisJobCreateRequest(
            extracted_text=upload.extracted_text,
            resume_id=resume_a.resume_id,
        ),
        user_a,
    )
    await store.save_analysis(
        response_b,
        AnalysisJobCreateRequest(
            extracted_text=upload.extracted_text,
            resume_id=resume_b.resume_id,
        ),
        user_b,
    )

    history_a = await store.list_analyses(user_a)

    assert [item.analysis_id for item in history_a.analyses] == [
        response_a.job_id
    ]
    with pytest.raises(Exception):
        await store.get_analysis(response_b.job_id, user_a)


@pytest.mark.asyncio
async def test_workspace_store_does_not_use_json_fallback_in_production(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    store = WorkspaceStore(
        session_factory=FailingSessionFactory(),  # type: ignore[arg-type]
        fallback_store=JsonWorkspaceStore(tmp_path / "workspace.json"),
    )
    upload = ResumeUploadResponse(
        filename="resume.docx",
        file_type="docx",
        extracted_text="Built REST APIs with Python",
        character_count=27,
    )

    with pytest.raises(ConnectionError):
        await store.save_uploaded_resume(upload)
