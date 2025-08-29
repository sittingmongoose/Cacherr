"""
Pytest configuration and shared fixtures for PlexCacheUltra tests.

This module provides shared fixtures, test configuration, and utilities
used across all test suites in the PlexCacheUltra project.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from unittest.mock import Mock, MagicMock
import logging

from src.core.container import DIContainer, ServiceLifetime
from src.core.interfaces import (
    MediaService, FileService, CacheService, NotificationService
)
from src.config.settings import Config
from src.repositories.cache_repository import CacheFileRepository
from src.repositories.config_repository import ConfigFileRepository
from src.repositories.metrics_repository import MetricsFileRepository
from src.application import ApplicationContext, ApplicationConfig, create_test_application

# Disable logging during tests unless explicitly enabled
logging.disable(logging.CRITICAL)

class TestConfig:
    """Test configuration settings."""
    
    # Test directories
    TEST_DATA_DIR = Path(__file__).parent / "fixtures" / "data"
    TEST_TEMP_DIR = Path(tempfile.gettempdir()) / "cacherr_tests"
    
    # Test timeouts
    DEFAULT_TIMEOUT = 30
    SHORT_TIMEOUT = 5
    
    # Test flags
    ENABLE_INTEGRATION_TESTS = True
    ENABLE_PERFORMANCE_TESTS = False
    SKIP_DOCKER_TESTS = True  # Skip Docker-dependent tests by default


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Provide test configuration."""
    return TestConfig()


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for each test."""
    temp_path = Path(tempfile.mkdtemp(prefix="cacherr_test_"))
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function") 
def test_data_dir(test_config: TestConfig) -> Path:
    """Provide path to test data directory."""
    test_config.TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return test_config.TEST_DATA_DIR


@pytest.fixture(scope="function")
def mock_config() -> Config:
    """Provide a mock configuration for testing."""
    config = Mock(spec=Config)
    config.validate.return_value = True
    config.CACHE_DIR = "/test/cache"
    config.ARRAY_DIR = "/test/array"
    config.DRY_RUN = True  # Always use dry run in tests
    config.PLEX_URL = "http://localhost:32400"
    config.PLEX_TOKEN = "test_token"
    config.WEBHOOK_URL = "http://localhost:5445/webhook"
    config.ENABLE_NOTIFICATIONS = False
    config.ENABLE_REAL_TIME_WATCHER = False
    return config


@pytest.fixture(scope="function")
def clean_container() -> Generator[DIContainer, None, None]:
    """Provide a clean DI container for each test."""
    container = DIContainer()
    try:
        yield container
    finally:
        container.dispose()


@pytest.fixture(scope="function")
def configured_container(clean_container: DIContainer, mock_config: Config) -> DIContainer:
    """Provide a DI container with basic test services registered."""
    container = clean_container
    
    # Register mock config
    container.register_instance(Config, mock_config)
    
    # Register mock services
    container.register_instance(MediaService, Mock(spec=MediaService))
    container.register_instance(FileService, Mock(spec=FileService))
    container.register_instance(CacheService, Mock(spec=CacheService))
    container.register_instance(NotificationService, Mock(spec=NotificationService))
    
    return container


@pytest.fixture(scope="function")
def test_cache_repository(temp_dir: Path) -> CacheFileRepository:
    """Provide a test cache repository with temporary storage."""
    cache_file = temp_dir / "test_cache.json"
    return CacheFileRepository(data_file=cache_file, auto_backup=False)


@pytest.fixture(scope="function")
def test_config_repository(temp_dir: Path) -> ConfigFileRepository:
    """Provide a test config repository with temporary storage."""
    config_file = temp_dir / "test_config.json"
    return ConfigFileRepository(data_file=config_file, auto_backup=False)


@pytest.fixture(scope="function")
def test_metrics_repository(temp_dir: Path) -> MetricsFileRepository:
    """Provide a test metrics repository with temporary storage."""
    metrics_file = temp_dir / "test_metrics.json"
    return MetricsFileRepository(data_file=metrics_file, auto_backup=False)


@pytest.fixture(scope="function")
def test_application_config() -> ApplicationConfig:
    """Provide test application configuration."""
    return ApplicationConfig(
        web={
            "testing": True,
            "debug": True,
            "port": 0  # Random port
        },
        enable_scheduler=False,
        enable_real_time_watcher=False,
        initialize_services_on_startup=False,
        setup_logging=False,
        log_level="DEBUG"
    )


@pytest.fixture(scope="function")
def test_application(mock_config: Config, test_application_config: ApplicationConfig) -> Generator[ApplicationContext, None, None]:
    """Provide a test application context."""
    app_context = ApplicationContext(mock_config, test_application_config)
    try:
        yield app_context
    finally:
        if app_context.is_started:
            app_context.shutdown()


@pytest.fixture(scope="function")
def started_test_application(test_application: ApplicationContext) -> ApplicationContext:
    """Provide a started test application context."""
    test_application.start()
    return test_application


# Mock service fixtures
@pytest.fixture(scope="function")
def mock_media_service() -> Mock:
    """Provide a mock media service."""
    service = Mock(spec=MediaService)
    service.get_media_info.return_value = {
        "title": "Test Movie",
        "duration": 7200000,  # 2 hours in ms
        "size": 1000000000,  # 1GB
        "format": "mkv"
    }
    service.is_media_file.return_value = True
    service.validate_media_file.return_value = True
    return service


@pytest.fixture(scope="function")
def mock_file_service() -> Mock:
    """Provide a mock file service."""
    service = Mock(spec=FileService)
    service.file_exists.return_value = True
    service.get_file_size.return_value = 1000000000
    service.get_file_modified_time.return_value = 1640995200  # 2022-01-01 timestamp
    service.copy_file.return_value = True
    service.move_file.return_value = True
    service.delete_file.return_value = True
    service.create_directory.return_value = True
    return service


@pytest.fixture(scope="function")
def mock_cache_service() -> Mock:
    """Provide a mock cache service."""
    service = Mock(spec=CacheService)
    service.cache_file.return_value = {
        "success": True,
        "cached_path": "/cache/test_file.mkv",
        "operation": "move",
        "size": 1000000000
    }
    service.restore_file.return_value = {
        "success": True,
        "restored_path": "/array/test_file.mkv",
        "operation": "move",
        "size": 1000000000
    }
    service.is_file_cached.return_value = False
    service.get_cache_status.return_value = {
        "total_files": 10,
        "total_size": 10000000000,
        "free_space": 5000000000
    }
    return service


@pytest.fixture(scope="function")
def mock_notification_service() -> Mock:
    """Provide a mock notification service."""
    service = Mock(spec=NotificationService)
    service.send_notification.return_value = True
    service.send_test_notification.return_value = True
    service.is_enabled.return_value = False  # Disabled by default in tests
    return service


# Test data fixtures
@pytest.fixture(scope="function")
def sample_cache_entries() -> list:
    """Provide sample cache entries for testing."""
    from src.core.repositories import CacheEntry
    from datetime import datetime, timedelta
    
    base_time = datetime.now()
    
    return [
        CacheEntry(
            file_path="/media/movies/movie1.mkv",
            cache_path="/cache/movie1.mkv",
            original_size=1500000000,  # 1.5GB
            cached_at=base_time - timedelta(hours=2),
            operation_type="move",
            file_hash="abc123",
            metadata={"title": "Movie 1", "year": 2021}
        ),
        CacheEntry(
            file_path="/media/movies/movie2.mkv", 
            cache_path="/cache/movie2.mkv",
            original_size=2000000000,  # 2GB
            cached_at=base_time - timedelta(hours=1),
            operation_type="copy",
            file_hash="def456",
            metadata={"title": "Movie 2", "year": 2022}
        ),
        CacheEntry(
            file_path="/media/tv/show1.mkv",
            cache_path="/cache/show1.mkv", 
            original_size=800000000,   # 800MB
            cached_at=base_time,
            operation_type="move",
            file_hash="ghi789",
            metadata={"title": "Show 1 S01E01", "show": "Show 1"}
        )
    ]


# Utility functions for tests
def assert_container_health(container: DIContainer) -> None:
    """Assert that a DI container is in a healthy state."""
    assert container is not None, "Container should not be None"
    assert not container._disposed, "Container should not be disposed"
    assert len(container.get_registered_services()) > 0, "Container should have registered services"


def assert_service_registered(container: DIContainer, service_type: type) -> None:
    """Assert that a specific service is registered in the container."""
    assert container.is_registered(service_type), f"Service {service_type.__name__} should be registered"


def create_test_file(path: Path, content: str = "test content", size: Optional[int] = None) -> Path:
    """Create a test file with specified content or size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if size is not None:
        # Create file with specific size
        with open(path, 'wb') as f:
            f.write(b'0' * size)
    else:
        # Create file with content
        with open(path, 'w') as f:
            f.write(content)
    
    return path


# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as requiring Docker"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on configuration."""
    # Skip Docker tests if not enabled
    if TestConfig.SKIP_DOCKER_TESTS:
        skip_docker = pytest.mark.skip(reason="Docker tests disabled")
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(skip_docker)
    
    # Skip performance tests if not enabled
    if not TestConfig.ENABLE_PERFORMANCE_TESTS:
        skip_perf = pytest.mark.skip(reason="Performance tests disabled")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_perf)


# Cleanup function
def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session."""
    # Clean up test temporary directories
    if TestConfig.TEST_TEMP_DIR.exists():
        shutil.rmtree(TestConfig.TEST_TEMP_DIR, ignore_errors=True)
    
    # Re-enable logging
    logging.disable(logging.NOTSET)