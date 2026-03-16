"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "task_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
