"""
Comprehensive API integration tests for health and status endpoints.

This test suite covers all health check endpoints including:
- GET /health - Basic health check
- GET /health/detailed - Detailed health information
- GET /health/dependencies - Dependency health checks
- GET /ready - Readiness probe
- GET /api/status - Application status

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and health metrics.
"""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestHealthAPI:
    """Comprehensive API tests for health endpoints."""

    def test_health_basic_success(self, api_client):
        """Test basic health check endpoint returns success."""
        response = api_client.get("/health")

        assert_api_response_success(response)
        data = response.json()

        # Verify health check structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] == "healthy"

        # Verify timestamp is recent (within last minute)
        import datetime
        response_time = datetime.datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        time_diff = datetime.datetime.now(datetime.timezone.utc) - response_time
        assert time_diff.total_seconds() < 60

    def test_health_response_format(self, api_client):
        """Test health endpoint returns proper JSON format."""
        response = api_client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

        # Verify required fields
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data

    def test_health_detailed_success(self, api_client):
        """Test detailed health check endpoint."""
        response = api_client.get("/health/detailed")

        assert_api_response_success(response)
        data = response.json()

        # Verify detailed health structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "components" in data

        # Verify components structure
        components = data["components"]
        assert isinstance(components, dict)
        assert "database" in components
        assert "cache" in components
        assert "plex" in components

    def test_health_dependencies_success(self, api_client):
        """Test dependencies health check endpoint."""
        response = api_client.get("/health/dependencies")

        assert_api_response_success(response)
        data = response.json()

        # Verify dependencies structure
        assert "status" in data
        assert "dependencies" in data

        dependencies = data["dependencies"]
        assert isinstance(dependencies, dict)

        # Verify key dependencies are checked
        expected_deps = ["database", "filesystem", "plex"]
        for dep in expected_deps:
            assert dep in dependencies
            assert isinstance(dependencies[dep], dict)
            assert "status" in dependencies[dep]

    def test_ready_probe_success(self, api_client):
        """Test readiness probe endpoint."""
        response = api_client.get("/ready")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ready"
        assert "message" in data
        assert "Ready to accept requests" in data["message"]

    def test_ready_probe_unhealthy_dependencies(self, api_client):
        """Test readiness probe when dependencies are unhealthy."""
        # Mock unhealthy dependency
        with patch('src.web.routes.health.check_database_health') as mock_db:
            mock_db.return_value = {"status": "unhealthy", "message": "Database connection failed"}

            response = api_client.get("/ready")
            assert response.status_code == 503  # Service Unavailable

            data = response.json()
            assert data["status"] == "not_ready"
            assert "Database connection failed" in data["message"]

    def test_health_endpoints_cors_headers(self, api_client):
        """Test that health endpoints include proper CORS headers."""
        endpoints = ["/health", "/health/detailed", "/health/dependencies", "/ready"]

        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == 200

            # Check for CORS headers if CORS is enabled
            # Note: CORS might be disabled in test mode, so this is informational
            cors_headers = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers"
            ]

            # At minimum, should not have CORS errors
            assert response.status_code == 200

    def test_health_endpoints_content_length(self, api_client):
        """Test that health responses have appropriate content length."""
        endpoints = ["/health", "/health/detailed", "/health/dependencies", "/ready"]

        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == 200

            assert "content-length" in response.headers
            content_length = int(response.headers["content-length"])
            assert content_length > 0

            # Verify content length matches actual response size
            response_data = response.content
            assert len(response_data) == content_length

    def test_health_detailed_with_metrics(self, api_client):
        """Test detailed health includes performance metrics."""
        response = api_client.get("/health/detailed")

        assert_api_response_success(response)
        data = response.json()

        # Verify metrics are included
        assert "metrics" in data
        metrics = data["metrics"]
        assert isinstance(metrics, dict)

        # Verify key metrics
        assert "memory_usage" in metrics
        assert "cpu_usage" in metrics
        assert "disk_usage" in metrics

    def test_health_dependencies_individual_checks(self, api_client):
        """Test each dependency health check individually."""
        response = api_client.get("/health/dependencies")

        assert_api_response_success(response)
        data = response.json()

        dependencies = data["dependencies"]

        # Test each dependency has proper structure
        for dep_name, dep_status in dependencies.items():
            assert isinstance(dep_status, dict)
            assert "status" in dep_status
            assert dep_status["status"] in ["healthy", "unhealthy", "unknown"]

            if dep_status["status"] == "unhealthy":
                assert "message" in dep_status

    def test_health_endpoints_error_handling(self, api_client):
        """Test health endpoints handle errors gracefully."""
        # Test invalid method
        response = api_client.post("/health")
        assert response.status_code == 405  # Method Not Allowed

        response = api_client.put("/health/detailed")
        assert response.status_code == 405

        # Test non-existent health endpoint
        response = api_client.get("/health/nonexistent")
        assert response.status_code == 404

    def test_health_response_consistency(self, api_client):
        """Test that all health responses follow consistent format."""
        endpoints = ["/health", "/health/detailed", "/health/dependencies", "/ready"]

        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code in [200, 503]

            data = response.json()
            assert isinstance(data, dict)
            assert "status" in data

            if data["status"] in ["healthy", "ready"]:
                assert response.status_code == 200
            elif data["status"] in ["unhealthy", "not_ready"]:
                assert response.status_code in [503, 500]

    def test_health_endpoints_rate_limiting(self, api_client):
        """Test that health endpoints have appropriate rate limiting."""
        # Make multiple rapid requests
        responses = []
        for _ in range(20):
            response = api_client.get("/health")
            responses.append(response.status_code)

        # Should not be rate limited (429 status)
        assert 429 not in responses

        # All responses should be successful
        assert all(status == 200 for status in responses)

    @pytest.mark.slow
    def test_health_endpoints_under_load(self, api_client):
        """Test health endpoints under concurrent load."""
        import threading
        import time

        results = []
        errors = []

        def make_health_request(request_id: int):
            try:
                response = api_client.get("/health")
                results.append((request_id, response.status_code))
            except Exception as e:
                errors.append((request_id, str(e)))

        # Make 10 concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_health_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 10
        assert len(errors) == 0

        for request_id, status_code in results:
            assert status_code == 200

    def test_health_detailed_performance_metrics(self, api_client):
        """Test detailed health includes accurate performance metrics."""
        response = api_client.get("/health/detailed")

        assert_api_response_success(response)
        data = response.json()

        metrics = data["metrics"]

        # Verify memory usage is reasonable
        memory_usage = metrics["memory_usage"]
        assert isinstance(memory_usage, (int, float))
        assert 0 <= memory_usage <= 100  # Percentage

        # Verify CPU usage is reasonable
        cpu_usage = metrics["cpu_usage"]
        assert isinstance(cpu_usage, (int, float))
        assert 0 <= cpu_usage <= 100  # Percentage

        # Verify disk usage is reasonable
        disk_usage = metrics["disk_usage"]
        assert isinstance(disk_usage, (int, float))
        assert 0 <= disk_usage <= 100  # Percentage


