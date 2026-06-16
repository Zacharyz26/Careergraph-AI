import re
from math import sqrt
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

from app.core.config import settings
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobEvidenceItem, JobProfile
from app.schemas.match import (
    MatchResult,
    RequirementEvidence,
    RequirementMatch,
    RequirementStatus,
    RequirementType,
    ScoredMatchEvidence,
)
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError
from app.services.evidence_judge_service import EvidenceJudgeService
from app.services.matching_taxonomy import (
    extract_concepts,
    has_transferable_relationship,
)
from app.services.user_facing_sanitizer import sanitize_user_facing_text

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

STATUS_VALUE: dict[RequirementStatus, float] = {
    "full_match": 1.0,
    "partial_match": 0.65,
    "transferable_match": 0.4,
    "missing": 0.0,
}

SOURCE_STRENGTH: dict[EvidenceSource, float] = {
    "experience": 1.0,
    "patents": 0.95,
    "papers": 0.9,
    "projects": 0.85,
    "certifications": 0.8,
    "skills": 0.7,
    "education": 0.6,
    "languages": 0.7,
}

REQUIREMENT_IMPORTANCE: dict[RequirementType, float] = {
    "required_skill": 1.0,
    "preferred_skill": 0.45,
    "responsibility": 0.8,
    "qualification": 0.9,
    "education_requirement": 0.75,
    "experience_requirement": 0.95,
}

SENIORITY_RANK = {
    "Internship": 0,
    "Entry-level": 1,
    "Junior": 2,
    "Mid-level": 3,
    "Senior": 4,
    "Leadership": 5,
}

TERM_NORMALIZATIONS = {
    "apis": "api",
    "built": "build",
    "building": "build",
    "builds": "build",
    "created": "create",
    "creating": "create",
    "creates": "create",
    "developed": "develop",
    "developing": "develop",
    "develops": "develop",
    "managed": "manage",
    "managing": "manage",
    "analyzed": "analyze",
    "analyzing": "analyze",
    "analysed": "analyze",
    "analysing": "analyze",
    "reports": "report",
    "workflows": "workflow",
    "dashboards": "dashboard",
    "campaigns": "campaign",
    "budgets": "budget",
    "contracts": "contract",
    "patients": "patient",
}


@dataclass(frozen=True)
class CandidateEvidenceItem:
    source_type: EvidenceSource
    text: str
    normalized_tokens: frozenset[str]
    normalized_concepts: frozenset[str]
    evidence_strength: float


@dataclass(frozen=True)
class JobRequirement:
    requirement_type: RequirementType
    importance: float
    text: str
    normalized_tokens: frozenset[str]
    normalized_concepts: frozenset[str]


@dataclass(frozen=True)
class MatchDecision:
    status: RequirementStatus
    match_strength: float
    confidence: float
    evidence: CandidateEvidenceItem | None
    reason: str
    similarity_score: float | None = None
    evaluation_method: Literal[
        "deterministic",
        "semantic",
        "llm_judge",
    ] = "deterministic"


