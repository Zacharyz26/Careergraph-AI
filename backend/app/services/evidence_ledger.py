import re
from dataclasses import dataclass

from app.schemas.candidate import CandidateProfile
from app.schemas.career_direction import (
    CandidateEvidenceSummary,
    CareerEvidenceItem,
    CareerEvidenceSource,
)
from app.services.matching_taxonomy import extract_concepts
from app.services.user_facing_sanitizer import sanitize_user_facing_text


SOURCE_STRENGTH: dict[CareerEvidenceSource, float] = {
    "education": 0.6,
    "skills": 0.55,
    "work": 1.0,
    "project": 0.85,
    "paper": 0.9,
    "patent": 0.95,
    "certification": 0.75,
    "leadership": 0.95,
    "language": 0.65,
}


@dataclass(frozen=True)
class EvidenceLedger:
    summary: CandidateEvidenceSummary

    @classmethod
    def from_candidate(cls, candidate: CandidateProfile) -> "EvidenceLedger":
        builder = _EvidenceLedgerBuilder()
        builder.add_candidate(candidate)
        return cls(summary=builder.summary())

    def all_evidence(self) -> list[CareerEvidenceItem]:
        return self.summary.all_evidence()

    def by_id(self) -> dict[str, CareerEvidenceItem]:
        return {item.evidence_id: item for item in self.all_evidence()}

    def by_normalized_text(self) -> dict[str, CareerEvidenceItem]:
        return {normalize_text(item.text): item for item in self.all_evidence()}

    def source_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.all_evidence():
            counts[item.source_type] = counts.get(item.source_type, 0) + 1
        return counts


class _EvidenceLedgerBuilder:
    def __init__(self) -> None:
        self.counter = 0
        self.buckets: dict[str, list[CareerEvidenceItem]] = {
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

    def add_candidate(self, candidate: CandidateProfile) -> None:
        for education in candidate.education:
            for text in nonempty(
                [
                    education.degree,
                    education.field_of_study,
                    *education.details,
                    *education.evidence,
                ]
            ):
                self.add("education_signals", "education", text)
        for group in candidate.skills:
            for skill in group.skills:
                self.add("skill_signals", "skills", skill)
        for experience in candidate.experience:
            for text in nonempty(
                [experience.title, *experience.bullets, *experience.evidence]
            ):
                self.add("work_signals", "work", text)
                if is_leadership_signal(text):
                    self.add("leadership_signals", "leadership", text)
        for project in candidate.projects:
            for text in nonempty(
                [
                    project.name,
                    project.description,
                    *project.technologies,
                    *project.bullets,
                    *project.evidence,
                ]
            ):
                self.add("project_signals", "project", text)
        for paper in candidate.papers:
            for text in nonempty(
                [paper.title, paper.description, *paper.topics, *paper.evidence]
            ):
                self.add("paper_signals", "paper", text)
        for patent in candidate.patents:
            for text in nonempty(
                [patent.title, patent.description, *patent.evidence]
            ):
                self.add("patent_signals", "patent", text)
        for certification in candidate.certifications:
            for text in nonempty(
                [certification.name, certification.issuer, *certification.evidence]
            ):
                self.add("certification_signals", "certification", text)
        for language in candidate.languages:
            text = " ".join(nonempty([language.language, language.proficiency]))
            if text:
                self.add("language_signals", "language", text)

    def add(
        self,
        bucket: str,
        source: CareerEvidenceSource,
        text: str,
    ) -> None:
        cleaned = sanitize_user_facing_text(text)
        normalized = normalize_text(cleaned)
        if not normalized:
            return
        if any(normalize_text(item.text) == normalized for item in self.buckets[bucket]):
            return
        self.counter += 1
        self.buckets[bucket].append(
            CareerEvidenceItem(
                evidence_id=f"E{self.counter:03d}",
                source_type=source,
                text=cleaned,
                evidence_strength=SOURCE_STRENGTH[source],
                normalized_concepts=sorted(extract_concepts(normalized)),
            )
        )

    def summary(self) -> CandidateEvidenceSummary:
        return CandidateEvidenceSummary(**self.buckets)


def normalize_text(value: str) -> str:
    value = value.casefold().replace("&", " and ")
    value = re.sub(r"[^a-z0-9+#.%:/-]+", " ", value)
    return " ".join(value.split())


def nonempty(values: list[str | None]) -> list[str]:
    return [value for value in values if value and value.strip()]


def is_leadership_signal(text: str) -> bool:
    normalized = normalize_text(text)
    return any(
        token in normalized
        for token in {
            "led",
            "lead",
            "managed",
            "coordinated",
            "organized",
            "president",
            "captain",
            "director",
        }
    )
