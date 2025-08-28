"""
WebSocket Manager for real-time communication with frontend clients.

This module provides a centralized WebSocket management system that handles:
- Client connections and disconnections
- Broadcasting messages to all connected clients
- Targeted messaging to specific clients
- Connection status tracking
- Event logging and monitoring

The manager integrates with Flask-SocketIO and provides a clean interface
for other services to send real-time updates.
"""

import logging
import json
from typing import Dict, Set, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum

from flask_socketio import SocketIO, emit, join_room, leave_room


class WebSocketEventType(Enum):
    """WebSocket event types for type safety."""
    STATUS_UPDATE = 'status_update'
    LOG_ENTRY = 'log_entry'
    OPERATION_PROGRESS = 'operation_progress'
    ERROR = 'error'
    CACHE_FILE_ADDED = 'cache_file_added'
    CACHE_FILE_REMOVED = 'cache_file_removed'
    CACHE_STATISTICS_UPDATED = 'cache_statistics_updated'
    OPERATION_FILE_UPDATE = 'operation_file_update'
    PONG = 'pong'


@dataclass
class WebSocketMessage:
    """Standardized WebSocket message format."""
    type: WebSocketEventType
    data: Any
    timestamp: str
    source: str = 'backend'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'source': self.source
        }


@dataclass
class ClientInfo:
    """Information about a connected WebSocket client."""
    sid: str
    connected_at: datetime
    last_seen: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    rooms: Set[str] = field(default_factory=set)


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    This class provides a centralized way to handle real-time communication
    between the backend and frontend clients. It manages client connections,
    room management, and message broadcasting.
    """
    
    def __init__(self, socketio: SocketIO):
        """
        Initialize the WebSocket manager.
        
        Args:
            socketio: Flask-SocketIO instance for WebSocket operations
        """
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        self.clients: Dict[str, ClientInfo] = {}
        self.rooms: Dict[str, Set[str]] = {}
        
        # Register event handlers
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            sid = self.socketio.server.eio.sid
            self._add_client(sid)
            self.logger.info(f"Client connected: {sid}")
            
            # Send initial connection confirmation
            emit('connected', {
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Connected to Cacherr WebSocket server'
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            sid = self.socketio.server.eio.sid
            self._remove_client(sid)
            self.logger.info(f"Client disconnected: {sid}")
        
        @self.socketio.on('join')
        def handle_join(data):
            """Handle client joining a room."""
            sid = self.socketio.server.eio.sid
            room = data.get('room')
            if room:
                self._join_room(sid, room)
                emit('joined_room', {'room': room}, room=sid)
                self.logger.info(f"Client {sid} joined room: {room}")
        
        @self.socketio.on('leave')
        def handle_leave(data):
            """Handle client leaving a room."""
            sid = self.socketio.server.eio.sid
            room = data.get('room')
            if room:
                self._leave_room(sid, room)
                emit('left_room', {'room': room}, room=sid)
                self.logger.info(f"Client {sid} left room: {room}")
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping message from client."""
            sid = self.socketio.server.eio.sid
            self._update_client_last_seen(sid)
            emit('pong', {
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'pong'
            }, room=sid)
    
    def _add_client(self, sid: str):
        """Add a new client to the manager."""
        self.clients[sid] = ClientInfo(
            sid=sid,
            connected_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
    
    def _remove_client(self, sid: str):
        """Remove a client from the manager."""
        if sid in self.clients:
            # Remove from all rooms
            client_info = self.clients[sid]
            for room in client_info.rooms.copy():
                self._leave_room(sid, room)
            
            del self.clients[sid]
    
    def _update_client_last_seen(self, sid: str):
        """Update the last seen timestamp for a client."""
        if sid in self.clients:
            self.clients[sid].last_seen = datetime.utcnow()
    
    def _join_room(self, sid: str, room: str):
        """Add a client to a room."""
        join_room(room)
        
        if sid in self.clients:
            self.clients[sid].rooms.add(room)
        
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(sid)
    
    def _leave_room(self, sid: str, room: str):
        """Remove a client from a room."""
        leave_room(room)
        
        if sid in self.clients:
            self.clients[sid].rooms.discard(room)
        
        if room in self.rooms:
            self.rooms[room].discard(sid)
            if not self.rooms[room]:
                del self.rooms[room]
    
    def broadcast(self, message: WebSocketMessage, room: Optional[str] = None):
        """
        Broadcast a message to all clients or clients in a specific room.
        
        Args:
            message: WebSocket message to broadcast
            room: Optional room name to broadcast to (if None, broadcasts to all)
        """
        try:
            message_dict = message.to_dict()
            
            if room:
                self.socketio.emit(message.type.value, message_dict, room=room)
                self.logger.debug(f"Broadcasted {message.type.value} to room {room}")
            else:
                self.socketio.emit(message.type.value, message_dict)
                self.logger.debug(f"Broadcasted {message.type.value} to all clients")
                
        except Exception as e:
            self.logger.error(f"Failed to broadcast message: {e}")
    
    def send_to_client(self, sid: str, message: WebSocketMessage):
        """
        Send a message to a specific client.
        
        Args:
            sid: Client session ID
            message: WebSocket message to send
        """
        try:
            if sid in self.clients:
                message_dict = message.to_dict()
                self.socketio.emit(message.type.value, message_dict, room=sid)
                self.logger.debug(f"Sent {message.type.value} to client {sid}")
            else:
                self.logger.warning(f"Client {sid} not found")
                
        except Exception as e:
            self.logger.error(f"Failed to send message to client {sid}: {e}")
    
    def get_connected_clients_count(self) -> int:
        """Get the number of currently connected clients."""
        return len(self.clients)
    
    def get_room_clients_count(self, room: str) -> int:
        """Get the number of clients in a specific room."""
        return len(self.rooms.get(room, set()))
    
    def get_client_info(self, sid: str) -> Optional[ClientInfo]:
        """Get information about a specific client."""
        return self.clients.get(sid)
    
    def get_all_clients(self) -> List[ClientInfo]:
        """Get information about all connected clients."""
        return list(self.clients.values())
    
    def cleanup_inactive_clients(self, max_idle_minutes: int = 30):
        """
        Clean up clients that have been inactive for too long.
        
        Args:
            max_idle_minutes: Maximum idle time in minutes before cleanup
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_idle_minutes)
        inactive_clients = [
            sid for sid, client in self.clients.items()
            if client.last_seen < cutoff_time
        ]
        
        for sid in inactive_clients:
            self.logger.info(f"Cleaning up inactive client: {sid}")
            self._remove_client(sid)


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> Optional[WebSocketManager]:
    """Get the global WebSocket manager instance."""
    return _websocket_manager


def set_websocket_manager(manager: WebSocketManager):
    """Set the global WebSocket manager instance."""
    global _websocket_manager
    _websocket_manager = manager


def broadcast_message(message: WebSocketMessage, room: Optional[str] = None):
    """
    Convenience function to broadcast a message using the global manager.
    
    Args:
        message: WebSocket message to broadcast
        room: Optional room name to broadcast to
    """
    manager = get_websocket_manager()
    if manager:
        manager.broadcast(message, room)
    else:
        logging.warning("WebSocket manager not initialized, cannot broadcast message")


def send_to_client(sid: str, message: WebSocketMessage):
    """
    Convenience function to send a message to a specific client.
    
    Args:
        sid: Client session ID
        message: WebSocket message to send
    """
    manager = get_websocket_manager()
    if manager:
        manager.send_to_client(sid, message)
    else:
        logging.warning("WebSocket manager not initialized, cannot send message")
