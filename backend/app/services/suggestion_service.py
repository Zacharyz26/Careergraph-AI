from app.schemas.job import JobRequirements
from app.schemas.resume import VerifiedFact
from app.schemas.suggestion import SuggestionRead


class SuggestionService:
    async def generate(
        self,
        current_resume: str,
        job: JobRequirements,
        facts: list[VerifiedFact],
    ) -> list[SuggestionRead]:
        # TODO: Reject any generated suggestion without one or more valid source facts.
        raise NotImplementedError
