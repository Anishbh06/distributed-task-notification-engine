"""WebSocket endpoint for task progress."""

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_task_and_verify_ownership
from app.core.redis_pubsub import manager
from app.core.security import decode_token
from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(tags=["websocket"])


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """Validate token and return user."""
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    repo = UserRepository(db)
    return await repo.get_by_id(UUID(payload["sub"]))


async def get_task_for_user(task_id: UUID, user_id: UUID, db: AsyncSession) -> Task | None:
    """Get task if it belongs to user."""
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task or str(task.user_id) != str(user_id):
        return None
    return task


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: UUID,
) -> None:
    """WebSocket endpoint for live task progress updates."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001)
            return

        task = await get_task_for_user(task_id, user.id, db)
        if not task:
            await websocket.close(code=4003)
            return

        await manager.connect(websocket, str(task_id))
        try:
            # Send initial status
            await websocket.send_json(
                {
                    "task_id": str(task_id),
                    "progress": task.progress,
                    "status": task.status,
                }
            )
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket, str(task_id))
