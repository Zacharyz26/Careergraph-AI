from dataclasses import dataclass

from app.schemas.candidate import RoleFamily
from app.schemas.career_direction import CandidateEvidenceSummary, CareerEvidenceItem
from app.services.matching_taxonomy import extract_concepts


STRONG_PROOF_SOURCES = {"work", "project", "paper", "patent"}


@dataclass(frozen=True)
class CapabilitySignal:
    label: str
    category: str
    keywords: tuple[str, ...]
    concepts: tuple[str, ...] = ()
    required_for_strong_fit: bool = False


@dataclass(frozen=True)
class CapabilityProfile:
    role_family: RoleFamily
    signals: tuple[CapabilitySignal, ...]

    def expected_gaps(self) -> list[str]:
        return [signal.label for signal in self.signals]


@dataclass(frozen=True)
class CapabilityAssessment:
    signal: CapabilitySignal
    status: str
    priority: str
    matched_evidence: tuple[CareerEvidenceItem, ...] = ()

    @property
    def gap_label(self) -> str:
        return self.signal.label


CAPABILITY_PROFILES: dict[RoleFamily, CapabilityProfile] = {
    "Software Engineering": CapabilityProfile(
        "Software Engineering",
        (
            CapabilitySignal("Implementation evidence from work or projects", "implementation_or_delivery", ("build", "develop", "implemented", "project"), required_for_strong_fit=True),
            CapabilitySignal("Production, deployment, testing, or reliability evidence", "implementation_or_delivery", ("deploy", "production", "test", "reliability", "docker", "kubernetes")),
            CapabilitySignal("Repository, demo, or technical artifact links", "portfolio_or_proof", ("github", "repository", "demo", "portfolio", "link")),
            CapabilitySignal("Impact, usage, performance, or quality metrics", "impact_or_metrics", ("performance", "latency", "users", "quality", "reduced", "improved")),
        ),
    ),
    "AI / Machine Learning": CapabilityProfile(
        "AI / Machine Learning",
        (
            CapabilitySignal("Modeling, experimentation, or evaluation evidence", "implementation_or_delivery", ("model", "experiment", "evaluation", "accuracy", "validation"), ("machine_learning", "model_evaluation"), True),
            CapabilitySignal("Python, ML framework, or data tooling evidence", "tool_or_platform", ("python", "pytorch", "tensorflow", "scikit", "sql")),
            CapabilitySignal("Deployment, API integration, or serving evidence", "implementation_or_delivery", ("deploy", "api", "serving", "cloud", "docker")),
            CapabilitySignal("Notebook, demo, GitHub, paper, or portfolio proof", "portfolio_or_proof", ("github", "notebook", "demo", "paper", "portfolio")),
        ),
    ),
    "Data / Analytics": CapabilityProfile(
        "Data / Analytics",
        (
            CapabilitySignal("Analysis, statistics, or decision-support evidence", "implementation_or_delivery", ("analysis", "statistics", "insight", "forecast"), ("data_analysis", "statistics"), True),
            CapabilitySignal("SQL, Python, Excel, BI, or dashboard tooling evidence", "tool_or_platform", ("sql", "python", "excel", "tableau", "power bi", "dashboard")),
            CapabilitySignal("Dashboard, notebook, report, or case-study artifact", "portfolio_or_proof", ("dashboard", "notebook", "report", "case study", "portfolio")),
            CapabilitySignal("Business impact, accuracy, lift, or decision outcome metrics", "impact_or_metrics", ("impact", "accuracy", "lift", "revenue", "cost", "decision")),
        ),
    ),
    "Finance / Accounting": CapabilityProfile(
        "Finance / Accounting",
        (
            CapabilitySignal("Financial modeling, valuation, accounting, or risk evidence", "implementation_or_delivery", ("model", "valuation", "accounting", "risk", "forecast"), ("financial_modeling", "valuation", "accounting", "risk_analysis"), True),
            CapabilitySignal("Excel, Python, SQL, BI, Bloomberg, or accounting-system tooling evidence", "tool_or_platform", ("excel", "python", "sql", "tableau", "power bi", "bloomberg", "erp")),
            CapabilitySignal("Investment memo, research note, audit workpaper, deck, or analysis sample", "portfolio_or_proof", ("memo", "research note", "deck", "workpaper", "sample", "presentation")),
            CapabilitySignal("Impact, return, risk, forecast accuracy, savings, or controls metrics", "impact_or_metrics", ("return", "risk", "accuracy", "savings", "controls", "impact")),
        ),
    ),
    "Marketing": CapabilityProfile(
        "Marketing",
        (
            CapabilitySignal("Campaign, content, growth, or market research evidence", "implementation_or_delivery", ("campaign", "content", "growth", "market research"), ("campaign_management", "content_marketing"), True),
            CapabilitySignal("Analytics, CRM, SEO, paid media, or experimentation tooling evidence", "tool_or_platform", ("analytics", "crm", "seo", "paid", "experiment", "hubspot", "salesforce")),
            CapabilitySignal("Portfolio, campaign sample, landing page, or case study", "portfolio_or_proof", ("portfolio", "sample", "landing page", "case study", "link")),
            CapabilitySignal("Conversion, reach, engagement, pipeline, retention, or revenue metrics", "impact_or_metrics", ("conversion", "reach", "engagement", "pipeline", "retention", "revenue")),
        ),
    ),
    "Healthcare": CapabilityProfile(
        "Healthcare",
        (
            CapabilitySignal("Clinical, patient, operational, or healthcare data evidence", "domain_experience", ("clinical", "patient", "healthcare", "medical"), ("patient_care", "clinical_operations", "healthcare_data"), True),
            CapabilitySignal("Required license, certification, training, or compliance evidence", "credential_or_education", ("license", "certification", "training", "compliance")),
            CapabilitySignal("Protocol, documentation, case, research, or quality artifact", "portfolio_or_proof", ("protocol", "documentation", "case", "research", "quality")),
            CapabilitySignal("Patient, safety, quality, efficiency, or outcome metrics", "impact_or_metrics", ("patient", "safety", "quality", "efficiency", "outcome")),
        ),
    ),
    "Business / Operations": CapabilityProfile(
        "Business / Operations",
        (
            CapabilitySignal("Process, project, logistics, or program delivery evidence", "implementation_or_delivery", ("process", "project", "operations", "logistics", "program"), ("process_improvement", "logistics"), True),
            CapabilitySignal("Spreadsheet, dashboard, ERP, automation, or analytics tooling evidence", "tool_or_platform", ("excel", "dashboard", "erp", "automation", "analytics")),
            CapabilitySignal("SOP, project plan, workflow, dashboard, or implementation artifact", "portfolio_or_proof", ("sop", "project plan", "workflow", "dashboard", "artifact")),
            CapabilitySignal("Cost, cycle-time, throughput, quality, or efficiency metrics", "impact_or_metrics", ("cost", "cycle", "throughput", "quality", "efficiency")),
        ),
    ),
    "Education": CapabilityProfile(
        "Education",
        (
            CapabilitySignal("Teaching, tutoring, curriculum, or learner-support evidence", "implementation_or_delivery", ("teaching", "tutoring", "curriculum", "student"), ("teaching", "tutoring", "curriculum"), True),
            CapabilitySignal("Lesson plan, curriculum, assessment, or learning artifact", "portfolio_or_proof", ("lesson", "curriculum", "assessment", "artifact")),
            CapabilitySignal("Classroom, LMS, assessment, or education technology evidence", "tool_or_platform", ("classroom", "lms", "assessment", "technology")),
            CapabilitySignal("Learner outcome, engagement, completion, or improvement metrics", "impact_or_metrics", ("outcome", "engagement", "completion", "improvement")),
        ),
    ),
    "Human Resources": CapabilityProfile(
        "Human Resources",
        (
            CapabilitySignal("Recruiting, onboarding, employee relations, or people-program evidence", "implementation_or_delivery", ("recruiting", "onboarding", "employee", "people"), ("recruiting", "onboarding"), True),
            CapabilitySignal("ATS, HRIS, analytics, survey, or compensation tooling evidence", "tool_or_platform", ("ats", "hris", "analytics", "survey", "compensation")),
            CapabilitySignal("Program material, playbook, training, or policy artifact", "portfolio_or_proof", ("playbook", "training", "policy", "program material")),
            CapabilitySignal("Hiring, retention, engagement, time-to-fill, or process metrics", "impact_or_metrics", ("hiring", "retention", "engagement", "time-to-fill", "process")),
        ),
    ),
    "Legal / Compliance": CapabilityProfile(
        "Legal / Compliance",
        (
            CapabilitySignal("Legal, compliance, regulatory, contract, or policy evidence", "domain_experience", ("legal", "compliance", "regulatory", "contract", "policy"), ("compliance", "contracts", "policy"), True),
            CapabilitySignal("Research memo, brief, contract review, policy, or audit artifact", "portfolio_or_proof", ("memo", "brief", "contract", "policy", "audit")),
            CapabilitySignal("Stakeholder, client, negotiation, or review-process evidence", "communication_or_positioning", ("stakeholder", "client", "negotiation", "review")),
            CapabilitySignal("Risk reduction, accuracy, cycle-time, or matter outcome metrics", "impact_or_metrics", ("risk", "accuracy", "cycle", "outcome")),
        ),
    ),
    "Product": CapabilityProfile(
        "Product",
        (
            CapabilitySignal("User, market, roadmap, launch, or requirements evidence", "implementation_or_delivery", ("user", "market", "roadmap", "launch", "requirements"), ("user_research", "roadmapping", "product_strategy"), True),
            CapabilitySignal("Analytics, experimentation, prioritization, or research tooling evidence", "tool_or_platform", ("analytics", "experiment", "prioritization", "research")),
            CapabilitySignal("PRD, prototype, case study, roadmap, or portfolio artifact", "portfolio_or_proof", ("prd", "prototype", "case study", "roadmap", "portfolio")),
            CapabilitySignal("Adoption, retention, conversion, revenue, or usage metrics", "impact_or_metrics", ("adoption", "retention", "conversion", "revenue", "usage")),
        ),
    ),
    "Design": CapabilityProfile(
        "Design",
        (
            CapabilitySignal("UX, UI, research, prototype, or visual design evidence", "implementation_or_delivery", ("ux", "ui", "research", "prototype", "visual"), ("ui_ux", "prototyping"), True),
            CapabilitySignal("Figma, prototyping, design-system, or handoff tooling evidence", "tool_or_platform", ("figma", "prototype", "design system", "handoff")),
            CapabilitySignal("Portfolio, case study, prototype, or design artifact links", "portfolio_or_proof", ("portfolio", "case study", "prototype", "link")),
            CapabilitySignal("User, accessibility, conversion, adoption, or usability metrics", "impact_or_metrics", ("user", "accessibility", "conversion", "adoption", "usability")),
        ),
    ),
}


