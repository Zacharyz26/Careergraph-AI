import httpx
import pytest

from app.main import app
from app.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    InferredTargetRole,
    ProjectItem,
    SkillGroup,
)
from app.schemas.career_direction import (
    CareerDirectionRecommendation,
    DirectionEvidence,
)
from app.schemas.job import JobEvidenceItem, JobProfile
from app.schemas.match import (
    MatchResult,
    RequirementMatch,
    ScoredMatchEvidence,
)
from app.schemas.suggestion import (
    SuggestionGenerateRequest,
    SuggestionItem,
    SuggestionResponse,
)
from app.services.llm_service import LLMService
from app.services.suggestion_service import SuggestionService


def candidate_profile() -> CandidateProfile:
    return CandidateProfile(
        skills=[
            SkillGroup(
                category="Backend",
                skills=["Python", "FastAPI"],
                evidence=["Python and FastAPI"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Example Co",
                title="Software Intern",
                bullets=["Built REST APIs with Python"],
                evidence=["Built REST APIs with Python"],
            )
        ],
        projects=[
            ProjectItem(
                name="Inventory service",
                technologies=["PostgreSQL"],
                bullets=["Created an inventory API backed by PostgreSQL"],
                evidence=["Created an inventory API backed by PostgreSQL"],
            )
        ],
        inferred_target_roles=[
            InferredTargetRole(
                role=role,
                role_family="Software Engineering",
                seniority_level=seniority,
                confidence=confidence,
                rationale="Supported by backend evidence.",
                evidence=["Built REST APIs with Python"],
            )
            for role, seniority, confidence in (
                ("Backend Engineer", "Entry-level", 0.9),
                ("Software Engineer", "Entry-level", 0.8),
                ("Backend Intern", "Internship", 0.7),
            )
        ],
    )


def job_profile() -> JobProfile:
    return JobProfile(
        job_title="Backend Developer",
        role_family="Software Engineering",
        seniority_level="Entry-level",
        required_skills=[
            JobEvidenceItem(value="Python", evidence=["Python is required"]),
            JobEvidenceItem(
                value="Kubernetes",
                evidence=["Kubernetes is required"],
            ),
        ],
        preferred_skills=[
            JobEvidenceItem(value="AWS", evidence=["AWS is preferred"])
        ],
    )


def match_result() -> MatchResult:
    return MatchResult(
        final_score=64,
        required_coverage_score=50,
        preferred_coverage_score=0,
        responsibility_alignment_score=70,
        education_fit_score=50,
        seniority_fit_score=90,
        evidence_strength_score=80,
        risk_penalty=15,
        requirement_matches=[
            RequirementMatch(
                requirement_type="required_skill",
                importance=1,
                requirement="Kubernetes",
                match_status="missing",
                match_strength=0,
                confidence=1,
                candidate_evidence=[],
                reason="No candidate evidence supports Kubernetes.",
            )
        ],
        matched_required_skills=["Python"],
        missing_required_skills=["Kubernetes"],
        missing_preferred_skills=["AWS"],
        matched_evidence=[
            ScoredMatchEvidence(
                requirement="Python",
                candidate_source="experience",
                candidate_evidence=["Built REST APIs with Python"],
                match_strength="full",
            )
        ],
        recommendation="Partial match",
        explanation="Python is supported; Kubernetes and AWS are not.",
    )


def career_direction() -> CareerDirectionRecommendation:
    return CareerDirectionRecommendation(
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
                evidence_id="E003",
                source_type="work",
                text="Built REST APIs with Python",
                evidence_strength=1,
                matched_concepts=["api_development"],
            )
        ],
        strengths_for_this_direction=["API development"],
        gaps_for_this_direction=["Cloud deployment evidence"],
        resume_positioning_advice=["Lead with backend API evidence."],
        example_job_titles=["Backend Developer"],
    )


def mocked_service(response: SuggestionResponse) -> SuggestionService:
    return SuggestionService(
        llm_service=LLMService(
            api_key=None,
            mock_response_factory=lambda response_model: response_model.model_validate(
                response.model_dump()
            ),
        )
    )


def generated_item(
    *,
    evidence_id: str,
    evidence_text: str,
    suggested_text: str,
    suggestion_type: str = "bullet_rewrite",
    risk_level: str = "low",
    related: str | None = None,
) -> SuggestionItem:
    return SuggestionItem(
        suggestion_type=suggestion_type,
        target_section="experience",
        original_text=evidence_text,
        suggested_text=suggested_text,
        reason="Clarifies supported experience.",
        source_evidence_ids=[evidence_id],
        source_evidence_text=[evidence_text],
        related_requirement_or_direction=related,
        risk_level=risk_level,
        requires_user_review=True,
        should_add_to_resume=True,
    )


def evidence_for(
    service: SuggestionService,
    candidate: CandidateProfile,
    text: str,
) -> tuple[str, str]:
    evidence = next(
        item
        for item in service.evidence_service.build_evidence_summary(candidate).all_evidence()
        if item.text == text
    )
    return evidence.evidence_id, evidence.text


