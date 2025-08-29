"""
WebSocket Manager for Cacherr
Handles Socket.IO v4 event connections and disconnections with proper function signatures.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask_socketio import SocketIO, emit
from flask import Flask

class WebSocketManager:
    """
    WebSocket Manager with proper Socket.IO v4 event handler signatures.

    This class handles WebSocket connections, disconnections, and maintains
    a registry of connected clients. It uses the correct function signatures
    required by Socket.IO v4 to avoid signature errors.
    """

    def __init__(self, socketio: SocketIO, logger: Optional[logging.Logger] = None):
        """
        Initialize the WebSocket manager.

        Args:
            socketio: Flask-SocketIO instance
            logger: Optional logger instance
        """
        self.socketio = socketio
        self.logger = logger or logging.getLogger(__name__)

        # Track connected clients
        self.connected_clients: Dict[str, Dict[str, Any]] = {}

        # Register event handlers with proper decorators
        self._register_event_handlers()

    def _register_event_handlers(self):
        """Register Socket.IO event handlers with proper function signatures."""

        # Register event handlers using method references
        self.socketio.on_event('connect', self._handle_connect)
        self.socketio.on_event('disconnect', self._handle_disconnect)
        self.socketio.on_event('ping', self._handle_ping)
        self.socketio.on_event('status', self._handle_status_request)

    def _handle_connect(self, sid):
        """
        Handle client connection with proper Socket.IO v4 signature.

        This function now accepts the 'sid' parameter that Socket.IO v4
        automatically passes to event handlers, fixing the signature errors.

        Args:
            sid: Session ID provided by Socket.IO
        """
        # Use sid parameter directly instead of trying to access server.eio.sid
        self.logger.info(f"Client connected: {sid}")

        # Store connection info
        self.connected_clients[sid] = {
            'connected_at': datetime.utcnow(),
            'last_seen': datetime.utcnow(),
            'user_agent': None,  # Can be populated from request headers if needed
            'ip_address': None   # Can be populated from request if needed
        }

        # Emit welcome message to the connected client
        self.socketio.emit('connection_ack', {
            'sid': sid,
            'message': 'Successfully connected to Cacherr',
            'timestamp': datetime.utcnow().isoformat()
        })

        self.logger.info(f"Connection established for client {sid}. Total clients: {len(self.connected_clients)}")

    def _handle_disconnect(self, sid):
        """
        Handle client disconnection with proper Socket.IO v4 signature.

        This function now accepts the 'sid' parameter that Socket.IO v4
        automatically passes to event handlers, fixing the signature errors.

        Args:
            sid: Session ID provided by Socket.IO
        """
        # Use sid parameter directly instead of trying to access server.eio.sid
        self.logger.info(f"Client disconnected: {sid}")

        # Clean up connection info
        if sid in self.connected_clients:
            connection_info = self.connected_clients[sid]
            connection_duration = datetime.utcnow() - connection_info['connected_at']
            self.logger.info(f"Client {sid} was connected for {connection_duration}")
            del self.connected_clients[sid]

        self.logger.info(f"Disconnection handled for client {sid}. Remaining clients: {len(self.connected_clients)}")

    def _handle_ping(self, sid, data=None):
        """
        Handle ping messages from clients.

        Args:
            sid: Session ID
            data: Optional ping data
        """
        self.logger.debug(f"Ping received from client {sid}")
        self.socketio.emit('pong', {'timestamp': datetime.utcnow().isoformat()})

    def _handle_status_request(self, sid):
        """
        Handle status requests from clients.

        Args:
            sid: Session ID
        """
        self.logger.debug(f"Status request from client {sid}")

        status_info = {
            'connected_clients': len(self.connected_clients),
            'server_status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'client_sid': sid
        }

        self.socketio.emit('status_response', status_info)

    def get_connected_clients_count(self) -> int:
        """Get the number of currently connected clients."""
        return len(self.connected_clients)

    def get_client_info(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connected client."""
        return self.connected_clients.get(sid)

    def broadcast_message(self, event: str, data: Any):
        """
        Broadcast a message to all connected clients.

        Args:
            event: Event name to emit
            data: Data to send with the event
        """
        self.socketio.emit(event, data)
        self.logger.info(f"Broadcasted '{event}' to {len(self.connected_clients)} clients")

    def send_to_client(self, sid: str, event: str, data: Any):
        """
        Send a message to a specific client.

        Args:
            sid: Session ID of the target client
            event: Event name to emit
            data: Data to send with the event
        """
        if sid in self.connected_clients:
            self.socketio.emit(event, data, to=sid)
            self.logger.debug(f"Sent '{event}' to client {sid}")
        else:
            self.logger.warning(f"Attempted to send message to disconnected client {sid}")

    def cleanup_disconnected_clients(self):
        """Clean up any stale client connections."""
        # This is a basic cleanup - in a real implementation,
        # you might want to implement heartbeat checks
        current_time = datetime.utcnow()
        stale_clients = []

        for sid, info in self.connected_clients.items():
            # Mark clients as stale if they haven't been seen for more than 5 minutes
            if (current_time - info['last_seen']).total_seconds() > 300:
                stale_clients.append(sid)

        for sid in stale_clients:
            self.logger.info(f"Cleaning up stale client connection: {sid}")
            del self.connected_clients[sid]

        if stale_clients:
            self.logger.info(f"Cleaned up {len(stale_clients)} stale client connections")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        if not self.connected_clients:
            return {
                'total_clients': 0,
                'oldest_connection': None,
                'newest_connection': None,
                'average_connection_time': 0
            }

        current_time = datetime.utcnow()
        connection_times = []

        oldest_connection = min(info['connected_at'] for info in self.connected_clients.values())
        newest_connection = max(info['connected_at'] for info in self.connected_clients.values())

        for info in self.connected_clients.values():
            connection_times.append((current_time - info['connected_at']).total_seconds())

        average_connection_time = sum(connection_times) / len(connection_times)

        return {
            'total_clients': len(self.connected_clients),
            'oldest_connection': oldest_connection.isoformat(),
            'newest_connection': newest_connection.isoformat(),
            'average_connection_time_seconds': round(average_connection_time, 2)
        }