"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, tasks, websocket

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(websocket.router)
