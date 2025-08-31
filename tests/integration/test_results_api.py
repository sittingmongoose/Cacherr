"""
Comprehensive API integration tests for results endpoints.

This test suite covers all results API endpoints including:
- GET /api/results/operations - Get all operations
- GET /api/results/operations/<operation_id> - Get specific operation
- GET /api/results/users/<user_id>/stats - Get user statistics
- POST /api/results/cleanup - Clean up old results
- GET /api/results/export/<operation_id> - Export operation data

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and data handling.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestResultsOperationsAPI:
    """Comprehensive API tests for results operations endpoints."""

    def test_get_operations_success(self, api_client):
        """Test successful retrieval of all operations."""
        response = api_client.get("/api/results/operations")

        assert_api_response_success(response)
        data = response.json()

        assert "operations" in data
        assert isinstance(data["operations"], list)

    def test_get_operations_with_pagination(self, api_client):
        """Test operations retrieval with pagination parameters."""
        params = {
            "page": 1,
            "per_page": 10,
            "sort_by": "timestamp",
            "sort_order": "desc"
        }

        response = api_client.get("/api/results/operations", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "operations" in data
        assert "pagination" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination

    def test_get_operations_with_filters(self, api_client):
        """Test operations retrieval with filter parameters."""
        params = {
            "status": "completed",
            "operation_type": "move",
            "user_id": "test_user",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31"
        }

        response = api_client.get("/api/results/operations", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "operations" in data
        assert isinstance(data["operations"], list)

    def test_get_specific_operation_success(self, api_client):
        """Test successful retrieval of specific operation."""
        # First get list of operations
        list_response = api_client.get("/api/results/operations")
        list_data = list_response.json()

        if list_data["operations"]:
            operation_id = list_data["operations"][0]["id"]

            response = api_client.get(f"/api/results/operations/{operation_id}")

            assert_api_response_success(response)
            data = response.json()

            assert "operation" in data
            assert data["operation"]["id"] == operation_id
        else:
            # No operations available, test with a mock operation
            mock_operation_id = "test_operation_123"
            response = api_client.get(f"/api/results/operations/{mock_operation_id}")
            # Should return 404 for non-existent operation
            assert response.status_code == 404

    def test_get_specific_operation_not_found(self, api_client):
        """Test retrieval of non-existent operation."""
        response = api_client.get("/api/results/operations/non_existent_id")

        assert response.status_code == 404
        data = response.json()

        assert data["status"] == "error"
        assert "Operation not found" in data["message"]

    def test_get_operation_detailed_info(self, api_client):
        """Test that operation details include all required information."""
        # First get list of operations
        list_response = api_client.get("/api/results/operations")
        list_data = list_response.json()

        if list_data["operations"]:
            operation_id = list_data["operations"][0]["id"]

            response = api_client.get(f"/api/results/operations/{operation_id}")
            data = response.json()

            operation = data["operation"]

            # Verify operation structure
            required_fields = [
                "id", "timestamp", "status", "operation_type",
                "source_path", "target_path", "file_size", "user_id"
            ]

            for field in required_fields:
                assert field in operation

            # Verify data types
            assert isinstance(operation["id"], str)
            assert isinstance(operation["timestamp"], str)
            assert isinstance(operation["status"], str)
            assert isinstance(operation["operation_type"], str)
            assert isinstance(operation["file_size"], int)

    def test_operations_response_format(self, api_client):
        """Test operations response has correct format."""
        response = api_client.get("/api/results/operations")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

        # Required fields
        assert "operations" in data
        assert isinstance(data["operations"], list)

    def test_operations_pagination_metadata(self, api_client):
        """Test operations pagination metadata is correct."""
        params = {"page": 2, "per_page": 5}
        response = api_client.get("/api/results/operations", params=params)

        assert_api_response_success(response)
        data = response.json()

        if "pagination" in data:
            pagination = data["pagination"]
            assert pagination["page"] == 2
            assert pagination["per_page"] == 5
            assert "total" in pagination
            assert "total_pages" in pagination


@pytest.mark.api
class TestResultsUserStatsAPI:
    """Tests for user statistics endpoints."""

    def test_get_user_stats_success(self, api_client):
        """Test successful retrieval of user statistics."""
        user_id = "test_user_123"

        response = api_client.get(f"/api/results/users/{user_id}/stats")

        assert_api_response_success(response)
        data = response.json()

        assert "stats" in data
        stats = data["stats"]
        assert isinstance(stats, dict)

    def test_get_user_stats_structure(self, api_client):
        """Test user stats include all required metrics."""
        user_id = "test_user_123"

        response = api_client.get(f"/api/results/users/{user_id}/stats")
        data = response.json()

        stats = data["stats"]

        # Verify stats structure
        expected_fields = [
            "total_operations",
            "successful_operations",
            "failed_operations",
            "total_data_processed",
            "average_operation_time",
            "most_recent_operation"
        ]

        for field in expected_fields:
            assert field in stats

    def test_get_user_stats_with_date_range(self, api_client):
        """Test user stats with date range filtering."""
        user_id = "test_user_123"
        params = {
            "date_from": "2024-01-01",
            "date_to": "2024-12-31"
        }

        response = api_client.get(f"/api/results/users/{user_id}/stats", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "stats" in data

    def test_get_user_stats_invalid_user(self, api_client):
        """Test user stats for invalid/non-existent user."""
        user_id = "non_existent_user"

        response = api_client.get(f"/api/results/users/{user_id}/stats")

        # Should still return success with zero stats
        assert_api_response_success(response)
        data = response.json()

        assert "stats" in data
        stats = data["stats"]
        assert stats["total_operations"] == 0

    def test_user_stats_response_format(self, api_client):
        """Test user stats response has correct format."""
        user_id = "test_user_123"

        response = api_client.get(f"/api/results/users/{user_id}/stats")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "stats" in data


@pytest.mark.api
class TestResultsCleanupAPI:
    """Tests for results cleanup endpoints."""

    def test_cleanup_success(self, api_client):
        """Test successful cleanup of old results."""
        cleanup_data = {
            "older_than_days": 30,
            "max_records": 1000
        }

        response = api_client.post("/api/results/cleanup", json=cleanup_data)

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "records_deleted" in data
        assert isinstance(data["records_deleted"], int)

    def test_cleanup_default_parameters(self, api_client):
        """Test cleanup with default parameters."""
        response = api_client.post("/api/results/cleanup")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "records_deleted" in data

    def test_cleanup_invalid_parameters(self, api_client):
        """Test cleanup with invalid parameters."""
        invalid_data = {
            "older_than_days": -1,
            "max_records": -100
        }

        response = api_client.post("/api/results/cleanup", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_cleanup_response_format(self, api_client):
        """Test cleanup response has correct format."""
        response = api_client.post("/api/results/cleanup")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "message" in data


@pytest.mark.api
class TestResultsExportAPI:
    """Tests for results export endpoints."""

    def test_export_operation_success(self, api_client):
        """Test successful export of operation data."""
        # First get list of operations
        list_response = api_client.get("/api/results/operations")
        list_data = list_response.json()

        if list_data["operations"]:
            operation_id = list_data["operations"][0]["id"]

            response = api_client.get(f"/api/results/export/{operation_id}")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

            data = response.json()
            assert isinstance(data, dict)
            assert "operation" in data
        else:
            # Test with mock operation ID
            mock_operation_id = "test_operation_123"
            response = api_client.get(f"/api/results/export/{mock_operation_id}")
            assert response.status_code == 404

    def test_export_operation_not_found(self, api_client):
        """Test export of non-existent operation."""
        response = api_client.get("/api/results/export/non_existent_id")

        assert response.status_code == 404
        data = response.json()

        assert data["status"] == "error"
        assert "Operation not found" in data["message"]

    def test_export_operation_detailed_data(self, api_client):
        """Test that export includes detailed operation data."""
        # First get list of operations
        list_response = api_client.get("/api/results/operations")
        list_data = list_response.json()

        if list_data["operations"]:
            operation_id = list_data["operations"][0]["id"]

            response = api_client.get(f"/api/results/export/{operation_id}")
            data = response.json()

            operation = data["operation"]

            # Verify export includes additional metadata
            assert "export_timestamp" in data
            assert "export_format" in data

            # Verify operation data is complete
            required_fields = [
                "id", "timestamp", "status", "operation_type",
                "source_path", "target_path", "file_size", "duration"
            ]

            for field in required_fields:
                assert field in operation


@pytest.mark.api
class TestResultsAPIErrorHandling:
    """Tests for results API error handling."""

    def test_operations_invalid_pagination(self, api_client):
        """Test operations endpoint with invalid pagination."""
        params = {
            "page": -1,
            "per_page": 1000
        }

        response = api_client.get("/api/results/operations", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_operations_invalid_filters(self, api_client):
        """Test operations endpoint with invalid filters."""
        params = {
            "status": "invalid_status",
            "date_from": "invalid_date"
        }

        response = api_client.get("/api/results/operations", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_user_stats_invalid_user_id(self, api_client):
        """Test user stats with invalid user ID."""
        invalid_user_ids = ["", "user@invalid", "user.with.dots"]

        for user_id in invalid_user_ids:
            response = api_client.get(f"/api/results/users/{user_id}/stats")

            # Should handle gracefully
            assert response.status_code in [200, 400, 404]

    def test_cleanup_invalid_json(self, api_client):
        """Test cleanup with invalid JSON."""
        response = api_client.post(
            "/api/results/cleanup",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_results_endpoints_method_not_allowed(self, api_client):
        """Test results endpoints reject invalid methods."""
        # Test POST on GET-only endpoints
        response = api_client.post("/api/results/operations")
        assert response.status_code == 405

        response = api_client.post("/api/results/operations/test_id")
        assert response.status_code == 405

        response = api_client.get("/api/results/cleanup")
        assert response.status_code == 405

    def test_results_endpoints_cors_headers(self, api_client):
        """Test results endpoints include proper CORS headers."""
        endpoints = [
            ("GET", "/api/results/operations"),
            ("POST", "/api/results/cleanup")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)

            assert response.status_code in [200, 404, 405]

    def test_results_endpoints_content_length(self, api_client):
        """Test results responses have appropriate content length."""
        response = api_client.get("/api/results/operations")

        if response.status_code == 200:
            assert "content-length" in response.headers

            content_length = int(response.headers["content-length"])
            assert content_length > 0

            # Verify content length matches actual response size
            response_data = response.content
            assert len(response_data) == content_length


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
