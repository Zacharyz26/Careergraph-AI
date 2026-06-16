import re
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.candidate import CandidateProfile, RoleFamily, SeniorityLevel
from app.schemas.career_direction import (
    CandidateEvidenceSummary,
    CareerDirectionProposalSet,
    CareerDirectionRecommendation,
    CareerDirectionResponse,
    CareerEvidenceItem,
    DirectionEvidence,
    ProposedCareerDirection,
)
from app.services.career_direction_proposal_service import (
    CareerDirectionProposalService,
)
from app.services.matching_service import (
    CandidateEvidenceItem,
    MatchingService,
)
from app.services.matching_taxonomy import extract_concepts


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
    coherence_score: float
    evidence: tuple[tuple[CandidateEvidenceItem, frozenset[str]], ...]
    missing_signals: tuple[str, ...]


class CareerDirectionService:
    STRONG_SOURCES = {"work", "project", "paper", "patent"}

    def __init__(
        self,
        matching_service: MatchingService | None = None,
        proposal_service: CareerDirectionProposalService | None = None,
    ) -> None:
        self.matching_service = matching_service or MatchingService()
        self.proposal_service = proposal_service or CareerDirectionProposalService(
            enabled=settings.career_directions_enable_llm
        )

    async def recommend(
        self,
        candidate: CandidateProfile,
    ) -> CareerDirectionResponse:
        summary = self.build_evidence_summary(candidate)
        if not summary.all_evidence():
            return CareerDirectionResponse()

        proposals = await self.proposal_service.propose(summary)
        if proposals is not None:
            recommendations = self._validate_and_rank(
                candidate,
                summary,
                proposals,
            )
            if recommendations:
                return CareerDirectionResponse(directions=recommendations)
        return self._deterministic_fallback(candidate, summary)

    def build_evidence_summary(
        self,
        candidate: CandidateProfile,
    ) -> CandidateEvidenceSummary:
        counters = 0
        buckets: dict[str, list[CareerEvidenceItem]] = {
            "education_signals": [],
            "skill_signals": [],
            "work_signals": [],
            "project_signals": [],
            "paper_signals": [],
            "patent_signals": [],
            "certification_signals": [],
            "leadership_signals": [],
            "language_signals": [],
        }

        def add(bucket: str, source: str, text: str, strength: float) -> None:
            nonlocal counters
            normalized = self._normalize(text)
            if not normalized:
                return
            if any(self._normalize(item.text) == normalized for item in buckets[bucket]):
                return
            counters += 1
            buckets[bucket].append(
                CareerEvidenceItem(
                    evidence_id=f"E{counters:03d}",
                    source_type=source,
                    text=text.strip(),
                    evidence_strength=strength,
                    normalized_concepts=sorted(extract_concepts(normalized)),
                )
            )

        for education in candidate.education:
            for text in self._nonempty(
                [
                    education.degree,
                    education.field_of_study,
                    *education.details,
                    *education.evidence,
                ]
            ):
                add("education_signals", "education", text, 0.6)
        for group in candidate.skills:
            for skill in group.skills:
                add("skill_signals", "skills", skill, 0.55)
        for experience in candidate.experience:
            for text in self._nonempty(
                [experience.title, *experience.bullets, *experience.evidence]
            ):
                add("work_signals", "work", text, 1.0)
                if self._is_leadership_signal(text):
                    add("leadership_signals", "leadership", text, 0.95)
        for project in candidate.projects:
            for text in self._nonempty(
                [
                    project.name,
                    project.description,
                    *project.technologies,
                    *project.bullets,
                    *project.evidence,
                ]
            ):
                add("project_signals", "project", text, 0.85)
        for paper in candidate.papers:
            for text in self._nonempty(
                [paper.title, paper.description, *paper.topics, *paper.evidence]
            ):
                add("paper_signals", "paper", text, 0.9)
        for patent in candidate.patents:
            for text in self._nonempty(
                [patent.title, patent.description, *patent.evidence]
            ):
                add("patent_signals", "patent", text, 0.95)
        for certification in candidate.certifications:
            for text in self._nonempty(
                [certification.name, certification.issuer, *certification.evidence]
            ):
                add("certification_signals", "certification", text, 0.75)
        for language in candidate.languages:
            text = " ".join(
                self._nonempty([language.language, language.proficiency])
            )
            if text:
                add("language_signals", "language", text, 0.65)
        return CandidateEvidenceSummary(**buckets)

    def _validate_and_rank(
        self,
        candidate: CandidateProfile,
        summary: CandidateEvidenceSummary,
        proposal_set: CareerDirectionProposalSet,
    ) -> list[CareerDirectionRecommendation]:
        evidence_by_id = {
            item.evidence_id: item for item in summary.all_evidence()
        }
        validated = []
        seen: set[tuple[str, str]] = set()
        for proposal in proposal_set.directions:
            key = (proposal.direction.casefold(), proposal.role_family)
            if key in seen:
                continue
            seen.add(key)
            evidence = [
                evidence_by_id[evidence_id]
                for evidence_id in proposal.supporting_evidence_ids
                if evidence_id in evidence_by_id
            ]
            evidence = self._deduplicate_evidence(evidence)
            if not evidence:
                continue
            validated.append(
                self._score_proposal(candidate, summary, proposal, evidence)
            )

        specialized_strength = max(
            (
                item["score"]
                for item in validated
                if item["proposal"].role_family
                not in {"General Internship", "Other"}
            ),
            default=0,
        )
        if specialized_strength >= 55:
            validated = [
                item
                for item in validated
                if item["proposal"].role_family != "General Internship"
            ]
        validated.sort(
            key=lambda item: (
                item["score"],
                item["evidence_diversity"],
                item["directness"],
            ),
            reverse=True,
        )
        selected = validated[:5]
        return [
            self._proposal_recommendation(item, rank)
            for rank, item in enumerate(selected, start=1)
        ]

    def _score_proposal(
        self,
        candidate: CandidateProfile,
        summary: CandidateEvidenceSummary,
        proposal: ProposedCareerDirection,
        evidence: list[CareerEvidenceItem],
    ) -> dict[str, object]:
        sources = {item.source_type for item in evidence}
        strong_evidence = [
            item
            for item in evidence
            if item.source_type in self.STRONG_SOURCES
            and item.evidence_strength >= 0.85
        ]
        skill_only = sources <= {"skills"}
        fit_type = proposal.proposed_fit_type
        if fit_type == "primary" and not strong_evidence:
            fit_type = "exploratory" if skill_only else "secondary"

        evidence_strength = (
            sum(item.evidence_strength for item in evidence) / len(evidence)
        )
        diversity = min(1, len(sources) / 4)
        direction_concepts = extract_concepts(
            self._normalize(
                " ".join(
                    [
                        proposal.direction,
                        proposal.rationale,
                        *proposal.example_job_titles,
                    ]
                )
            )
        )
        evidence_concepts = set().union(
            *(set(item.normalized_concepts) for item in evidence)
        )
        directness = (
            min(1, len(direction_concepts & evidence_concepts) / max(1, len(direction_concepts)))
            if direction_concepts
            else self._proposal_text_directness(proposal, evidence)
        )
        family_roles = [
            role
            for role in candidate.inferred_target_roles
            if role.role_family == proposal.role_family
        ]
        family_consistency = max(
            (role.confidence for role in family_roles),
            default=0.45 if strong_evidence else 0.2,
        )
        family_support = self._family_profile_support(summary)
        strongest_family_support = max(family_support.values(), default=0)
        proposal_family_support = family_support.get(proposal.role_family, 0)
        coherence = (
            proposal_family_support / strongest_family_support
            if strongest_family_support
            else 0
        )
        evidence_concentration = min(
            1,
            sum(item.evidence_strength for item in evidence) / 2.5,
        )
        seniority_fit = self._seniority_consistency(
            candidate,
            proposal.likely_seniority_level,
            proposal.role_family,
        )
        gap_severity = min(1, len(proposal.possible_gaps) / 4)
        score = (
            evidence_strength * 20
            + diversity * 12
            + directness * 15
            + family_consistency * 6
            + seniority_fit * 7
            + (1 - gap_severity) * 5
            + coherence * 25
            + evidence_concentration * 10
        )
        if skill_only:
            score = min(score, 38)
        isolated_support = len(evidence) == 1 or len(sources) == 1
        if isolated_support and coherence < 0.6:
            score = min(score, 48)
            fit_type = (
                "transferable"
                if proposal_family_support > 0
                else "exploratory"
            )
        elif fit_type == "primary" and (
            coherence < 0.7
            or (diversity < 0.5 and not strong_evidence)
        ):
            fit_type = "secondary"
        confidence = min(
            1,
            evidence_strength * 0.3
            + diversity * 0.15
            + directness * 0.15
            + family_consistency * 0.1
            + coherence * 0.3,
        )
        if skill_only:
            confidence = min(confidence, 0.4)
        return {
            "proposal": proposal,
            "evidence": evidence,
            "fit_type": fit_type,
            "score": min(100, score),
            "confidence": confidence,
            "evidence_diversity": diversity,
            "directness": directness,
            "coherence": coherence,
            "strong_evidence": strong_evidence,
        }

    def _proposal_recommendation(
        self,
        item: dict[str, object],
        rank: int,
    ) -> CareerDirectionRecommendation:
        proposal = item["proposal"]
        evidence = item["evidence"]
        score = round(item["score"])
        confidence_value = item["confidence"]
        confidence = (
            "High"
            if confidence_value >= 0.72
            else "Medium"
            if confidence_value >= 0.48
            else "Low"
        )
        uncertainty = 6 if confidence == "High" else 10 if confidence == "Medium" else 15
        strengths = [
            f"{evidence_item.source_type.title()} evidence: {evidence_item.text}"
            for evidence_item in evidence[:4]
        ]
        advice = [
            f"Lead with evidence {evidence_item.evidence_id}: {evidence_item.text}"
            for evidence_item in evidence[:2]
        ]
        if proposal.possible_gaps:
            advice.append(
                "Address only gaps you can support with real experience; do not add unverified claims."
            )
        return CareerDirectionRecommendation(
            rank=rank,
            direction=proposal.direction,
            role_family=proposal.role_family,
            seniority_level=proposal.likely_seniority_level,
            fit_type=item["fit_type"],
            score_range_low=max(0, score - uncertainty),
            score_range_high=min(100, score + uncertainty),
            score_midpoint=score,
            confidence_level=confidence,
            matched_evidence=[
                DirectionEvidence(
                    evidence_id=evidence_item.evidence_id,
                    source_type=evidence_item.source_type,
                    text=evidence_item.text,
                    evidence_strength=evidence_item.evidence_strength,
                    matched_concepts=evidence_item.normalized_concepts,
                )
                for evidence_item in evidence
            ],
            strengths_for_this_direction=strengths,
            gaps_for_this_direction=proposal.possible_gaps,
            resume_positioning_advice=advice,
            example_job_titles=proposal.example_job_titles,
        )

    def _deterministic_fallback(
        self,
        candidate: CandidateProfile,
        summary: CandidateEvidenceSummary,
    ) -> CareerDirectionResponse:
        evidence_index = self.matching_service.build_candidate_evidence_index(candidate)
        summary_items = summary.all_evidence()
        scored = [
            result
            for definition in DIRECTION_CATALOG
            if (
                result := self._score_catalog_direction(
                    candidate,
                    summary,
                    evidence_index,
                    definition,
                )
            )
            and result.score >= 18
        ]
        scored.sort(
            key=lambda item: (item.score, item.evidence_score, item.experience_score),
            reverse=True,
        )
        selected = scored[:5]
        return CareerDirectionResponse(
            directions=[
                self._catalog_recommendation(
                    item,
                    rank,
                    selected,
                    candidate,
                    summary_items,
                )
                for rank, item in enumerate(selected, start=1)
            ]
        )

    def _score_catalog_direction(
        self,
        candidate: CandidateProfile,
        summary: CandidateEvidenceSummary,
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
        if not matched:
            return None
        skill_score = self._source_score(matched, {"skills"})
        experience_score = self._source_score(matched, {"experience"})
        artifact_score = self._source_score(matched, {"projects", "papers", "patents"})
        education_score = self._source_score(matched, {"education", "certifications"})
        evidence_score = self._evidence_score(matched)
        family_support = self._family_profile_support(summary)
        strongest_family_support = max(family_support.values(), default=0)
        coherence_score = (
            family_support.get(definition.role_family, 0)
            / strongest_family_support
            * 100
            if strongest_family_support
            else 0
        )
        seniority_score = self._fallback_seniority_score(candidate, inferred)
        inferred_score = max((role.confidence for role in inferred), default=0) * 100
        score = (
            skill_score * 0.2
            + experience_score * 0.2
            + artifact_score * 0.16
            + education_score * 0.1
            + seniority_score * 0.06
            + evidence_score * 0.08
            + inferred_score * 0.05
            + coherence_score * 0.15
        )
        source_count = len({item.source_type for item, _ in matched})
        if source_count == 1 and coherence_score < 60:
            score = min(score, 48)
        supported = set().union(*(signals for _, signals in matched)) if matched else set()
        return ScoredDirection(
            definition=definition,
            score=min(100, score),
            skill_score=skill_score,
            experience_score=experience_score,
            artifact_score=artifact_score,
            education_score=education_score,
            seniority_score=seniority_score,
            evidence_score=evidence_score,
            coherence_score=coherence_score,
            evidence=tuple(sorted(matched, key=lambda pair: pair[0].evidence_strength, reverse=True)[:6]),
            missing_signals=tuple(sorted((definition.concepts | definition.keywords) - supported)[:3]),
        )

    def _catalog_recommendation(
        self,
        item: ScoredDirection,
        rank: int,
        selected: list[ScoredDirection],
        candidate: CandidateProfile,
        summary_items: list[CareerEvidenceItem],
    ) -> CareerDirectionRecommendation:
        midpoint = round(item.score)
        uncertainty = 6 if item.evidence_score >= 75 else 10 if item.evidence_score >= 50 else 15
        confidence = "High" if item.evidence_score >= 75 and len(item.evidence) >= 3 else "Medium" if item.evidence_score >= 50 and len(item.evidence) >= 2 else "Low"
        evidence = []
        for evidence_item, signals in item.evidence:
            summary_item = self._resolve_summary_evidence(
                evidence_item.text,
                signals,
                summary_items,
            )
            if summary_item:
                evidence.append(
                    DirectionEvidence(
                        evidence_id=summary_item.evidence_id,
                        source_type=summary_item.source_type,
                        text=summary_item.text,
                        evidence_strength=summary_item.evidence_strength,
                        matched_concepts=sorted(signals),
                    )
                )
        return CareerDirectionRecommendation(
            rank=rank,
            direction=item.definition.direction,
            role_family=item.definition.role_family,
            seniority_level=self._catalog_seniority(item, candidate),
            fit_type=self._catalog_fit_type(item, rank, selected),
            score_range_low=max(0, midpoint - uncertainty),
            score_range_high=min(100, midpoint + uncertainty),
            score_midpoint=midpoint,
            confidence_level=confidence,
            matched_evidence=evidence,
            strengths_for_this_direction=[
                f"{value.source_type.title()} evidence: {value.text}"
                for value in evidence[:4]
            ],
            gaps_for_this_direction=[
                f"No clear evidence currently supports: {signal.replace('_', ' ')}."
                for signal in item.missing_signals
            ],
            resume_positioning_advice=[
                f"Lead with evidence {value.evidence_id}: {value.text}"
                for value in evidence[:2]
            ],
            example_job_titles=list(item.definition.example_titles),
        )

    def _source_score(
        self,
        matched: list[tuple[CandidateEvidenceItem, frozenset[str]]],
        sources: set[str],
    ) -> float:
        relevant = [(item, signals) for item, signals in matched if item.source_type in sources]
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
        return min(100, sum(item.evidence_strength for item, _ in matched) / len(matched) * 100 + min(20, len(matched) * 3))

    def _fallback_seniority_score(self, candidate: CandidateProfile, inferred: list) -> float:
        if inferred:
            return max(role.confidence for role in inferred) * 100
        if candidate.experience:
            return 65
        if candidate.education or candidate.projects:
            return 55
        return 35

    def _catalog_fit_type(
        self,
        item: ScoredDirection,
        rank: int,
        selected: list[ScoredDirection],
    ) -> str:
        if rank == 1 and item.score >= 55:
            return "primary"
        if (
            item.coherence_score >= 65
            and (item.experience_score >= 45 or item.artifact_score >= 45)
        ):
            return "secondary"
        top_family = selected[0].definition.role_family if selected else None
        if item.definition.role_family != top_family and item.score >= 28:
            return "transferable"
        return "exploratory"

    def _catalog_seniority(
        self,
        item: ScoredDirection,
        candidate: CandidateProfile,
    ) -> SeniorityLevel:
        roles = [
            role for role in candidate.inferred_target_roles
            if role.role_family == item.definition.role_family
        ]
        if roles:
            return max(roles, key=lambda role: role.confidence).seniority_level
        if item.experience_score >= 65:
            return "Junior"
        if item.education_score or item.artifact_score:
            return "Entry-level"
        return "Unknown"

    def _seniority_consistency(
        self,
        candidate: CandidateProfile,
        seniority: SeniorityLevel,
        family: RoleFamily,
    ) -> float:
        roles = [
            role for role in candidate.inferred_target_roles
            if role.role_family == family
        ]
        if roles:
            exact = [
                role.confidence for role in roles
                if role.seniority_level == seniority
            ]
            return max(exact, default=max(role.confidence for role in roles) * 0.75)
        if seniority in {"Internship", "Entry-level", "Unknown"}:
            return 0.7
        return 0.45 if candidate.experience else 0.2

    def _is_leadership_signal(self, text: str) -> bool:
        normalized = self._normalize(text)
        return any(
            token in normalized.split()
            for token in {"lead", "led", "manage", "managed", "supervise", "mentored"}
        ) or "project lead" in normalized or "team lead" in normalized

    def _proposal_text_directness(
        self,
        proposal: ProposedCareerDirection,
        evidence: list[CareerEvidenceItem],
    ) -> float:
        proposal_tokens = set(
            self._normalize(
                " ".join(
                    [
                        proposal.direction,
                        proposal.rationale,
                        *proposal.example_job_titles,
                    ]
                )
            ).split()
        )
        if not proposal_tokens:
            return 0
        evidence_tokens = set(
            self._normalize(" ".join(item.text for item in evidence)).split()
        )
        return min(1, len(proposal_tokens & evidence_tokens) / 3)

    def _family_profile_support(
        self,
        summary: CandidateEvidenceSummary,
    ) -> dict[RoleFamily, float]:
        family_definitions: dict[RoleFamily, list[DirectionDefinition]] = {}
        for definition in DIRECTION_CATALOG:
            family_definitions.setdefault(definition.role_family, []).append(
                definition
            )

        support: dict[RoleFamily, float] = {}
        for family, definitions in family_definitions.items():
            concepts = set().union(
                *(set(definition.concepts) for definition in definitions)
            )
            keywords = set().union(
                *(set(definition.keywords) for definition in definitions)
            )
            matched = [
                item
                for item in summary.all_evidence()
                if concepts & set(item.normalized_concepts)
                or any(self._phrase_present(keyword, item.text) for keyword in keywords)
            ]
            if not matched:
                support[family] = 0
                continue
            sources = {item.source_type for item in matched}
            strong_sources = {
                item.source_type
                for item in matched
                if item.source_type in self.STRONG_SOURCES
            }
            strength = sum(item.evidence_strength for item in matched)
            support[family] = (
                strength
                + min(2.5, len(sources) * 0.55)
                + min(2, len(strong_sources) * 0.7)
            )
        return support

    def _deduplicate_evidence(
        self,
        evidence: list[CareerEvidenceItem],
    ) -> list[CareerEvidenceItem]:
        seen = set()
        result = []
        for item in evidence:
            if item.evidence_id not in seen:
                seen.add(item.evidence_id)
                result.append(item)
        return result

    def _resolve_summary_evidence(
        self,
        text: str,
        signals: frozenset[str],
        summary_items: list[CareerEvidenceItem],
    ) -> CareerEvidenceItem | None:
        normalized_text = self._normalize(text)
        exact = next(
            (
                item
                for item in summary_items
                if self._normalize(item.text) == normalized_text
            ),
            None,
        )
        if exact:
            return exact
        contained = [
            item
            for item in summary_items
            if self._normalize(item.text) in normalized_text
            or normalized_text in self._normalize(item.text)
        ]
        if contained:
            return max(contained, key=lambda item: item.evidence_strength)
        conceptual = [
            item
            for item in summary_items
            if signals & set(item.normalized_concepts)
        ]
        return (
            max(conceptual, key=lambda item: item.evidence_strength)
            if conceptual
            else None
        )

    def _phrase_present(self, phrase: str, text: str) -> bool:
        return f" {self._normalize(phrase)} " in f" {self._normalize(text)} "

    def _normalize(self, value: str) -> str:
        value = value.casefold().replace("&", " and ")
        value = re.sub(r"[^a-z0-9+#.]+", " ", value)
        return " ".join(value.split())

    def _nonempty(self, values: list[str | None]) -> list[str]:
        return [value for value in values if value and value.strip()]
