"""Celery task definitions."""

import json
import time
from datetime import datetime as sa_datetime
from datetime import timezone as sa_timezone
from contextlib import contextmanager

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.task import Task, TaskStatus

# Sync engine for Celery workers
sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SyncSession = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


@contextmanager
def get_sync_session():
    """Context manager for sync database session."""
    session = SyncSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_task_progress(task_id: str, progress: int, status: str, result: dict | None = None, error_message: str | None = None) -> None:
    """Update task in Postgres (sync) using models."""
    with get_sync_session() as session:
        task = session.get(Task, task_id)
        if task:
            task.progress = progress
            task.status = status
            if result is not None:
                task.result = result
            if error_message is not None:
                task.error_message = error_message
            task.updated_at = sa_datetime.now(sa_timezone.utc)


def publish_progress(task_id: str, progress: int, status: str) -> None:
    """Publish progress to Redis Pub/Sub."""
    r = redis.from_url(settings.REDIS_URL)
    msg = json.dumps({"task_id": task_id, "progress": progress, "status": status})
    r.publish(settings.PROGRESS_CHANNEL, msg)


@celery_app.task(bind=True, name="workers.tasks.simulate_heavy_task")
def simulate_heavy_task(self, task_id: str) -> dict:
    """Simulate a 10-second heavy task, updating progress every 2 seconds."""
    try:
        # Mark as RUNNING
        update_task_progress(task_id, 0, TaskStatus.RUNNING.value)
        publish_progress(task_id, 0, TaskStatus.RUNNING.value)

        for progress in range(1, 101):
            time.sleep(0.5)
            status = TaskStatus.COMPLETED.value if progress == 100 else TaskStatus.RUNNING.value
            result = {"done": True} if progress == 100 else None
            update_task_progress(task_id, progress, status, result=result)
            publish_progress(task_id, progress, status)

        return {"done": True}
    except Exception as e:
        update_task_progress(task_id, 0, TaskStatus.FAILED.value, error_message=str(e))
        publish_progress(task_id, 0, TaskStatus.FAILED.value)
        raise
