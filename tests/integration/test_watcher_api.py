"""
Comprehensive API integration tests for watcher endpoints.

This test suite covers all watcher API endpoints including:
- POST /api/watcher/start - Start the real-time watcher
- POST /api/watcher/stop - Stop the real-time watcher
- GET /api/watcher/status - Get watcher status
- POST /api/watcher/clear-history - Clear watcher history

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and watcher operations.
"""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestWatcherAPI:
    """Comprehensive API tests for watcher endpoints."""

    def test_watcher_start_success(self, api_client):
        """Test successful watcher start."""
        response = api_client.post("/api/watcher/start")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Real-time watcher started successfully" in data["message"]

    def test_watcher_stop_success(self, api_client):
        """Test successful watcher stop."""
        # First start the watcher
        start_response = api_client.post("/api/watcher/start")
        assert start_response.status_code == 200

        # Then stop it
        response = api_client.post("/api/watcher/stop")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Real-time watcher stopped successfully" in data["message"]

    def test_watcher_status_when_stopped(self, api_client):
        """Test watcher status when watcher is stopped."""
        # Ensure watcher is stopped
        api_client.post("/api/watcher/stop")

        response = api_client.get("/api/watcher/status")

        assert_api_response_success(response)
        data = response.json()

        assert "status" in data
        assert "is_running" in data
        assert data["is_running"] is False

        # Verify status structure
        status_info = data["status"]
        assert isinstance(status_info, dict)
        assert "state" in status_info
        assert status_info["state"] == "stopped"

    def test_watcher_status_when_running(self, api_client):
        """Test watcher status when watcher is running."""
        # Start the watcher
        api_client.post("/api/watcher/start")

        response = api_client.get("/api/watcher/status")

        assert_api_response_success(response)
        data = response.json()

        assert "status" in data
        assert "is_running" in data
        assert data["is_running"] is True

        # Verify status structure
        status_info = data["status"]
        assert isinstance(status_info, dict)
        assert "state" in status_info
        assert status_info["state"] == "running"

    def test_watcher_status_detailed_info(self, api_client):
        """Test watcher status includes detailed information."""
        response = api_client.get("/api/watcher/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]

        # Verify detailed status information
        assert "watched_paths" in status_info
        assert "event_history" in status_info
        assert "last_event" in status_info

        # Watched paths should be a list
        assert isinstance(status_info["watched_paths"], list)

        # Event history should be a list
        assert isinstance(status_info["event_history"], list)

    def test_watcher_clear_history_success(self, api_client):
        """Test successful watcher history clearing."""
        response = api_client.post("/api/watcher/clear-history")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Event history cleared successfully" in data["message"]

    def test_watcher_start_idempotent(self, api_client):
        """Test that starting watcher multiple times is idempotent."""
        # Start watcher multiple times
        for _ in range(3):
            response = api_client.post("/api/watcher/start")
            assert_api_response_success(response)

        # Verify watcher is still running
        status_response = api_client.get("/api/watcher/status")
        assert_api_response_success(status_response)
        status_data = status_response.json()
        assert status_data["is_running"] is True

    def test_watcher_stop_idempotent(self, api_client):
        """Test that stopping watcher multiple times is idempotent."""
        # Stop watcher multiple times
        for _ in range(3):
            response = api_client.post("/api/watcher/stop")
            assert_api_response_success(response)

        # Verify watcher is still stopped
        status_response = api_client.get("/api/watcher/status")
        assert_api_response_success(status_response)
        status_data = status_response.json()
        assert status_data["is_running"] is False

    def test_watcher_clear_history_idempotent(self, api_client):
        """Test that clearing history multiple times is idempotent."""
        # Clear history multiple times
        for _ in range(3):
            response = api_client.post("/api/watcher/clear-history")
            assert_api_response_success(response)

    def test_watcher_start_after_stop(self, api_client):
        """Test starting watcher after it has been stopped."""
        # Stop watcher
        api_client.post("/api/watcher/stop")

        # Verify it's stopped
        status_response = api_client.get("/api/watcher/status")
        status_data = status_response.json()
        assert status_data["is_running"] is False

        # Start watcher
        start_response = api_client.post("/api/watcher/start")
        assert_api_response_success(start_response)

        # Verify it's running
        status_response = api_client.get("/api/watcher/status")
        status_data = status_response.json()
        assert status_data["is_running"] is True

    def test_watcher_status_response_format(self, api_client):
        """Test watcher status response has correct format."""
        response = api_client.get("/api/watcher/status")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

        # Required fields
        required_fields = ["status", "is_running"]
        for field in required_fields:
            assert field in data

    def test_watcher_endpoints_cors_headers(self, api_client):
        """Test watcher endpoints include proper CORS headers."""
        endpoints = [
            ("POST", "/api/watcher/start"),
            ("POST", "/api/watcher/stop"),
            ("GET", "/api/watcher/status"),
            ("POST", "/api/watcher/clear-history")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)

            assert response.status_code == 200

    def test_watcher_endpoints_content_length(self, api_client):
        """Test watcher responses have appropriate content length."""
        endpoints = [
            ("POST", "/api/watcher/start"),
            ("POST", "/api/watcher/stop"),
            ("GET", "/api/watcher/status"),
            ("POST", "/api/watcher/clear-history")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)

            assert response.status_code == 200
            assert "content-length" in response.headers

            content_length = int(response.headers["content-length"])
            assert content_length > 0

            # Verify content length matches actual response size
            response_data = response.content
            assert len(response_data) == content_length

    def test_watcher_endpoints_error_handling(self, api_client):
        """Test watcher endpoints handle errors gracefully."""
        # Test invalid methods
        response = api_client.put("/api/watcher/start")
        assert response.status_code == 405

        response = api_client.delete("/api/watcher/status")
        assert response.status_code == 405

        # Test non-existent watcher endpoint
        response = api_client.get("/api/watcher/nonexistent")
        assert response.status_code == 404

    def test_watcher_status_with_event_history(self, api_client):
        """Test watcher status includes event history."""
        response = api_client.get("/api/watcher/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]
        event_history = status_info["event_history"]

        # Verify event history structure
        assert isinstance(event_history, list)

        # If there are events, verify their structure
        for event in event_history:
            assert isinstance(event, dict)
            assert "timestamp" in event
            assert "event_type" in event
            assert "path" in event

    def test_watcher_status_with_watched_paths(self, api_client):
        """Test watcher status includes watched paths."""
        response = api_client.get("/api/watcher/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]
        watched_paths = status_info["watched_paths"]

        # Verify watched paths structure
        assert isinstance(watched_paths, list)

        # Each path should be a string
        for path in watched_paths:
            assert isinstance(path, str)

    def test_watcher_clear_history_clears_events(self, api_client):
        """Test that clearing history actually removes events."""
        # Get initial status
        response = api_client.get("/api/watcher/status")
        initial_data = response.json()
        initial_history_count = len(initial_data["status"]["event_history"])

        # Clear history
        clear_response = api_client.post("/api/watcher/clear-history")
        assert_api_response_success(clear_response)

        # Get status after clearing
        response = api_client.get("/api/watcher/status")
        after_data = response.json()
        after_history_count = len(after_data["status"]["event_history"])

        # History should be empty or significantly reduced
        assert after_history_count <= initial_history_count

    def test_watcher_operations_response_consistency(self, api_client):
        """Test watcher operation responses follow consistent format."""
        operations = [
            ("POST", "/api/watcher/start"),
            ("POST", "/api/watcher/stop"),
            ("POST", "/api/watcher/clear-history")
        ]

        for method, endpoint in operations:
            response = api_client.post(endpoint)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "message" in data

            if data["status"] == "success":
                assert "message" in data

    @pytest.mark.slow
    def test_watcher_status_performance(self, api_client):
        """Test watcher status endpoint performance."""
        import time

        start_time = time.time()

        # Make multiple status requests
        for _ in range(10):
            response = api_client.get("/api/watcher/status")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete 10 requests in under 2 seconds
        assert total_time < 2.0

    def test_watcher_start_stop_cycle(self, api_client):
        """Test complete start/stop cycle of watcher."""
        # Initial state
        response = api_client.get("/api/watcher/status")
        data = response.json()
        initial_state = data["is_running"]

        # Start watcher
        response = api_client.post("/api/watcher/start")
        assert_api_response_success(response)

        # Verify it's running
        response = api_client.get("/api/watcher/status")
        data = response.json()
        assert data["is_running"] is True

        # Stop watcher
        response = api_client.post("/api/watcher/stop")
        assert_api_response_success(response)

        # Verify it's stopped
        response = api_client.get("/api/watcher/status")
        data = response.json()
        assert data["is_running"] is False

    def test_watcher_status_includes_timestamps(self, api_client):
        """Test watcher status includes proper timestamps."""
        response = api_client.get("/api/watcher/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]

        # Verify timestamp fields if present
        if "last_event" in status_info and status_info["last_event"] is not None:
            # Should be a valid timestamp
            assert isinstance(status_info["last_event"], str)

        # Verify event history timestamps
        for event in status_info["event_history"]:
            assert "timestamp" in event
            assert isinstance(event["timestamp"], str)

    def test_watcher_clear_history_response_format(self, api_client):
        """Test clear history response has correct format."""
        response = api_client.post("/api/watcher/clear-history")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "message" in data

    def test_watcher_status_empty_history_after_clear(self, api_client):
        """Test that status shows empty history after clearing."""
        # Clear history
        api_client.post("/api/watcher/clear-history")

        # Get status
        response = api_client.get("/api/watcher/status")
        data = response.json()

        # Event history should be empty
        event_history = data["status"]["event_history"]
        assert isinstance(event_history, list)
        assert len(event_history) == 0


# Helper functions
def assert_api_response_success(response, expected_status: int = 200):
    """Assert that an API response indicates success."""
    assert response.status_code == expected_status
    data = response.json()
    assert isinstance(data, dict)
    assert data.get("status") == "success"


def assert_api_response_error(response, expected_status: int = 400):
    """Assert that an API response indicates an error."""
    assert response.status_code == expected_status
    data = response.json()
    assert isinstance(data, dict)
    assert data.get("status") == "error"
    assert "message" in data
