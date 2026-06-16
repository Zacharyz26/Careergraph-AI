import pytest
from httpx import Request, Response
from openai import APITimeoutError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from app.schemas.candidate import (
    CandidateProfile,
    EducationItem,
    InferredTargetRole,
)
from app.services.llm_service import LLMService, MissingAPIKeyError
from app.services.resume_profile_service import ResumeProfileService


def test_candidate_profile_defaults_missing_sections() -> None:
    profile = CandidateProfile()

    assert profile.basic_info.full_name is None
    assert profile.education == []
    assert profile.patents == []
    assert profile.improvement_areas == []
    assert profile.inferred_target_roles == []


def test_inferred_target_role_must_be_labeled_inferred() -> None:
    with pytest.raises(ValidationError):
        InferredTargetRole(
            role="Operations Coordinator",
            role_family="Business / Operations",
            seniority_level="Entry-level",
            confidence=0.8,
            rationale="Resume lists scheduling and process coordination.",
            evidence=["Coordinated weekly operating schedules"],
            is_inferred=False,
        )


def test_inferred_target_role_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        InferredTargetRole(
            role="Financial Analyst",
            role_family="Finance / Accounting",
            seniority_level="Junior",
            confidence=1.2,
            rationale="Resume lists financial modeling.",
            evidence=["Built monthly financial models"],
        )


@pytest.mark.parametrize(
    ("role_family", "seniority_level"),
    [
        ("Operations", "Entry-level"),
        ("Business / Operations", "entry"),
    ],
)
def test_inferred_target_role_rejects_nonstandard_taxonomy_values(
    role_family: str,
    seniority_level: str,
) -> None:
    with pytest.raises(ValidationError):
        InferredTargetRole.model_validate(
            {
                "role": "Operations Coordinator",
                "role_family": role_family,
                "seniority_level": seniority_level,
                "confidence": 0.7,
                "rationale": "Resume lists process coordination.",
                "evidence": ["Coordinated weekly schedules"],
            }
        )


def test_candidate_profile_rejects_more_than_six_inferred_roles() -> None:
    roles = [
        InferredTargetRole(
            role=f"Role {index}",
            role_family="Other",
            seniority_level="Unknown",
            confidence=0.4,
            rationale="Supported by broad resume evidence.",
            evidence=["Broad resume evidence"],
        )
        for index in range(7)
    ]

    with pytest.raises(ValidationError):
        CandidateProfile.model_validate({"inferred_target_roles": roles})


@pytest.mark.asyncio
async def test_profile_service_uses_structured_mock_response() -> None:
    expected = CandidateProfile(
        strengths=["Built Python APIs"],
        inferred_target_roles=[
            InferredTargetRole(
                role="Backend Engineer",
                role_family="Software Engineering",
                seniority_level="Junior",
                confidence=0.9,
                rationale="Resume lists Python and FastAPI API work.",
                evidence=["Developed APIs with Python and FastAPI"],
            ),
            InferredTargetRole(
                role="Software Engineer",
                role_family="Software Engineering",
                seniority_level="Junior",
                confidence=0.82,
                rationale="Resume demonstrates software development experience.",
                evidence=["Developed APIs with Python and FastAPI"],
            ),
            InferredTargetRole(
                role="API Developer",
                role_family="Software Engineering",
                seniority_level="Junior",
                confidence=0.76,
                rationale="Resume specifically demonstrates API development.",
                evidence=["Developed APIs with Python and FastAPI"],
            ),
        ],
    )
    llm_service = LLMService(
        api_key=None,
        mock_response_factory=lambda response_model: response_model.model_validate(
            expected.model_dump()
        ),
    )

    profile = await ResumeProfileService(llm_service).build_profile(
        "Developed APIs with Python and FastAPI"
    )

    assert profile == expected


@pytest.mark.asyncio
async def test_profile_service_removes_layout_comments_and_unstated_graduation_date() -> None:
    mocked_profile = CandidateProfile(
        education=[
            EducationItem(
                institution="Example University",
                graduation_date="May 2027",
                evidence=["Example University"],
            )
        ],
        improvement_areas=[
            "Use a cleaner font and improve page spacing.",
            "Project impact is unclear.",
        ],
        inferred_target_roles=[
            InferredTargetRole(
                role=f"Broad Role {index}",
                role_family="Other",
                seniority_level="Unknown",
                confidence=0.4,
                rationale="The resume provides broad transferable evidence.",
                evidence=["Example University"],
            )
            for index in range(1, 4)
        ],
    )
    llm_service = LLMService(
        api_key=None,
        mock_response_factory=lambda response_model: response_model.model_validate(
            mocked_profile.model_dump()
        ),
    )

    profile = await ResumeProfileService(llm_service).build_profile(
        "Example University\nCompleted interdisciplinary coursework"
    )

    assert profile.education[0].graduation_date is None
    assert profile.improvement_areas == ["Project impact is unclear."]


@pytest.mark.asyncio
async def test_llm_service_requires_api_key_without_mock() -> None:
    service = LLMService(api_key="")

    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        await service.generate_structured(
            system_prompt="Extract only stated facts.",
            user_prompt="Python developer",
            response_model=CandidateProfile,
        )


def test_llm_service_reports_timeout_without_exposing_api_key() -> None:
    service = LLMService(api_key="sk-secret", timeout_seconds=60)
    error = APITimeoutError(request=Request("POST", "https://api.openai.com"))

    detail = service._public_provider_error(error)

    assert "timed out after 60 seconds" in detail
    assert "sk-secret" not in detail


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            AuthenticationError(
                "invalid key",
                response=Response(
                    401,
                    request=Request("POST", "https://api.openai.com"),
                ),
                body=None,
            ),
            "Check OPENAI_API_KEY",
        ),
        (
            RateLimitError(
                "quota exceeded",
                response=Response(
                    429,
                    request=Request("POST", "https://api.openai.com"),
                ),
                body=None,
            ),
            "usage and billing",
        ),
    ],
)
def test_llm_service_classifies_provider_errors(
    error: Exception,
    expected: str,
) -> None:
    detail = LLMService(api_key="sk-secret")._public_provider_error(error)

    assert expected in detail
    assert "sk-secret" not in detail
