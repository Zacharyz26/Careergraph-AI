from typing import Literal

from pydantic import Field, model_validator

from app.schemas.candidate import CandidateProfile, RoleFamily, SeniorityLevel
from app.schemas.common import APIModel
CareerEvidenceSource = Literal[
    "education",
    "skills",
    "work",
    "project",
    "paper",
    "patent",
    "certification",
    "leadership",
    "language",
]

FitType = Literal["primary", "secondary", "transferable", "exploratory"]
ConfidenceLevel = Literal["High", "Medium", "Low"]


class CareerDirectionRequest(APIModel):
    candidate_profile: CandidateProfile


class DirectionEvidence(APIModel):
    evidence_id: str
    source_type: CareerEvidenceSource
    text: str
    evidence_strength: float = Field(ge=0, le=1)
    matched_concepts: list[str] = Field(default_factory=list)


class CareerEvidenceItem(APIModel):
    evidence_id: str
    source_type: CareerEvidenceSource
    text: str
    evidence_strength: float = Field(ge=0, le=1)
    normalized_concepts: list[str] = Field(default_factory=list)


class CandidateEvidenceSummary(APIModel):
    education_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    skill_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    work_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    project_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    paper_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    patent_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    certification_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    leadership_signals: list[CareerEvidenceItem] = Field(default_factory=list)
    language_signals: list[CareerEvidenceItem] = Field(default_factory=list)

    def all_evidence(self) -> list[CareerEvidenceItem]:
        return [
            *self.education_signals,
            *self.skill_signals,
            *self.work_signals,
            *self.project_signals,
            *self.paper_signals,
            *self.patent_signals,
            *self.certification_signals,
            *self.leadership_signals,
            *self.language_signals,
        ]


class ProposedCareerDirection(APIModel):
    direction: str
    role_family: RoleFamily
    likely_seniority_level: SeniorityLevel
    proposed_fit_type: FitType
    rationale: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    possible_gaps: list[str] = Field(default_factory=list)
    example_job_titles: list[str] = Field(default_factory=list)


class CareerDirectionProposalSet(APIModel):
    directions: list[ProposedCareerDirection] = Field(
        min_length=8,
        max_length=12,
    )


class CareerDirectionRecommendation(APIModel):
    rank: int = Field(ge=1, le=5)
    direction: str
    role_family: RoleFamily
    seniority_level: SeniorityLevel
    fit_type: FitType
    score_range_low: int = Field(ge=0, le=100)
    score_range_high: int = Field(ge=0, le=100)
    score_midpoint: int = Field(ge=0, le=100)
    confidence_level: ConfidenceLevel
    matched_evidence: list[DirectionEvidence] = Field(default_factory=list)
    strengths_for_this_direction: list[str] = Field(default_factory=list)
    gaps_for_this_direction: list[str] = Field(default_factory=list)
    resume_positioning_advice: list[str] = Field(default_factory=list)
    example_job_titles: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_score_range(self) -> "CareerDirectionRecommendation":
        if not self.score_range_low <= self.score_midpoint <= self.score_range_high:
            raise ValueError("score_midpoint must be inside the score range")
        return self


class CareerDirectionResponse(APIModel):
    directions: list[CareerDirectionRecommendation] = Field(
        default_factory=list,
        max_length=5,
    )
