import httpx
import pytest

from app.main import app
from app.schemas.candidate import (
    CandidateProfile,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    InferredTargetRole,
    ProjectItem,
    SkillGroup,
)
from app.schemas.job import JobEvidenceItem, JobProfile
from app.schemas.match import EvidenceJudgeResult
from app.services.embedding_service import EmbeddingService
from app.services.evidence_judge_service import EvidenceJudgeService
from app.services.llm_service import LLMService
from app.services.matching_service import MatchingService


def roles(
    primary_role: str,
    role_family: str,
    seniority: str = "Entry-level",
) -> list[InferredTargetRole]:
    return [
        InferredTargetRole(
            role=role,
            role_family=role_family,
            seniority_level=seniority,
            confidence=confidence,
            rationale="Supported by candidate profile evidence.",
            evidence=[f"Evidence for {primary_role}"],
        )
        for role, confidence in (
            (primary_role, 0.92),
            (f"Junior {primary_role}", 0.8),
            (f"{role_family} Associate", 0.7),
        )
    ]


def requirement(value: str) -> JobEvidenceItem:
    return JobEvidenceItem(value=value, evidence=[value])


def get_match(result, text: str):
    return next(
        match for match in result.requirement_matches
        if match.requirement == text
    )


def deterministic_service() -> MatchingService:
    return MatchingService(
        embedding_service=EmbeddingService(api_key=""),
        evidence_judge=EvidenceJudgeService(enabled=False),
    )


@pytest.mark.asyncio
async def test_ai_ml_candidate_vs_ml_intern_job() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Machine Learning",
                skills=["Python", "PyTorch", "Machine Learning"],
                evidence=["Python, PyTorch, machine learning"],
            )
        ],
        projects=[
            ProjectItem(
                name="Image classifier",
                technologies=["PyTorch"],
                bullets=[
                    "Trained a neural network and evaluated model accuracy"
                ],
                evidence=[
                    "Trained a neural network and evaluated model accuracy"
                ],
            )
        ],
        education=[
            EducationItem(
                institution="Example University",
                field_of_study="Computer Science",
                evidence=["Computer Science"],
            )
        ],
        inferred_target_roles=roles(
            "Machine Learning Engineer",
            "AI / Machine Learning",
            "Internship",
        ),
    )
    job = JobProfile(
        job_title="Machine Learning Intern",
        role_family="AI / Machine Learning",
        seniority_level="Internship",
        employment_type="Internship",
        required_skills=[requirement("Python"), requirement("Machine Learning")],
        preferred_skills=[requirement("PyTorch")],
        responsibilities=[
            requirement("Train machine learning models"),
            requirement("Evaluate model performance"),
        ],
        education_requirements=[requirement("Computer Science")],
    )

    result = await deterministic_service().score(candidate, job)

    assert result.final_score >= 75
    assert result.missing_required_skills == []
    assert get_match(result, "Python").match_status == "full_match"
    assert get_match(result, "Machine Learning").candidate_evidence


@pytest.mark.asyncio
async def test_finance_candidate_vs_financial_analyst_job() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Finance",
                skills=["Financial modeling", "Excel", "Budgeting"],
                evidence=["Financial modeling, Excel, budgeting"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Example Finance",
                title="Finance Intern",
                bullets=[
                    "Built monthly financial models in Excel",
                    "Prepared budgets and analyzed spending variances",
                ],
                evidence=["Built monthly financial models in Excel"],
            )
        ],
        education=[
            EducationItem(
                institution="Example University",
                degree="Bachelor of Commerce",
                field_of_study="Finance",
                evidence=["Bachelor of Commerce in Finance"],
            )
        ],
        inferred_target_roles=roles(
            "Financial Analyst",
            "Finance / Accounting",
        ),
    )
    job = JobProfile(
        job_title="Financial Analyst",
        role_family="Finance / Accounting",
        seniority_level="Entry-level",
        employment_type="Full-time",
        required_skills=[
            requirement("Financial modeling"),
            requirement("Excel"),
        ],
        preferred_skills=[requirement("Budgeting")],
        responsibilities=[
            requirement("Prepare financial forecasts"),
            requirement("Analyze budget variances"),
        ],
        qualifications=[requirement("Finance experience")],
        education_requirements=[requirement("Finance degree")],
    )

    result = await deterministic_service().score(candidate, job)

    assert result.final_score >= 70
    assert result.required_coverage_score >= 80
    assert get_match(result, "Financial modeling").candidate_evidence
    assert "Excel" in result.matched_required_skills


@pytest.mark.asyncio
async def test_match_output_does_not_leak_internal_markers() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Software",
                skills=["Python (E018)"],
                evidence=["Python (E018)"],
            )
        ],
        inferred_target_roles=roles("Software Engineer", "Software Engineering"),
    )
    job = JobProfile(
        job_title="Software Engineer",
        role_family="Software Engineering",
        seniority_level="Entry-level",
        employment_type="Full-time",
        required_skills=[requirement("Python [source: jd]")],
    )

    result = await deterministic_service().score(candidate, job)
    output = " ".join(
        [
            result.explanation,
            *result.risks,
            *result.matched_required_skills,
            *result.missing_required_skills,
            *[match.requirement for match in result.requirement_matches],
            *[match.reason for match in result.requirement_matches],
            *[
                evidence.text
                for match in result.requirement_matches
                for evidence in match.candidate_evidence
            ],
        ]
    )

    assert "E018" not in output
    assert "[source" not in output.casefold()


