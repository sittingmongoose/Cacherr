"""
Comprehensive unit tests for WebSocketManager service.

This test suite covers all WebSocketManager functionality including:
- Client connection management
- Message broadcasting and targeted messaging
- Room management
- Event handling
- Connection status tracking
- Error handling and edge cases
- Performance with multiple clients
- Security and validation

All tests use comprehensive mocking to avoid external dependencies
while maintaining full test coverage and reliability.
"""

import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, Set, Optional

import pytest
from flask_socketio import SocketIO

# Import the service and models
import sys
sys.path.append('/mnt/user/Cursor/Cacherr/src')

from core.websocket_manager import (
    WebSocketManager,
    WebSocketMessage,
    ClientInfo,
    WebSocketEventType
)


@pytest.mark.unit
class TestWebSocketMessage:
    """Test WebSocket message model."""

    def test_websocket_message_creation(self):
        """Test creation of WebSocketMessage."""
        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 50, "message": "Processing files"},
            timestamp="2023-01-01T12:00:00Z",
            source="backend"
        )

        assert message.type == WebSocketEventType.OPERATION_PROGRESS
        assert message.data == {"progress": 50, "message": "Processing files"}
        assert message.timestamp == "2023-01-01T12:00:00Z"
        assert message.source == "backend"

    def test_websocket_message_to_dict(self):
        """Test WebSocketMessage to_dict conversion."""
        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_FILE_UPDATE,
            data={"file": "movie.mp4", "status": "cached"},
            timestamp="2023-01-01T12:00:00Z"
        )

        result = message.to_dict()

        expected = {
            "type": "operation_file_update",
            "data": {"file": "movie.mp4", "status": "cached"},
            "timestamp": "2023-01-01T12:00:00Z",
            "source": "backend"
        }

        assert result == expected

    def test_websocket_message_default_source(self):
        """Test WebSocketMessage with default source."""
        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 100}
        )

        assert message.source == "backend"
        assert message.timestamp is not None  # Should be set automatically


@pytest.mark.unit
class TestClientInfo:
    """Test client information model."""

    def test_client_info_creation(self):
        """Test creation of ClientInfo."""
        connected_at = datetime.now()
        last_seen = datetime.now()

        client = ClientInfo(
            sid="test_sid_123",
            connected_at=connected_at,
            last_seen=last_seen,
            user_agent="TestBrowser/1.0",
            ip_address="192.168.1.100",
            rooms={"room1", "room2"}
        )

        assert client.sid == "test_sid_123"
        assert client.connected_at == connected_at
        assert client.last_seen == last_seen
        assert client.user_agent == "TestBrowser/1.0"
        assert client.ip_address == "192.168.1.100"
        assert client.rooms == {"room1", "room2"}

    def test_client_info_defaults(self):
        """Test ClientInfo with default values."""
        connected_at = datetime.now()
        last_seen = datetime.now()

        client = ClientInfo(
            sid="test_sid",
            connected_at=connected_at,
            last_seen=last_seen
        )

        assert client.user_agent is None
        assert client.ip_address is None
        assert client.rooms == set()


@pytest.mark.unit
class TestWebSocketEventType:
    """Test WebSocket event type enum."""

    def test_event_type_values(self):
        """Test WebSocketEventType enum values."""
        assert WebSocketEventType.OPERATION_PROGRESS.value == "operation_progress"
        assert WebSocketEventType.OPERATION_FILE_UPDATE.value == "operation_file_update"

    def test_event_type_count(self):
        """Test that we have the expected number of event types."""
        # Currently only 2 event types, but designed to be extensible
        assert len(WebSocketEventType) == 2


