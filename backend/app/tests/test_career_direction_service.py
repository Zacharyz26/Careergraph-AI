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
from app.schemas.career_direction import (
    CareerDirectionProposalSet,
    ProposedCareerDirection,
)
from app.services.career_direction_proposal_service import (
    CareerDirectionProposalService,
)
from app.services.career_direction_service import CareerDirectionService
from app.services.llm_service import LLMService


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


def fallback_service() -> CareerDirectionService:
    return CareerDirectionService(
        proposal_service=CareerDirectionProposalService(
            LLMService(api_key=""),
            enabled=False,
        )
    )


def proposal(
    name: str,
    family: str,
    evidence_ids: list[str],
    *,
    fit_type: str = "secondary",
    seniority: str = "Entry-level",
    gaps: list[str] | None = None,
) -> ProposedCareerDirection:
    return ProposedCareerDirection(
        direction=name,
        role_family=family,
        likely_seniority_level=seniority,
        proposed_fit_type=fit_type,
        rationale=f"Evidence supports {name}.",
        supporting_evidence_ids=evidence_ids,
        possible_gaps=gaps or [],
        example_job_titles=[name],
    )


def llm_service(proposals: list[ProposedCareerDirection]) -> CareerDirectionService:
    proposal_set = CareerDirectionProposalSet(directions=proposals)
    return CareerDirectionService(
        proposal_service=CareerDirectionProposalService(
            LLMService(
                api_key=None,
                mock_response_factory=lambda response_model: response_model.model_validate(
                    proposal_set.model_dump()
                ),
            ),
            enabled=True,
        )
    )


def fill_proposals(
    primary: list[ProposedCareerDirection],
    evidence_id: str,
) -> list[ProposedCareerDirection]:
    fillers = [
        ("Data Analytics", "Data / Analytics"),
        ("Product Analysis", "Product"),
        ("Research Analysis", "Research"),
        ("Business Operations", "Business / Operations"),
        ("Technical Education", "Education"),
        ("Customer Solutions", "Sales / Customer Success"),
        ("General Internship Pathways", "General Internship"),
        ("Professional Support", "Other"),
        ("Compliance Analysis", "Legal / Compliance"),
        ("Engineering Analysis", "Engineering"),
    ]
    result = list(primary)
    for name, family in fillers:
        if len(result) >= 8:
            break
        result.append(
            proposal(
                name,
                family,
                [evidence_id],
                fit_type="exploratory",
            )
        )
    return result


@pytest.mark.asyncio
async def test_recommends_ai_ml_directions_from_project_evidence() -> None:
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

    result = await fallback_service().recommend(candidate)

    assert result.directions
    assert result.directions[0].role_family == "AI / Machine Learning"
    assert result.directions[0].matched_evidence
    assert result.directions[0].seniority_level == "Internship"
    assert any(
        direction.direction == "NLP and Language AI"
        for direction in result.directions
    )


@pytest.mark.asyncio
async def test_recommends_finance_and_accounting_directions() -> None:
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

    result = await fallback_service().recommend(candidate)
    families = [direction.role_family for direction in result.directions]

    assert families[0] == "Finance / Accounting"
    assert any(
        direction.direction == "Financial Analysis"
        for direction in result.directions
    )
    assert all(direction.matched_evidence for direction in result.directions)


@pytest.mark.asyncio
async def test_recommends_marketing_direction() -> None:
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

    result = await fallback_service().recommend(candidate)

    assert result.directions[0].direction == "Digital Marketing"
    assert result.directions[0].fit_type == "primary"
    assert result.directions[0].confidence_level in {"High", "Medium"}


@pytest.mark.asyncio
async def test_recommends_backend_direction_from_work_and_project_evidence() -> None:
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

    result = await fallback_service().recommend(candidate)
    top = result.directions[0]

    assert top.direction == "Backend Engineering"
    assert top.seniority_level == "Junior"
    assert {evidence.source_type for evidence in top.matched_evidence} & {
        "work",
        "project",
    }
    assert top.score_range_low <= top.score_midpoint <= top.score_range_high


