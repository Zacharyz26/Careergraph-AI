from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, resume_id: UUID, user_id: UUID) -> Resume | None:
        # TODO: Implement an ownership-scoped SQLAlchemy select.
        raise NotImplementedError

    async def add(self, resume: Resume) -> Resume:
        self.session.add(resume)
        await self.session.flush()
        return resume
