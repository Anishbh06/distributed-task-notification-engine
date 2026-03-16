"""Task API integration tests."""

from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@patch("app.services.task_service.simulate_heavy_task")
async def test_create_task_returns_task_id(
    mock_celery_task: MagicMock,
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """POST /tasks returns task_id immediately and enqueues Celery task."""
    mock_celery_task.delay.return_value = MagicMock(id="celery-task-123")
    mock_celery_task.delay.return_value.id = "celery-task-123"

    response = await client.post("/api/v1/tasks", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert len(data["task_id"]) > 0  # UUID string
    mock_celery_task.delay.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.task_service.simulate_heavy_task")
async def test_create_task_enqueues_with_correct_id(
    mock_celery_task: MagicMock,
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Celery task is dispatched with the created task's UUID."""
    mock_celery_task.delay.return_value = MagicMock(id="celery-xyz")

    response = await client.post("/api/v1/tasks", headers=auth_headers)
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    mock_celery_task.delay.assert_called_once_with(task_id)


@pytest.mark.asyncio
@patch("app.services.task_service.simulate_heavy_task")
async def test_get_task_returns_status(
    mock_celery_task: MagicMock,
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """GET /tasks/{task_id} returns task details after creation."""
    mock_celery_task.delay.return_value = MagicMock(id="celery-123")

    create_resp = await client.post("/api/v1/tasks", headers=auth_headers)
    assert create_resp.status_code == 200
    task_id = create_resp.json()["task_id"]

    get_resp = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == task_id
    assert data["status"] == "PENDING"
    assert data["progress"] == 0