def capability_profile_for(role_family: RoleFamily | str | None) -> CapabilityProfile:
    if role_family in CAPABILITY_PROFILES:
        return CAPABILITY_PROFILES[role_family]  # type: ignore[index]
    return CapabilityProfile(
        "Other",
        (
            CapabilitySignal("Target-relevant delivery evidence", "implementation_or_delivery", ("project", "work", "delivered", "built"), required_for_strong_fit=True),
            CapabilitySignal("Target-relevant tools, platforms, or methods", "tool_or_platform", ("tool", "platform", "method")),
            CapabilitySignal("Portfolio, work sample, case study, or artifact evidence", "portfolio_or_proof", ("portfolio", "sample", "case study", "artifact")),
            CapabilitySignal("Impact, quality, scale, or outcome metrics", "impact_or_metrics", ("impact", "quality", "scale", "outcome")),
        ),
    )


def assess_capabilities(
    summary: CandidateEvidenceSummary,
    role_family: RoleFamily | str | None,
) -> list[CapabilityAssessment]:
    profile = capability_profile_for(role_family)
    evidence = summary.all_evidence()
    return [
        _assess_signal(signal, evidence)
        for signal in profile.signals
    ]


def readiness_score(assessments: list[CapabilityAssessment]) -> float:
    if not assessments:
        return 0
    points = {
        "strong_proof": 1.0,
        "weak_proof": 0.55,
        "optional_enhancement": 0.25,
        "missing_proof": 0,
    }
    return sum(points[item.status] for item in assessments) / len(assessments)


