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
    EvidenceGapItem,
    PositioningAdviceItem,
    RecommendedNextActionItem,
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


def finance_candidate_profile() -> CandidateProfile:
    return CandidateProfile(
        skills=[
            SkillGroup(
                category="Finance",
                skills=["Financial modeling", "Valuation", "Market research"],
                evidence=[
                    "Financial modeling and valuation coursework",
                    "Market research for investment analysis",
                ],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Student Investment Fund",
                title="Equity Research Analyst",
                bullets=[
                    "Researched public companies and presented investment views"
                ],
                evidence=[
                    "Researched public companies and presented investment views"
                ],
            )
        ],
        projects=[
            ProjectItem(
                name="DCF analysis",
                technologies=["Excel"],
                bullets=["Built a DCF analysis for a listed company"],
                evidence=["Built a DCF analysis for a listed company"],
            )
        ],
        inferred_target_roles=[
            InferredTargetRole(
                role=role,
                role_family="Finance / Accounting",
                seniority_level="Entry-level",
                confidence=confidence,
                rationale="Supported by finance research and modeling evidence.",
                evidence=["Built a DCF analysis for a listed company"],
            )
            for role, confidence in (
                ("Investment Analyst", 0.86),
                ("Financial Analyst", 0.82),
                ("Equity Research Analyst", 0.78),
            )
        ],
    )

def finance_career_direction() -> CareerDirectionRecommendation:
    return CareerDirectionRecommendation(
        rank=1,
        direction="Investment Analyst",
        role_family="Finance / Accounting",
        seniority_level="Entry-level",
        fit_type="primary",
        score_range_low=78,
        score_range_high=88,
        score_midpoint=83,
        confidence_level="High",
        matched_evidence=[
            DirectionEvidence(
                evidence_id="E003",
                source_type="project",
                text="Built a DCF analysis for a listed company",
                evidence_strength=0.9,
                matched_concepts=["financial_modeling"],
            )
        ],
        strengths_for_this_direction=["Financial modeling", "Equity research"],
        gaps_for_this_direction=[],
        resume_positioning_advice=["Lead with finance research evidence."],
        example_job_titles=["Investment Analyst"],
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
        resume_ready_improvements=[
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

    assert len(result.resume_ready_improvements) == 1
    assert result.resume_ready_improvements[0].source_evidence_ids == [evidence_id]
    assert result.resume_ready_improvements[0].source_evidence_text == [evidence_text]
    assert result.resume_ready_improvements[0].requires_user_review is True


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
        resume_ready_improvements=[
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
        for item in result.resume_ready_improvements
    )
    assert "Kubernetes" in result.missing_but_not_addable
    assert any(gap.gap == "Kubernetes" for gap in result.evidence_gaps)
    assert any(action.target_gap == "Kubernetes" for action in result.recommended_next_actions)
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
        resume_ready_improvements=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="Created a PostgreSQL-backed inventory API.",
                suggestion_type="project_emphasis",
                related="Backend Engineering",
            )
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            career_direction_result=career_direction(),
            suggestion_mode="career_direction",
        )
    )

    assert (
        result.resume_ready_improvements[0].related_requirement_or_direction
        == "Backend Engineering"
    )
    assert "Cloud deployment evidence" in result.missing_but_not_addable
    assert result.evidence_gaps
    assert result.recommended_next_actions


