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
from app.services.career_direction_service import CareerDirectionService


def inferred_roles(
    role: str,
    family: str,
    seniority: str = "Entry-level",
) -> list[InferredTargetRole]:
    return [
        InferredTargetRole(
            role=title,
            role_family=family,
            seniority_level=seniority,
            confidence=confidence,
            rationale="Supported by profile evidence.",
            evidence=[f"Evidence for {role}"],
        )
        for title, confidence in (
            (role, 0.9),
            (f"Junior {role}", 0.8),
            (f"{family} Associate", 0.7),
        )
    ]


def test_recommends_ai_ml_directions_from_project_evidence() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="AI",
                skills=["Python", "PyTorch", "Machine Learning", "NLP"],
                evidence=["Python, PyTorch, machine learning, NLP"],
            )
        ],
        projects=[
            ProjectItem(
                name="Text classifier",
                technologies=["PyTorch"],
                bullets=["Trained and evaluated an NLP model"],
                evidence=["Trained and evaluated an NLP model"],
            )
        ],
        education=[
            EducationItem(
                institution="Example University",
                field_of_study="Computer Science",
                evidence=["Computer Science"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Machine Learning Engineer",
            "AI / Machine Learning",
            "Internship",
        ),
    )

    result = CareerDirectionService().recommend(candidate)

    assert result.directions
    assert result.directions[0].role_family == "AI / Machine Learning"
    assert result.directions[0].matched_evidence
    assert result.directions[0].seniority_level == "Internship"
    assert any(
        direction.direction == "NLP and Language AI"
        for direction in result.directions
    )


def test_recommends_finance_and_accounting_directions() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Finance",
                skills=["Financial modeling", "Excel", "Budgeting", "Accounting"],
                evidence=["Financial modeling, Excel, budgeting, accounting"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Example Finance",
                title="Finance Intern",
                bullets=[
                    "Built financial forecasts and analyzed budget variances",
                    "Completed account reconciliations",
                ],
                evidence=["Built financial forecasts and analyzed budget variances"],
            )
        ],
        education=[
            EducationItem(
                institution="Example University",
                field_of_study="Accounting",
                evidence=["Accounting"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Financial Analyst",
            "Finance / Accounting",
        ),
    )

    result = CareerDirectionService().recommend(candidate)
    families = [direction.role_family for direction in result.directions]

    assert families[0] == "Finance / Accounting"
    assert any(
        direction.direction == "Financial Analysis"
        for direction in result.directions
    )
    assert all(direction.matched_evidence for direction in result.directions)


def test_recommends_marketing_direction() -> None:
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
                    "Coordinated social media campaigns and campaign analytics"
                ],
                evidence=[
                    "Coordinated social media campaigns and campaign analytics"
                ],
            )
        ],
        certifications=[
            CertificationItem(
                name="Google Analytics Certification",
                evidence=["Google Analytics Certification"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Marketing Coordinator",
            "Marketing",
        ),
    )

    result = CareerDirectionService().recommend(candidate)

    assert result.directions[0].direction == "Digital Marketing"
    assert result.directions[0].fit_type == "primary"
    assert result.directions[0].confidence_level in {"High", "Medium"}


def test_recommends_backend_direction_from_work_and_project_evidence() -> None:
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
                bullets=["Developed REST APIs and database services"],
                evidence=["Developed REST APIs and database services"],
            )
        ],
        projects=[
            ProjectItem(
                name="Inventory API",
                technologies=["Python", "PostgreSQL"],
                bullets=["Built a tested backend API"],
                evidence=["Built a tested backend API"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Backend Developer",
            "Software Engineering",
            "Junior",
        ),
    )

    result = CareerDirectionService().recommend(candidate)
    top = result.directions[0]

    assert top.direction == "Backend Engineering"
    assert top.seniority_level == "Junior"
    assert {evidence.source_type for evidence in top.matched_evidence} & {
        "experience",
        "projects",
    }
    assert top.score_range_low <= top.score_midpoint <= top.score_range_high


def test_sparse_profile_returns_fewer_low_confidence_directions() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="General",
                skills=["Excel"],
                evidence=["Excel"],
            )
        ]
    )

    result = CareerDirectionService().recommend(candidate)

    assert 1 <= len(result.directions) < 5
    assert all(
        direction.confidence_level == "Low"
        for direction in result.directions
    )
    assert all(direction.matched_evidence for direction in result.directions)


@pytest.mark.asyncio
async def test_career_direction_api_returns_ranked_results() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Software",
                skills=["Python", "FastAPI"],
                evidence=["Python and FastAPI"],
            )
        ],
        projects=[
            ProjectItem(
                name="API project",
                technologies=["Python", "FastAPI"],
                evidence=["Built a REST API with FastAPI"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Backend Developer",
            "Software Engineering",
        ),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/career-directions/recommend",
            json={"candidate_profile": candidate.model_dump()},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["directions"][0]["rank"] == 1
    assert body["directions"][0]["matched_evidence"]
