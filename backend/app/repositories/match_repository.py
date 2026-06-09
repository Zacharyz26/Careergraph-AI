from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match


class MatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, match_id: UUID, user_id: UUID) -> Match | None:
        # TODO: Implement an ownership-scoped SQLAlchemy select.
        raise NotImplementedError

    async def add(self, match: Match) -> Match:
        self.session.add(match)
        await self.session.flush()
        return match
