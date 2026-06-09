from io import BytesIO

import httpx
import pytest
from docx import Document

from app.main import app
from app.schemas.candidate import CandidateProfile, InferredTargetRole
from app.services.llm_service import LLMService
from app.services.resume_profile_service import ResumeProfileService


@pytest.mark.asyncio
async def test_health_check() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_docx_resume() -> None:
    document = Document()
    document.add_paragraph("Backend Engineer with Python experience")
    buffer = BytesIO()
    document.save(buffer)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/resumes/upload",
            files={
                "file": (
                    "resume.docx",
                    buffer.getvalue(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "resume.docx",
        "file_type": "docx",
        "extracted_text": "Backend Engineer with Python experience",
        "character_count": 39,
    }


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.txt", b"plain text", "text/plain")},
        )

    assert response.status_code == 400
    assert "Only PDF and DOCX" in response.json()["detail"]


@pytest.mark.asyncio
async def test_parse_profile_with_mock_llm(monkeypatch) -> None:
    from app.api.v1 import resumes

    mocked_profile = CandidateProfile(
        strengths=["Python API development"],
        patents=[],
        inferred_target_roles=[
            InferredTargetRole(
                role=role,
                role_family="Software Engineering",
                seniority_level="Junior",
                confidence=confidence,
                rationale="The resume states Python API development.",
                evidence=["Developed Python APIs."],
            )
            for role, confidence in (
                ("Backend Engineer", 0.9),
                ("Software Engineer", 0.8),
                ("API Developer", 0.75),
            )
        ],
    )
    mock_llm = LLMService(
        api_key=None,
        mock_response_factory=lambda response_model: response_model.model_validate(
            mocked_profile.model_dump()
        ),
    )
    monkeypatch.setattr(
        resumes,
        "resume_profile_service",
        ResumeProfileService(mock_llm),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/resumes/parse-profile",
            json={"extracted_text": "Developed Python APIs."},
        )

    assert response.status_code == 200
    assert response.json()["strengths"] == ["Python API development"]
    assert response.json()["patents"] == []
    assert len(response.json()["inferred_target_roles"]) == 3
    assert response.json()["inferred_target_roles"][0]["role_family"] == (
        "Software Engineering"
    )


@pytest.mark.asyncio
async def test_parse_profile_rejects_blank_text() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/resumes/parse-profile",
            json={"extracted_text": "   "},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_parse_profile_reports_missing_api_key(monkeypatch) -> None:
    from app.api.v1 import resumes

    monkeypatch.setattr(
        resumes,
        "resume_profile_service",
        ResumeProfileService(LLMService(api_key="")),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/resumes/parse-profile",
            json={"extracted_text": "Python backend engineer"},
        )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
