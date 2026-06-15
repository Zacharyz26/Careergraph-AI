import json
import re

from app.schemas.career_direction import (
    CandidateEvidenceSummary,
    CareerEvidenceItem,
)
from app.schemas.suggestion import (
    SuggestionGenerateRequest,
    SuggestionItem,
    SuggestionResponse,
)
from app.services.career_direction_service import CareerDirectionService
from app.services.llm_service import LLMService, LLMServiceError, MissingAPIKeyError
from app.services.matching_taxonomy import extract_concepts

SUGGESTION_SYSTEM_PROMPT = """
Generate evidence-grounded resume improvement suggestions.

Safety rules:
- Use only the supplied candidate evidence.
- Never invent skills, tools, certifications, projects, employment, links,
  metrics, achievements, dates, or education.
- Every bullet rewrite must cite valid source evidence IDs and preserve factual
  meaning.
- Missing requirements and direction gaps must go in missing_but_not_addable;
  never insert them into suggested resume text.
- Improve wording, structure, clarity, emphasis, grouping, and positioning only.
- If evidence is weak or ambiguous, use medium or high risk.
- Distinguish changes that can be made now from gaps requiring future learning
  or project work.
- requires_user_review must always be true.
- should_add_to_resume must be false for gap disclosures and unsupported claims.
- Keep suggestions specific and actionable.
""".strip()

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")


