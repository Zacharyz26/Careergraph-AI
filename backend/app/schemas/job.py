from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.candidate import RoleFamily, SeniorityLevel
from app.schemas.common import APIModel, ProcessingState

EmploymentType = Literal[
    "Internship",
    "Full-time",
    "Part-time",
    "Contract",
    "Temporary",
    "Unknown",
]

RemotePolicy = Literal["On-site", "Hybrid", "Remote", "Unknown"]
VisaSponsorship = Literal["Provided", "Not provided"]


class JobEvidenceItem(APIModel):
    value: str
    evidence: list[str] = Field(default_factory=list)


class SalaryInfo(APIModel):
    raw_text: str
    minimum: float | None = Field(default=None, ge=0)
    maximum: float | None = Field(default=None, ge=0)
    currency: str | None = None
    period: str | None = None
    evidence: list[str] = Field(min_length=1)


class JobProfileEvidence(APIModel):
    job_title: list[str] = Field(default_factory=list)
    company_name: list[str] = Field(default_factory=list)
    role_family: list[str] = Field(default_factory=list)
    seniority_level: list[str] = Field(default_factory=list)
    employment_type: list[str] = Field(default_factory=list)
    location: list[str] = Field(default_factory=list)
    remote_policy: list[str] = Field(default_factory=list)
    visa_sponsorship: list[str] = Field(default_factory=list)


class JobProfile(APIModel):
    job_title: str | None = None
    company_name: str | None = None
    role_family: RoleFamily
    seniority_level: SeniorityLevel = "Unknown"
    employment_type: EmploymentType = "Unknown"
    location: str | None = None
    remote_policy: RemotePolicy = "Unknown"
    salary: SalaryInfo | None = None
    visa_sponsorship: VisaSponsorship | None = None
    required_skills: list[JobEvidenceItem] = Field(default_factory=list)
    preferred_skills: list[JobEvidenceItem] = Field(default_factory=list)
    responsibilities: list[JobEvidenceItem] = Field(default_factory=list)
    qualifications: list[JobEvidenceItem] = Field(default_factory=list)
    education_requirements: list[JobEvidenceItem] = Field(default_factory=list)
    experience_requirements: list[JobEvidenceItem] = Field(default_factory=list)
    benefits: list[JobEvidenceItem] = Field(default_factory=list)
    evidence: JobProfileEvidence = Field(default_factory=JobProfileEvidence)


class JobParseRequest(APIModel):
    raw_job_description: str = Field(min_length=1, max_length=100_000)

    @field_validator("raw_job_description")
    @classmethod
    def reject_blank_description(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError(
                "raw_job_description must contain non-whitespace characters"
            )
        return stripped


class JobRequirements(APIModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    seniority: str | None = None
    location: str | None = None


class JobCreate(APIModel):
    raw_description: str = Field(min_length=20)
    title: str | None = None
    company: str | None = None
    source: str = "pasted"


class JobRead(APIModel):
    id: UUID
    user_id: UUID
    title: str | None
    company: str | None
    raw_description: str
    requirements: JobRequirements | None = None
    processing_state: ProcessingState
    created_at: datetime
