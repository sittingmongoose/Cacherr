"""
Pytest configuration and fixtures for API integration tests.

Provides reusable fixtures for API testing including test client setup,
authentication handling, database cleanup, and common test data.
All fixtures are designed to be isolated and not affect production data.
"""

import pytest
import json
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from src.web.app import create_app, FlaskAppConfig
from src.core.container import DIContainer
from src.config.settings import Config
from src.repositories.cache_repository import CacheFileRepository
from src.repositories.config_repository import ConfigFileRepository
from src.repositories.metrics_repository import MetricsFileRepository
from src.core.plex_cache_engine import CacherrEngine
from src.core.secure_cached_files_service import SecureCachedFilesService
from src.core.file_operations import FileOperations


@pytest.fixture(scope="session")
def test_container():
    """Create a test DI container with mock services."""
    container = DIContainer()

    # Register mock config
    mock_config = Mock(spec=Config)
    mock_config.validate.return_value = True
    mock_config.CACHE_DIR = "/test/cache"
    mock_config.ARRAY_DIR = "/test/array"
    mock_config.DRY_RUN = True
    mock_config.PLEX_URL = "http://localhost:32400"
    mock_config.PLEX_TOKEN = "test_token_123"
    mock_config.WEBHOOK_URL = "http://localhost:5445/webhook"
    mock_config.ENABLE_NOTIFICATIONS = False
    mock_config.ENABLE_REAL_TIME_WATCHER = False
    mock_config.PLEX_TIMEOUT = 30
    mock_config.PLEX_VERIFY_SSL = True
    mock_config.MAX_CONCURRENT_MOVES_CACHE = 3
    mock_config.MAX_CONCURRENT_MOVES_ARRAY = 1
    mock_config.MAX_CONCURRENT_LOCAL_TRANSFERS = 5
    mock_config.MAX_CONCURRENT_NETWORK_TRANSFERS = 2
    mock_config.SOURCE_PATHS = ["/media/movies", "/media/tv"]
    mock_config.FILE_EXTENSIONS = ["mp4", "mkv", "avi"]
    mock_config.MIN_FILE_SIZE = 100
    mock_config.MAX_FILE_SIZE = 10000
    mock_config.COPY_TO_CACHE = True
    mock_config.AUTO_CLEAN = False
    mock_config.WATCHED_MOVE = True

    container.register_instance(Config, mock_config)

    # Register mock services
    mock_media_service = Mock()
    mock_media_service.get_media_info.return_value = {
        "title": "Test Movie",
        "duration": 7200000,
        "size": 1000000000,
        "format": "mkv"
    }
    mock_media_service.is_media_file.return_value = True
    mock_media_service.validate_media_file.return_value = True

    mock_file_service = Mock()
    mock_file_service.file_exists.return_value = True
    mock_file_service.get_file_size.return_value = 1000000000
    mock_file_service.get_file_modified_time.return_value = 1640995200
    mock_file_service.copy_file.return_value = True
    mock_file_service.move_file.return_value = True
    mock_file_service.delete_file.return_value = True
    mock_file_service.create_directory.return_value = True

    mock_cache_service = Mock()
    mock_cache_service.cache_file.return_value = {
        "success": True,
        "cached_path": "/cache/test_file.mkv",
        "operation": "move",
        "size": 1000000000
    }
    mock_cache_service.restore_file.return_value = {
        "success": True,
        "restored_path": "/array/test_file.mkv",
        "operation": "move",
        "size": 1000000000
    }
    mock_cache_service.is_file_cached.return_value = False
    mock_cache_service.get_cache_status.return_value = {
        "total_files": 10,
        "total_size": 10000000000,
        "free_space": 5000000000
    }

    mock_notification_service = Mock()
    mock_notification_service.send_notification.return_value = True
    mock_notification_service.send_test_notification.return_value = True
    mock_notification_service.is_enabled.return_value = False

    container.register_instance(SecureCachedFilesService, mock_media_service)
    container.register_instance(FileOperations, mock_file_service)
    container.register_instance(CacherrEngine, mock_cache_service)
    container.register_instance(Mock, mock_notification_service)  # For NotificationService interface

    return container


@pytest.fixture(scope="function")
def api_client(test_container):
    """
    Create a test client for API integration testing.

    This fixture provides a FastAPI test client configured for testing
    with isolated database connections and mocked external dependencies.
    The client automatically handles request/response serialization.

    Returns:
        TestClient: Configured test client for API requests
    """
    config = FlaskAppConfig(
        testing=True,
        debug=True,
        enable_cors=False,  # Disable CORS for testing
        log_level='WARNING'  # Reduce log noise
    )

    app = create_app(test_container, config)
    return TestClient(app)


@pytest.fixture(scope="function")
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_path = Path(tempfile.mkdtemp(prefix="cacherr_api_test_"))
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def test_cache_repository(temp_data_dir):
    """Provide a test cache repository."""
    cache_file = temp_data_dir / "test_cache.json"
    return CacheFileRepository(data_file=cache_file, auto_backup=False)


@pytest.fixture(scope="function")
def test_config_repository(temp_data_dir):
    """Provide a test config repository."""
    config_file = temp_data_dir / "test_config.json"
    return ConfigFileRepository(data_file=config_file, auto_backup=False)


@pytest.fixture(scope="function")
def test_metrics_repository(temp_data_dir):
    """Provide a test metrics repository."""
    metrics_file = temp_data_dir / "test_metrics.json"
    return MetricsFileRepository(data_file=metrics_file, auto_backup=False)


@pytest.fixture(scope="function")
def sample_config_data():
    """Provide sample configuration data for testing."""
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
            "max_file_size": 10000,
            "copy_to_cache": True,
            "auto_clean": False,
            "watched_move": True
        },
        "performance": {
            "max_concurrent_moves_cache": 3,
            "max_concurrent_moves_array": 1,
            "max_concurrent_local_transfers": 5,
            "max_concurrent_network_transfers": 2
        },
        "notifications": {
            "webhook_url": "http://localhost:5445/webhook",
            "enable_notifications": False,
            "discord_webhook": "",
            "slack_webhook": "",
            "email_smtp_server": "",
            "email_recipients": []
        },
        "advanced": {
            "enable_real_time_watcher": False,
            "watcher_interval": 60,
            "log_level": "INFO",
            "max_log_files": 10,
            "log_max_size": 10485760
        }
    }


@pytest.fixture(scope="function")
def sample_plex_credentials():
    """Provide sample Plex credentials for testing."""
    return {
        "url": "http://localhost:32400",
        "token": "valid_test_token_12345"
    }


@pytest.fixture(scope="function")
def invalid_config_data():
    """Provide invalid configuration data for error testing."""
    return {
        "plex": {
            "url": "not-a-valid-url",
            "token": "",
            "timeout": -1,
            "verify_ssl": "not_a_boolean"
        },
        "media": {
            "source_paths": [],  # Empty source paths
            "cache_path": "",
            "file_extensions": [],
            "min_file_size": -100,
            "max_file_size": -1000
        }
    }


# Utility functions for API tests
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


def assert_json_response(response):
    """Assert that response contains valid JSON."""
    assert response.headers.get("content-type") == "application/json"
    return response.json()


def create_test_media_file(temp_dir: Path, filename: str = "test_movie.mkv", size: int = 1000000):
    """Create a test media file."""
    file_path = temp_dir / filename
    with open(file_path, 'wb') as f:
        f.write(b'0' * size)
    return file_path


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers for integration tests."""
    config.addinivalue_line(
        "markers", "api: mark test as API integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_plex: mark test as requiring Plex server"
    )
