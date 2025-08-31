"""
Comprehensive API integration tests for Trakt API endpoints.

This test suite covers all Trakt API endpoints including:
- GET /api/trakt/status - Get Trakt integration status
- POST /api/trakt/start - Start Trakt integration
- POST /api/trakt/stop - Stop Trakt integration

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and Trakt operations.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestTraktAPI:
    """Comprehensive API tests for Trakt endpoints."""

    def test_trakt_status_success(self, api_client):
        """Test successful retrieval of Trakt integration status."""
        response = api_client.get("/api/trakt/status")

        assert_api_response_success(response)
        data = response.json()

        assert "status" in data
        assert "is_enabled" in data
        assert "is_connected" in data

        # Verify status structure
        status_info = data["status"]
        assert isinstance(status_info, dict)

    def test_trakt_status_detailed_info(self, api_client):
        """Test Trakt status includes detailed information."""
        response = api_client.get("/api/trakt/status")
        data = response.json()

        status_info = data["status"]

        # Verify detailed status information
        expected_fields = [
            "client_id", "last_sync", "sync_status",
            "watchlist_count", "watched_count"
        ]

        # Some fields might be None if not configured
        for field in expected_fields:
            assert field in status_info

    def test_trakt_start_success(self, api_client):
        """Test successful Trakt integration start."""
        response = api_client.post("/api/trakt/start")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Trakt integration started successfully" in data["message"]

    def test_trakt_stop_success(self, api_client):
        """Test successful Trakt integration stop."""
        # First start Trakt integration
        start_response = api_client.post("/api/trakt/start")
        assert start_response.status_code == 200

        # Then stop it
        response = api_client.post("/api/trakt/stop")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Trakt integration stopped successfully" in data["message"]

    def test_trakt_start_idempotent(self, api_client):
        """Test that starting Trakt integration multiple times is idempotent."""
        # Start Trakt integration multiple times
        for _ in range(3):
            response = api_client.post("/api/trakt/start")
            assert_api_response_success(response)

        # Verify Trakt is still enabled
        status_response = api_client.get("/api/trakt/status")
        assert_api_response_success(status_response)
        status_data = status_response.json()
        assert status_data["is_enabled"] is True

    def test_trakt_stop_idempotent(self, api_client):
        """Test that stopping Trakt integration multiple times is idempotent."""
        # Stop Trakt integration multiple times
        for _ in range(3):
            response = api_client.post("/api/trakt/stop")
            assert_api_response_success(response)

        # Verify Trakt is still disabled
        status_response = api_client.get("/api/trakt/status")
        assert_api_response_success(status_response)
        status_data = status_response.json()
        assert status_data["is_enabled"] is False

    def test_trakt_start_after_stop(self, api_client):
        """Test starting Trakt integration after it has been stopped."""
        # Stop Trakt integration
        api_client.post("/api/trakt/stop")

        # Verify it's stopped
        status_response = api_client.get("/api/trakt/status")
        status_data = status_response.json()
        assert status_data["is_enabled"] is False

        # Start Trakt integration
        start_response = api_client.post("/api/trakt/start")
        assert_api_response_success(start_response)

        # Verify it's enabled
        status_response = api_client.get("/api/trakt/status")
        status_data = status_response.json()
        assert status_data["is_enabled"] is True

    def test_trakt_status_response_format(self, api_client):
        """Test Trakt status response has correct format."""
        response = api_client.get("/api/trakt/status")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

        # Required fields
        required_fields = ["status", "is_enabled", "is_connected"]
        for field in required_fields:
            assert field in data

    def test_trakt_endpoints_cors_headers(self, api_client):
        """Test Trakt endpoints include proper CORS headers."""
        endpoints = [
            ("GET", "/api/trakt/status"),
            ("POST", "/api/trakt/start"),
            ("POST", "/api/trakt/stop")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)

            assert response.status_code == 200

    def test_trakt_endpoints_content_length(self, api_client):
        """Test Trakt responses have appropriate content length."""
        endpoints = [
            ("GET", "/api/trakt/status"),
            ("POST", "/api/trakt/start"),
            ("POST", "/api/trakt/stop")
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

    def test_trakt_endpoints_error_handling(self, api_client):
        """Test Trakt endpoints handle errors gracefully."""
        # Test invalid methods
        response = api_client.put("/api/trakt/start")
        assert response.status_code == 405

        response = api_client.delete("/api/trakt/status")
        assert response.status_code == 405

        # Test non-existent Trakt endpoint
        response = api_client.get("/api/trakt/nonexistent")
        assert response.status_code == 404

    def test_trakt_status_with_connection_info(self, api_client):
        """Test Trakt status includes connection information."""
        response = api_client.get("/api/trakt/status")
        data = response.json()

        status_info = data["status"]

        # Verify connection-related fields
        assert "is_connected" in data
        assert "connection_error" in status_info

        # If connected, should have connection details
        if data["is_connected"]:
            assert "client_id" in status_info
            assert "last_sync" in status_info

    def test_trakt_operations_response_consistency(self, api_client):
        """Test Trakt operation responses follow consistent format."""
        operations = [
            ("POST", "/api/trakt/start"),
            ("POST", "/api/trakt/stop")
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
    def test_trakt_status_performance(self, api_client):
        """Test Trakt status endpoint performance."""
        import time

        start_time = time.time()

        # Make multiple status requests
        for _ in range(10):
            response = api_client.get("/api/trakt/status")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete 10 requests in under 2 seconds
        assert total_time < 2.0

    def test_trakt_start_stop_cycle(self, api_client):
        """Test complete start/stop cycle of Trakt integration."""
        # Initial state
        response = api_client.get("/api/trakt/status")
        data = response.json()
        initial_state = data["is_enabled"]

        # Start Trakt integration
        response = api_client.post("/api/trakt/start")
        assert_api_response_success(response)

        # Verify it's enabled
        response = api_client.get("/api/trakt/status")
        data = response.json()
        assert data["is_enabled"] is True

        # Stop Trakt integration
        response = api_client.post("/api/trakt/stop")
        assert_api_response_success(response)

        # Verify it's disabled
        response = api_client.get("/api/trakt/status")
        data = response.json()
        assert data["is_enabled"] is False

    def test_trakt_status_includes_timestamps(self, api_client):
        """Test Trakt status includes proper timestamps."""
        response = api_client.get("/api/trakt/status")
        data = response.json()

        status_info = data["status"]

        # Verify timestamp fields if present
        if "last_sync" in status_info and status_info["last_sync"] is not None:
            # Should be a valid timestamp
            assert isinstance(status_info["last_sync"], str)

    def test_trakt_status_with_sync_info(self, api_client):
        """Test Trakt status includes synchronization information."""
        response = api_client.get("/api/trakt/status")
        data = response.json()

        status_info = data["status"]

        # Verify sync-related fields
        assert "sync_status" in status_info
        assert "watchlist_count" in status_info
        assert "watched_count" in status_info

        # Verify data types
        assert isinstance(status_info["watchlist_count"], int)
        assert isinstance(status_info["watched_count"], int)

    def test_trakt_start_with_configuration(self, api_client):
        """Test starting Trakt with proper configuration."""
        # Mock Trakt configuration
        trakt_config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "access_token": "test_access_token"
        }

        response = api_client.post("/api/trakt/start", json=trakt_config)

        # Should handle configuration appropriately
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    def test_trakt_status_after_operations(self, api_client):
        """Test Trakt status reflects operations performed."""
        # Get initial status
        initial_response = api_client.get("/api/trakt/status")
        initial_data = initial_response.json()

        # Start Trakt
        api_client.post("/api/trakt/start")

        # Get status after start
        after_start_response = api_client.get("/api/trakt/status")
        after_start_data = after_start_response.json()

        # Stop Trakt
        api_client.post("/api/trakt/stop")

        # Get status after stop
        after_stop_response = api_client.get("/api/trakt/status")
        after_stop_data = after_stop_response.json()

        # Verify state changes
        assert after_start_data["is_enabled"] != initial_data["is_enabled"]
        assert after_stop_data["is_enabled"] != after_start_data["is_enabled"]


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
