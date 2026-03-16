"""Task schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskCreateResponse(BaseModel):
    """Schema for task creation response."""

    task_id: str


class TaskResponse(BaseModel):
    """Schema for task in API responses."""

    id: str
    user_id: str
    status: str
    progress: int
    result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskProgressMessage(BaseModel):
    """Schema for WebSocket progress message."""

    task_id: str
    progress: int
    status: str
