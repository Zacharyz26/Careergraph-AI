from dataclasses import dataclass

from app.schemas.candidate import RoleFamily
from app.schemas.career_direction import CandidateEvidenceSummary, CareerEvidenceItem
from app.services.capability_map import assess_capabilities
from app.services.user_facing_sanitizer import sanitize_user_facing_text


@dataclass(frozen=True)
class AdvisorProof:
    label: str
    source_type: str
    text: str
    evidence_strength: float


@dataclass(frozen=True)
class AdvisorGap:
    label: str
    category: str
    priority: str
    status: str


@dataclass(frozen=True)
class AdvisorPlan:
    strong_proof: tuple[AdvisorProof, ...]
    weak_proof: tuple[AdvisorProof, ...]
    missing_proof: tuple[AdvisorGap, ...]
    optional_enhancements: tuple[AdvisorGap, ...]

    def model_context(self) -> dict[str, object]:
        return {
            "strong_proof": [proof.__dict__ for proof in self.strong_proof],
            "weak_proof": [proof.__dict__ for proof in self.weak_proof],
            "missing_proof": [gap.__dict__ for gap in self.missing_proof],
            "optional_enhancements": [
                gap.__dict__ for gap in self.optional_enhancements
            ],
        }


class AdvisorPlanner:
    def plan(
        self,
        summary: CandidateEvidenceSummary,
        role_family: RoleFamily | str | None,
    ) -> AdvisorPlan:
        evidence = sorted(
            summary.all_evidence(),
            key=lambda item: item.evidence_strength,
            reverse=True,
        )
        strong = tuple(
            self._proof(item)
            for item in evidence
            if item.source_type in {"work", "project", "paper", "patent"}
            and item.evidence_strength >= 0.85
        )[:5]
        weak = tuple(
            self._proof(item)
            for item in evidence
            if item.source_type not in {"work", "project", "paper", "patent"}
        )[:4]
        assessments = assess_capabilities(summary, role_family)
        missing = tuple(
            AdvisorGap(
                label=sanitize_user_facing_text(item.gap_label),
                category=item.signal.category,
                priority=item.priority,
                status=item.status,
            )
            for item in assessments
            if item.status == "missing_proof"
        )
        optional = tuple(
            AdvisorGap(
                label=sanitize_user_facing_text(item.gap_label),
                category=item.signal.category,
                priority=item.priority,
                status=item.status,
            )
            for item in assessments
            if item.status == "optional_enhancement"
        )
        return AdvisorPlan(
            strong_proof=strong,
            weak_proof=weak,
            missing_proof=missing,
            optional_enhancements=optional,
        )

    def _proof(self, item: CareerEvidenceItem) -> AdvisorProof:
        return AdvisorProof(
            label=f"{item.source_type.title()} evidence",
            source_type=item.source_type,
            text=sanitize_user_facing_text(item.text),
            evidence_strength=item.evidence_strength,
        )