@pytest.mark.asyncio
async def test_bullet_rewrite_keeps_only_valid_source_evidence() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Built REST APIs with Python",
    )
    response = SuggestionResponse(
        overall_summary="Strengthen the experience wording.",
        suggestions=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="Built REST APIs with Python.",
            )
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(candidate_profile=candidate)
    )

    assert len(result.suggestions) == 1
    assert result.suggestions[0].source_evidence_ids == [evidence_id]
    assert result.suggestions[0].source_evidence_text == [evidence_text]
    assert result.suggestions[0].requires_user_review is True


@pytest.mark.asyncio
async def test_missing_unsupported_skills_are_not_added_to_suggested_text() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Built REST APIs with Python",
    )
    response = SuggestionResponse(
        overall_summary="Tailor for the job.",
        suggestions=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="Built Kubernetes services with Python.",
            )
        ],
        missing_but_not_addable=["Kubernetes"],
    )
    request = SuggestionGenerateRequest(
        candidate_profile=candidate,
        job_profile=job_profile(),
        match_result=match_result(),
        suggestion_mode="job_specific",
    )

    result = await mocked_service(response).generate(request)

    assert all(
        "kubernetes" not in item.suggested_text.casefold()
        for item in result.suggestions
    )
    assert "Kubernetes" in result.missing_but_not_addable
    assert any("unsafe suggestion" in warning for warning in result.warnings)


@pytest.mark.asyncio
async def test_career_direction_mode_preserves_direction_context() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Created an inventory API backed by PostgreSQL",
    )
    response = SuggestionResponse(
        overall_summary="Position the resume for backend engineering.",
        suggestions=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text=evidence_text,
                suggestion_type="project_emphasis",
                related="Backend Engineering",
            )
        ],
        suggested_resume_focus=["Backend Engineering"],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            career_direction_result=career_direction(),
            suggestion_mode="career_direction",
        )
    )

    assert result.suggested_resume_focus == ["Backend Engineering"]
    assert (
        result.suggestions[0].related_requirement_or_direction
        == "Backend Engineering"
    )
    assert "Cloud deployment evidence" in result.missing_but_not_addable


@pytest.mark.asyncio
async def test_job_specific_mode_uses_gaps_and_matched_evidence() -> None:
    candidate = candidate_profile()
    service = SuggestionService(llm_service=LLMService(api_key=""))
    request = SuggestionGenerateRequest(
        candidate_profile=candidate,
        job_profile=job_profile(),
        match_result=match_result(),
        suggestion_mode="job_specific",
    )

    result = await service.generate(request)

    assert {"Kubernetes", "AWS"} <= set(result.missing_but_not_addable)
    assert any(
        suggestion.related_requirement_or_direction == "Backend Developer"
        for suggestion in result.suggestions
    )
    assert all(suggestion.source_evidence_text for suggestion in result.suggestions)


@pytest.mark.asyncio
async def test_weak_skill_evidence_increases_risk_level() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(bootstrap, candidate, "FastAPI")
    response = SuggestionResponse(
        overall_summary="Group supported skills.",
        suggestions=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="FastAPI",
                suggestion_type="skill_grouping",
                risk_level="low",
            )
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(candidate_profile=candidate)
    )

    assert result.suggestions[0].risk_level == "medium"


@pytest.mark.asyncio
async def test_hallucinated_certifications_links_metrics_and_tools_are_removed() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Built REST APIs with Python",
    )
    unsafe_texts = [
        "Built Kubernetes services with Python.",
        "Improved API throughput by 50%.",
        "AWS Certified Developer with backend experience.",
        "Portfolio: https://example.com/backend",
    ]
    response = SuggestionResponse(
        overall_summary="Unsafe generated claims should be removed.",
        suggestions=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text=text,
            )
            for text in unsafe_texts
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            job_profile=job_profile(),
            match_result=match_result(),
            suggestion_mode="job_specific",
        )
    )

    assert result.suggestions == []
    assert len(result.warnings) == len(unsafe_texts)


@pytest.mark.asyncio
async def test_suggestion_api_route_uses_deterministic_fallback(monkeypatch) -> None:
    from app.api.v1 import suggestions

    monkeypatch.setattr(
        suggestions,
        "suggestion_service",
        SuggestionService(llm_service=LLMService(api_key="")),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/suggestions/generate",
            json={
                "candidate_profile": candidate_profile().model_dump(),
                "suggestion_mode": "general",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["suggestions"]
    assert all(item["requires_user_review"] for item in body["suggestions"])


def test_request_infers_mode_from_supplied_context() -> None:
    career_request = SuggestionGenerateRequest(
        candidate_profile=candidate_profile(),
        target_direction="Backend Engineering",
    )
    job_request = SuggestionGenerateRequest(
        candidate_profile=candidate_profile(),
        job_profile=job_profile(),
        match_result=match_result(),
    )

    assert career_request.suggestion_mode == "career_direction"
    assert job_request.suggestion_mode == "job_specific"
