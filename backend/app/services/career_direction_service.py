import re
from dataclasses import dataclass

from app.schemas.candidate import CandidateProfile, RoleFamily, SeniorityLevel
from app.schemas.career_direction import (
    CareerDirectionRecommendation,
    CareerDirectionResponse,
    DirectionEvidence,
)
from app.services.matching_service import (
    CandidateEvidenceItem,
    MatchingService,
)


@dataclass(frozen=True)
class DirectionDefinition:
    direction: str
    role_family: RoleFamily
    concepts: frozenset[str]
    keywords: frozenset[str]
    example_titles: tuple[str, ...]


def direction(
    name: str,
    family: RoleFamily,
    concepts: set[str],
    keywords: set[str],
    titles: tuple[str, ...],
) -> DirectionDefinition:
    return DirectionDefinition(
        direction=name,
        role_family=family,
        concepts=frozenset(concepts),
        keywords=frozenset(keywords),
        example_titles=titles,
    )


DIRECTION_CATALOG = (
    direction("Backend Engineering", "Software Engineering", {"api_development", "backend_development", "databases"}, {"python", "java", "c#", "node", "fastapi", "django", "spring"}, ("Backend Developer", "API Developer", "Software Engineer")),
    direction("Frontend Engineering", "Software Engineering", {"frontend_development", "software_testing"}, {"javascript", "typescript", "html", "css", "react", "angular", "vue"}, ("Frontend Developer", "UI Engineer", "Web Developer")),
    direction("DevOps and Cloud Engineering", "Software Engineering", {"devops", "cloud"}, {"docker", "kubernetes", "terraform", "aws", "azure", "gcp", "ci cd"}, ("DevOps Engineer", "Cloud Engineer", "Platform Engineer")),
    direction("Machine Learning Engineering", "AI / Machine Learning", {"machine_learning", "deep_learning", "model_evaluation", "pytorch", "tensorflow"}, {"python", "scikit learn", "pytorch", "tensorflow"}, ("Machine Learning Engineer", "Applied ML Engineer", "ML Intern")),
    direction("NLP and Language AI", "AI / Machine Learning", {"machine_learning", "nlp", "model_evaluation"}, {"python", "transformers", "language model", "nlp"}, ("NLP Engineer", "Applied AI Engineer", "Language AI Intern")),
    direction("Data Analytics", "Data / Analytics", {"data_analysis", "sql", "statistics", "dashboards", "data_visualization"}, {"sql", "excel", "tableau", "power bi", "python", "r"}, ("Data Analyst", "Reporting Analyst", "Analytics Associate")),
    direction("Business Intelligence", "Data / Analytics", {"sql", "dashboards", "data_visualization", "data_analysis"}, {"tableau", "power bi", "looker", "excel"}, ("Business Intelligence Analyst", "BI Developer", "Reporting Analyst")),
    direction("Product Management", "Product", {"product_strategy", "roadmapping", "product_metrics", "user_research", "experimentation"}, {"product", "roadmap", "kpi", "a b testing"}, ("Associate Product Manager", "Product Analyst", "Product Manager")),
    direction("UX and Product Design", "Design", {"ui_ux", "prototyping", "figma", "user_research"}, {"figma", "wireframe", "prototype", "design"}, ("UX Designer", "Product Designer", "UX Research Assistant")),
    direction("Digital Marketing", "Marketing", {"seo", "content_marketing", "social_media", "campaign_management", "marketing_analytics"}, {"seo", "campaign", "social media", "content"}, ("Marketing Coordinator", "Digital Marketing Specialist", "Campaign Assistant")),
    direction("Financial Analysis", "Finance / Accounting", {"financial_modeling", "budgeting", "valuation", "risk_analysis", "excel"}, {"finance", "forecast", "variance", "excel"}, ("Financial Analyst", "FP&A Analyst", "Finance Associate")),
    direction("Accounting and Audit", "Finance / Accounting", {"accounting", "auditing", "risk_controls", "compliance"}, {"gaap", "ifrs", "ledger", "reconciliation", "cpa"}, ("Staff Accountant", "Audit Associate", "Accounting Analyst")),
    direction("Business Operations", "Business / Operations", {"process_improvement", "stakeholder_coordination", "budgeting", "data_analysis"}, {"operations", "process", "vendor", "schedule"}, ("Operations Coordinator", "Business Operations Analyst", "Program Coordinator")),
    direction("Supply Chain and Logistics", "Business / Operations", {"logistics", "process_improvement", "stakeholder_coordination"}, {"inventory", "procurement", "warehouse", "supply chain"}, ("Supply Chain Analyst", "Logistics Coordinator", "Procurement Assistant")),
    direction("Clinical and Patient Operations", "Healthcare", {"patient_care", "clinical_operations", "medical_terminology"}, {"patient", "clinical", "medical", "nursing"}, ("Clinical Coordinator", "Patient Care Assistant", "Healthcare Operations Associate")),
    direction("Healthcare Analytics", "Healthcare", {"healthcare_data", "data_analysis", "statistics"}, {"clinical data", "health data", "sql", "statistics"}, ("Healthcare Data Analyst", "Clinical Data Coordinator", "Health Informatics Analyst")),
    direction("Research and Analysis", "Research", {"literature_review", "experimental_design", "publications", "statistics"}, {"research", "publication", "study", "experiment"}, ("Research Assistant", "Research Analyst", "Lab Coordinator")),
    direction("Teaching and Learning Support", "Education", {"teaching", "curriculum", "tutoring", "classroom_management"}, {"teaching", "lesson", "student", "curriculum"}, ("Teaching Assistant", "Tutor", "Education Program Assistant")),
    direction("Engineering Design and Analysis", "Engineering", {"experimental_design", "process_improvement"}, {"cad", "solidworks", "matlab", "simulation", "engineering"}, ("Junior Engineer", "Design Engineer", "Engineering Analyst")),
    direction("Sales and Account Development", "Sales / Customer Success", {"crm", "client_communication", "account_management"}, {"sales", "crm", "pipeline", "prospect"}, ("Sales Development Representative", "Account Coordinator", "Sales Associate")),
    direction("Customer Success and Support", "Sales / Customer Success", {"customer_support", "client_communication", "account_management"}, {"customer", "support", "client", "onboarding"}, ("Customer Success Associate", "Support Specialist", "Client Services Coordinator")),
    direction("Talent Acquisition and HR", "Human Resources", {"recruiting", "onboarding", "employee_relations"}, {"recruiting", "candidate", "human resources", "hr"}, ("HR Coordinator", "Recruiting Coordinator", "People Operations Assistant")),
    direction("Compliance and Risk", "Legal / Compliance", {"compliance", "risk_controls", "policy", "auditing"}, {"compliance", "regulatory", "governance", "controls"}, ("Compliance Analyst", "Risk and Controls Analyst", "Regulatory Associate")),
    direction("Contracts and Legal Operations", "Legal / Compliance", {"contracts", "policy", "compliance"}, {"contract", "legal", "policy"}, ("Legal Operations Coordinator", "Contracts Administrator", "Legal Assistant")),
    direction("General Internship Pathways", "General Internship", set(), {"intern", "internship", "student", "coursework"}, ("General Intern", "Program Intern", "Rotational Intern")),
    direction("General Professional Support", "Other", {"stakeholder_coordination"}, {"documentation", "coordination", "administration", "communication"}, ("Administrative Coordinator", "Program Assistant", "Project Assistant")),
)


