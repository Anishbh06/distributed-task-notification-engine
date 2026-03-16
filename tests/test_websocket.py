"""WebSocket integration tests."""


def test_websocket_connection_manager_exists() -> None:
    """ConnectionManager is properly configured for task progress."""
    from app.core.redis_pubsub import manager

    assert manager is not None
    assert hasattr(manager, "connect")
    assert hasattr(manager, "disconnect")
    assert hasattr(manager, "start_subscriber")
    assert hasattr(manager, "stop_subscriber")
