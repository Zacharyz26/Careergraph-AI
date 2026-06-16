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
- Review the complete structured profile before identifying a gap. Do not
  suggest adding information that already exists in another section.
- Improve wording, structure, clarity, emphasis, grouping, and positioning only.
- Prioritize substantive improvements to work, projects, patents, skills,
  section emphasis, and target-direction alignment.
- Do not return no-op rewrites, cosmetic formatting advice, placeholder text, or
  generic suggestions that merely repeat the source evidence.
- If a useful rewrite requires a missing metric or fact, keep the safe existing
  wording and put the missing information in missing_but_not_addable.
- If evidence is weak or ambiguous, use medium or high risk.
- Distinguish changes that can be made now from gaps requiring future learning
  or project work.
- requires_user_review must always be true.
- should_add_to_resume must be false for gap disclosures and unsupported claims.
- Keep suggestions specific and actionable.
""".strip()

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
PLACEHOLDER_PATTERN = re.compile(
    r"\[(?:insert|add|metric|number|details?)[^\]]*\]"
    r"|<(?:insert|add|metric|number|details?)[^>]*>"
    r"|\b(?:tbd|xx+|x%)\b",
    re.IGNORECASE,
)
COSMETIC_TERMS = {
    "font",
    "font size",
    "formatting",
    "margin",
    "spacing",
    "template",
    "typography",
    "color scheme",
    "visual layout",
}
LOW_INFORMATION_TOKENS = {
    "add",
    "clarify",
    "clear",
    "evidence",
    "include",
    "missing",
    "needs",
    "resume",
    "section",
    "unclear",
}
SUGGESTION_PRIORITY = {
    "bullet_rewrite": 0,
    "experience_emphasis": 1,
    "project_emphasis": 2,
    "evidence_strengthening": 3,
    "skill_grouping": 4,
    "section_reorder": 5,
    "headline_summary": 6,
    "gap_disclosure": 7,
}


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
            "candidate_profile": request.candidate_profile.model_dump(),
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
        seen_suggestions: set[tuple[str, str, tuple[str, ...]]] = set()

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
            low_value_reason = self._low_value_reason(suggestion, evidence)
            if low_value_reason:
                warnings.append(
                    "Removed a low-value suggestion: " + low_value_reason
                )
                continue

            risk = suggestion.risk_level
            if evidence and max(item.evidence_strength for item in evidence) < 0.75:
                risk = "medium" if risk == "low" else risk

            validated = suggestion.model_copy(
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
            key = (
                validated.suggestion_type,
                self._normalize(validated.suggested_text),
                tuple(validated.source_evidence_ids),
            )
            if key in seen_suggestions:
                warnings.append("Removed a duplicate suggestion.")
                continue
            seen_suggestions.add(key)
            safe_suggestions.append(validated)

        generated_missing = self._known_generated_gaps(
            generated.missing_but_not_addable,
            unsupported,
        )
        missing = self._deduplicate([*unsupported, *generated_missing])
        return SuggestionResponse(
            overall_summary=generated.overall_summary,
            suggestions=sorted(
                safe_suggestions,
                key=lambda item: SUGGESTION_PRIORITY[item.suggestion_type],
            )[:6],
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

        if PLACEHOLDER_PATTERN.search(suggestion.suggested_text):
            reasons.append("contains placeholder text")

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

    def _low_value_reason(
        self,
        suggestion: SuggestionItem,
        evidence: list[CareerEvidenceItem],
    ) -> str | None:
        suggested = self._normalize(suggestion.suggested_text)
        original = self._normalize(suggestion.original_text or "")
        evidence_texts = {self._normalize(item.text) for item in evidence}
        if any(term in suggested for term in COSMETIC_TERMS):
            return "contains cosmetic formatting advice"
        if suggested and (
            suggested == original
            or suggested in evidence_texts
        ):
            return "does not materially change or reposition the source evidence"
        if suggestion.should_add_to_resume and len(suggested.split()) < 3:
            return "is too short to provide a meaningful resume improvement"
        return None

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
        return [
            gap
            for gap in self._deduplicate(gaps)
            if not self._gap_is_already_supported(gap, request)
        ]

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
            section = item.source_type
            suggestions.append(
                SuggestionItem(
                    suggestion_type="section_reorder",
                    target_section=section,
                    original_text=item.text,
                    suggested_text=(
                        f"Prioritize the {section} section and place this supported "
                        f"evidence near the top: {item.text}"
                    ),
                    reason=(
                        "This is among the strongest available evidence for the "
                        "selected direction and can be emphasized without adding claims."
                    ),
                    source_evidence_ids=[item.evidence_id],
                    source_evidence_text=[item.text],
                    related_requirement_or_direction=self._target_label(request),
                    risk_level=(
                        "low" if item.evidence_strength >= 0.85 else "medium"
                    ),
                    requires_user_review=True,
                    should_add_to_resume=False,
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
        return " ".join(
            self._normalize(value)
            for value in self._flatten_values(
                request.candidate_profile.model_dump()
            )
        )

    def _gap_is_already_supported(
        self,
        gap: str,
        request: SuggestionGenerateRequest,
    ) -> bool:
        normalized_gap = self._normalize(gap)
        candidate_text = self._candidate_text(request)
        content_tokens = {
            token
            for token in normalized_gap.split()
            if token not in LOW_INFORMATION_TOKENS and len(token) > 2
        }
        if content_tokens:
            candidate_tokens = set(candidate_text.split())
            coverage = len(content_tokens & candidate_tokens) / len(content_tokens)
            if coverage >= 0.8:
                return True
        gap_concepts = extract_concepts(normalized_gap)
        candidate_concepts = extract_concepts(candidate_text)
        if (
            len(content_tokens) >= 2
            and gap_concepts
            and gap_concepts <= candidate_concepts
        ):
            return True
        if {"link", "links", "url", "github", "portfolio"} & content_tokens:
            profile = request.candidate_profile
            return bool(
                profile.basic_info.linkedin_url
                or profile.basic_info.github_url
                or profile.basic_info.portfolio_url
                or any(project.url for project in profile.projects)
                or any(paper.url for paper in profile.papers)
            )
        return False

    def _flatten_values(self, value: object) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            return [
                text
                for nested in value.values()
                for text in self._flatten_values(nested)
            ]
        if isinstance(value, list):
            return [
                text
                for nested in value
                for text in self._flatten_values(nested)
            ]
        return []

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
