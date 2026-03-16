"""Task service for dispatching background jobs."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.repositories.task_repository import TaskRepository
from workers.tasks import simulate_heavy_task


class TaskService:
    """Handles task creation and dispatching to Celery."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)

    async def create_task(self, user_id: UUID) -> UUID:
        """Create task record and dispatch to Celery. Returns task_id."""
        task = await self.task_repo.create_task(user_id=user_id)
        await self.session.flush()
        celery_result = simulate_heavy_task.delay(str(task.id))
        await self.task_repo.update(task, celery_task_id=celery_result.id)
        await self.session.flush()
        return task.id
