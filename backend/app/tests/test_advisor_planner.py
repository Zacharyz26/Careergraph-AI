from app.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    InferredTargetRole,
    ProjectItem,
    SkillGroup,
)
from app.services.advisor_planner import AdvisorPlanner
from app.services.evidence_ledger import EvidenceLedger


def finance_profile_without_artifacts_or_metrics() -> CandidateProfile:
    return CandidateProfile(
        skills=[
            SkillGroup(
                category="Finance",
                skills=["Financial modeling", "Valuation", "Excel"],
                evidence=["Financial modeling, valuation, Excel"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Student Fund",
                title="Research Analyst",
                bullets=["Researched companies and discussed investment views"],
                evidence=["Researched companies and discussed investment views"],
            )
        ],
        projects=[
            ProjectItem(
                name="DCF analysis",
                technologies=["Excel"],
                bullets=["Built a DCF analysis for a public company"],
                evidence=["Built a DCF analysis for a public company"],
            )
        ],
        inferred_target_roles=[
            InferredTargetRole(
                role=role,
                role_family="Finance / Accounting",
                seniority_level="Entry-level",
                confidence=confidence,
                rationale="Supported by finance evidence.",
                evidence=["Built a DCF analysis for a public company"],
            )
            for role, confidence in (
                ("Investment Analyst", 0.9),
                ("Financial Analyst", 0.82),
                ("Equity Research Analyst", 0.78),
            )
        ],
    )


def test_advisor_planner_classifies_strong_and_missing_finance_proof() -> None:
    summary = EvidenceLedger.from_candidate(
        finance_profile_without_artifacts_or_metrics()
    ).summary

    plan = AdvisorPlanner().plan(summary, "Finance / Accounting")

    assert plan.strong_proof
    missing_labels = {
        *[gap.label for gap in plan.missing_proof],
        *[gap.label for gap in plan.optional_enhancements],
    }
    assert any("memo" in label.casefold() or "sample" in label.casefold() for label in missing_labels)
    assert any("metrics" in label.casefold() for label in missing_labels)