@pytest.mark.asyncio
async def test_advisor_keeps_positioning_gaps_and_next_actions_separate() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Created an inventory API backed by PostgreSQL",
    )
    response = SuggestionResponse(
        overall_summary="Position for backend engineering without adding missing claims.",
        positioning_advice=[
            PositioningAdviceItem(
                target_section="projects",
                advice="Lead with the inventory API project because it supports backend API evidence.",
                reason="The project is directly aligned with backend engineering.",
                source_evidence_ids=[evidence_id],
                source_evidence_text=[evidence_text],
                related_requirement_or_direction="Backend Engineering",
                requires_user_review=True,
            )
        ],
        evidence_gaps=[
            EvidenceGapItem(
                gap="Cloud deployment evidence",
                why_it_matters="Deployment is relevant to backend engineering roles.",
                evidence_needed="A deployed project or deployment note.",
                related_requirement_or_direction="Backend Engineering",
                should_add_to_resume=False,
                requires_user_review=True,
            )
        ],
        recommended_next_actions=[
            RecommendedNextActionItem(
                action="Deploy the existing inventory API and document the deployment steps.",
                rationale="This creates verifiable deployment evidence.",
                target_gap="Cloud deployment evidence",
                suggested_artifact="Deployment README or demo link.",
                priority="high",
                should_add_to_resume=False,
                requires_user_review=True,
            )
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            career_direction_result=career_direction(),
            suggestion_mode="career_direction",
        )
    )

    assert result.resume_ready_improvements == []
    assert result.positioning_advice[0].source_evidence_ids == [evidence_id]
    assert "Cloud deployment evidence" in result.missing_but_not_addable
    assert any(gap.gap == "Cloud deployment evidence" for gap in result.evidence_gaps)
    assert any(
        action.target_gap == "Cloud deployment evidence"
        for action in result.recommended_next_actions
    )
    deployment_gap = next(
        gap
        for gap in result.evidence_gaps
        if gap.gap == "Cloud deployment evidence"
    )
    assert deployment_gap.category == "implementation_or_delivery"
    assert deployment_gap.priority == "high"


@pytest.mark.asyncio
async def test_quality_layer_ranks_high_value_resume_ready_items_first() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    work_id, work_text = evidence_for(
        bootstrap,
        candidate,
        "Built REST APIs with Python",
    )
    project_id, project_text = evidence_for(
        bootstrap,
        candidate,
        "Created an inventory API backed by PostgreSQL",
    )
    response = SuggestionResponse(
        overall_summary="Rank higher-value improvements first.",
        resume_ready_improvements=[
            SuggestionItem(
                suggestion_type="bullet_rewrite",
                target_section="experience",
                original_text=work_text,
                suggested_text="Built REST APIs with Python.",
                reason="Clarifies supported experience.",
                source_evidence_ids=[work_id],
                source_evidence_text=[work_text],
                risk_level="low",
                requires_user_review=True,
                should_add_to_resume=True,
            ),
            SuggestionItem(
                suggestion_type="project_emphasis",
                target_section="project",
                original_text=project_text,
                suggested_text=(
                    "Feature the inventory API project using PostgreSQL "
                    "evidence from the resume."
                ),
                reason="Prioritizes a target-relevant project artifact.",
                source_evidence_ids=[project_id],
                source_evidence_text=[project_text],
                related_requirement_or_direction="Backend Engineering",
                risk_level="low",
                requires_user_review=True,
                should_add_to_resume=True,
            ),
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            career_direction_result=career_direction(),
            suggestion_mode="career_direction",
        )
    )

    assert result.resume_ready_improvements[0].suggestion_type == "project_emphasis"
    assert result.resume_ready_improvements[0].quality_level == "high"
    assert (
        result.resume_ready_improvements[0].quality_score
        > result.resume_ready_improvements[1].quality_score
    )


@pytest.mark.asyncio
async def test_quality_layer_removes_low_value_positioning_advice() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Created an inventory API backed by PostgreSQL",
    )
    response = SuggestionResponse(
        overall_summary="Remove generic advice.",
        positioning_advice=[
            PositioningAdviceItem(
                target_section="projects",
                advice="Lead projects.",
                reason="Too generic.",
                source_evidence_ids=[evidence_id],
                source_evidence_text=[evidence_text],
                requires_user_review=True,
            ),
            PositioningAdviceItem(
                target_section="projects",
                advice=(
                    "Prioritize the inventory API project because it is the "
                    "strongest backend implementation evidence."
                ),
                reason="Connects a concrete project to target positioning.",
                source_evidence_ids=[evidence_id],
                source_evidence_text=[evidence_text],
                related_requirement_or_direction="Backend Engineering",
                requires_user_review=True,
            ),
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            career_direction_result=career_direction(),
            suggestion_mode="career_direction",
        )
    )

    assert len(result.positioning_advice) == 1
    assert result.positioning_advice[0].quality_level == "high"
    assert any("low-value positioning advice" in warning for warning in result.warnings)


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
    categories = {gap.gap: gap.category for gap in result.evidence_gaps}
    assert categories["Kubernetes"] == "tool_or_platform"
    assert categories["AWS"] == "tool_or_platform"
    assert any(
        advice.related_requirement_or_direction == "Backend Developer"
        for advice in result.positioning_advice
    )
    assert all(advice.source_evidence_text for advice in result.positioning_advice)
    assert any(action.target_gap == "Kubernetes" for action in result.recommended_next_actions)


