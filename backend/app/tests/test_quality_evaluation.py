import pytest

from app.schemas.suggestion import SuggestionGenerateRequest
from app.services.career_direction_proposal_service import (
    CareerDirectionProposalService,
)
from app.services.career_direction_service import CareerDirectionService
from app.services.llm_service import LLMService
from app.services.suggestion_service import SuggestionService
from app.services.user_facing_sanitizer import has_user_facing_artifact
from app.tests.quality_fixtures import (
    finance_profile,
    healthcare_profile,
    marketing_profile,
)


def fallback_direction_service() -> CareerDirectionService:
    return CareerDirectionService(
        proposal_service=CareerDirectionProposalService(
            LLMService(api_key=""),
            enabled=False,
        )
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("profile_factory", "expected_family"),
    [
        (finance_profile, "Finance / Accounting"),
        (marketing_profile, "Marketing"),
        (healthcare_profile, "Healthcare"),
    ],
)
async def test_direction_quality_is_domain_relevant(
    profile_factory,
    expected_family: str,
) -> None:
    result = await fallback_direction_service().recommend(profile_factory())

    assert result.directions
    assert result.directions[0].role_family == expected_family
    assert result.directions[0].matched_evidence
    assert result.directions[0].gaps_for_this_direction


@pytest.mark.asyncio
@pytest.mark.parametrize("profile_factory", [finance_profile, marketing_profile])
async def test_advisor_quality_has_useful_gaps_without_artifacts(profile_factory) -> None:
    profile = profile_factory()
    direction = (await fallback_direction_service().recommend(profile)).directions[0]

    result = await SuggestionService(
        llm_service=LLMService(api_key="")
    ).generate(
        SuggestionGenerateRequest(
            candidate_profile=profile,
            career_direction_result=direction,
            suggestion_mode="career_direction",
        )
    )
    user_facing_text = " ".join(
        [
            result.overall_summary,
            *[item.advice for item in result.positioning_advice],
            *[item.suggested_text for item in result.resume_ready_improvements],
            *[gap.gap for gap in result.evidence_gaps],
            *[action.action for action in result.recommended_next_actions],
        ]
    )

    assert result.positioning_advice
    assert result.evidence_gaps
    assert result.recommended_next_actions
    assert not has_user_facing_artifact(user_facing_text)
    assert any(gap.priority in {"high", "medium"} for gap in result.evidence_gaps)
