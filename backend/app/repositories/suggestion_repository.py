from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.suggestion import Suggestion


class SuggestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, suggestion_id: UUID, user_id: UUID) -> Suggestion | None:
        # TODO: Join through the resume to enforce user ownership.
        raise NotImplementedError

    async def add(self, suggestion: Suggestion) -> Suggestion:
        self.session.add(suggestion)
        await self.session.flush()
        return suggestion
