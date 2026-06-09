import pytest
from pydantic import ValidationError

from app.schemas.job import (
    JobEvidenceItem,
    JobProfile,
    JobProfileEvidence,
    SalaryInfo,
)
from app.services.job_parser_service import JobParserService
from app.services.llm_service import LLMService, MissingAPIKeyError


def test_job_profile_defaults_missing_optional_information() -> None:
    profile = JobProfile(role_family="Other")

    assert profile.company_name is None
    assert profile.salary is None
    assert profile.visa_sponsorship is None
    assert profile.required_skills == []
    assert profile.preferred_skills == []
    assert profile.seniority_level == "Unknown"
    assert profile.employment_type == "Unknown"
    assert profile.remote_policy == "Unknown"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("role_family", "Technology"),
        ("seniority_level", "entry"),
        ("employment_type", "Permanent"),
        ("remote_policy", "Flexible"),
    ],
)
def test_job_profile_rejects_nonstandard_taxonomy_values(
    field: str,
    value: str,
) -> None:
    payload = {"role_family": "Software Engineering", field: value}

    with pytest.raises(ValidationError):
        JobProfile.model_validate(payload)


def test_salary_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        SalaryInfo(raw_text="$80,000 per year", evidence=[])


@pytest.mark.asyncio
async def test_job_parser_service_uses_structured_mock_response() -> None:
    expected = JobProfile(
        job_title="Data Analyst",
        company_name=None,
        role_family="Data / Analytics",
        seniority_level="Entry-level",
        employment_type="Full-time",
        location="Toronto, ON",
        remote_policy="Hybrid",
        required_skills=[
            JobEvidenceItem(
                value="SQL",
                evidence=["Required qualifications: SQL"],
            )
        ],
        preferred_skills=[
            JobEvidenceItem(
                value="Python",
                evidence=["Python is considered an asset"],
            )
        ],
        responsibilities=[
            JobEvidenceItem(
                value="Build recurring reports",
                evidence=["Build recurring reports for business teams"],
            )
        ],
        qualifications=[
            JobEvidenceItem(
                value="Bachelor's degree",
                evidence=["Bachelor's degree required"],
            )
        ],
        evidence=JobProfileEvidence(
            location=["Data Analyst in Toronto"],
            remote_policy=["hybrid position"],
        ),
    )
    llm_service = LLMService(
        api_key=None,
        mock_response_factory=lambda response_model: response_model.model_validate(
            expected.model_dump()
        ),
    )

    profile = await JobParserService(llm_service).parse(
        "Data Analyst in Toronto. Required: SQL. Python is an asset. "
        "This is a hybrid position."
    )

    assert profile == expected
    assert profile.company_name is None


@pytest.mark.asyncio
async def test_job_parser_removes_scalar_claims_without_source_evidence() -> None:
    mocked_profile = JobProfile(
        company_name="Invented Company",
        role_family="Finance / Accounting",
        location="New York",
        remote_policy="Remote",
        visa_sponsorship="Provided",
        salary=SalaryInfo(
            raw_text="$100,000",
            minimum=100_000,
            currency="USD",
            period="year",
            evidence=["$100,000"],
        ),
        evidence=JobProfileEvidence(
            company_name=["Invented Company"],
            location=["New York"],
            remote_policy=["Remote"],
            visa_sponsorship=["Sponsorship provided"],
        ),
    )
    llm_service = LLMService(
        api_key=None,
        mock_response_factory=lambda response_model: response_model.model_validate(
            mocked_profile.model_dump()
        ),
    )

    profile = await JobParserService(llm_service).parse(
        "Accountant responsible for monthly reporting."
    )

    assert profile.company_name is None
    assert profile.location is None
    assert profile.remote_policy == "Unknown"
    assert profile.visa_sponsorship is None
    assert profile.salary is None


@pytest.mark.asyncio
async def test_job_parser_service_requires_api_key_without_mock() -> None:
    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        await JobParserService(LLMService(api_key="")).parse(
            "Full-time analyst responsible for monthly reporting."
        )