@pytest.mark.asyncio
async def test_marketing_candidate_vs_marketing_coordinator_job() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Marketing",
                skills=["SEO", "Content marketing", "Campaign management"],
                evidence=["SEO, content marketing, campaign management"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Example Agency",
                title="Marketing Assistant",
                bullets=[
                    "Coordinated social media campaigns",
                    "Reported campaign analytics to stakeholders",
                ],
                evidence=["Coordinated social media campaigns"],
            )
        ],
        certifications=[
            CertificationItem(
                name="Google Analytics Certification",
                issuer="Google",
                evidence=["Google Analytics Certification"],
            )
        ],
        inferred_target_roles=roles("Marketing Coordinator", "Marketing"),
    )
    job = JobProfile(
        job_title="Marketing Coordinator",
        role_family="Marketing",
        seniority_level="Entry-level",
        employment_type="Full-time",
        required_skills=[
            requirement("Campaign management"),
            requirement("Social media"),
        ],
        preferred_skills=[requirement("SEO")],
        responsibilities=[
            requirement("Coordinate marketing campaigns"),
            requirement("Report campaign analytics"),
        ],
    )

    result = await deterministic_service().score(candidate, job)

    assert result.final_score >= 70
    assert result.missing_required_skills == []
    assert get_match(result, "Social media").candidate_evidence
    assert result.responsibility_alignment_score >= 65


@pytest.mark.asyncio
async def test_software_candidate_vs_backend_developer_job() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Software",
                skills=["Python", "FastAPI", "PostgreSQL", "Testing"],
                evidence=["Python, FastAPI, PostgreSQL, testing"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Example Software",
                title="Backend Developer",
                bullets=[
                    "Developed REST APIs with FastAPI",
                    "Wrote integration tests and optimized PostgreSQL queries",
                ],
                evidence=["Developed REST APIs with FastAPI"],
            )
        ],
        projects=[
            ProjectItem(
                name="Inventory service",
                technologies=["Python", "PostgreSQL"],
                bullets=["Built a backend inventory API"],
                evidence=["Built a backend inventory API"],
            )
        ],
        inferred_target_roles=roles(
            "Backend Developer",
            "Software Engineering",
            "Junior",
        ),
    )
    job = JobProfile(
        job_title="Backend Developer",
        role_family="Software Engineering",
        seniority_level="Junior",
        employment_type="Full-time",
        required_skills=[
            requirement("Python"),
            requirement("API development"),
            requirement("Databases"),
        ],
        preferred_skills=[requirement("Software testing")],
        responsibilities=[
            requirement("Develop backend APIs"),
            requirement("Write integration tests"),
        ],
    )

    result = await deterministic_service().score(candidate, job)

    assert result.final_score >= 75
    assert result.missing_required_skills == []
    assert get_match(result, "API development").match_status in {
        "full_match",
        "partial_match",
    }
    assert get_match(result, "API development").candidate_evidence


@pytest.mark.asyncio
async def test_low_match_does_not_invent_required_evidence() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Education",
                skills=["Curriculum planning", "Tutoring"],
                evidence=["Curriculum planning and tutoring"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Example School",
                title="Teaching Assistant",
                bullets=["Tutored students and prepared lesson plans"],
                evidence=["Tutored students and prepared lesson plans"],
            )
        ],
        inferred_target_roles=roles("Teaching Assistant", "Education"),
    )
    job = JobProfile(
        job_title="Senior Backend Developer",
        role_family="Software Engineering",
        seniority_level="Senior",
        employment_type="Full-time",
        required_skills=[
            requirement("Python"),
            requirement("Kubernetes"),
            requirement("API development"),
        ],
        responsibilities=[requirement("Design distributed backend systems")],
        experience_requirements=[requirement("Five years backend experience")],
    )

    result = await deterministic_service().score(candidate, job)

    assert result.final_score < 35
    assert result.recommendation == "Low match"
    assert result.missing_required_skills == [
        "Python",
        "Kubernetes",
        "API development",
    ]
    assert all(
        get_match(result, skill).match_status == "missing"
        for skill in result.missing_required_skills
    )
    assert result.risk_penalty > 0


@pytest.mark.asyncio
async def test_transferable_match_is_not_treated_as_full() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Analytics",
                skills=["Data analysis"],
                evidence=["Performed data analysis for sales reporting"],
            )
        ],
        inferred_target_roles=roles("Business Analyst", "Data / Analytics"),
    )
    job = JobProfile(
        job_title="Marketing Analyst",
        role_family="Marketing",
        required_skills=[requirement("Marketing analytics")],
    )

    result = await deterministic_service().score(candidate, job)
    match = get_match(result, "Marketing analytics")

    assert match.match_status == "transferable_match"
    assert match.match_strength < 0.5
    assert match.candidate_evidence
    assert "Marketing analytics" in result.transferable_matches
    assert "Marketing analytics" not in result.matched_required_skills


