import httpx
import pytest

from app.main import app
from app.schemas.job import JobEvidenceItem, JobProfile, JobProfileEvidence
from app.services.job_parser_service import JobParserService
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_parse_job_with_mock_llm(monkeypatch) -> None:
    from app.api.v1 import jobs

    mocked_profile = JobProfile(
        job_title="Marketing Coordinator",
        company_name="Example Company",
        role_family="Marketing",
        seniority_level="Entry-level",
        employment_type="Full-time",
        remote_policy="Hybrid",
        required_skills=[
            JobEvidenceItem(
                value="Campaign coordination",
                evidence=["Coordinate multi-channel campaigns"],
            )
        ],
        evidence=JobProfileEvidence(
            company_name=["Example Company"],
            remote_policy=["full-time hybrid role"],
        ),
    )
    mock_llm = LLMService(
        api_key=None,
        mock_response_factory=lambda response_model: response_model.model_validate(
            mocked_profile.model_dump()
        ),
    )
    monkeypatch.setattr(
        jobs,
        "job_parser_service",
        JobParserService(mock_llm),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/jobs/parse",
            json={
                "raw_job_description": (
                    "Example Company seeks a Marketing Coordinator to coordinate "
                    "multi-channel campaigns. This is a full-time hybrid role."
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["role_family"] == "Marketing"
    assert response.json()["required_skills"][0]["value"] == (
        "Campaign coordination"
    )


@pytest.mark.asyncio
async def test_parse_job_rejects_blank_description() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/jobs/parse",
            json={"raw_job_description": "   "},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_parse_job_reports_missing_api_key(monkeypatch) -> None:
    from app.api.v1 import jobs

    monkeypatch.setattr(
        jobs,
        "job_parser_service",
        JobParserService(LLMService(api_key="")),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/jobs/parse",
            json={
                "raw_job_description": (
                    "Full-time accountant responsible for monthly reporting."
                )
            },
        )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
