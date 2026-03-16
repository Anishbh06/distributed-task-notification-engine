"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.redis_pubsub import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: Redis Pub/Sub subscriber; Shutdown: stop subscriber."""
    await manager.start_subscriber()
    yield
    await manager.stop_subscriber()


app = FastAPI(
    title="Distributed Task & Notification Engine",
    description="API for submitting heavy background tasks with real-time WebSocket progress updates",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
