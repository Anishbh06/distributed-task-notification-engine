"""Redis Pub/Sub manager for WebSocket progress broadcasting."""

import asyncio
import json
from collections import defaultdict

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings


class ConnectionManager:
    """Manages WebSocket connections and broadcasts task progress from Redis Pub/Sub."""

    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._pubsub_task: asyncio.Task | None = None
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """Accept WebSocket and register for task_id."""
        await websocket.accept()
        self.connections[task_id].add(websocket)

    def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """Remove WebSocket from task_id subscribers."""
        if task_id in self.connections:
            self.connections[task_id].discard(websocket)
            if not self.connections[task_id]:
                del self.connections[task_id]

    async def _broadcast_to_task(self, task_id: str, message: dict) -> None:
        """Send message to all WebSockets subscribed to task_id."""
        if task_id not in self.connections:
            return
        dead = set()
        for ws in self.connections[task_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.connections[task_id].discard(ws)

    async def _run_subscriber(self) -> None:
        """Subscribe to Redis channel and forward messages to WebSockets."""
        self._redis = aioredis.from_url(settings.REDIS_URL)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(settings.PROGRESS_CHANNEL)

        while True:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    task_id = data.get("task_id")
                    if task_id:
                        await self._broadcast_to_task(task_id, data)
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    async def start_subscriber(self) -> None:
        """Start background task for Redis subscription."""
        self._pubsub_task = asyncio.create_task(self._run_subscriber())

    async def stop_subscriber(self) -> None:
        """Stop Redis subscriber and clean up."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe(settings.PROGRESS_CHANNEL)
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()


manager = ConnectionManager()
