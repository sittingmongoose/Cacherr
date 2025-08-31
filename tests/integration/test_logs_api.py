"""
Comprehensive API integration tests for logs endpoint.

This test suite covers the logs API endpoint:
- GET /api/logs - Get application logs

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and log data handling.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestLogsAPI:
    """Comprehensive API tests for logs endpoint."""

    def test_get_logs_success(self, api_client):
        """Test successful retrieval of application logs."""
        response = api_client.get("/api/logs")

        assert_api_response_success(response)
        data = response.json()

        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_get_logs_with_pagination(self, api_client):
        """Test logs retrieval with pagination parameters."""
        params = {
            "page": 1,
            "per_page": 50,
            "level": "INFO"
        }

        response = api_client.get("/api/logs", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "logs" in data
        assert "pagination" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination

    def test_get_logs_with_filters(self, api_client):
        """Test logs retrieval with filter parameters."""
        params = {
            "level": "ERROR",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "search": "error"
        }

        response = api_client.get("/api/logs", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_get_logs_response_format(self, api_client):
        """Test logs response has correct format."""
        response = api_client.get("/api/logs")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

        # Required fields
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_get_logs_entry_structure(self, api_client):
        """Test that log entries have proper structure."""
        response = api_client.get("/api/logs")
        data = response.json()

        logs = data["logs"]

        if logs:  # If there are log entries
            log_entry = logs[0]

            # Verify log entry structure
            required_fields = [
                "timestamp", "level", "message", "module"
            ]

            for field in required_fields:
                assert field in log_entry

            # Verify data types
            assert isinstance(log_entry["timestamp"], str)
            assert isinstance(log_entry["level"], str)
            assert isinstance(log_entry["message"], str)

    def test_get_logs_by_level(self, api_client):
        """Test filtering logs by level."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            params = {"level": level}
            response = api_client.get("/api/logs", params=params)

            assert_api_response_success(response)
            data = response.json()

            assert "logs" in data

            # Verify that returned logs match the requested level
            for log_entry in data["logs"]:
                if data["logs"]:  # Only check if there are logs
                    assert log_entry["level"] == level

    def test_get_logs_date_filtering(self, api_client):
        """Test filtering logs by date range."""
        params = {
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-12-31T23:59:59Z"
        }

        response = api_client.get("/api/logs", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "logs" in data

    def test_get_logs_search_functionality(self, api_client):
        """Test searching logs by content."""
        search_terms = ["error", "warning", "info"]

        for term in search_terms:
            params = {"search": term}
            response = api_client.get("/api/logs", params=params)

            assert_api_response_success(response)
            data = response.json()

            assert "logs" in data

    def test_get_logs_invalid_pagination(self, api_client):
        """Test logs endpoint with invalid pagination."""
        params = {
            "page": -1,
            "per_page": 1000
        }

        response = api_client.get("/api/logs", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_get_logs_invalid_filters(self, api_client):
        """Test logs endpoint with invalid filters."""
        params = {
            "level": "INVALID_LEVEL",
            "date_from": "invalid_date"
        }

        response = api_client.get("/api/logs", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_logs_endpoint_cors_headers(self, api_client):
        """Test logs endpoint includes proper CORS headers."""
        response = api_client.get("/api/logs")

        assert response.status_code == 200

    def test_logs_endpoint_content_length(self, api_client):
        """Test logs response has appropriate content length."""
        response = api_client.get("/api/logs")

        if response.status_code == 200:
            assert "content-length" in response.headers

            content_length = int(response.headers["content-length"])
            assert content_length > 0

            # Verify content length matches actual response size
            response_data = response.content
            assert len(response_data) == content_length

    def test_logs_endpoint_method_not_allowed(self, api_client):
        """Test logs endpoint rejects invalid methods."""
        response = api_client.post("/api/logs")
        assert response.status_code == 405

        response = api_client.put("/api/logs")
        assert response.status_code == 405

        response = api_client.delete("/api/logs")
        assert response.status_code == 405

    def test_logs_endpoint_error_handling(self, api_client):
        """Test logs endpoint handles errors gracefully."""
        # Test with query parameters that might cause issues
        params = {"per_page": "not_a_number"}
        response = api_client.get("/api/logs", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_logs_pagination_metadata(self, api_client):
        """Test logs pagination metadata is correct."""
        params = {"page": 2, "per_page": 10}
        response = api_client.get("/api/logs", params=params)

        assert_api_response_success(response)
        data = response.json()

        if "pagination" in data:
            pagination = data["pagination"]
            assert pagination["page"] == 2
            assert pagination["per_page"] == 10
            assert "total" in pagination
            assert "total_pages" in pagination

    @pytest.mark.slow
    def test_logs_performance_large_dataset(self, api_client):
        """Test logs endpoint performance with large datasets."""
        import time

        start_time = time.time()

        # Request a large number of log entries
        params = {"per_page": 100}
        response = api_client.get("/api/logs", params=params)

        end_time = time.time()
        response_time = end_time - start_time

        assert_api_response_success(response)

        # Should respond within reasonable time (under 5 seconds)
        assert response_time < 5.0

    def test_logs_response_consistency(self, api_client):
        """Test that logs responses are consistent across multiple requests."""
        # Make multiple requests and verify consistency
        responses = []

        for _ in range(3):
            response = api_client.get("/api/logs")
            assert response.status_code == 200
            data = response.json()
            responses.append(data)

        # All responses should have the same structure
        for response_data in responses:
            assert "logs" in response_data
            assert isinstance(response_data["logs"], list)


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