@pytest.mark.asyncio
async def test_sparse_profile_returns_fewer_low_confidence_directions() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="General",
                skills=["Excel"],
                evidence=["Excel"],
            )
        ]
    )

    result = await fallback_service().recommend(candidate)

    assert 1 <= len(result.directions) < 5
    assert all(
        direction.confidence_level == "Low"
        for direction in result.directions
    )
    assert all(direction.matched_evidence for direction in result.directions)


@pytest.mark.asyncio
async def test_career_direction_api_returns_ranked_results(monkeypatch) -> None:
    from app.api.v1 import career_directions

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
    monkeypatch.setattr(
        career_directions,
        "career_direction_service",
        fallback_service(),
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


@pytest.mark.asyncio
async def test_llm_proposes_specialized_aigc_and_cv_directions() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="AI",
                skills=["PyTorch", "Computer Vision", "Generative AI"],
                evidence=["PyTorch, computer vision, generative AI"],
            )
        ],
        projects=[
            ProjectItem(
                name="Multimodal image generator",
                bullets=[
                    "Trained a diffusion model and evaluated generated images"
                ],
                evidence=[
                    "Trained a diffusion model and evaluated generated images"
                ],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Computer Vision Engineer",
            "AI / Machine Learning",
            "Internship",
        ),
    )
    summary = fallback_service().build_evidence_summary(candidate)
    project_id = summary.project_signals[-1].evidence_id
    vision_skill_id = next(
        item.evidence_id
        for item in summary.skill_signals
        if item.text == "Computer Vision"
    )
    proposals = fill_proposals(
        [
            proposal(
                "Generative AI Engineering",
                "AI / Machine Learning",
                [project_id],
                fit_type="primary",
                seniority="Internship",
            ),
            proposal(
                "Computer Vision Engineering",
                "AI / Machine Learning",
                [vision_skill_id, project_id],
                fit_type="primary",
                seniority="Internship",
            ),
        ],
        project_id,
    )

    result = await llm_service(proposals).recommend(candidate)
    names = [item.direction for item in result.directions]

    assert "Generative AI Engineering" in names
    assert "Computer Vision Engineering" in names
    assert any(
        evidence.evidence_id == project_id
        for item in result.directions[:2]
        for evidence in item.matched_evidence
    )


@pytest.mark.asyncio
async def test_llm_proposes_healthcare_direction_from_clinical_evidence() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Healthcare",
                skills=["Medical terminology"],
                evidence=["Medical terminology"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Community Clinic",
                title="Clinical Assistant",
                bullets=["Supported patient intake and clinical operations"],
                evidence=["Supported patient intake and clinical operations"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Clinical Coordinator",
            "Healthcare",
        ),
    )
    summary = fallback_service().build_evidence_summary(candidate)
    work_id = summary.work_signals[-1].evidence_id
    proposals = fill_proposals(
        [
            proposal(
                "Clinical Operations",
                "Healthcare",
                [work_id],
                fit_type="primary",
            )
        ],
        work_id,
    )

    result = await llm_service(proposals).recommend(candidate)

    assert result.directions[0].role_family == "Healthcare"
    assert result.directions[0].fit_type == "primary"


@pytest.mark.asyncio
async def test_generic_internship_is_suppressed_when_specialized_fit_is_strong() -> None:
    candidate = CandidateProfile(
        experience=[
            ExperienceItem(
                organization="Example Agency",
                title="Marketing Assistant",
                bullets=["Managed content campaigns and SEO reporting"],
                evidence=["Managed content campaigns and SEO reporting"],
            )
        ],
        inferred_target_roles=inferred_roles("Marketing Coordinator", "Marketing"),
    )
    summary = fallback_service().build_evidence_summary(candidate)
    work_id = summary.work_signals[-1].evidence_id
    proposals = fill_proposals(
        [
            proposal(
                "Digital Marketing",
                "Marketing",
                [work_id],
                fit_type="primary",
            ),
            proposal(
                "General Internship Pathways",
                "General Internship",
                [work_id],
                fit_type="exploratory",
            ),
        ],
        work_id,
    )

    result = await llm_service(proposals).recommend(candidate)

    assert result.directions[0].direction == "Digital Marketing"
    assert all(
        item.role_family != "General Internship"
        for item in result.directions
    )


