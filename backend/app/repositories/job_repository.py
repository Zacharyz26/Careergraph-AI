from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: UUID, user_id: UUID) -> Job | None:
        # TODO: Implement an ownership-scoped SQLAlchemy select.
        raise NotImplementedError

    async def add(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.flush()
        return job