class MatchingService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        evidence_judge: EvidenceJudgeService | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.evidence_judge = evidence_judge or EvidenceJudgeService(
            enabled=settings.matching_enable_llm_judge
        )

    async def score(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
    ) -> MatchResult:
        evidence_index = self.build_candidate_evidence_index(candidate)
        requirements = self.build_job_requirement_list(job)
        decisions = [
            self._evaluate_requirement(requirement, evidence_index)
            for requirement in requirements
        ]
        if settings.matching_enable_semantic and self.embedding_service.is_available:
            decisions = await self._apply_semantic_matching(
                requirements,
                evidence_index,
                decisions,
            )
        if self.evidence_judge.is_available:
            decisions = await self._apply_evidence_judge(
                requirements,
                evidence_index,
                decisions,
            )
        requirement_matches = [
            self._to_requirement_match(requirement, decision)
            for requirement, decision in zip(requirements, decisions, strict=True)
        ]

        required_score = self._coverage(
            requirement_matches,
            {"required_skill", "qualification", "experience_requirement"},
        )
        preferred_score = self._coverage(
            requirement_matches,
            {"preferred_skill"},
        )
        responsibility_score = self._coverage(
            requirement_matches,
            {"responsibility"},
        )
        education_score = self._coverage(
            requirement_matches,
            {"education_requirement"},
        )
        seniority_score = self._seniority_fit(candidate, job)
        evidence_score = self._evidence_strength(requirement_matches)
        risk_penalty, risks = self._risk_penalty(requirement_matches)

        weighted_parts = [
            (required_score, 0.45, self._has_type(requirements, {
                "required_skill", "qualification", "experience_requirement"
            })),
            (preferred_score, 0.08, self._has_type(requirements, {"preferred_skill"})),
            (
                responsibility_score,
                0.20,
                self._has_type(requirements, {"responsibility"}),
            ),
            (
                education_score,
                0.10,
                self._has_type(requirements, {"education_requirement"}),
            ),
            (seniority_score, 0.07, job.seniority_level != "Unknown"),
            (evidence_score, 0.10, bool(requirement_matches)),
        ]
        active_weight = sum(weight for _, weight, active in weighted_parts if active)
        base_score = (
            sum(score * weight for score, weight, active in weighted_parts if active)
            / active_weight
            if active_weight
            else 0
        )
        final_score = max(0, min(100, round(base_score - risk_penalty)))

        matched_required = self._skill_list(
            requirement_matches,
            "required_skill",
            {"full_match", "partial_match"},
        )
        matched_preferred = self._skill_list(
            requirement_matches,
            "preferred_skill",
            {"full_match", "partial_match"},
        )
        missing_required = self._skill_list(
            requirement_matches,
            "required_skill",
            {"missing"},
        )
        missing_preferred = self._skill_list(
            requirement_matches,
            "preferred_skill",
            {"missing"},
        )
        transferable = [
            match.requirement
            for match in requirement_matches
            if match.match_status == "transferable_match"
        ]

        return MatchResult(
            final_score=final_score,
            required_coverage_score=required_score,
            preferred_coverage_score=preferred_score,
            responsibility_alignment_score=responsibility_score,
            education_fit_score=education_score,
            seniority_fit_score=seniority_score,
            evidence_strength_score=evidence_score,
            risk_penalty=risk_penalty,
            requirement_matches=requirement_matches,
            matched_required_skills=matched_required,
            matched_preferred_skills=matched_preferred,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            transferable_matches=transferable,
            matched_evidence=self._legacy_evidence(requirement_matches),
            risks=risks,
            recommendation=self._recommendation(final_score),
            explanation=self._explanation(
                final_score,
                requirement_matches,
                risk_penalty,
            ),
        )

    def build_candidate_evidence_index(
        self,
        candidate: CandidateProfile,
    ) -> list[CandidateEvidenceItem]:
        items: list[CandidateEvidenceItem] = []
        for group in candidate.skills:
            for skill in group.skills:
                items.append(self._evidence("skills", skill, group.evidence))
        for experience in candidate.experience:
            for text in self._nonempty(
                [experience.title, *experience.bullets, *experience.evidence]
            ):
                items.append(self._evidence("experience", text))
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
                items.append(self._evidence("projects", text))
        for paper in candidate.papers:
            for text in self._nonempty(
                [
                    paper.title,
                    paper.description,
                    *paper.topics,
                    *paper.evidence,
                ]
            ):
                items.append(self._evidence("papers", text))
        for patent in candidate.patents:
            for text in self._nonempty(
                [patent.title, patent.description, *patent.evidence]
            ):
                items.append(self._evidence("patents", text))
        for education in candidate.education:
            for text in self._nonempty(
                [
                    education.degree,
                    education.field_of_study,
                    *education.details,
                    *education.evidence,
                ]
            ):
                items.append(self._evidence("education", text))
        for certification in candidate.certifications:
            for text in self._nonempty(
                [certification.name, certification.issuer, *certification.evidence]
            ):
                items.append(self._evidence("certifications", text))
        for language in candidate.languages:
            text = " ".join(
                self._nonempty([language.language, language.proficiency])
            )
            if text:
                items.append(self._evidence("languages", text, language.evidence))
        return self._deduplicate_index(items)

    def build_job_requirement_list(
        self,
        job: JobProfile,
    ) -> list[JobRequirement]:
        groups: list[tuple[RequirementType, list[JobEvidenceItem]]] = [
            ("required_skill", job.required_skills),
            ("preferred_skill", job.preferred_skills),
            ("responsibility", job.responsibilities),
            ("qualification", job.qualifications),
            ("education_requirement", job.education_requirements),
            ("experience_requirement", job.experience_requirements),
        ]
        return [
            self._requirement(requirement_type, item.value)
            for requirement_type, items in groups
            for item in items
        ]

    def _evaluate_requirement(
        self,
        requirement: JobRequirement,
        evidence_index: list[CandidateEvidenceItem],
    ) -> MatchDecision:
        best = MatchDecision("missing", 0, 1, None, "No supporting evidence found.")
        for evidence in evidence_index:
            decision = self._compare(requirement, evidence)
            if (decision.match_strength, decision.confidence) > (
                best.match_strength,
                best.confidence,
            ):
                best = decision
        return best

    def _compare(
        self,
        requirement: JobRequirement,
        evidence: CandidateEvidenceItem,
    ) -> MatchDecision:
        requirement_text = self._normalize(requirement.text)
        evidence_text = self._normalize(evidence.text)
        if requirement_text == evidence_text or self._phrase_present(
            requirement_text,
            evidence_text,
        ):
            return MatchDecision(
                "full_match",
                evidence.evidence_strength,
                0.98,
                evidence,
                "The candidate evidence explicitly states the requirement.",
            )

        token_coverage = self._token_coverage(
            requirement.normalized_tokens,
            evidence.normalized_tokens,
        )
        sequence = SequenceMatcher(None, requirement_text, evidence_text).ratio()
        if token_coverage >= 0.8 or sequence >= 0.88:
            return MatchDecision(
                "full_match",
                evidence.evidence_strength * 0.95,
                max(0.82, token_coverage),
                evidence,
                "Normalized wording closely matches the requirement.",
            )

        shared_concepts = (
            requirement.normalized_concepts & evidence.normalized_concepts
        )
        if shared_concepts:
            return MatchDecision(
                "full_match",
                evidence.evidence_strength * 0.9,
                0.86,
                evidence,
                "Candidate evidence supports the same normalized concept: "
                + ", ".join(sorted(shared_concepts))
                + ".",
            )
        if has_transferable_relationship(
            requirement.normalized_concepts,
            evidence.normalized_concepts,
        ):
            return MatchDecision(
                "transferable_match",
                evidence.evidence_strength * 0.4,
                0.58,
                evidence,
                "Candidate evidence is related and potentially transferable, "
                "but does not directly satisfy the requirement.",
            )
        if token_coverage >= 0.5 or sequence >= 0.62:
            return MatchDecision(
                "partial_match",
                evidence.evidence_strength * 0.65,
                max(0.6, token_coverage),
                evidence,
                "Candidate evidence covers part of the requirement.",
            )
        return MatchDecision("missing", 0, 1, None, "No supporting evidence found.")

    async def _apply_semantic_matching(
        self,
        requirements: list[JobRequirement],
        evidence_index: list[CandidateEvidenceItem],
        decisions: list[MatchDecision],
    ) -> list[MatchDecision]:
        if not requirements or not evidence_index:
            return decisions
        texts = [item.text for item in requirements] + [
            item.text for item in evidence_index
        ]
        try:
            vectors = await self.embedding_service.embed(texts)
        except EmbeddingServiceError:
            return decisions
        if len(vectors) != len(texts):
            return decisions

        requirement_vectors = vectors[: len(requirements)]
        evidence_vectors = vectors[len(requirements) :]
        updated = list(decisions)
        for index, (requirement, current) in enumerate(
            zip(requirements, decisions, strict=True)
        ):
            if current.status == "full_match":
                continue
            best_similarity = -1.0
            best_evidence = None
            for evidence, vector in zip(
                evidence_index,
                evidence_vectors,
                strict=True,
            ):
                similarity = self._cosine_similarity(
                    requirement_vectors[index],
                    vector,
                )
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_evidence = evidence

            semantic = self._semantic_decision(best_similarity, best_evidence)
            if semantic is None and best_evidence and best_similarity >= 0.55:
                semantic = MatchDecision(
                    status="missing",
                    match_strength=0,
                    confidence=round(best_similarity, 4),
                    evidence=best_evidence,
                    reason=(
                        "Semantic similarity is ambiguous and does not meet the "
                        "matching threshold."
                    ),
                    similarity_score=round(best_similarity, 4),
                    evaluation_method="semantic",
                )
            if semantic and (
                semantic.match_strength > current.match_strength
                or (
                    semantic.match_strength == current.match_strength
                    and (
                        current.similarity_score is None
                        or semantic.similarity_score is not None
                    )
                )
            ):
                updated[index] = semantic
        return updated

    def _semantic_decision(
        self,
        similarity: float,
        evidence: CandidateEvidenceItem | None,
    ) -> MatchDecision | None:
        if evidence is None or similarity < 0.64:
            return None
        if similarity >= 0.90:
            status: RequirementStatus = "full_match"
            factor = 0.9
            reason = (
                "Semantic similarity strongly connects the requirement to the "
                "candidate evidence."
            )
        elif similarity >= 0.76:
            status = "partial_match"
            factor = 0.65
            reason = (
                "Semantic similarity indicates meaningful but incomplete "
                "support."
            )
        else:
            status = "transferable_match"
            factor = 0.4
            reason = (
                "Semantic similarity indicates related, potentially "
                "transferable evidence."
            )
        return MatchDecision(
            status=status,
            match_strength=evidence.evidence_strength * factor,
            confidence=min(0.95, max(0.55, similarity)),
            evidence=evidence,
            reason=reason,
            similarity_score=round(similarity, 4),
            evaluation_method="semantic",
        )

    async def _apply_evidence_judge(
        self,
        requirements: list[JobRequirement],
        evidence_index: list[CandidateEvidenceItem],
        decisions: list[MatchDecision],
    ) -> list[MatchDecision]:
        updated = list(decisions)
        for index, (requirement, decision) in enumerate(
            zip(requirements, decisions, strict=True)
        ):
            if not self._is_ambiguous(decision):
                continue
            candidates = self._judge_candidates(decision, evidence_index)
            result = await self.evidence_judge.judge(
                requirement=requirement.text,
                candidate_evidence=[item.text for item in candidates],
            )
            if result is None:
                continue
            evidence = next(
                (
                    item
                    for item in candidates
                    if item.text in result.supported_evidence
                ),
                None,
            )
            factor = STATUS_VALUE[result.match_status]
            updated[index] = MatchDecision(
                status=result.match_status,
                match_strength=(evidence.evidence_strength * factor if evidence else 0),
                confidence=result.confidence,
                evidence=evidence,
                reason=result.reason,
                similarity_score=decision.similarity_score,
                evaluation_method="llm_judge",
            )
        return updated

    def _is_ambiguous(self, decision: MatchDecision) -> bool:
        if decision.status in {"partial_match", "transferable_match"}:
            return True
        return (
            decision.status == "missing"
            and decision.similarity_score is not None
            and decision.similarity_score >= 0.55
        )

    def _judge_candidates(
        self,
        decision: MatchDecision,
        evidence_index: list[CandidateEvidenceItem],
    ) -> list[CandidateEvidenceItem]:
        if decision.evidence:
            remaining = [
                item for item in evidence_index if item != decision.evidence
            ]
            return [decision.evidence, *remaining[:2]]
        return evidence_index[:3]

    def _evidence(
        self,
        source_type: EvidenceSource,
        text: str,
        fallback_evidence: list[str] | None = None,
    ) -> CandidateEvidenceItem:
        display_text = (
            fallback_evidence[0]
            if fallback_evidence
            else text
        )
        normalized = self._normalize(text)
        return CandidateEvidenceItem(
            source_type=source_type,
            text=sanitize_user_facing_text(display_text),
            normalized_tokens=frozenset(normalized.split()),
            normalized_concepts=extract_concepts(normalized),
            evidence_strength=SOURCE_STRENGTH[source_type],
        )

    def _requirement(
        self,
        requirement_type: RequirementType,
        text: str,
    ) -> JobRequirement:
        display_text = sanitize_user_facing_text(text)
        normalized = self._normalize(display_text)
        return JobRequirement(
            requirement_type=requirement_type,
            importance=REQUIREMENT_IMPORTANCE[requirement_type],
            text=display_text,
            normalized_tokens=frozenset(normalized.split()),
            normalized_concepts=extract_concepts(normalized),
        )

    def _to_requirement_match(
        self,
        requirement: JobRequirement,
        decision: MatchDecision,
    ) -> RequirementMatch:
        evidence = []
        if decision.evidence:
            evidence.append(
                RequirementEvidence(
                    source_type=decision.evidence.source_type,
                    text=decision.evidence.text,
                    evidence_strength=decision.evidence.evidence_strength,
                    normalized_concepts=sorted(
                        decision.evidence.normalized_concepts
                    ),
                )
            )
        return RequirementMatch(
            requirement_type=requirement.requirement_type,
            importance=requirement.importance,
            requirement=requirement.text,
            match_status=decision.status,
            match_strength=round(decision.match_strength, 3),
            confidence=round(decision.confidence, 3),
            similarity_score=decision.similarity_score,
            evaluation_method=decision.evaluation_method,
            candidate_evidence=evidence,
            reason=sanitize_user_facing_text(decision.reason),
        )

    def _coverage(
        self,
        matches: list[RequirementMatch],
        types: set[RequirementType],
    ) -> int:
        relevant = [match for match in matches if match.requirement_type in types]
        if not relevant:
            return 100
        denominator = sum(match.importance for match in relevant)
        points = sum(
            STATUS_VALUE[match.match_status] * match.importance
            for match in relevant
        )
        return round(points / denominator * 100)

    def _evidence_strength(self, matches: list[RequirementMatch]) -> int:
        matched = [
            match
            for match in matches
            if match.match_status != "missing" and match.candidate_evidence
        ]
        if not matched:
            return 0
        return round(
            sum(
                match.match_strength * match.confidence
                for match in matched
            )
            / len(matched)
            * 100
        )

    def _seniority_fit(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
    ) -> int:
        if job.seniority_level == "Unknown":
            return 100
        relevant_roles = [
            role
            for role in candidate.inferred_target_roles
            if role.role_family == job.role_family
        ]
        if not relevant_roles:
            return 0
        scores = []
        for role in relevant_roles:
            if role.seniority_level == "Unknown":
                compatibility = 0.5
            else:
                difference = (
                    SENIORITY_RANK[role.seniority_level]
                    - SENIORITY_RANK[job.seniority_level]
                )
                compatibility = 1 if difference >= 0 else 0.6 if difference == -1 else 0
            scores.append(compatibility * role.confidence)
        return round(max(scores) * 100)

    def _risk_penalty(
        self,
        matches: list[RequirementMatch],
    ) -> tuple[int, list[str]]:
        risks = []
        penalty = 0
        for match in matches:
            if match.match_status != "missing":
                continue
            if match.requirement_type == "required_skill":
                penalty += 7
                risks.append(
                    sanitize_user_facing_text(
                        f"Missing required skill: {match.requirement}"
                    )
                )
            elif match.requirement_type == "experience_requirement":
                penalty += 6
                risks.append(
                    sanitize_user_facing_text(
                        f"Missing experience requirement: {match.requirement}"
                    )
                )
            elif match.requirement_type == "qualification":
                penalty += 5
                risks.append(
                    sanitize_user_facing_text(
                        f"Missing qualification: {match.requirement}"
                    )
                )
            elif match.requirement_type == "education_requirement":
                penalty += 4
                risks.append(
                    sanitize_user_facing_text(
                        f"Education requirement not supported: {match.requirement}"
                    )
                )
        return min(35, penalty), risks

    def _skill_list(
        self,
        matches: list[RequirementMatch],
        requirement_type: RequirementType,
        statuses: set[RequirementStatus],
    ) -> list[str]:
        return [
            match.requirement
            for match in matches
            if match.requirement_type == requirement_type
            and match.match_status in statuses
        ]

    def _legacy_evidence(
        self,
        matches: list[RequirementMatch],
    ) -> list[ScoredMatchEvidence]:
        return [
            ScoredMatchEvidence(
                requirement=match.requirement,
                candidate_source=match.candidate_evidence[0].source_type,
                candidate_evidence=[match.candidate_evidence[0].text],
                match_strength={
                    "full_match": "full",
                    "partial_match": "partial",
                    "transferable_match": "transferable",
                }[match.match_status],
            )
            for match in matches
            if match.match_status != "missing" and match.candidate_evidence
        ]

    def _explanation(
        self,
        score: int,
        matches: list[RequirementMatch],
        penalty: int,
    ) -> str:
        counts = {
            status: sum(match.match_status == status for match in matches)
            for status in STATUS_VALUE
        }
        return sanitize_user_facing_text(
            f"Score {score}/100 from {counts['full_match']} full, "
            f"{counts['partial_match']} partial, "
            f"{counts['transferable_match']} transferable, and "
            f"{counts['missing']} missing requirement decisions. "
            f"Risk penalties reduced the score by {penalty} points."
        )

    def _recommendation(self, score: int) -> str:
        if score >= 80:
            return "Strong match"
        if score >= 65:
            return "Good match after tailoring"
        if score >= 50:
            return "Partial match"
        return "Low match"

    def _normalize(self, value: str) -> str:
        value = value.casefold().replace("&", " and ")
        value = re.sub(r"[^a-z0-9+#.]+", " ", value)
        return " ".join(
            TERM_NORMALIZATIONS.get(token, token)
            for token in value.split()
        )

    def _token_coverage(
        self,
        requirement_tokens: frozenset[str],
        evidence_tokens: frozenset[str],
    ) -> float:
        if not requirement_tokens:
            return 0
        return len(requirement_tokens & evidence_tokens) / len(requirement_tokens)

    def _phrase_present(self, phrase: str, text: str) -> bool:
        return bool(phrase) and f" {phrase} " in f" {text} "

    def _nonempty(self, values: list[str | None]) -> list[str]:
        return [value for value in values if value and value.strip()]

    def _deduplicate_index(
        self,
        items: list[CandidateEvidenceItem],
    ) -> list[CandidateEvidenceItem]:
        seen: set[tuple[str, str]] = set()
        result = []
        for item in items:
            key = (item.source_type, self._normalize(item.text))
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def _has_type(
        self,
        requirements: list[JobRequirement],
        types: set[RequirementType],
    ) -> bool:
        return any(item.requirement_type in types for item in requirements)

    def _cosine_similarity(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        if not left or not right or len(left) != len(right):
            return 0
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0
        return sum(a * b for a, b in zip(left, right, strict=True)) / (
            left_norm * right_norm
        )