@dataclass(frozen=True)
class ScoredDirection:
    definition: DirectionDefinition
    score: float
    skill_score: float
    experience_score: float
    artifact_score: float
    education_score: float
    seniority_score: float
    evidence_score: float
    evidence: tuple[tuple[CandidateEvidenceItem, frozenset[str]], ...]
    missing_signals: tuple[str, ...]


class CareerDirectionService:
    def __init__(self, matching_service: MatchingService | None = None) -> None:
        self.matching_service = matching_service or MatchingService()

    def recommend(self, candidate: CandidateProfile) -> CareerDirectionResponse:
        evidence_index = self.matching_service.build_candidate_evidence_index(
            candidate
        )
        if not evidence_index:
            return CareerDirectionResponse()

        scored = [
            result
            for definition in DIRECTION_CATALOG
            if (result := self._score_direction(candidate, evidence_index, definition))
            and result.score >= 18
        ]
        scored.sort(
            key=lambda item: (
                item.score,
                item.evidence_score,
                item.experience_score,
            ),
            reverse=True,
        )

        selected = scored[:5]
        return CareerDirectionResponse(
            directions=[
                self._to_recommendation(item, rank, selected, candidate)
                for rank, item in enumerate(selected, start=1)
            ]
        )

    def _score_direction(
        self,
        candidate: CandidateProfile,
        evidence_index: list[CandidateEvidenceItem],
        definition: DirectionDefinition,
    ) -> ScoredDirection | None:
        matched = []
        for item in evidence_index:
            concepts = item.normalized_concepts & definition.concepts
            keyword_matches = {
                keyword
                for keyword in definition.keywords
                if self._phrase_present(keyword, item.text)
            }
            signals = frozenset((*concepts, *keyword_matches))
            if signals:
                matched.append((item, signals))

        inferred = [
            role
            for role in candidate.inferred_target_roles
            if role.role_family == definition.role_family
        ]
        if not matched and not inferred:
            return None

        skill_score = self._source_score(matched, {"skills"})
        experience_score = self._source_score(matched, {"experience"})
        artifact_score = self._source_score(
            matched,
            {"projects", "papers", "patents"},
        )
        education_score = self._source_score(
            matched,
            {"education", "certifications"},
        )
        evidence_score = self._evidence_score(matched)
        seniority_score = self._seniority_score(candidate, inferred)
        inferred_score = max((role.confidence for role in inferred), default=0) * 100

        score = (
            skill_score * 0.25
            + experience_score * 0.25
            + artifact_score * 0.18
            + education_score * 0.12
            + seniority_score * 0.08
            + evidence_score * 0.07
            + inferred_score * 0.05
        )
        supported_signals = set().union(
            *(signals for _, signals in matched)
        ) if matched else set()
        missing = tuple(
            sorted(
                (definition.concepts | definition.keywords) - supported_signals
            )[:3]
        )
        return ScoredDirection(
            definition=definition,
            score=min(100, score),
            skill_score=skill_score,
            experience_score=experience_score,
            artifact_score=artifact_score,
            education_score=education_score,
            seniority_score=seniority_score,
            evidence_score=evidence_score,
            evidence=tuple(sorted(
                matched,
                key=lambda pair: pair[0].evidence_strength,
                reverse=True,
            )[:6]),
            missing_signals=missing,
        )

    def _source_score(
        self,
        matched: list[tuple[CandidateEvidenceItem, frozenset[str]]],
        sources: set[str],
    ) -> float:
        relevant = [
            (item, signals)
            for item, signals in matched
            if item.source_type in sources
        ]
        if not relevant:
            return 0
        breadth = min(1, len(set().union(*(signals for _, signals in relevant))) / 3)
        strength = sum(item.evidence_strength for item, _ in relevant) / len(relevant)
        return (breadth * 0.6 + strength * 0.4) * 100

    def _evidence_score(
        self,
        matched: list[tuple[CandidateEvidenceItem, frozenset[str]]],
    ) -> float:
        if not matched:
            return 0
        return min(
            100,
            sum(item.evidence_strength for item, _ in matched)
            / len(matched)
            * 100
            + min(20, len(matched) * 3),
        )

    def _seniority_score(
        self,
        candidate: CandidateProfile,
        inferred_roles: list,
    ) -> float:
        if inferred_roles:
            return max(role.confidence for role in inferred_roles) * 100
        if candidate.experience:
            return 65
        if candidate.education or candidate.projects:
            return 55
        return 35

    def _to_recommendation(
        self,
        item: ScoredDirection,
        rank: int,
        selected: list[ScoredDirection],
        candidate: CandidateProfile,
    ) -> CareerDirectionRecommendation:
        midpoint = round(item.score)
        uncertainty = 6 if item.evidence_score >= 75 else 10 if item.evidence_score >= 50 else 15
        confidence = (
            "High"
            if item.evidence_score >= 75 and len(item.evidence) >= 3
            else "Medium"
            if item.evidence_score >= 50 and len(item.evidence) >= 2
            else "Low"
        )
        fit_type = self._fit_type(item, rank, selected)
        seniority = self._direction_seniority(item, candidate)
        evidence = [
            DirectionEvidence(
                source_type=evidence_item.source_type,
                text=evidence_item.text,
                evidence_strength=evidence_item.evidence_strength,
                matched_concepts=sorted(signals),
            )
            for evidence_item, signals in item.evidence
        ]
        strengths = [
            f"{source.replace('_', ' ').title()} evidence supports {', '.join(sorted(signals))}."
            for source, signals in self._group_signals(item.evidence)
        ][:4]
        gaps = [
            f"No clear evidence currently supports: {self._display_signal(signal)}."
            for signal in item.missing_signals
        ]
        advice = [
            f"Lead with the {evidence_item.source_type} evidence: {evidence_item.text}"
            for evidence_item, _ in item.evidence[:2]
        ]
        if gaps:
            advice.append(
                "Clarify only genuinely supported experience related to the listed gaps; do not add unsupported claims."
            )
        return CareerDirectionRecommendation(
            rank=rank,
            direction=item.definition.direction,
            role_family=item.definition.role_family,
            seniority_level=seniority,
            fit_type=fit_type,
            score_range_low=max(0, midpoint - uncertainty),
            score_range_high=min(100, midpoint + uncertainty),
            score_midpoint=midpoint,
            confidence_level=confidence,
            matched_evidence=evidence,
            strengths_for_this_direction=strengths,
            gaps_for_this_direction=gaps,
            resume_positioning_advice=advice,
            example_job_titles=list(item.definition.example_titles),
        )

    def _fit_type(
        self,
        item: ScoredDirection,
        rank: int,
        selected: list[ScoredDirection],
    ) -> str:
        if rank == 1 and item.score >= 55:
            return "primary"
        if item.experience_score >= 45 or item.artifact_score >= 45:
            return "secondary"
        top_family = selected[0].definition.role_family if selected else None
        if item.definition.role_family != top_family and item.score >= 28:
            return "transferable"
        return "exploratory"

    def _direction_seniority(
        self,
        item: ScoredDirection,
        candidate: CandidateProfile,
    ) -> SeniorityLevel:
        family_roles = [
            role
            for role in candidate.inferred_target_roles
            if role.role_family == item.definition.role_family
        ]
        if family_roles:
            return max(family_roles, key=lambda role: role.confidence).seniority_level
        if item.experience_score >= 65:
            return "Junior"
        if item.education_score or item.artifact_score:
            return "Entry-level"
        return "Unknown"

    def _group_signals(
        self,
        evidence: tuple[tuple[CandidateEvidenceItem, frozenset[str]], ...],
    ) -> list[tuple[str, set[str]]]:
        grouped: dict[str, set[str]] = {}
        for item, signals in evidence:
            grouped.setdefault(item.source_type, set()).update(signals)
        return list(grouped.items())

    def _phrase_present(self, phrase: str, text: str) -> bool:
        normalized_phrase = self._normalize(phrase)
        normalized_text = self._normalize(text)
        return f" {normalized_phrase} " in f" {normalized_text} "

    def _normalize(self, value: str) -> str:
        value = value.casefold().replace("&", " and ")
        value = re.sub(r"[^a-z0-9+#.]+", " ", value)
        return " ".join(value.split())

    def _display_signal(self, signal: str) -> str:
        return signal.replace("_", " ")