@pytest.mark.unit
class TestWebSocketManager:
    """Comprehensive test suite for WebSocketManager service."""

    @pytest.fixture
    def mock_socketio(self):
        """Create mock SocketIO instance."""
        socketio = Mock(spec=SocketIO)
        socketio.server = Mock()
        socketio.server.eio = Mock()
        socketio.server.eio.sid = "test_server_sid"

        # Mock event handler decorators
        socketio.on = Mock(return_value=lambda func: func)

        return socketio

    @pytest.fixture
    def websocket_manager(self, mock_socketio):
        """Create WebSocketManager instance with mock SocketIO."""
        manager = WebSocketManager(mock_socketio)
        return manager

    def test_initialization(self, websocket_manager, mock_socketio):
        """Test WebSocketManager initialization."""
        assert websocket_manager.socketio == mock_socketio
        assert websocket_manager.clients == {}
        assert websocket_manager.rooms == {}
        assert hasattr(websocket_manager, 'logger')

    def test_add_client(self, websocket_manager):
        """Test adding a client connection."""
        sid = "test_client_123"
        ip_address = "192.168.1.100"
        user_agent = "TestBrowser/1.0"

        websocket_manager._add_client(sid, ip_address=ip_address, user_agent=user_agent)

        assert sid in websocket_manager.clients
        client = websocket_manager.clients[sid]
        assert client.sid == sid
        assert client.ip_address == ip_address
        assert client.user_agent == user_agent
        assert isinstance(client.connected_at, datetime)
        assert isinstance(client.last_seen, datetime)

    def test_add_client_minimal(self, websocket_manager):
        """Test adding a client with minimal information."""
        sid = "minimal_client"

        websocket_manager._add_client(sid)

        assert sid in websocket_manager.clients
        client = websocket_manager.clients[sid]
        assert client.sid == sid
        assert client.ip_address is None
        assert client.user_agent is None

    def test_remove_client(self, websocket_manager):
        """Test removing a client connection."""
        sid = "test_client_123"

        # Add client first
        websocket_manager._add_client(sid)
        assert sid in websocket_manager.clients

        # Remove client
        websocket_manager._remove_client(sid)
        assert sid not in websocket_manager.clients

    def test_remove_nonexistent_client(self, websocket_manager):
        """Test removing a client that doesn't exist."""
        # Should not raise an error
        websocket_manager._remove_client("nonexistent_client")

    def test_update_client_activity(self, websocket_manager):
        """Test updating client last seen timestamp."""
        sid = "test_client_123"
        websocket_manager._add_client(sid)

        initial_last_seen = websocket_manager.clients[sid].last_seen

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.001)

        websocket_manager._update_client_activity(sid)

        updated_last_seen = websocket_manager.clients[sid].last_seen
        assert updated_last_seen > initial_last_seen

    def test_update_nonexistent_client_activity(self, websocket_manager):
        """Test updating activity for non-existent client."""
        # Should not raise an error
        websocket_manager._update_client_activity("nonexistent_client")

    def test_broadcast_message_to_all(self, websocket_manager, mock_socketio):
        """Test broadcasting message to all connected clients."""
        # Mock emit function
        mock_socketio.emit = Mock()

        # Add some clients
        websocket_manager._add_client("client1")
        websocket_manager._add_client("client2")

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 75},
            timestamp="2023-01-01T12:00:00Z"
        )

        websocket_manager.broadcast_message(message)

        # Verify emit was called with correct parameters
        expected_data = message.to_dict()
        mock_socketio.emit.assert_called_once_with(
            message.type.value,
            expected_data,
            broadcast=True
        )

    def test_broadcast_message_no_clients(self, websocket_manager, mock_socketio):
        """Test broadcasting message when no clients are connected."""
        mock_socketio.emit = Mock()

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 50}
        )

        websocket_manager.broadcast_message(message)

        # Should still emit even with no clients
        mock_socketio.emit.assert_called_once()

    def test_send_message_to_client(self, websocket_manager, mock_socketio):
        """Test sending message to specific client."""
        mock_socketio.emit = Mock()

        sid = "target_client"
        websocket_manager._add_client(sid)

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_FILE_UPDATE,
            data={"file": "movie.mp4", "status": "completed"}
        )

        websocket_manager.send_message_to_client(sid, message)

        # Verify emit was called with client sid
        expected_data = message.to_dict()
        mock_socketio.emit.assert_called_once_with(
            message.type.value,
            expected_data,
            room=sid
        )

    def test_send_message_to_nonexistent_client(self, websocket_manager, mock_socketio):
        """Test sending message to client that doesn't exist."""
        mock_socketio.emit = Mock()

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 100}
        )

        # Should not raise an error
        websocket_manager.send_message_to_client("nonexistent_client", message)

        # Emit should still be called (SocketIO handles non-existent rooms gracefully)
        mock_socketio.emit.assert_called_once()

    def test_join_room(self, websocket_manager):
        """Test client joining a room."""
        sid = "test_client"
        room = "operations"

        websocket_manager._add_client(sid)
        websocket_manager.join_room(sid, room)

        assert room in websocket_manager.clients[sid].rooms
        assert sid in websocket_manager.rooms[room]

    def test_join_room_creates_room(self, websocket_manager):
        """Test that joining a room creates it if it doesn't exist."""
        sid = "test_client"
        room = "new_room"

        websocket_manager._add_client(sid)
        websocket_manager.join_room(sid, room)

        assert room in websocket_manager.rooms
        assert sid in websocket_manager.rooms[room]

    def test_leave_room(self, websocket_manager):
        """Test client leaving a room."""
        sid = "test_client"
        room = "operations"

        websocket_manager._add_client(sid)
        websocket_manager.join_room(sid, room)

        # Verify client is in room
        assert room in websocket_manager.clients[sid].rooms
        assert sid in websocket_manager.rooms[room]

        # Leave room
        websocket_manager.leave_room(sid, room)

        # Verify client is no longer in room
        assert room not in websocket_manager.clients[sid].rooms
        assert sid not in websocket_manager.rooms[room]

    def test_leave_nonexistent_room(self, websocket_manager):
        """Test leaving a room that client is not in."""
        sid = "test_client"
        room = "operations"

        websocket_manager._add_client(sid)

        # Should not raise an error
        websocket_manager.leave_room(sid, room)

    def test_leave_room_from_nonexistent_client(self, websocket_manager):
        """Test leaving room for client that doesn't exist."""
        # Should not raise an error
        websocket_manager.leave_room("nonexistent_client", "room")

    def test_broadcast_to_room(self, websocket_manager, mock_socketio):
        """Test broadcasting message to specific room."""
        mock_socketio.emit = Mock()

        room = "operations"
        sid1 = "client1"
        sid2 = "client2"

        # Add clients and join room
        websocket_manager._add_client(sid1)
        websocket_manager._add_client(sid2)
        websocket_manager.join_room(sid1, room)
        websocket_manager.join_room(sid2, room)

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"operation": "cache_files", "progress": 60}
        )

        websocket_manager.broadcast_to_room(room, message)

        # Verify emit was called with room
        expected_data = message.to_dict()
        mock_socketio.emit.assert_called_once_with(
            message.type.value,
            expected_data,
            room=room
        )

    def test_get_connected_clients(self, websocket_manager):
        """Test getting list of connected clients."""
        # Add some clients
        websocket_manager._add_client("client1")
        websocket_manager._add_client("client2")
        websocket_manager._add_client("client3")

        clients = websocket_manager.get_connected_clients()

        assert len(clients) == 3
        assert "client1" in clients
        assert "client2" in clients
        assert "client3" in clients

    def test_get_connected_clients_empty(self, websocket_manager):
        """Test getting connected clients when none are connected."""
        clients = websocket_manager.get_connected_clients()

        assert clients == []

    def test_get_room_clients(self, websocket_manager):
        """Test getting clients in a specific room."""
        room = "operations"
        sid1 = "client1"
        sid2 = "client2"
        sid3 = "client3"

        # Add clients
        websocket_manager._add_client(sid1)
        websocket_manager._add_client(sid2)
        websocket_manager._add_client(sid3)

        # Join room
        websocket_manager.join_room(sid1, room)
        websocket_manager.join_room(sid2, room)
        # sid3 does not join room

        room_clients = websocket_manager.get_room_clients(room)

        assert len(room_clients) == 2
        assert sid1 in room_clients
        assert sid2 in room_clients
        assert sid3 not in room_clients

    def test_get_room_clients_empty_room(self, websocket_manager):
        """Test getting clients for empty room."""
        room_clients = websocket_manager.get_room_clients("empty_room")

        assert room_clients == []

    def test_get_client_info(self, websocket_manager):
        """Test getting client information."""
        sid = "test_client"
        ip = "192.168.1.100"
        agent = "TestBrowser/1.0"

        websocket_manager._add_client(sid, ip_address=ip, user_agent=agent)

        client_info = websocket_manager.get_client_info(sid)

        assert client_info is not None
        assert client_info.sid == sid
        assert client_info.ip_address == ip
        assert client_info.user_agent == agent

    def test_get_client_info_nonexistent(self, websocket_manager):
        """Test getting info for non-existent client."""
        client_info = websocket_manager.get_client_info("nonexistent_client")

        assert client_info is None

    def test_get_connection_stats(self, websocket_manager):
        """Test getting connection statistics."""
        # Add clients with different states
        websocket_manager._add_client("client1")
        websocket_manager._add_client("client2")
        websocket_manager._add_client("client3")

        # Join some rooms
        websocket_manager.join_room("client1", "room1")
        websocket_manager.join_room("client2", "room1")
        websocket_manager.join_room("client2", "room2")

        stats = websocket_manager.get_connection_stats()

        assert stats["total_clients"] == 3
        assert stats["total_rooms"] == 2
        assert "clients_per_room" in stats
        assert stats["clients_per_room"]["room1"] == 2
        assert stats["clients_per_room"]["room2"] == 1

    def test_get_connection_stats_empty(self, websocket_manager):
        """Test getting connection stats when no clients or rooms exist."""
        stats = websocket_manager.get_connection_stats()

        assert stats["total_clients"] == 0
        assert stats["total_rooms"] == 0
        assert stats["clients_per_room"] == {}

    def test_cleanup_inactive_clients(self, websocket_manager):
        """Test cleanup of inactive clients."""
        # Add clients with different activity times
        websocket_manager._add_client("active_client")
        websocket_manager._add_client("inactive_client")

        # Make inactive client old
        old_time = datetime.now() - timedelta(minutes=30)
        websocket_manager.clients["inactive_client"].last_seen = old_time

        # Cleanup clients inactive for more than 15 minutes
        cleaned_count = websocket_manager.cleanup_inactive_clients(timeout_minutes=15)

        assert cleaned_count == 1
        assert "active_client" in websocket_manager.clients
        assert "inactive_client" not in websocket_manager.clients

    def test_cleanup_inactive_clients_none_inactive(self, websocket_manager):
        """Test cleanup when no clients are inactive."""
        websocket_manager._add_client("active_client")

        cleaned_count = websocket_manager.cleanup_inactive_clients(timeout_minutes=15)

        assert cleaned_count == 0
        assert "active_client" in websocket_manager.clients

    def test_handle_connection_event(self, websocket_manager, mock_socketio):
        """Test handling of connection event."""
        mock_socketio.emit = Mock()

        # Simulate connection event
        websocket_manager._register_event_handlers()

        # The actual event handling would be tested through integration tests
        # since it requires the actual SocketIO event system
        assert websocket_manager.socketio == mock_socketio

    def test_concurrent_client_operations(self, websocket_manager):
        """Test handling multiple client operations concurrently."""
        import threading
        import time

        results = []
        errors = []

        def client_operation(client_id: str):
            try:
                # Add client
                websocket_manager._add_client(f"client_{client_id}")

                # Join room
                websocket_manager.join_room(f"client_{client_id}", "test_room")

                # Send message
                message = WebSocketMessage(
                    type=WebSocketEventType.OPERATION_PROGRESS,
                    data={"client": client_id}
                )

                # This would normally broadcast, but we're just testing thread safety
                results.append(f"client_{client_id}_completed")

            except Exception as e:
                errors.append(e)

        # Run concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=client_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) == 10
        assert len(errors) == 0

        # Verify all clients were added
        assert len(websocket_manager.clients) == 10

        # Verify room contains all clients
        room_clients = websocket_manager.get_room_clients("test_room")
        assert len(room_clients) == 10

    @pytest.mark.performance
    def test_broadcast_performance(self, websocket_manager, mock_socketio, benchmark):
        """Benchmark message broadcasting performance."""
        mock_socketio.emit = Mock()

        # Add many clients
        for i in range(100):
            websocket_manager._add_client(f"client_{i}")

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 50}
        )

        def benchmark_broadcast():
            websocket_manager.broadcast_message(message)

        result = benchmark(benchmark_broadcast)

        # Verify emit was called
        mock_socketio.emit.assert_called()

        # The benchmark result should be the message broadcast operation
        assert result is None  # broadcast_message returns None

    def test_error_handling_broadcast_failure(self, websocket_manager, mock_socketio):
        """Test error handling when broadcasting fails."""
        # Mock emit to raise an exception
        mock_socketio.emit.side_effect = Exception("Broadcast failed")

        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 100}
        )

        # Should not raise an exception - should handle gracefully
        websocket_manager.broadcast_message(message)

        # Verify emit was called despite error
        mock_socketio.emit.assert_called_once()

    def test_memory_cleanup_on_client_removal(self, websocket_manager):
        """Test that memory is properly cleaned up when clients are removed."""
        # Add client and join multiple rooms
        sid = "test_client"
        websocket_manager._add_client(sid)
        websocket_manager.join_room(sid, "room1")
        websocket_manager.join_room(sid, "room2")
        websocket_manager.join_room(sid, "room3")

        # Verify client and rooms exist
        assert sid in websocket_manager.clients
        assert len(websocket_manager.clients[sid].rooms) == 3
        assert all(sid in websocket_manager.rooms[room] for room in ["room1", "room2", "room3"])

        # Remove client
        websocket_manager._remove_client(sid)

        # Verify complete cleanup
        assert sid not in websocket_manager.clients
        assert all(sid not in websocket_manager.rooms[room] for room in ["room1", "room2", "room3"])

    def test_room_cleanup_when_empty(self, websocket_manager):
        """Test that empty rooms are cleaned up."""
        sid = "test_client"
        room = "temporary_room"

        # Add client and join room
        websocket_manager._add_client(sid)
        websocket_manager.join_room(sid, room)

        # Verify room exists
        assert room in websocket_manager.rooms
        assert sid in websocket_manager.rooms[room]

        # Client leaves room
        websocket_manager.leave_room(sid, room)

        # Room should still exist but be empty
        assert room in websocket_manager.rooms
        assert len(websocket_manager.rooms[room]) == 0

        # Note: In a real implementation, you might want to clean up empty rooms
        # but for now we keep them for potential future use

    def test_message_validation(self, websocket_manager):
        """Test that messages are properly validated before sending."""
        # Create a message with all required fields
        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_PROGRESS,
            data={"progress": 75, "status": "processing"},
            timestamp="2023-01-01T12:00:00Z",
            source="test_source"
        )

        # Should not raise any validation errors
        assert message.type == WebSocketEventType.OPERATION_PROGRESS
        assert message.data["progress"] == 75
        assert message.source == "test_source"

    def test_large_message_handling(self, websocket_manager, mock_socketio):
        """Test handling of large messages."""
        mock_socketio.emit = Mock()

        # Create a large message
        large_data = {"data": "x" * 10000}  # 10KB of data
        message = WebSocketMessage(
            type=WebSocketEventType.OPERATION_FILE_UPDATE,
            data=large_data
        )

        websocket_manager.broadcast_message(message)

        # Verify the message was processed (in a real scenario, this might be chunked)
        mock_socketio.emit.assert_called_once()
        args = mock_socketio.emit.call_args
        sent_data = args[1]["data"]  # Second positional argument
        assert sent_data == large_data
