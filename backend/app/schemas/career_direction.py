from typing import Literal

from pydantic import Field, model_validator

from app.schemas.candidate import CandidateProfile, RoleFamily, SeniorityLevel
from app.schemas.common import APIModel
from app.schemas.match import EvidenceSource

FitType = Literal["primary", "secondary", "transferable", "exploratory"]
ConfidenceLevel = Literal["High", "Medium", "Low"]


class CareerDirectionRequest(APIModel):
    candidate_profile: CandidateProfile


class DirectionEvidence(APIModel):
    source_type: EvidenceSource
    text: str
    evidence_strength: float = Field(ge=0, le=1)
    matched_concepts: list[str] = Field(default_factory=list)


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
