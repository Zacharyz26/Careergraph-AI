from app.schemas.match import EvidenceJudgeResult
from app.services.llm_service import LLMService, LLMServiceError

EVIDENCE_JUDGE_PROMPT = """
Judge whether the supplied candidate evidence supports one job requirement.

Rules:
- Use only the candidate evidence strings provided.
- Never add, rewrite, or infer evidence that is not present.
- Choose exactly one status: full_match, partial_match, transferable_match, or
  missing.
- full_match requires direct support.
- partial_match requires meaningful but incomplete support.
- transferable_match means related evidence that may transfer but does not
  directly satisfy the requirement.
- missing means no supplied evidence supports the requirement.
- supported_evidence must contain only exact strings from the supplied list.
- Do not assign any aggregate or final score.
""".strip()


class EvidenceJudgeService:
    def __init__(
        self,
        llm_service: LLMService | None = None,
        *,
        enabled: bool = False,
    ) -> None:
        self.llm_service = llm_service or LLMService()
        self.enabled = enabled

    @property
    def is_available(self) -> bool:
        return self.enabled and bool(
            self.llm_service.api_key or self.llm_service.mock_response_factory
        )

    async def judge(
        self,
        *,
        requirement: str,
        candidate_evidence: list[str],
    ) -> EvidenceJudgeResult | None:
        if not self.is_available or not candidate_evidence:
            return None
        try:
            result = await self.llm_service.generate_structured(
                system_prompt=EVIDENCE_JUDGE_PROMPT,
                user_prompt=(
                    f"Requirement:\n{requirement}\n\n"
                    "Candidate evidence:\n"
                    + "\n".join(f"- {item}" for item in candidate_evidence)
                ),
                response_model=EvidenceJudgeResult,
            )
        except LLMServiceError:
            return None

        allowed = set(candidate_evidence)
        supported = [item for item in result.supported_evidence if item in allowed]
        if result.match_status != "missing" and not supported:
            return EvidenceJudgeResult(
                match_status="missing",
                confidence=1,
                reason="The judge returned no supported candidate evidence.",
                supported_evidence=[],
            )
        return result.model_copy(update={"supported_evidence": supported})
