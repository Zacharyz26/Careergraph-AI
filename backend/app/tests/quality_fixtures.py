from app.schemas.candidate import (
    CandidateProfile,
    ExperienceItem,
    InferredTargetRole,
    ProjectItem,
    SkillGroup,
)


def inferred_roles(
    role_family: str,
    roles: tuple[str, str, str],
) -> list[InferredTargetRole]:
    return [
        InferredTargetRole(
            role=role,
            role_family=role_family,
            seniority_level="Entry-level",
            confidence=confidence,
            rationale="Supported by profile evidence.",
            evidence=[f"Evidence supports {role}"],
        )
        for role, confidence in zip(roles, (0.9, 0.82, 0.74), strict=True)
    ]


def finance_profile() -> CandidateProfile:
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
                organization="Student Investment Fund",
                title="Equity Research Analyst",
                bullets=["Built DCF models and presented investment views"],
                evidence=["Built DCF models and presented investment views"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Finance / Accounting",
            ("Investment Analyst", "Financial Analyst", "Equity Research Analyst"),
        ),
    )


def marketing_profile() -> CandidateProfile:
    return CandidateProfile(
        skills=[
            SkillGroup(
                category="Marketing",
                skills=["SEO", "Content marketing", "Campaign analytics"],
                evidence=["SEO, content marketing, campaign analytics"],
            )
        ],
        projects=[
            ProjectItem(
                name="Campus campaign",
                bullets=["Planned a social media campaign for a student event"],
                evidence=["Planned a social media campaign for a student event"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Marketing",
            ("Marketing Coordinator", "Digital Marketing Specialist", "Campaign Assistant"),
        ),
    )


def healthcare_profile() -> CandidateProfile:
    return CandidateProfile(
        skills=[
            SkillGroup(
                category="Healthcare",
                skills=["Patient communication", "Clinical documentation"],
                evidence=["Patient communication and clinical documentation"],
            )
        ],
        experience=[
            ExperienceItem(
                organization="Community Clinic",
                title="Volunteer",
                bullets=["Supported patient intake and organized clinic records"],
                evidence=["Supported patient intake and organized clinic records"],
            )
        ],
        inferred_target_roles=inferred_roles(
            "Healthcare",
            ("Clinical Coordinator", "Healthcare Operations Associate", "Patient Care Assistant"),
        ),
    )
