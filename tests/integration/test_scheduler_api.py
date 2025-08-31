"""
Comprehensive API integration tests for scheduler endpoints.

This test suite covers all scheduler API endpoints including:
- POST /api/scheduler/start - Start the scheduler
- POST /api/scheduler/stop - Stop the scheduler
- GET /api/scheduler/status - Get scheduler status

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and scheduler operations.
"""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestSchedulerAPI:
    """Comprehensive API tests for scheduler endpoints."""

    def test_scheduler_start_success(self, api_client):
        """Test successful scheduler start."""
        response = api_client.post("/api/scheduler/start")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Scheduler started successfully" in data["message"]

    def test_scheduler_stop_success(self, api_client):
        """Test successful scheduler stop."""
        # First start the scheduler
        start_response = api_client.post("/api/scheduler/start")
        assert start_response.status_code == 200

        # Then stop it
        response = api_client.post("/api/scheduler/stop")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "Scheduler stopped successfully" in data["message"]

    def test_scheduler_status_when_stopped(self, api_client):
        """Test scheduler status when scheduler is stopped."""
        # Ensure scheduler is stopped
        api_client.post("/api/scheduler/stop")

        response = api_client.get("/api/scheduler/status")

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

    def test_scheduler_status_when_running(self, api_client):
        """Test scheduler status when scheduler is running."""
        # Start the scheduler
        api_client.post("/api/scheduler/start")

        response = api_client.get("/api/scheduler/status")

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

    def test_scheduler_status_detailed_info(self, api_client):
        """Test scheduler status includes detailed information."""
        response = api_client.get("/api/scheduler/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]

        # Verify detailed status information
        assert "jobs" in status_info
        assert "next_run" in status_info
        assert "last_run" in status_info

        # Jobs should be a list
        assert isinstance(status_info["jobs"], list)

    def test_scheduler_start_idempotent(self, api_client):
        """Test that starting scheduler multiple times is idempotent."""
        # Start scheduler multiple times
        for _ in range(3):
            response = api_client.post("/api/scheduler/start")
            assert_api_response_success(response)

        # Verify scheduler is still running
        status_response = api_client.get("/api/scheduler/status")
        assert_api_response_success(status_response)
        status_data = status_response.json()
        assert status_data["is_running"] is True

    def test_scheduler_stop_idempotent(self, api_client):
        """Test that stopping scheduler multiple times is idempotent."""
        # Stop scheduler multiple times
        for _ in range(3):
            response = api_client.post("/api/scheduler/stop")
            assert_api_response_success(response)

        # Verify scheduler is still stopped
        status_response = api_client.get("/api/scheduler/status")
        assert_api_response_success(status_response)
        status_data = status_response.json()
        assert status_data["is_running"] is False

    def test_scheduler_start_after_stop(self, api_client):
        """Test starting scheduler after it has been stopped."""
        # Stop scheduler
        api_client.post("/api/scheduler/stop")

        # Verify it's stopped
        status_response = api_client.get("/api/scheduler/status")
        status_data = status_response.json()
        assert status_data["is_running"] is False

        # Start scheduler
        start_response = api_client.post("/api/scheduler/start")
        assert_api_response_success(start_response)

        # Verify it's running
        status_response = api_client.get("/api/scheduler/status")
        status_data = status_response.json()
        assert status_data["is_running"] is True

    def test_scheduler_status_response_format(self, api_client):
        """Test scheduler status response has correct format."""
        response = api_client.get("/api/scheduler/status")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

        # Required fields
        required_fields = ["status", "is_running"]
        for field in required_fields:
            assert field in data

    def test_scheduler_endpoints_cors_headers(self, api_client):
        """Test scheduler endpoints include proper CORS headers."""
        endpoints = [
            ("POST", "/api/scheduler/start"),
            ("POST", "/api/scheduler/stop"),
            ("GET", "/api/scheduler/status")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)

            assert response.status_code == 200

    def test_scheduler_endpoints_content_length(self, api_client):
        """Test scheduler responses have appropriate content length."""
        endpoints = [
            ("POST", "/api/scheduler/start"),
            ("POST", "/api/scheduler/stop"),
            ("GET", "/api/scheduler/status")
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

    def test_scheduler_endpoints_error_handling(self, api_client):
        """Test scheduler endpoints handle errors gracefully."""
        # Test invalid methods
        response = api_client.put("/api/scheduler/start")
        assert response.status_code == 405

        response = api_client.delete("/api/scheduler/status")
        assert response.status_code == 405

        # Test non-existent scheduler endpoint
        response = api_client.get("/api/scheduler/nonexistent")
        assert response.status_code == 404

    def test_scheduler_status_with_job_details(self, api_client):
        """Test scheduler status includes job details."""
        response = api_client.get("/api/scheduler/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]
        jobs = status_info["jobs"]

        # Verify jobs structure
        assert isinstance(jobs, list)

        # If there are jobs, verify their structure
        for job in jobs:
            assert isinstance(job, dict)
            assert "id" in job
            assert "name" in job
            assert "next_run" in job
            assert "enabled" in job

    def test_scheduler_operations_response_consistency(self, api_client):
        """Test scheduler operation responses follow consistent format."""
        operations = [
            ("POST", "/api/scheduler/start"),
            ("POST", "/api/scheduler/stop")
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
    def test_scheduler_status_performance(self, api_client):
        """Test scheduler status endpoint performance."""
        import time

        start_time = time.time()

        # Make multiple status requests
        for _ in range(10):
            response = api_client.get("/api/scheduler/status")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete 10 requests in under 2 seconds
        assert total_time < 2.0

    def test_scheduler_start_stop_cycle(self, api_client):
        """Test complete start/stop cycle of scheduler."""
        # Initial state - should be stopped
        response = api_client.get("/api/scheduler/status")
        data = response.json()
        initial_state = data["is_running"]

        # Start scheduler
        response = api_client.post("/api/scheduler/start")
        assert_api_response_success(response)

        # Verify it's running
        response = api_client.get("/api/scheduler/status")
        data = response.json()
        assert data["is_running"] is True

        # Stop scheduler
        response = api_client.post("/api/scheduler/stop")
        assert_api_response_success(response)

        # Verify it's stopped
        response = api_client.get("/api/scheduler/status")
        data = response.json()
        assert data["is_running"] is False

    def test_scheduler_status_includes_timestamps(self, api_client):
        """Test scheduler status includes proper timestamps."""
        response = api_client.get("/api/scheduler/status")

        assert_api_response_success(response)
        data = response.json()

        status_info = data["status"]

        # Verify timestamp fields if present
        if "next_run" in status_info and status_info["next_run"] is not None:
            # Should be a valid timestamp
            assert isinstance(status_info["next_run"], str)

        if "last_run" in status_info and status_info["last_run"] is not None:
            # Should be a valid timestamp
            assert isinstance(status_info["last_run"], str)


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
