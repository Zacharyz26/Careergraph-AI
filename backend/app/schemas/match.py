from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.candidate import CandidateProfile
from app.schemas.common import APIModel, ProcessingState
from app.schemas.job import JobProfile


class MatchCreate(APIModel):
    resume_id: UUID
    job_id: UUID


class MatchEvidence(APIModel):
    requirement: str
    source_fact_id: str
    explanation: str | None = None


class MatchComponentScores(APIModel):
    skill_keyword_coverage: float = Field(ge=0, le=100)
    semantic_similarity: float = Field(ge=0, le=100)
    experience_relevance: float = Field(ge=0, le=100)
    project_relevance: float = Field(ge=0, le=100)
    education_fit: float = Field(ge=0, le=100)
    preference_fit: float = Field(ge=0, le=100)


class MatchRead(APIModel):
    id: UUID
    resume_id: UUID
    job_id: UUID
    state: ProcessingState
    final_score: float | None = Field(default=None, ge=0, le=100)
    component_scores: MatchComponentScores | None = None
    matched_evidence: list[MatchEvidence] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    created_at: datetime


class MatchScoreRequest(APIModel):
    candidate_profile: CandidateProfile
    job_profile: JobProfile


EvidenceSource = Literal[
    "skills",
    "experience",
    "projects",
    "papers",
    "patents",
    "education",
    "certifications",
    "languages",
]

RequirementType = Literal[
    "required_skill",
    "preferred_skill",
    "responsibility",
    "qualification",
    "education_requirement",
    "experience_requirement",
]

RequirementStatus = Literal[
    "full_match",
    "partial_match",
    "transferable_match",
    "missing",
]


class RequirementEvidence(APIModel):
    source_type: EvidenceSource
    text: str
    evidence_strength: float = Field(ge=0, le=1)
    normalized_concepts: list[str] = Field(default_factory=list)


class RequirementMatch(APIModel):
    requirement_type: RequirementType
    importance: float = Field(ge=0, le=1)
    requirement: str
    match_status: RequirementStatus
    match_strength: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    similarity_score: float | None = Field(default=None, ge=-1, le=1)
    evaluation_method: Literal[
        "deterministic",
        "semantic",
        "llm_judge",
    ] = "deterministic"
    candidate_evidence: list[RequirementEvidence] = Field(default_factory=list)
    reason: str


class EvidenceJudgeResult(APIModel):
    match_status: RequirementStatus
    confidence: float = Field(ge=0, le=1)
    reason: str
    supported_evidence: list[str] = Field(default_factory=list)


class ScoredMatchEvidence(APIModel):
    requirement: str
    candidate_source: Literal[
        "skills",
        "experience",
        "projects",
        "papers",
        "patents",
        "education",
        "certifications",
        "languages",
    ]
    candidate_evidence: list[str] = Field(min_length=1)
    match_strength: Literal["full", "partial", "transferable"]


class MatchResult(APIModel):
    final_score: int = Field(ge=0, le=100)
    required_coverage_score: int = Field(ge=0, le=100)
    preferred_coverage_score: int = Field(ge=0, le=100)
    responsibility_alignment_score: int = Field(ge=0, le=100)
    education_fit_score: int = Field(ge=0, le=100)
    seniority_fit_score: int = Field(ge=0, le=100)
    evidence_strength_score: int = Field(ge=0, le=100)
    risk_penalty: int = Field(ge=0, le=100)
    requirement_matches: list[RequirementMatch] = Field(default_factory=list)
    matched_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    transferable_matches: list[str] = Field(default_factory=list)
    matched_evidence: list[ScoredMatchEvidence] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: Literal[
        "Strong match",
        "Good match after tailoring",
        "Partial match",
        "Low match",
    ]
    explanation: str