@pytest.mark.asyncio
async def test_semantic_matching_finds_paraphrase_missed_by_keywords() -> None:
    candidate = CandidateProfile(
        experience=[
            ExperienceItem(
                organization="Example Finance",
                title="Finance Intern",
                bullets=["Produced forward-looking sales projections"],
                evidence=["Produced forward-looking sales projections"],
            )
        ],
        inferred_target_roles=roles(
            "Financial Analyst",
            "Finance / Accounting",
        ),
    )
    job = JobProfile(
        job_title="Financial Analyst",
        role_family="Finance / Accounting",
        required_skills=[requirement("Forecast future revenue")],
    )

    async def semantic_provider(texts: list[str]) -> list[list[float]]:
        return [
            [1.0, 0.0] if "forecast future revenue" in text.casefold()
            or "sales projections" in text.casefold() else [0.0, 1.0]
            for text in texts
        ]

    deterministic = await MatchingService(
        embedding_service=EmbeddingService(api_key="")
    ).score(candidate, job)
    hybrid = await MatchingService(
        embedding_service=EmbeddingService(provider=semantic_provider)
    ).score(candidate, job)

    deterministic_match = get_match(deterministic, "Forecast future revenue")
    semantic_match = get_match(hybrid, "Forecast future revenue")
    assert deterministic_match.match_status == "missing"
    assert semantic_match.match_status == "full_match"
    assert semantic_match.evaluation_method == "semantic"
    assert semantic_match.similarity_score == pytest.approx(1.0)
    assert semantic_match.candidate_evidence


@pytest.mark.asyncio
async def test_llm_judge_only_uses_supplied_evidence() -> None:
    candidate = CandidateProfile(
        experience=[
            ExperienceItem(
                organization="Example Operations",
                title="Coordinator",
                bullets=["Coordinated vendors and weekly delivery schedules"],
                evidence=["Coordinated vendors and weekly delivery schedules"],
            )
        ],
        inferred_target_roles=roles(
            "Operations Coordinator",
            "Business / Operations",
        ),
    )
    job = JobProfile(
        job_title="Customer Success Coordinator",
        role_family="Sales / Customer Success",
        required_skills=[requirement("Client relationship management")],
    )

    async def ambiguous_provider(texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            if "client relationship" in text.casefold():
                vectors.append([1.0, 0.0])
            elif "vendors" in text.casefold():
                vectors.append([0.8, 0.6])
            else:
                vectors.append([0.0, 1.0])
        return vectors

    judge_result = EvidenceJudgeResult(
        match_status="transferable_match",
        confidence=0.81,
        reason="Vendor coordination is transferable but not direct client account management.",
        supported_evidence=[
            "Coordinated vendors and weekly delivery schedules",
            "Invented account management evidence",
        ],
    )
    judge = EvidenceJudgeService(
        LLMService(
            api_key=None,
            mock_response_factory=lambda response_model: response_model.model_validate(
                judge_result.model_dump()
            ),
        ),
        enabled=True,
    )

    result = await MatchingService(
        embedding_service=EmbeddingService(provider=ambiguous_provider),
        evidence_judge=judge,
    ).score(candidate, job)
    match = get_match(result, "Client relationship management")

    assert match.evaluation_method == "llm_judge"
    assert match.match_status == "transferable_match"
    assert match.candidate_evidence[0].text == (
        "Coordinated vendors and weekly delivery schedules"
    )
    assert "Invented account management evidence" not in [
        evidence.text for evidence in match.candidate_evidence
    ]


def test_evidence_index_includes_all_supported_sources() -> None:
    candidate = CandidateProfile(
        skills=[SkillGroup(category="General", skills=["Excel"])],
        certifications=[
            CertificationItem(name="CPA", evidence=["CPA certification"])
        ],
        languages=[],
        inferred_target_roles=roles("Accountant", "Finance / Accounting"),
    )

    index = deterministic_service().build_candidate_evidence_index(candidate)

    assert {item.source_type for item in index} >= {"skills", "certifications"}
    assert all(item.normalized_tokens for item in index)
    assert all(0 <= item.evidence_strength <= 1 for item in index)


@pytest.mark.asyncio
async def test_score_match_api_returns_requirement_decisions(monkeypatch) -> None:
    from app.api.v1 import matches

    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Software",
                skills=["Python"],
                evidence=["Python"],
            )
        ],
        inferred_target_roles=roles(
            "Software Developer",
            "Software Engineering",
        ),
    )
    job = JobProfile(
        job_title="Software Developer",
        role_family="Software Engineering",
        seniority_level="Entry-level",
        required_skills=[requirement("Python")],
    )
    monkeypatch.setattr(matches, "matching_service", deterministic_service())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/matches/score",
            json={
                "candidate_profile": candidate.model_dump(),
                "job_profile": job.model_dump(),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["requirement_matches"][0]["match_status"] == "full_match"
    assert body["requirement_matches"][0]["candidate_evidence"]
    assert body["explanation"]
