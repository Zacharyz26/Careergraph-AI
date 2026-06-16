import json
import re

from app.schemas.career_direction import (
    CandidateEvidenceSummary,
    CareerEvidenceItem,
)
from app.schemas.suggestion import (
    AdvisorQuality,
    EvidenceGapItem,
    EvidenceGapCategory,
    PositioningAdviceItem,
    RecommendedNextActionItem,
    SuggestionGenerateRequest,
    SuggestionItem,
    SuggestionResponse,
)
from app.core.config import settings
from app.services.advisor_planner import AdvisorPlanner
from app.services.career_direction_service import CareerDirectionService
from app.services.llm_service import LLMService, LLMServiceError, MissingAPIKeyError
from app.services.matching_taxonomy import extract_concepts
from app.services.user_facing_sanitizer import (
    sanitize_user_facing_text,
    user_facing_artifact_reasons,
)

SUGGESTION_SYSTEM_PROMPT = """
Generate an evidence-grounded Resume Positioning and Career Gap Advisor response.

Safety rules:
- Use only the supplied candidate evidence.
- Never invent skills, tools, certifications, projects, employment, links,
  metrics, achievements, dates, or education.
- resume_ready_improvements are the only resume-ready text. Every item must cite
  valid source evidence IDs in metadata and preserve factual meaning.
- Never put internal evidence IDs, debug markers, citation tokens, or trace IDs
  inside resume-ready text.
- Missing requirements and direction gaps must go in evidence_gaps,
  recommended_next_actions, and missing_but_not_addable; never insert them into
  resume_ready_improvements.
- Review the complete structured profile before identifying a gap. Do not
  suggest adding information that already exists in another section.
- Positioning advice should explain how to emphasize existing evidence, group
  skills, order sections, choose section emphasis, and align the resume to the
  target direction.
- Prioritize substantive improvements to work, projects, patents, skills,
  section emphasis, and target-direction alignment.
- Do not return no-op rewrites, cosmetic formatting advice, placeholder text, or
  generic suggestions that merely repeat the source evidence.
- If a useful improvement requires a missing metric or fact, put it in
  evidence_gaps and recommended_next_actions instead of resume-ready text.
- recommended_next_actions must be concrete ways to build evidence, such as a
  project, portfolio artifact, measurement plan, demo link, deployment exercise,
  certification study, case study, analysis sample, or writing sample. Keep the
  action general to the target direction and evidence gap.
- If evidence is weak or ambiguous, use medium or high risk.
- Distinguish changes that can be made now from gaps requiring future learning
  or project work.
- requires_user_review must always be true.
- should_add_to_resume must be false for gap disclosures and unsupported claims.
- Keep suggestions specific and actionable.
""".strip()

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
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
HIGH_VALUE_SECTIONS = {"work", "project", "paper", "patent", "skills"}
ACTION_VERBS = {
    "analyze",
    "build",
    "complete",
    "create",
    "deploy",
    "design",
    "document",
    "measure",
    "publish",
    "validate",
    "write",
}
ROLE_FAMILY_ENHANCEMENT_GAPS = {
    "software": [
        "Production or deployment evidence for relevant projects",
        "Repository, demo, or portfolio links for technical work",
        "API integration, testing, or system design evidence",
        "Impact, usage, reliability, or performance metrics",
    ],
    "engineering": [
        "Implementation or delivery evidence for core technical work",
        "Design, testing, validation, or failure-analysis evidence",
        "Portfolio, demo, report, or project artifact links",
        "Impact, efficiency, quality, or performance metrics",
    ],
    "data": [
        "SQL, Python, dashboard, or analytics tooling evidence",
        "Model, experiment, or analysis evaluation evidence",
        "Portfolio, notebook, dashboard, or case study links",
        "Business impact, accuracy, lift, or decision outcome metrics",
    ],
    "finance": [
        "Financial modeling, valuation, or investment analysis sample evidence",
        "Excel, Python, SQL, Bloomberg, Tableau, or data tooling evidence",
        "Investment memo, research note, presentation, or deck evidence",
        "Impact, return, risk, forecast accuracy, or decision outcome metrics",
    ],
    "consulting": [
        "Client problem framing, recommendation, or case study evidence",
        "Presentation, deck, workshop, or stakeholder communication evidence",
        "Analytical model, research, or market sizing artifact evidence",
        "Impact, adoption, savings, revenue, or operational outcome metrics",
    ],
    "marketing": [
        "Campaign, content, or growth case study evidence",
        "Analytics, CRM, SEO, paid media, or experimentation tooling evidence",
        "Portfolio, sample, landing page, or content links",
        "Conversion, reach, pipeline, revenue, retention, or engagement metrics",
    ],
    "design": [
        "Portfolio or case study links for design work",
        "User research, usability testing, or design rationale evidence",
        "Figma, prototyping, design system, or handoff tooling evidence",
        "User, conversion, accessibility, or adoption outcome metrics",
    ],
    "healthcare": [
        "Clinical, patient, research, or operational domain evidence",
        "License, certification, training, or compliance evidence when required",
        "Documentation, protocol, quality improvement, or case evidence",
        "Patient, safety, efficiency, quality, or outcome metrics",
    ],
    "legal": [
        "Legal research, memo, brief, contract, or policy writing sample evidence",
        "Regulatory, compliance, litigation, or transaction domain evidence",
        "Client, stakeholder, negotiation, or review-process evidence",
        "Risk reduction, cycle-time, accuracy, or matter outcome metrics",
    ],
    "hr": [
        "Recruiting, talent, learning, or people-program evidence",
        "ATS, HRIS, analytics, survey, or compensation tooling evidence",
        "Program materials, playbooks, training, or policy artifacts",
        "Hiring, retention, engagement, time-to-fill, or process metrics",
    ],
    "operations": [
        "Process improvement, supply chain, project, or program evidence",
        "Dashboard, ERP, spreadsheet, automation, or analytics tooling evidence",
        "SOP, workflow, project plan, or implementation artifact evidence",
        "Cost, cycle-time, throughput, quality, or efficiency metrics",
    ],
    "education": [
        "Teaching, curriculum, tutoring, or learning-design evidence",
        "Lesson plan, curriculum, assessment, or portfolio artifact evidence",
        "Classroom, LMS, assessment, or education technology evidence",
        "Learner outcome, engagement, completion, or improvement metrics",
    ],
    "product": [
        "Roadmap, requirements, launch, or product discovery evidence",
        "User research, experiment, analytics, or prioritization evidence",
        "PRD, prototype, case study, or portfolio artifact links",
        "Adoption, retention, conversion, revenue, or usage metrics",
    ],
}
GENERAL_ENHANCEMENT_GAPS = [
    "Portfolio, work sample, demo, or project artifact evidence",
    "Target-relevant tooling or platform evidence",
    "Impact, scale, quality, or outcome metrics",
]


