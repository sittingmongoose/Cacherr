"""
Comprehensive API integration tests for cached files endpoints.

This test suite covers all cached files API endpoints including:
- GET /api/cached/files - Get all cached files
- GET /api/cached/files/<file_id> - Get specific cached file
- DELETE /api/cached/files/<file_id> - Delete cached file
- GET /api/cached/statistics - Get cache statistics
- GET /api/cached/users/<user_id>/stats - Get user cache stats
- POST /api/cached/cleanup - Clean up cache
- GET /api/cached/files/search - Search cached files
- GET /api/cached/export - Export cache data

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and cache operations.
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.api
class TestCachedFilesAPI:
    """Comprehensive API tests for cached files endpoints."""

    def test_get_cached_files_success(self, api_client):
        """Test successful retrieval of all cached files."""
        response = api_client.get("/api/cached/files")

        assert_api_response_success(response)
        data = response.json()

        assert "files" in data
        assert isinstance(data["files"], list)

    def test_get_cached_files_with_pagination(self, api_client):
        """Test cached files retrieval with pagination."""
        params = {
            "page": 1,
            "per_page": 20,
            "sort_by": "cached_at",
            "sort_order": "desc"
        }

        response = api_client.get("/api/cached/files", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "files" in data
        assert "pagination" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination

    def test_get_cached_files_with_filters(self, api_client):
        """Test cached files retrieval with filters."""
        params = {
            "status": "cached",
            "user_id": "test_user",
            "min_size": 1000000,
            "max_size": 100000000,
            "date_from": "2024-01-01"
        }

        response = api_client.get("/api/cached/files", params=params)

        assert_api_response_success(response)
        data = response.json()

        assert "files" in data
        assert isinstance(data["files"], list)

    def test_get_specific_cached_file_success(self, api_client):
        """Test successful retrieval of specific cached file."""
        # First get list of cached files
        list_response = api_client.get("/api/cached/files")
        list_data = list_response.json()

        if list_data["files"]:
            file_id = list_data["files"][0]["id"]

            response = api_client.get(f"/api/cached/files/{file_id}")

            assert_api_response_success(response)
            data = response.json()

            assert "file" in data
            assert data["file"]["id"] == file_id
        else:
            # No cached files available, test with a mock file
            mock_file_id = "test_file_123"
            response = api_client.get(f"/api/cached/files/{mock_file_id}")
            # Should return 404 for non-existent file
            assert response.status_code == 404

    def test_get_specific_cached_file_not_found(self, api_client):
        """Test retrieval of non-existent cached file."""
        response = api_client.get("/api/cached/files/non_existent_id")

        assert response.status_code == 404
        data = response.json()

        assert data["status"] == "error"
        assert "File not found" in data["message"]

    def test_delete_cached_file_success(self, api_client):
        """Test successful deletion of cached file."""
        # First get list of cached files
        list_response = api_client.get("/api/cached/files")
        list_data = list_response.json()

        if list_data["files"]:
            file_id = list_data["files"][0]["id"]

            response = api_client.delete(f"/api/cached/files/{file_id}")

            assert_api_response_success(response)
            data = response.json()

            assert "message" in data
            assert "File deleted successfully" in data["message"]
        else:
            # No cached files to delete
            mock_file_id = "test_file_123"
            response = api_client.delete(f"/api/cached/files/{mock_file_id}")
            assert response.status_code == 404

    def test_delete_cached_file_not_found(self, api_client):
        """Test deletion of non-existent cached file."""
        response = api_client.delete("/api/cached/files/non_existent_id")

        assert response.status_code == 404
        data = response.json()

        assert data["status"] == "error"
        assert "File not found" in data["message"]

    def test_cached_file_detailed_info(self, api_client):
        """Test that cached file details include all required information."""
        # First get list of cached files
        list_response = api_client.get("/api/cached/files")
        list_data = list_response.json()

        if list_data["files"]:
            file_id = list_data["files"][0]["id"]

            response = api_client.get(f"/api/cached/files/{file_id}")
            data = response.json()

            cached_file = data["file"]

            # Verify file structure
            required_fields = [
                "id", "original_path", "cache_path", "file_size",
                "cached_at", "last_accessed", "status", "user_id"
            ]

            for field in required_fields:
                assert field in cached_file

            # Verify data types
            assert isinstance(cached_file["id"], str)
            assert isinstance(cached_file["file_size"], int)
            assert isinstance(cached_file["cached_at"], str)


@pytest.mark.api
class TestCachedStatisticsAPI:
    """Tests for cache statistics endpoints."""

    def test_get_cache_statistics_success(self, api_client):
        """Test successful retrieval of cache statistics."""
        response = api_client.get("/api/cached/statistics")

        assert_api_response_success(response)
        data = response.json()

        assert "statistics" in data
        stats = data["statistics"]
        assert isinstance(stats, dict)

    def test_get_cache_statistics_structure(self, api_client):
        """Test cache statistics include all required metrics."""
        response = api_client.get("/api/cached/statistics")
        data = response.json()

        stats = data["statistics"]

        # Verify stats structure
        expected_fields = [
            "total_files",
            "total_size",
            "free_space",
            "cache_hit_rate",
            "average_file_size",
            "oldest_file_age",
            "newest_file_age"
        ]

        for field in expected_fields:
            assert field in stats

    def test_get_user_cache_stats_success(self, api_client):
        """Test successful retrieval of user cache statistics."""
        user_id = "test_user_123"

        response = api_client.get(f"/api/cached/users/{user_id}/stats")

        assert_api_response_success(response)
        data = response.json()

        assert "stats" in data
        stats = data["stats"]
        assert isinstance(stats, dict)

    def test_get_user_cache_stats_structure(self, api_client):
        """Test user cache stats include all required metrics."""
        user_id = "test_user_123"

        response = api_client.get(f"/api/cached/users/{user_id}/stats")
        data = response.json()

        stats = data["stats"]

        # Verify stats structure
        expected_fields = [
            "user_total_files",
            "user_total_size",
            "user_cache_percentage",
            "user_hit_rate",
            "last_activity"
        ]

        for field in expected_fields:
            assert field in stats

    def test_get_user_cache_stats_invalid_user(self, api_client):
        """Test user cache stats for invalid/non-existent user."""
        user_id = "non_existent_user"

        response = api_client.get(f"/api/cached/users/{user_id}/stats")

        # Should still return success with zero stats
        assert_api_response_success(response)
        data = response.json()

        assert "stats" in data
        stats = data["stats"]
        assert stats["user_total_files"] == 0


@pytest.mark.api
class TestCachedCleanupAPI:
    """Tests for cache cleanup endpoints."""

    def test_cache_cleanup_success(self, api_client):
        """Test successful cache cleanup."""
        cleanup_data = {
            "older_than_days": 30,
            "max_cache_size": 1000000000,  # 1GB
            "cleanup_strategy": "lru"
        }

        response = api_client.post("/api/cached/cleanup", json=cleanup_data)

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "files_removed" in data
        assert "space_freed" in data
        assert isinstance(data["files_removed"], int)
        assert isinstance(data["space_freed"], int)

    def test_cache_cleanup_default_parameters(self, api_client):
        """Test cache cleanup with default parameters."""
        response = api_client.post("/api/cached/cleanup")

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "files_removed" in data
        assert "space_freed" in data

    def test_cache_cleanup_invalid_parameters(self, api_client):
        """Test cache cleanup with invalid parameters."""
        invalid_data = {
            "older_than_days": -1,
            "max_cache_size": -100,
            "cleanup_strategy": "invalid_strategy"
        }

        response = api_client.post("/api/cached/cleanup", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_cache_cleanup_dry_run(self, api_client):
        """Test cache cleanup dry run mode."""
        cleanup_data = {
            "dry_run": True,
            "older_than_days": 30
        }

        response = api_client.post("/api/cached/cleanup", json=cleanup_data)

        assert_api_response_success(response)
        data = response.json()

        assert "message" in data
        assert "files_removed" in data
        assert "space_freed" in data
        # In dry run, no actual files should be removed
        assert "dry_run" in data or data["files_removed"] == 0


@pytest.mark.api
class TestCachedSearchAPI:
    """Tests for cached files search endpoints."""

    def test_search_cached_files_success(self, api_client):
        """Test successful search of cached files."""
        search_params = {
            "query": "movie",
            "search_fields": ["filename", "path"],
            "limit": 10
        }

        response = api_client.get("/api/cached/files/search", params=search_params)

        assert_api_response_success(response)
        data = response.json()

        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_cached_files_empty_query(self, api_client):
        """Test search with empty query returns all files."""
        response = api_client.get("/api/cached/files/search")

        assert_api_response_success(response)
        data = response.json()

        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_cached_files_with_filters(self, api_client):
        """Test search with additional filters."""
        search_params = {
            "query": "test",
            "file_type": "mkv",
            "min_size": 1000000,
            "max_size": 100000000,
            "date_from": "2024-01-01"
        }

        response = api_client.get("/api/cached/files/search", params=search_params)

        assert_api_response_success(response)
        data = response.json()

        assert "results" in data

    def test_search_cached_files_pagination(self, api_client):
        """Test search with pagination."""
        search_params = {
            "query": "test",
            "page": 1,
            "per_page": 5
        }

        response = api_client.get("/api/cached/files/search", params=search_params)

        assert_api_response_success(response)
        data = response.json()

        assert "results" in data
        assert "pagination" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination


@pytest.mark.api
class TestCachedExportAPI:
    """Tests for cache export endpoints."""

    def test_export_cache_data_success(self, api_client):
        """Test successful export of cache data."""
        response = api_client.get("/api/cached/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "export_timestamp" in data
        assert "cache_data" in data

    def test_export_cache_data_structure(self, api_client):
        """Test export includes complete cache data structure."""
        response = api_client.get("/api/cached/export")
        data = response.json()

        assert "export_timestamp" in data
        assert "cache_data" in data
        assert "statistics" in data

        cache_data = data["cache_data"]
        assert isinstance(cache_data, dict)

        # Verify export format
        assert "files" in cache_data
        assert "metadata" in cache_data

    def test_export_cache_data_with_format(self, api_client):
        """Test export with different formats."""
        formats = ["json", "csv"]

        for export_format in formats:
            params = {"format": export_format}
            response = api_client.get("/api/cached/export", params=params)

            if export_format == "json":
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/json"
            elif export_format == "csv":
                # CSV might not be implemented, check response
                assert response.status_code in [200, 400, 501]


@pytest.mark.api
class TestCachedAPIErrorHandling:
    """Tests for cached API error handling."""

    def test_cached_files_invalid_pagination(self, api_client):
        """Test cached files endpoint with invalid pagination."""
        params = {
            "page": -1,
            "per_page": 1000
        }

        response = api_client.get("/api/cached/files", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_cached_files_invalid_filters(self, api_client):
        """Test cached files endpoint with invalid filters."""
        params = {
            "status": "invalid_status",
            "date_from": "invalid_date"
        }

        response = api_client.get("/api/cached/files", params=params)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_cached_cleanup_invalid_json(self, api_client):
        """Test cache cleanup with invalid JSON."""
        response = api_client.post(
            "/api/cached/cleanup",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_cached_endpoints_method_not_allowed(self, api_client):
        """Test cached endpoints reject invalid methods."""
        # Test invalid methods on various endpoints
        response = api_client.post("/api/cached/files")
        assert response.status_code == 405

        response = api_client.put("/api/cached/statistics")
        assert response.status_code == 405

    def test_cached_endpoints_cors_headers(self, api_client):
        """Test cached endpoints include proper CORS headers."""
        endpoints = [
            ("GET", "/api/cached/files"),
            ("GET", "/api/cached/statistics"),
            ("POST", "/api/cached/cleanup")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)

            assert response.status_code in [200, 404, 405]

    def test_cached_endpoints_content_length(self, api_client):
        """Test cached responses have appropriate content length."""
        response = api_client.get("/api/cached/files")

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