@pytest.mark.asyncio
async def test_skill_only_primary_proposal_is_downgraded() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="Software",
                skills=["Python"],
                evidence=["Python"],
            )
        ]
    )
    summary = fallback_service().build_evidence_summary(candidate)
    skill_id = summary.skill_signals[0].evidence_id
    proposals = fill_proposals(
        [
            proposal(
                "Backend Engineering",
                "Software Engineering",
                [skill_id],
                fit_type="primary",
            )
        ],
        skill_id,
    )

    result = await llm_service(proposals).recommend(candidate)
    backend = next(
        item for item in result.directions
        if item.direction == "Backend Engineering"
    )

    assert backend.fit_type == "exploratory"
    assert backend.score_midpoint <= 38
    assert backend.confidence_level == "Low"


@pytest.mark.asyncio
async def test_hallucinated_evidence_ids_are_removed() -> None:
    candidate = CandidateProfile(
        experience=[
            ExperienceItem(
                organization="Example Finance",
                title="Finance Intern",
                bullets=["Built monthly financial forecasts"],
                evidence=["Built monthly financial forecasts"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Financial Analyst",
            "Finance / Accounting",
        ),
    )
    summary = fallback_service().build_evidence_summary(candidate)
    valid_id = summary.work_signals[-1].evidence_id
    proposals = fill_proposals(
        [
            proposal(
                "Financial Analysis",
                "Finance / Accounting",
                [valid_id, "E999"],
                fit_type="primary",
            ),
            proposal(
                "Cloud Engineering",
                "Software Engineering",
                ["E999"],
                fit_type="primary",
            ),
        ],
        valid_id,
    )

    result = await llm_service(proposals).recommend(candidate)

    assert all(
        evidence.evidence_id != "E999"
        for item in result.directions
        for evidence in item.matched_evidence
    )
    assert all(item.direction != "Cloud Engineering" for item in result.directions)


@pytest.mark.asyncio
async def test_isolated_transferable_evidence_does_not_rival_coherent_profile() -> None:
    candidate = CandidateProfile(
        skills=[
            SkillGroup(
                category="AI",
                skills=["Python", "PyTorch", "Machine Learning", "NLP"],
                evidence=["Python, PyTorch, machine learning, NLP"],
            )
        ],
        education=[
            EducationItem(
                institution="Example University",
                field_of_study="Computer Science",
                details=["Coursework in machine learning and statistics"],
                evidence=["Computer Science"],
            )
        ],
        projects=[
            ProjectItem(
                name="Language model evaluator",
                technologies=["Python", "PyTorch"],
                bullets=["Trained and evaluated an NLP model"],
                evidence=["Trained and evaluated an NLP model"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Student Association",
                title="Event Coordinator",
                bullets=["Coordinated one student event"],
                evidence=["Coordinated one student event"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Machine Learning Engineer",
            "AI / Machine Learning",
            "Internship",
        ),
    )
    summary = fallback_service().build_evidence_summary(candidate)
    project_id = next(
        item.evidence_id
        for item in summary.project_signals
        if item.text == "Trained and evaluated an NLP model"
    )
    ai_skill_id = next(
        item.evidence_id
        for item in summary.skill_signals
        if item.text == "Machine Learning"
    )
    education_id = next(
        item.evidence_id
        for item in summary.education_signals
        if "machine learning" in item.text.casefold()
    )
    coordination_id = next(
        item.evidence_id
        for item in summary.work_signals
        if item.text == "Coordinated one student event"
    )
    proposals = fill_proposals(
        [
            proposal(
                "Machine Learning Engineering",
                "AI / Machine Learning",
                [project_id, ai_skill_id, education_id],
                fit_type="primary",
                seniority="Internship",
            ),
            proposal(
                "Business Operations",
                "Business / Operations",
                [coordination_id],
                fit_type="primary",
                seniority="Internship",
            ),
        ],
        project_id,
    )

    result = await llm_service(proposals).recommend(candidate)
    machine_learning = next(
        item
        for item in result.directions
        if item.direction == "Machine Learning Engineering"
    )
    operations = next(
        item
        for item in result.directions
        if item.direction == "Business Operations"
    )

    assert result.directions[0].direction == "Machine Learning Engineering"
    assert operations.fit_type in {"transferable", "exploratory"}
    assert machine_learning.score_midpoint - operations.score_midpoint >= 20
