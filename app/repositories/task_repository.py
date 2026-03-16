"""Task repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Task-specific repository operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def create_task(
        self,
        user_id: UUID,
        celery_task_id: str | None = None,
    ) -> Task:
        """Create a new task record."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        task = Task(
            user_id=user_id,
            celery_task_id=celery_task_id,
            status="PENDING",
            progress=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, id: UUID) -> Task | None:
        """Get task by primary key."""
        result = await self.session.execute(select(Task).where(Task.id == id))
        return result.scalar_one_or_none()

    async def update_progress(self, task_id: UUID, progress: int, status: str) -> Task | None:
        """Update task progress and status."""
        from datetime import datetime, timezone

        task = await self.get_by_id(task_id)
        if task is None:
            return None
        task.progress = progress
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def update_status(
        self,
        task_id: UUID,
        status: str,
        result: dict | None = None,
        error_message: str | None = None,
    ) -> Task | None:
        """Update task status, optionally with result or error."""
        from datetime import datetime, timezone

        task = await self.get_by_id(task_id)
        if task is None:
            return None
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        if result is not None:
            task.result = result
        if error_message is not None:
            task.error_message = error_message
        await self.session.flush()
        await self.session.refresh(task)
        return task