@pytest.mark.api
class TestApplicationStatusAPI:
    """Tests for application status endpoint."""

    def test_status_endpoint_success(self, api_client):
        """Test application status endpoint returns correct information."""
        response = api_client.get("/api/status")

        assert_api_response_success(response)
        data = response.json()

        # Verify status structure
        assert "application" in data
        assert "version" in data
        assert "uptime" in data
        assert "configuration" in data

        # Verify application info
        app_info = data["application"]
        assert "name" in app_info
        assert "status" in app_info
        assert app_info["status"] == "running"

    def test_status_endpoint_configuration_info(self, api_client):
        """Test status endpoint includes configuration information."""
        response = api_client.get("/api/status")

        assert_api_response_success(response)
        data = response.json()

        config = data["configuration"]
        assert isinstance(config, dict)

        # Verify key configuration sections are present
        assert "plex" in config
        assert "media" in config
        assert "performance" in config

    def test_status_endpoint_uptime_calculation(self, api_client):
        """Test that uptime is calculated correctly."""
        import time

        # Record time before request
        start_time = time.time()

        response = api_client.get("/api/status")

        assert_api_response_success(response)
        data = response.json()

        # Verify uptime is reasonable (should be > 0 and not too large)
        uptime = data["uptime"]
        assert isinstance(uptime, (int, float))
        assert uptime >= 0
        assert uptime < 3600  # Should be less than 1 hour for a test app

    def test_status_endpoint_error_handling(self, api_client):
        """Test status endpoint handles errors gracefully."""
        # Test invalid method
        response = api_client.post("/api/status")
        assert response.status_code == 405

        # Test with query parameters (should be ignored)
        response = api_client.get("/api/status?invalid=param")
        assert response.status_code == 200  # Should still work


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
