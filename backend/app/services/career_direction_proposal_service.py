from app.core.config import settings
from app.schemas.common import PreferredLanguage
from app.schemas.career_direction import (
    CandidateEvidenceSummary,
    CareerDirectionProposalSet,
)
from app.services.language_preferences import advisor_language_instruction
from app.services.llm_service import LLMService, LLMServiceError

CAREER_DIRECTION_PROMPT = """
Propose 8 to 12 evidence-grounded career directions for one candidate.

Rules:
- Use only the supplied evidence items and cite their evidence_id values.
- Never invent skills, work, projects, education, certifications, languages,
  metrics, or links.
- Do not recommend fashionable roles without direct supporting evidence.
- An isolated skill token is not enough for a primary direction.
- Evaluate the complete evidence pattern. A single activity or transferable
  experience must not rival a direction supported coherently by education,
  skills, projects, work, papers, patents, or certifications.
- Cite evidence from multiple source types when the profile supports it. Do not
  cherry-pick one item while ignoring a stronger, coherent evidence pattern.
- Prefer specific directions when work, project, paper, patent, or substantial
  education evidence supports them.
- Label adjacent paths as transferable or exploratory rather than overstating fit.
- Do not include General Internship Pathways unless the evidence is sparse,
  broad, or unclear.
- Use only the controlled role_family and seniority values in the schema.
- possible_gaps must describe absent evidence, not invented candidate weaknesses.
- example_job_titles must be plausible examples for the proposed direction.
- Do not rank the directions and do not assign scores.
""".strip()


class CareerDirectionProposalService:
    def __init__(
        self,
        llm_service: LLMService | None = None,
        *,
        enabled: bool = True,
    ) -> None:
        self.llm_service = llm_service or LLMService(
            model=settings.openai_direction_model or settings.openai_model,
            timeout_seconds=(
                settings.openai_direction_timeout_seconds
                or settings.openai_timeout_seconds
            ),
        )
        self.enabled = enabled

    @property
    def is_available(self) -> bool:
        return self.enabled and bool(
            self.llm_service.api_key or self.llm_service.mock_response_factory
        )

    async def propose(
        self,
        summary: CandidateEvidenceSummary,
        preferred_language: PreferredLanguage = "en",
    ) -> CareerDirectionProposalSet | None:
        if not self.is_available:
            return None
        try:
            return await self.llm_service.generate_structured(
                system_prompt=CAREER_DIRECTION_PROMPT,
                user_prompt=(
                    advisor_language_instruction(preferred_language)
                    + "\nFor career directions, translate user-facing direction "
                    "names, rationales, possible gaps, and example job titles "
                    "according to the language preference when natural. Do not "
                    "translate evidence_id values or controlled enum values.\n\n"
                    "Candidate evidence summary:\n"
                    + summary.model_dump_json(indent=2)
                ),
                response_model=CareerDirectionProposalSet,
            )
        except LLMServiceError:
            return None