@pytest.mark.asyncio
async def test_weak_skill_evidence_increases_risk_level() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(bootstrap, candidate, "FastAPI")
    response = SuggestionResponse(
        overall_summary="Group supported skills.",
        resume_ready_improvements=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="Group FastAPI under API development skills.",
                suggestion_type="skill_grouping",
                risk_level="low",
            )
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(candidate_profile=candidate)
    )

    assert result.resume_ready_improvements[0].risk_level == "medium"


@pytest.mark.asyncio
async def test_noop_and_cosmetic_suggestions_are_removed() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Built REST APIs with Python",
    )
    response = SuggestionResponse(
        overall_summary="Improve the resume.",
        resume_ready_improvements=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text=evidence_text,
            ),
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="Use a larger font and cleaner formatting.",
                suggestion_type="experience_emphasis",
            ),
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(candidate_profile=candidate)
    )

    assert result.resume_ready_improvements == []
    assert len(
        [
            warning
            for warning in result.warnings
            if "low-value suggestion" in warning
        ]
    ) == 2


@pytest.mark.asyncio
async def test_resume_ready_text_with_internal_marker_is_removed() -> None:
    candidate = candidate_profile()
    bootstrap = SuggestionService(llm_service=LLMService(api_key=""))
    evidence_id, evidence_text = evidence_for(
        bootstrap,
        candidate,
        "Built REST APIs with Python",
    )
    response = SuggestionResponse(
        overall_summary="Do not leak internal evidence markers.",
        resume_ready_improvements=[
            generated_item(
                evidence_id=evidence_id,
                evidence_text=evidence_text,
                suggested_text="Built REST APIs with Python (E018).",
            )
        ],
    )

    result = await mocked_service(response).generate(
        SuggestionGenerateRequest(candidate_profile=candidate)
    )

    assert result.resume_ready_improvements == []
    assert any("internal evidence marker" in warning for warning in result.warnings)


@pytest.mark.asyncio
async def test_existing_profile_information_is_not_reported_as_missing() -> None:
    candidate = candidate_profile().model_copy(deep=True)
    candidate.projects[0].url = "https://example.com/inventory"
    candidate.improvement_areas = [
        "Add a project link.",
        "Cloud deployment evidence is missing.",
    ]
    candidate.skills[0].skills.append("AWS")
    service = SuggestionService(llm_service=LLMService(api_key=""))

    result = await service.generate(
        SuggestionGenerateRequest(candidate_profile=candidate)
    )

    assert "Add a project link." not in result.missing_but_not_addable
    assert "Cloud deployment evidence is missing." not in (
        result.missing_but_not_addable
    )


@pytest.mark.asyncio
async def test_related_tool_does_not_satisfy_exact_missing_skill() -> None:
    candidate = candidate_profile().model_copy(deep=True)
    candidate.skills[0].skills.append("Docker")
    service = SuggestionService(llm_service=LLMService(api_key=""))

    result = await service.generate(
        SuggestionGenerateRequest(
            candidate_profile=candidate,
            job_profile=job_profile(),
            match_result=match_result(),
            suggestion_mode="job_specific",
        )
    )

    assert "Kubernetes" in result.missing_but_not_addable


@pytest.mark.asyncio
async def test_career_direction_with_no_explicit_gaps_gets_enhancement_gaps() -> None:
    service = SuggestionService(llm_service=LLMService(api_key=""))

    result = await service.generate(
        SuggestionGenerateRequest(
            candidate_profile=finance_candidate_profile(),
            career_direction_result=finance_career_direction(),
            suggestion_mode="career_direction",
        )
    )

    assert result.evidence_gaps
    assert result.missing_but_not_addable
    categories = {gap.category for gap in result.evidence_gaps}
    assert "portfolio_or_proof" in categories
    assert "impact_or_metrics" in categories
    assert all(gap.should_add_to_resume is False for gap in result.evidence_gaps)
    assert all(
        action.should_add_to_resume is False
        for action in result.recommended_next_actions
    )


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
        resume_ready_improvements=[
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

    assert result.resume_ready_improvements == []
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
    assert body["positioning_advice"]
    assert "resume_ready_improvements" in body
    assert all(item["requires_user_review"] for item in body["positioning_advice"])


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