class SuggestionService:
    def __init__(
        self,
        llm_service: LLMService | None = None,
        evidence_service: CareerDirectionService | None = None,
        advisor_planner: AdvisorPlanner | None = None,
    ) -> None:
        self.llm_service = llm_service or LLMService(
            model=settings.openai_advisor_model or settings.openai_model
        )
        self.evidence_service = evidence_service or CareerDirectionService()
        self.advisor_planner = advisor_planner or AdvisorPlanner()

    async def generate(
        self,
        request: SuggestionGenerateRequest,
    ) -> SuggestionResponse:
        summary = self.evidence_service.build_evidence_summary(
            request.candidate_profile
        )
        if not summary.all_evidence():
            gaps = self._unsupported_gaps(request)
            return SuggestionResponse(
                overall_summary=(
                    "The profile needs more concrete resume evidence before "
                    "meaningful positioning advice can be generated."
                ),
                evidence_gaps=self._gap_items(gaps, request),
                recommended_next_actions=self._next_actions(gaps, request),
                missing_but_not_addable=gaps,
                warnings=["No resume-ready claims were generated."],
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
            "advisor_plan": self.advisor_planner.plan(
                summary,
                self._target_role_family(request),
            ).model_context(),
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
        safe_improvements = []
        safe_positioning = []
        warnings = list(generated.warnings)
        seen_suggestions: set[tuple[str, str, tuple[str, ...]]] = set()

        for suggestion in generated.resume_ready_improvements:
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
                    "suggested_text": sanitize_user_facing_text(
                        suggestion.suggested_text
                    ),
                    "reason": sanitize_user_facing_text(suggestion.reason),
                    "target_section": sanitize_user_facing_text(
                        suggestion.target_section
                    ),
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
            quality_score = self._quality_score_improvement(
                validated,
                evidence,
                request,
            )
            if quality_score < 45:
                warnings.append(
                    "Removed a low-value suggestion: quality score below threshold."
                )
                continue
            validated = validated.model_copy(
                update={
                    "quality_score": quality_score,
                    "quality_level": self._quality_level(quality_score),
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
            safe_improvements.append(validated)

        for advice in generated.positioning_advice:
            evidence = self._resolve_advice_evidence(
                advice,
                evidence_by_id,
                evidence_by_text,
            )
            if not evidence:
                warnings.append(
                    "Removed positioning advice that had no valid source evidence."
                )
                continue
            artifact_reasons = user_facing_artifact_reasons(advice.advice)
            if artifact_reasons:
                warnings.append(
                    "Removed positioning advice with user-facing artifacts: "
                    + "; ".join(artifact_reasons)
                )
                continue
            if self._low_value_text_reason(advice.advice):
                warnings.append(
                    "Removed low-value positioning advice: "
                    + self._low_value_text_reason(advice.advice)
                )
                continue
            quality_score = self._quality_score_positioning(
                advice,
                evidence,
                request,
            )
            if quality_score < 45:
                warnings.append(
                    "Removed low-value positioning advice: quality score below threshold."
                )
                continue
            safe_positioning.append(
                advice.model_copy(
                    update={
                        "advice": sanitize_user_facing_text(advice.advice),
                        "reason": sanitize_user_facing_text(advice.reason),
                        "target_section": sanitize_user_facing_text(
                            advice.target_section
                        ),
                        "source_evidence_ids": [
                            item.evidence_id for item in evidence
                        ],
                        "source_evidence_text": [item.text for item in evidence],
                        "quality_score": quality_score,
                        "quality_level": self._quality_level(quality_score),
                        "requires_user_review": True,
                    }
                )
            )

        generated_missing = self._known_generated_gaps(
            generated.missing_but_not_addable,
            unsupported,
        )
        generated_gap_values = [
            sanitize_user_facing_text(gap.gap)
            for gap in generated.evidence_gaps
            if not self._gap_is_already_supported(gap.gap, request)
        ]
        missing = self._deduplicate(
            [*unsupported, *generated_missing, *generated_gap_values]
        )
        evidence_gaps = self._merge_gap_items(
            self._gap_items(missing, request),
            generated.evidence_gaps,
            request,
        )
        next_actions = self._merge_next_actions(
            self._next_actions(missing, request),
            generated.recommended_next_actions,
            missing,
        )
        return SuggestionResponse(
            overall_summary=sanitize_user_facing_text(generated.overall_summary),
            resume_ready_improvements=sorted(
                safe_improvements,
                key=lambda item: (
                    item.quality_score,
                    -SUGGESTION_PRIORITY[item.suggestion_type],
                ),
                reverse=True,
            )[:6],
            positioning_advice=sorted(
                safe_positioning,
                key=lambda item: item.quality_score,
                reverse=True,
            )[:6],
            evidence_gaps=sorted(
                evidence_gaps,
                key=lambda item: self._priority_rank(item.priority),
                reverse=True,
            )[:8],
            recommended_next_actions=sorted(
                next_actions,
                key=lambda item: (
                    self._priority_rank(item.priority),
                    item.quality_score,
                ),
                reverse=True,
            )[:8],
            missing_but_not_addable=missing,
            warnings=self._deduplicate(
                [sanitize_user_facing_text(warning) for warning in warnings]
            ),
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

    def _resolve_advice_evidence(
        self,
        advice: PositioningAdviceItem,
        evidence_by_id: dict[str, CareerEvidenceItem],
        evidence_by_text: dict[str, CareerEvidenceItem],
    ) -> list[CareerEvidenceItem]:
        evidence = [
            evidence_by_id[evidence_id]
            for evidence_id in advice.source_evidence_ids
            if evidence_id in evidence_by_id
        ]
        evidence.extend(
            evidence_by_text[normalized]
            for text in advice.source_evidence_text
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

        reasons.extend(user_facing_artifact_reasons(suggestion.suggested_text))

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

    def _low_value_text_reason(self, text: str) -> str | None:
        normalized = self._normalize(text)
        if any(term in normalized for term in COSMETIC_TERMS):
            return "contains cosmetic formatting advice"
        if len(normalized.split()) < 5:
            return "is too short to be actionable"
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
        gaps.extend(self._enhancement_gaps(request, gaps))
        return [
            sanitize_user_facing_text(gap)
            for gap in self._deduplicate([sanitize_user_facing_text(gap) for gap in gaps])
            if not self._gap_is_already_supported(gap, request)
        ]

    def _enhancement_gaps(
        self,
        request: SuggestionGenerateRequest,
        current_gaps: list[str],
    ) -> list[str]:
        if request.suggestion_mode == "job_specific" and current_gaps:
            return []
        if not (
            request.target_direction
            or request.career_direction_result
            or request.job_profile
        ):
            return []

        role_context = " ".join(
            value
            for value in [
                request.target_direction,
                request.career_direction_result.direction
                if request.career_direction_result
                else None,
                request.career_direction_result.role_family
                if request.career_direction_result
                else None,
                request.job_profile.job_title if request.job_profile else None,
                request.job_profile.role_family if request.job_profile else None,
            ]
            if value
        )
        normalized_context = self._normalize(role_context)
        summary = self.evidence_service.build_evidence_summary(
            request.candidate_profile
        )
        plan = self.advisor_planner.plan(summary, self._target_role_family(request))
        planned_gaps = [
            gap.label
            for gap in [*plan.missing_proof, *plan.optional_enhancements]
        ]
        selected_gaps = [
            gap
            for gap in planned_gaps
        ] or [
            gap
            for family, gaps in ROLE_FAMILY_ENHANCEMENT_GAPS.items()
            if family in normalized_context
            for gap in gaps
        ] or GENERAL_ENHANCEMENT_GAPS

        existing_categories = {
            self._gap_category(gap)
            for gap in current_gaps
            if not self._gap_is_already_supported(gap, request)
        }
        enhancement_gaps = []
        for gap in selected_gaps:
            category = self._gap_category(gap)
            if category in existing_categories:
                continue
            if self._gap_is_already_supported(gap, request):
                continue
            enhancement_gaps.append(gap)
            existing_categories.add(category)
            if len(enhancement_gaps) >= 4:
                break
        return enhancement_gaps

    def _deterministic_fallback(
        self,
        request: SuggestionGenerateRequest,
        summary: CandidateEvidenceSummary,
    ) -> SuggestionResponse:
        plan = self.advisor_planner.plan(summary, self._target_role_family(request))
        evidence = sorted(
            summary.all_evidence(),
            key=lambda item: item.evidence_strength,
            reverse=True,
        )
        improvements = []
        positioning = []
        planned_evidence_text = {proof.text for proof in plan.strong_proof}
        prioritized_evidence = [
            item for item in evidence if item.text in planned_evidence_text
        ] or evidence
        for item in prioritized_evidence[:3]:
            section = item.source_type
            advice_text = (
                f"Lead the {section} section with this target-relevant proof: "
                f"{item.text}"
            )
            advice_text = sanitize_user_facing_text(advice_text)
            quality_score = self._quality_score_positioning_text(
                section=section,
                text=item.text,
                advice=advice_text,
                evidence_strength=item.evidence_strength,
                request=request,
            )
            positioning.append(
                PositioningAdviceItem(
                    target_section=section,
                    advice=advice_text,
                    reason=(
                        "This is among the strongest available evidence for the "
                        "selected direction and can be emphasized without adding claims."
                    ),
                    source_evidence_ids=[item.evidence_id],
                    source_evidence_text=[item.text],
                    related_requirement_or_direction=self._target_label(request),
                    quality_score=quality_score,
                    quality_level=self._quality_level(quality_score),
                    requires_user_review=True,
                )
            )
        gaps = self._unsupported_gaps(request)
        return SuggestionResponse(
            overall_summary=(
                "Generated conservative career-positioning advice from the "
                "strongest available evidence and current target gaps."
            ),
            resume_ready_improvements=improvements[:3],
            positioning_advice=sorted(
                positioning,
                key=lambda item: item.quality_score,
                reverse=True,
            ),
            evidence_gaps=self._gap_items(gaps, request),
            recommended_next_actions=self._next_actions(gaps, request),
            missing_but_not_addable=gaps,
            warnings=[
                "LLM generation was unavailable; only conservative positioning guidance was returned."
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

    def _target_role_family(
        self,
        request: SuggestionGenerateRequest,
    ) -> str | None:
        if request.career_direction_result:
            return request.career_direction_result.role_family
        if request.job_profile:
            return request.job_profile.role_family
        if request.target_direction:
            normalized_target = self._normalize(request.target_direction)
            for role in request.candidate_profile.inferred_target_roles:
                if (
                    self._normalize(role.role) in normalized_target
                    or normalized_target in self._normalize(role.role)
                ):
                    return role.role_family
        if request.candidate_profile.inferred_target_roles:
            return request.candidate_profile.inferred_target_roles[0].role_family
        return None

    def _gap_items(
        self,
        gaps: list[str],
        request: SuggestionGenerateRequest,
    ) -> list[EvidenceGapItem]:
        target = self._target_label(request)
        return [
            EvidenceGapItem(
                gap=sanitize_user_facing_text(gap),
                category=self._gap_category(gap),
                priority=self._gap_priority(gap, index),
                why_it_matters=sanitize_user_facing_text(
                    f"This signal is relevant to {target} positioning."
                    if target
                    else "This would make the resume positioning more credible and complete."
                ),
                evidence_needed=sanitize_user_facing_text(
                    "Develop a concrete proof point first, such as a project, "
                    "role experience, credential, portfolio artifact, measured "
                    "result, or public link."
                ),
                related_requirement_or_direction=(
                    sanitize_user_facing_text(target) if target else None
                ),
                should_add_to_resume=False,
                requires_user_review=True,
            )
            for index, gap in enumerate(gaps)
        ]

    def _next_actions(
        self,
        gaps: list[str],
        request: SuggestionGenerateRequest,
    ) -> list[RecommendedNextActionItem]:
        target = self._target_label(request)
        return [
            RecommendedNextActionItem(
                action=sanitize_user_facing_text(self._action_for_gap(gap, target)),
                rationale=sanitize_user_facing_text(
                    "This gives you a stronger proof point to reference in future "
                    "resume updates."
                ),
                target_gap=sanitize_user_facing_text(gap),
                suggested_artifact=sanitize_user_facing_text(
                    "A portfolio entry, case study, demo, credential, project "
                    "write-up, or measured result from real work."
                ),
                priority=self._gap_priority(gap, index),
                quality_score=self._quality_score_action(gap, target, index),
                quality_level=self._quality_level(
                    self._quality_score_action(gap, target, index)
                ),
                should_add_to_resume=False,
                requires_user_review=True,
            )
            for index, gap in enumerate(gaps[:6])
        ]

    def _action_for_gap(self, gap: str, target: str | None) -> str:
        normalized = self._normalize(gap)
        if any(token in normalized for token in {"link", "github", "portfolio", "demo"}):
            return "Publish or attach a real project, portfolio, GitHub, or demo link for existing work."
        if any(token in normalized for token in {"deploy", "deployment", "cloud", "docker", "kubernetes", "api"}):
            return "Build a small deployable project that demonstrates the missing implementation or production signal."
        if any(token in normalized for token in {"metric", "impact", "result", "performance"}):
            return "Measure an existing project or work result and document the method before adding impact claims."
        if any(token in normalized for token in {"certification", "credential"}):
            return "Complete the credential before listing it, or omit it from resume-ready text."
        if target:
            return f"Create a concrete artifact that demonstrates '{gap}' for {target}."
        return f"Create concrete evidence for '{gap}' before adding it to the resume."

    def _merge_gap_items(
        self,
        base: list[EvidenceGapItem],
        generated: list[EvidenceGapItem],
        request: SuggestionGenerateRequest,
    ) -> list[EvidenceGapItem]:
        by_gap = {self._normalize(item.gap): item for item in base}
        for item in generated:
            normalized = self._normalize(item.gap)
            if not normalized or self._gap_is_already_supported(item.gap, request):
                continue
            by_gap[normalized] = item.model_copy(
                update={
                    "category": self._gap_category(item.gap),
                    "priority": self._gap_priority(item.gap, 0),
                    "should_add_to_resume": False,
                    "requires_user_review": True,
                }
            )
        return list(by_gap.values())

    def _merge_next_actions(
        self,
        base: list[RecommendedNextActionItem],
        generated: list[RecommendedNextActionItem],
        gaps: list[str],
    ) -> list[RecommendedNextActionItem]:
        known_gaps = {self._normalize(gap) for gap in gaps}
        seen = {self._normalize(item.action) for item in base}
        result = list(base)
        for item in generated:
            normalized_action = self._normalize(item.action)
            normalized_gap = self._normalize(item.target_gap or "")
            if not normalized_action or normalized_action in seen:
                continue
            if normalized_gap and normalized_gap not in known_gaps:
                continue
            seen.add(normalized_action)
            quality_score = self._quality_score_action(
                item.target_gap or item.action,
                None,
                len(result),
                item.action,
            )
            result.append(
                item.model_copy(
                    update={
                        "quality_score": quality_score,
                        "quality_level": self._quality_level(quality_score),
                        "should_add_to_resume": False,
                        "requires_user_review": True,
                    }
                )
            )
        return result

    def _quality_score_improvement(
        self,
        suggestion: SuggestionItem,
        evidence: list[CareerEvidenceItem],
        request: SuggestionGenerateRequest,
    ) -> int:
        score = 35
        if suggestion.suggestion_type in {
            "experience_emphasis",
            "project_emphasis",
            "evidence_strengthening",
            "skill_grouping",
        }:
            score += 15
        if suggestion.target_section.casefold() in HIGH_VALUE_SECTIONS:
            score += 10
        if evidence:
            score += round(max(item.evidence_strength for item in evidence) * 20)
            if len({item.source_type for item in evidence}) > 1:
                score += 8
        if self._target_label(request) and suggestion.related_requirement_or_direction:
            score += 10
        token_count = len(self._normalize(suggestion.suggested_text).split())
        if token_count >= 8:
            score += 8
        elif token_count <= 4:
            score -= 12
        if suggestion.suggestion_type == "bullet_rewrite":
            score -= 5
        return max(0, min(100, score))

    def _quality_score_positioning(
        self,
        advice: PositioningAdviceItem,
        evidence: list[CareerEvidenceItem],
        request: SuggestionGenerateRequest,
    ) -> int:
        strength = max((item.evidence_strength for item in evidence), default=0.5)
        return self._quality_score_positioning_text(
            section=advice.target_section,
            text=" ".join(item.text for item in evidence),
            advice=advice.advice,
            evidence_strength=strength,
            request=request,
        )

    def _quality_score_positioning_text(
        self,
        *,
        section: str,
        text: str,
        advice: str,
        evidence_strength: float,
        request: SuggestionGenerateRequest,
    ) -> int:
        normalized_advice = self._normalize(advice)
        score = 30 + round(evidence_strength * 25)
        if section.casefold() in HIGH_VALUE_SECTIONS:
            score += 12
        if self._target_label(request):
            score += 10
        if any(
            token in normalized_advice
            for token in {"prioritize", "lead", "group", "emphasize", "place"}
        ):
            score += 10
        if len(set(normalized_advice.split()) - LOW_INFORMATION_TOKENS) >= 8:
            score += 8
        if self._normalize(text) and self._normalize(text) in normalized_advice:
            score += 5
        return max(0, min(100, score))

    def _quality_score_action(
        self,
        gap: str,
        target: str | None,
        index: int,
        action: str | None = None,
    ) -> int:
        action_text = self._normalize(action or self._action_for_gap(gap, target))
        score = 45
        if self._gap_category(gap) in {
            "target_skill",
            "implementation_or_delivery",
            "portfolio_or_proof",
            "impact_or_metrics",
        }:
            score += 15
        if ACTION_VERBS & set(action_text.split()):
            score += 15
        if target:
            score += 8
        if index < 3:
            score += 7
        if len(action_text.split()) >= 8:
            score += 5
        return max(0, min(100, score))

    def _quality_level(self, score: int) -> AdvisorQuality:
        if score >= 75:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    def _priority_rank(self, priority: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)

    def _gap_category(self, gap: str) -> EvidenceGapCategory:
        normalized = self._normalize(gap)
        if any(
            token in normalized
            for token in {"certification", "credential", "degree", "coursework", "license"}
        ):
            return "credential_or_education"
        if any(
            token in normalized
            for token in {"deploy", "deployment", "production", "serving", "api integration", "implementation"}
        ):
            return "implementation_or_delivery"
        if any(
            token in normalized
            for token in {"docker", "kubernetes", "aws", "azure", "gcp", "cloud", "tableau", "power bi", "excel", "sql", "figma", "crm"}
        ):
            return "tool_or_platform"
        if any(
            token in normalized
            for token in {
                "link",
                "github",
                "portfolio",
                "demo",
                "case study",
                "sample",
                "artifact",
                "memo",
                "note",
                "deck",
                "report",
            }
        ):
            return "portfolio_or_proof"
        if any(
            token in normalized
            for token in {"metric", "impact", "result", "performance", "conversion", "revenue", "cost", "accuracy"}
        ):
            return "impact_or_metrics"
        if any(
            token in normalized
            for token in {"domain", "industry", "clinical", "patient", "finance", "marketing", "legal", "hr", "operations"}
        ):
            return "domain_experience"
        if any(
            token in normalized
            for token in {
                "positioning",
                "headline",
                "summary",
                "section",
                "story",
                "communication",
                "presentation",
                "stakeholder",
                "client",
            }
        ):
            return "communication_or_positioning"
        if len(normalized.split()) <= 3:
            return "target_skill"
        return "other"

    def _gap_priority(self, gap: str, index: int) -> str:
        category = self._gap_category(gap)
        if category in {
            "target_skill",
            "implementation_or_delivery",
            "portfolio_or_proof",
            "impact_or_metrics",
        }:
            return "high" if index < 5 else "medium"
        if category in {"tool_or_platform", "credential_or_education"}:
            return "medium"
        return "low" if index >= 5 else "medium"

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