def _assess_signal(
    signal: CapabilitySignal,
    evidence: list[CareerEvidenceItem],
) -> CapabilityAssessment:
    matched = tuple(
        item
        for item in evidence
        if _signal_matches_evidence(signal, item)
    )
    if matched:
        if any(
            item.source_type in STRONG_PROOF_SOURCES
            and item.evidence_strength >= 0.85
            for item in matched
        ):
            return CapabilityAssessment(signal, "strong_proof", "high", matched)
        return CapabilityAssessment(signal, "weak_proof", "medium", matched)
    if signal.required_for_strong_fit:
        return CapabilityAssessment(signal, "missing_proof", "high")
    return CapabilityAssessment(signal, "optional_enhancement", "medium")


def _signal_matches_evidence(
    signal: CapabilitySignal,
    evidence: CareerEvidenceItem,
) -> bool:
    normalized = _normalize(evidence.text)
    if any(_phrase_present(keyword, normalized) for keyword in signal.keywords):
        return True
    evidence_concepts = set(evidence.normalized_concepts) | set(extract_concepts(normalized))
    return bool(set(signal.concepts) & evidence_concepts)


def _phrase_present(phrase: str, text: str) -> bool:
    return f" {phrase.casefold()} " in f" {text} "


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("&", " and ").split())
