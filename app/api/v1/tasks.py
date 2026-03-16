"""Task routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_task_and_verify_ownership
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreateResponse, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse)
async def create_task(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskCreateResponse:
    """Create and dispatch a background task. Returns task_id immediately."""
    service = TaskService(db)
    task_id = await service.create_task(user_id=current_user.id)
    return TaskCreateResponse(task_id=str(task_id))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task: Annotated[Task, Depends(get_task_and_verify_ownership)],
) -> TaskResponse:
    """Get task status and details."""
    return TaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        status=task.status,
        progress=task.progress,
        result=task.result,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
