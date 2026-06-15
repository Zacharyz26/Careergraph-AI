from app.schemas.career_direction import (
    CandidateEvidenceSummary,
    CareerDirectionProposalSet,
)
from app.services.llm_service import LLMService, LLMServiceError

CAREER_DIRECTION_PROMPT = """
Propose 8 to 12 evidence-grounded career directions for one candidate.

Rules:
- Use only the supplied evidence items and cite their evidence_id values.
- Never invent skills, work, projects, education, certifications, languages,
  metrics, or links.
- Do not recommend fashionable roles without direct supporting evidence.
- An isolated skill token is not enough for a primary direction.
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
        self.llm_service = llm_service or LLMService()
        self.enabled = enabled

    @property
    def is_available(self) -> bool:
        return self.enabled and bool(
            self.llm_service.api_key or self.llm_service.mock_response_factory
        )

    async def propose(
        self,
        summary: CandidateEvidenceSummary,
    ) -> CareerDirectionProposalSet | None:
        if not self.is_available:
            return None
        try:
            return await self.llm_service.generate_structured(
                system_prompt=CAREER_DIRECTION_PROMPT,
                user_prompt=(
                    "Candidate evidence summary:\n"
                    + summary.model_dump_json(indent=2)
                ),
                response_model=CareerDirectionProposalSet,
            )
        except LLMServiceError:
            return None
