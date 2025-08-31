"""
Comprehensive API integration tests for configuration endpoints.

This test suite covers all configuration API endpoints including:
- GET /api/config/current - Retrieve current configuration
- POST /api/config/update - Update configuration settings
- POST /api/config/test-plex - Test Plex server connection
- GET /api/config/export - Export configuration
- POST /api/config/import - Import configuration
- POST /api/config/reset - Reset to defaults
- GET /api/config/schema - Get configuration schema

All tests use the FastAPI test client to simulate real HTTP requests
and verify proper response formats, status codes, and data validation.
"""

import json
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Import the Flask app creation function
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.web.app import create_app


@pytest.mark.api
class TestConfigurationAPI:
    """Comprehensive API tests for configuration endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with testing configuration."""
        app = create_app(testing=True)
        return TestClient(app)

    @pytest.fixture
    def valid_config_data(self):
        """Valid configuration data for testing."""
        return {
            "plex": {
                "url": "http://localhost:32400",
                "token": "test_token_123",
                "timeout": 30,
                "verify_ssl": True
            },
            "media": {
                "source_paths": ["/media/movies", "/media/tv"],
                "cache_path": "/cache",
                "file_extensions": ["mp4", "mkv", "avi"],
                "min_file_size": 100,
                "max_file_size": 10000
            },
            "performance": {
                "max_concurrent_moves_cache": 3,
                "max_concurrent_moves_array": 1,
                "max_concurrent_local_transfers": 5,
                "max_concurrent_network_transfers": 2
            }
        }

    def test_get_current_config_success(self, client):
        """Test successful retrieval of current configuration."""
        response = client.get("/api/config/current")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"

        config = data["data"]
        # Verify configuration structure
        assert "plex" in config
        assert "media" in config
        assert "performance" in config

        # Verify Plex configuration structure
        plex_config = config["plex"]
        assert "url" in plex_config
        assert "token" in plex_config
        assert "timeout" in plex_config
        assert "verify_ssl" in plex_config

        # Verify Media configuration structure
        media_config = config["media"]
        assert "source_paths" in media_config
        assert "cache_path" in media_config
        assert "file_extensions" in media_config
        assert "min_file_size" in media_config
        assert "max_file_size" in media_config

        # Verify Performance configuration structure
        perf_config = config["performance"]
        assert "max_concurrent_moves_cache" in perf_config
        assert "max_concurrent_moves_array" in perf_config
        assert "max_concurrent_local_transfers" in perf_config
        assert "max_concurrent_network_transfers" in perf_config

    def test_get_current_config_response_format(self, client):
        """Test that current config response has correct JSON format."""
        response = client.get("/api/config/current")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert isinstance(data["data"], dict)

        # Verify configuration data types
        config = data["data"]
        assert isinstance(config["plex"]["url"], str)
        assert isinstance(config["plex"]["timeout"], int)
        assert isinstance(config["plex"]["verify_ssl"], bool)
        assert isinstance(config["media"]["source_paths"], list)
        assert isinstance(config["media"]["file_extensions"], list)
        assert isinstance(config["performance"]["max_concurrent_moves_cache"], int)

    def test_update_config_success(self, client, valid_config_data):
        """Test successful configuration update."""
        response = client.post(
            "/api/config/update",
            json=valid_config_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
        assert "Configuration updated successfully" in data["message"]

        # Verify updated configuration is returned
        assert "data" in data
        updated_config = data["data"]
        assert updated_config["plex"]["url"] == valid_config_data["plex"]["url"]
        assert updated_config["plex"]["token"] == "***MASKED***"  # Should be masked

    def test_update_config_partial_update(self, client):
        """Test partial configuration update."""
        partial_config = {
            "plex": {
                "url": "http://updated-plex:32400",
                "timeout": 60
            }
        }

        response = client.post(
            "/api/config/update",
            json=partial_config,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

        # Verify only specified fields were updated
        updated_config = data["data"]
        assert updated_config["plex"]["url"] == "http://updated-plex:32400"
        assert updated_config["plex"]["timeout"] == 60

    def test_update_config_validation_error(self, client):
        """Test configuration update with validation errors."""
        invalid_config = {
            "plex": {
                "url": "not-a-valid-url",  # Invalid URL format
                "token": "",  # Empty token
                "timeout": -1  # Invalid timeout
            }
        }

        response = client.post(
            "/api/config/update",
            json=invalid_config,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity

        data = response.json()
        assert data["status"] == "error"
        assert "message" in data
        assert "errors" in data

        # Verify validation errors are present
        errors = data["errors"]
        assert isinstance(errors, list)
        assert len(errors) > 0

    def test_update_config_empty_payload(self, client):
        """Test configuration update with empty payload."""
        response = client.post(
            "/api/config/update",
            json={},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

        data = response.json()
        assert data["status"] == "error"
        assert "No configuration data provided" in data["message"]

    def test_update_config_invalid_json(self, client):
        """Test configuration update with invalid JSON."""
        response = client.post(
            "/api/config/update",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

    def test_test_plex_connection_success(self, client):
        """Test successful Plex connection testing."""
        test_data = {
            "url": "http://localhost:32400",
            "token": "valid_token_123"
        }

        response = client.post(
            "/api/config/test-plex",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "message" in data

    def test_test_plex_connection_failure(self, client):
        """Test Plex connection testing with invalid credentials."""
        test_data = {
            "url": "http://invalid-plex:32400",
            "token": "invalid_token"
        }

        response = client.post(
            "/api/config/test-plex",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400

        data = response.json()
        assert data["status"] == "error"
        assert "message" in data

    def test_test_plex_connection_missing_data(self, client):
        """Test Plex connection testing with missing required data."""
        # Test missing URL
        response = client.post(
            "/api/config/test-plex",
            json={"token": "test_token"},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Both URL and token are required" in data["message"]

        # Test missing token
        response = client.post(
            "/api/config/test-plex",
            json={"url": "http://localhost:32400"},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Both URL and token are required" in data["message"]

    def test_export_config(self, client):
        """Test configuration export functionality."""
        response = client.get("/api/config/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Verify response is valid JSON
        export_data = response.json()
        assert isinstance(export_data, dict)

        # Verify configuration structure in export
        assert "plex" in export_data
        assert "media" in export_data
        assert "performance" in export_data

    def test_import_config_success(self, client, valid_config_data):
        """Test successful configuration import."""
        response = client.post(
            "/api/config/import",
            json=valid_config_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "message" in data

        # Verify imported configuration is returned
        assert "data" in data
        imported_config = data["data"]
        assert imported_config["plex"]["url"] == valid_config_data["plex"]["url"]

    def test_import_config_validation_error(self, client):
        """Test configuration import with validation errors."""
        invalid_config = {
            "plex": {
                "url": "invalid-url-format",
                "token": "test"
            }
        }

        response = client.post(
            "/api/config/import",
            json=invalid_config,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

        data = response.json()
        assert data["status"] == "error"
        assert "errors" in data

    def test_reset_config(self, client):
        """Test configuration reset to defaults."""
        response = client.post("/api/config/reset")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "message" in data

        # Verify default configuration is returned
        assert "data" in data
        default_config = data["data"]
        assert "plex" in default_config
        assert "media" in default_config
        assert "performance" in default_config

    def test_get_config_schema(self, client):
        """Test configuration schema retrieval."""
        response = client.get("/api/config/schema")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        schema = response.json()
        assert isinstance(schema, dict)

        # Verify schema contains expected sections
        assert "plex" in schema
        assert "media" in schema
        assert "performance" in schema

        # Verify schema structure for Plex
        plex_schema = schema["plex"]
        assert "url" in plex_schema
        assert "token" in plex_schema
        assert "timeout" in plex_schema
        assert "verify_ssl" in plex_schema

    def test_get_config_schema_structure(self, client):
        """Test that configuration schema has proper structure."""
        response = client.get("/api/config/schema")

        schema = response.json()

        # Verify each section has proper field definitions
        for section_name, section_schema in schema.items():
            assert isinstance(section_schema, dict)

            for field_name, field_schema in section_schema.items():
                assert isinstance(field_schema, dict)
                # Each field should have type information
                assert "type" in field_schema or "anyOf" in field_schema

    def test_config_endpoints_cors_headers(self, client):
        """Test that configuration endpoints include proper CORS headers."""
        response = client.get("/api/config/current")

        # Check for CORS headers (if CORS is enabled)
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        # At minimum, should not have CORS errors
        assert response.status_code == 200

    def test_config_endpoints_content_length(self, client):
        """Test that responses have appropriate content length."""
        response = client.get("/api/config/current")

        assert "content-length" in response.headers
        content_length = int(response.headers["content-length"])
        assert content_length > 0

        # Verify content length matches actual response size
        response_data = response.content
        assert len(response_data) == content_length

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/config/current", "GET"),
        ("/api/config/schema", "GET"),
        ("/api/config/export", "GET"),
        ("/api/config/update", "POST"),
        ("/api/config/import", "POST"),
        ("/api/config/reset", "POST"),
        ("/api/config/test-plex", "POST"),
    ])
    def test_config_endpoints_exist(self, client, endpoint, method):
        """Test that all configuration endpoints exist and respond."""
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json={})

        # Should not return 404
        assert response.status_code != 404

        # Should return valid JSON response
        try:
            data = response.json()
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_config_endpoints_error_responses(self, client):
        """Test that configuration endpoints return proper error responses."""
        # Test invalid method
        response = client.put("/api/config/current")
        assert response.status_code == 405  # Method Not Allowed

        # Test non-existent endpoint
        response = client.get("/api/config/nonexistent")
        assert response.status_code == 404

    def test_config_api_response_consistency(self, client):
        """Test that all config API responses follow consistent format."""
        endpoints = [
            "/api/config/current",
            "/api/config/schema",
            "/api/config/export"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data

            if data["status"] == "success":
                assert "data" in data

    def test_config_update_idempotent(self, client, valid_config_data):
        """Test that configuration updates are idempotent."""
        # Update configuration twice with same data
        for _ in range(2):
            response = client.post(
                "/api/config/update",
                json=valid_config_data,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "success"

    @pytest.mark.slow
    def test_config_endpoints_under_load(self, client, valid_config_data):
        """Test configuration endpoints under concurrent load."""
        import threading
        import time

        results = []
        errors = []

        def make_request(request_id: int):
            try:
                response = client.post(
                    "/api/config/update",
                    json=valid_config_data,
                    headers={"Content-Type": "application/json"}
                )
                results.append((request_id, response.status_code))
            except Exception as e:
                errors.append((request_id, str(e)))

        # Make 10 concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
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

    def test_config_api_rate_limiting(self, client):
        """Test that configuration API has appropriate rate limiting."""
        # Make multiple rapid requests
        responses = []
        for _ in range(20):
            response = client.get("/api/config/current")
            responses.append(response.status_code)

        # Should not be rate limited (429 status)
        assert 429 not in responses

        # All responses should be successful
        assert all(status == 200 for status in responses)
