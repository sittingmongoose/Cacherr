from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from flask import request
from flask_socketio import SocketIO


logger = logging.getLogger(__name__)


class WebSocketManager:
    """Wraps Flask-SocketIO event registration with safe defaults.

    Fixes two common issues seen in logs:
    - Connect handler must accept an `auth` argument in Flask-SocketIO>=5.
    - Use `flask.request.sid` to get the current client's SID; do not access
      `self.socketio.server.eio.sid` (it doesn't exist).
    """

    def __init__(self, socketio: SocketIO, namespace: str = "/") -> None:
        self.socketio = socketio
        self.namespace = namespace
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        # Local closures capture `self` and register proper signatures.
        def handle_connect(auth: Optional[dict[str, Any]] = None) -> bool | None:
            """Handle new WebSocket connections.

            Flask-SocketIO passes an optional `auth` payload. Return False to
            reject the connection, True/None to accept.
            """

            sid = request.sid
            logger.info("Client connected", extra={"sid": sid, "auth": auth})

            # Add auth validation here if needed; example:
            # if self._requires_auth and not self._validate_auth(auth):
            #     logger.warning("Auth failed", extra={"sid": sid})
            #     return False
            return True

        def handle_disconnect() -> None:
            sid = request.sid
            logger.info("Client disconnected", extra={"sid": sid})

        # Register handlers explicitly (decorators inside methods are brittle).
        self.socketio.on_event("connect", handle_connect, namespace=self.namespace)
        self.socketio.on_event(
            "disconnect", handle_disconnect, namespace=self.namespace
        )

    # Helper API for sending events
    def emit(self, event: str, data: Any, to: Optional[str] = None, room: Optional[str] = None) -> None:
        """Emit an event to a specific SID or room, or broadcast if none."""
        self.socketio.emit(event, data, to=to, room=room, namespace=self.namespace)