class SuggestionService:
    def __init__(
        self,
        llm_service: LLMService | None = None,
        evidence_service: CareerDirectionService | None = None,
    ) -> None:
        self.llm_service = llm_service or LLMService()
        self.evidence_service = evidence_service or CareerDirectionService()

    async def generate(
        self,
        request: SuggestionGenerateRequest,
    ) -> SuggestionResponse:
        summary = self.evidence_service.build_evidence_summary(
            request.candidate_profile
        )
        if not summary.all_evidence():
            return SuggestionResponse(
                overall_summary="The profile contains no evidence that can support safe resume changes.",
                missing_but_not_addable=self._unsupported_gaps(request),
                warnings=["No resume claims were generated without source evidence."],
            )

        if not (
            self.llm_service.api_key or self.llm_service.mock_response_factory
        ):
            return self._deterministic_fallback(request, summary)

        try:
            generated = await self.llm_service.generate_structured(
                system_prompt=SUGGESTION_SYSTEM_PROMPT,
                user_prompt=self._build_prompt(request, summary),
                response_model=SuggestionResponse,
            )
        except MissingAPIKeyError:
            return self._deterministic_fallback(request, summary)
        except LLMServiceError:
            return self._deterministic_fallback(request, summary)
        return self._validate_response(request, summary, generated)

    def _build_prompt(
        self,
        request: SuggestionGenerateRequest,
        summary: CandidateEvidenceSummary,
    ) -> str:
        context = {
            "suggestion_mode": request.suggestion_mode,
            "target_direction": request.target_direction,
            "career_direction_result": (
                request.career_direction_result.model_dump()
                if request.career_direction_result
                else None
            ),
            "job_profile": (
                request.job_profile.model_dump() if request.job_profile else None
            ),
            "match_result": (
                request.match_result.model_dump() if request.match_result else None
            ),
            "unsupported_gaps": self._unsupported_gaps(request),
        }
        return (
            "Candidate evidence summary:\n"
            + summary.model_dump_json(indent=2)
            + "\n\nSuggestion context:\n"
            + json.dumps(context, indent=2, default=str)
        )

    def _validate_response(
        self,
        request: SuggestionGenerateRequest,
        summary: CandidateEvidenceSummary,
        generated: SuggestionResponse,
    ) -> SuggestionResponse:
        evidence_by_id = {
            item.evidence_id: item for item in summary.all_evidence()
        }
        evidence_by_text = {
            self._normalize(item.text): item for item in summary.all_evidence()
        }
        unsupported = self._unsupported_gaps(request)
        safe_suggestions = []
        warnings = list(generated.warnings)

        for suggestion in generated.suggestions:
            evidence = self._resolve_evidence(
                suggestion,
                evidence_by_id,
                evidence_by_text,
            )
            if suggestion.should_add_to_resume and not evidence:
                warnings.append(
                    "Removed a resume-ready suggestion that had no valid source evidence."
                )
                continue

            unsafe_reasons = self._unsafe_reasons(
                suggestion,
                evidence,
                unsupported,
                summary,
            )
            if unsafe_reasons:
                warnings.append(
                    "Removed an unsafe suggestion: " + "; ".join(unsafe_reasons)
                )
                continue

            risk = suggestion.risk_level
            if evidence and max(item.evidence_strength for item in evidence) < 0.75:
                risk = "medium" if risk == "low" else risk

            safe_suggestions.append(
                suggestion.model_copy(
                    update={
                        "source_evidence_ids": [
                            item.evidence_id for item in evidence
                        ],
                        "source_evidence_text": [item.text for item in evidence],
                        "risk_level": risk,
                        "should_add_to_resume": suggestion.should_add_to_resume,
                        "requires_user_review": True,
                        "original_text": (
                            evidence[0].text
                            if suggestion.suggestion_type == "bullet_rewrite"
                            and evidence
                            else suggestion.original_text
                        ),
                    }
                )
            )

        generated_missing = self._known_generated_gaps(
            generated.missing_but_not_addable,
            unsupported,
        )
        missing = self._deduplicate([*unsupported, *generated_missing])
        return SuggestionResponse(
            overall_summary=generated.overall_summary,
            suggestions=safe_suggestions,
            missing_but_not_addable=missing,
            suggested_resume_focus=generated.suggested_resume_focus,
            warnings=self._deduplicate(warnings),
        )

    def _resolve_evidence(
        self,
        suggestion: SuggestionItem,
        evidence_by_id: dict[str, CareerEvidenceItem],
        evidence_by_text: dict[str, CareerEvidenceItem],
    ) -> list[CareerEvidenceItem]:
        evidence = [
            evidence_by_id[evidence_id]
            for evidence_id in suggestion.source_evidence_ids
            if evidence_id in evidence_by_id
        ]
        evidence.extend(
            evidence_by_text[normalized]
            for text in suggestion.source_evidence_text
            if (normalized := self._normalize(text)) in evidence_by_text
        )
        return self._deduplicate_evidence(evidence)

    def _unsafe_reasons(
        self,
        suggestion: SuggestionItem,
        evidence: list[CareerEvidenceItem],
        unsupported: list[str],
        summary: CandidateEvidenceSummary,
    ) -> list[str]:
        reasons = []
        suggested = self._normalize(suggestion.suggested_text)
        source_text = " ".join(self._normalize(item.text) for item in evidence)

        for gap in unsupported:
            normalized_gap = self._normalize(gap)
            if normalized_gap and normalized_gap in suggested:
                reasons.append(f"contains unsupported gap '{gap}'")

        for number in NUMBER_PATTERN.findall(suggestion.suggested_text):
            if number not in NUMBER_PATTERN.findall(source_text):
                reasons.append(f"introduces unsupported metric '{number}'")

        for url in URL_PATTERN.findall(suggestion.suggested_text):
            if url.casefold() not in source_text:
                reasons.append("introduces an unsupported link")

        certification_markers = {"certified", "certification", "credential"}
        if (
            certification_markers & set(suggested.split())
            and not certification_markers & set(source_text.split())
        ):
            reasons.append("introduces an unsupported certification claim")

        supported_concepts = set().union(
            *(set(item.normalized_concepts) for item in summary.all_evidence())
        )
        suggested_concepts = extract_concepts(suggested)
        unsupported_concepts = suggested_concepts - supported_concepts
        if unsupported_concepts:
            reasons.append(
                "introduces unsupported concepts: "
                + ", ".join(sorted(unsupported_concepts))
            )
        return reasons

    def _unsupported_gaps(
        self,
        request: SuggestionGenerateRequest,
    ) -> list[str]:
        gaps = []
        candidate_text = self._candidate_text(request)
        if request.match_result:
            gaps.extend(request.match_result.missing_required_skills)
            gaps.extend(request.match_result.missing_preferred_skills)
            gaps.extend(
                match.requirement
                for match in request.match_result.requirement_matches
                if match.match_status == "missing"
            )
        if request.job_profile:
            for requirement in [
                *request.job_profile.required_skills,
                *request.job_profile.preferred_skills,
            ]:
                normalized = self._normalize(requirement.value)
                if normalized and normalized not in candidate_text:
                    gaps.append(requirement.value)
        if request.career_direction_result:
            gaps.extend(request.career_direction_result.gaps_for_this_direction)
        gaps.extend(request.candidate_profile.improvement_areas)
        return self._deduplicate(gaps)

    def _deterministic_fallback(
        self,
        request: SuggestionGenerateRequest,
        summary: CandidateEvidenceSummary,
    ) -> SuggestionResponse:
        evidence = sorted(
            summary.all_evidence(),
            key=lambda item: item.evidence_strength,
            reverse=True,
        )
        suggestions = []
        for item in evidence[:3]:
            suggestion_type = (
                "experience_emphasis"
                if item.source_type in {"work", "leadership"}
                else "project_emphasis"
                if item.source_type in {"project", "paper", "patent"}
                else "skill_grouping"
            )
            suggestions.append(
                SuggestionItem(
                    suggestion_type=suggestion_type,
                    target_section=item.source_type,
                    original_text=item.text,
                    suggested_text=item.text,
                    reason=(
                        "Emphasize this existing evidence for clearer resume "
                        "positioning without changing its factual meaning."
                    ),
                    source_evidence_ids=[item.evidence_id],
                    source_evidence_text=[item.text],
                    related_requirement_or_direction=self._target_label(request),
                    risk_level=(
                        "low" if item.evidence_strength >= 0.85 else "medium"
                    ),
                    requires_user_review=True,
                    should_add_to_resume=True,
                )
            )
        return SuggestionResponse(
            overall_summary=(
                "Generated conservative evidence-emphasis suggestions without "
                "LLM rewriting."
            ),
            suggestions=suggestions,
            missing_but_not_addable=self._unsupported_gaps(request),
            suggested_resume_focus=[
                self._target_label(request)
                or "Lead with the strongest supported experience and projects."
            ],
            warnings=[
                "LLM generation was unavailable; no new wording or claims were created."
            ],
        )

    def _target_label(self, request: SuggestionGenerateRequest) -> str | None:
        if request.target_direction:
            return request.target_direction
        if request.career_direction_result:
            return request.career_direction_result.direction
        if request.job_profile:
            return request.job_profile.job_title or request.job_profile.role_family
        return None

    def _candidate_text(self, request: SuggestionGenerateRequest) -> str:
        summary = self.evidence_service.build_evidence_summary(
            request.candidate_profile
        )
        return " ".join(
            self._normalize(item.text) for item in summary.all_evidence()
        )

    def _known_generated_gaps(
        self,
        generated: list[str],
        known: list[str],
    ) -> list[str]:
        normalized_known = [self._normalize(value) for value in known]
        return [
            value
            for value in generated
            if any(
                normalized
                and (
                    normalized in self._normalize(value)
                    or self._normalize(value) in normalized
                )
                for normalized in normalized_known
            )
        ]

    def _normalize(self, value: str) -> str:
        value = value.casefold().replace("&", " and ")
        value = re.sub(r"[^a-z0-9+#.%:/-]+", " ", value)
        return " ".join(value.split())

    def _deduplicate(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            normalized = self._normalize(value)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(value)
        return result

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
