from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import APIModel

RoleFamily = Literal[
    "Software Engineering",
    "AI / Machine Learning",
    "Data / Analytics",
    "Product",
    "Design",
    "Marketing",
    "Finance / Accounting",
    "Business / Operations",
    "Healthcare",
    "Research",
    "Education",
    "Engineering",
    "Sales / Customer Success",
    "Human Resources",
    "Legal / Compliance",
    "General Internship",
    "Other",
]

SeniorityLevel = Literal[
    "Internship",
    "Entry-level",
    "Junior",
    "Mid-level",
    "Senior",
    "Leadership",
    "Unknown",
]


class BasicInfo(APIModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    headline: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str | None) -> str | None:
        if value is not None and "@" not in value:
            raise ValueError("email must look like an email address")
        return value


class EducationItem(APIModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    graduation_date: str | None = None
    details: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class SkillGroup(APIModel):
    category: str
    skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ExperienceItem(APIModel):
    organization: str
    title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ProjectItem(APIModel):
    name: str
    description: str | None = None
    role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    url: str | None = None
    evidence: list[str] = Field(default_factory=list)


class PatentItem(APIModel):
    title: str
    patent_number: str | None = None
    status: str | None = None
    filing_date: str | None = None
    issue_date: str | None = None
    inventors: list[str] = Field(default_factory=list)
    description: str | None = None
    evidence: list[str] = Field(default_factory=list)


class PaperItem(APIModel):
    title: str
    publication: str | None = None
    publication_date: str | None = None
    authors: list[str] = Field(default_factory=list)
    description: str | None = None
    topics: list[str] = Field(default_factory=list)
    url: str | None = None
    evidence: list[str] = Field(default_factory=list)


class CertificationItem(APIModel):
    name: str
    issuer: str | None = None
    issue_date: str | None = None
    expiration_date: str | None = None
    credential_id: str | None = None
    evidence: list[str] = Field(default_factory=list)


class LanguageItem(APIModel):
    language: str
    proficiency: str | None = None
    evidence: list[str] = Field(default_factory=list)


class InferredTargetRole(APIModel):
    role: str
    role_family: RoleFamily
    seniority_level: SeniorityLevel
    confidence: float = Field(ge=0, le=1)
    rationale: str
    is_inferred: Literal[True] = True
    evidence: list[str] = Field(min_length=1)


class CandidateProfile(APIModel):
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    papers: list[PaperItem] = Field(default_factory=list)
    patents: list[PatentItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    inferred_target_roles: list[InferredTargetRole] = Field(
        default_factory=list,
        min_length=3,
        max_length=6,
    )
