"""
Test utilities and helper functions for PlexCacheUltra tests.

This module provides common utilities, helpers, and assertion functions
that can be reused across different test modules.
"""

import time
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import threading

from src.core.container import DIContainer
from src.core.interfaces import MediaService, FileService, CacheService
from src.config.settings import Config
from src.repositories.cache_repository import CacheFileRepository
from src.core.repositories import CacheEntry


class TestTimer:
    """Context manager for timing test operations."""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.duration
        print(f"{self.description} took {duration:.3f} seconds")
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class TestDataBuilder:
    """Builder class for creating test data objects."""
    
    @staticmethod
    def create_cache_entry(
        file_path: str = "/media/test.mkv",
        cache_path: str = "/cache/test.mkv",
        size: int = 1000000000,
        operation_type: str = "move",
        **kwargs
    ) -> CacheEntry:
        """Create a test cache entry with sensible defaults."""
        defaults = {
            "file_path": file_path,
            "cache_path": cache_path,
            "original_size": size,
            "cached_at": datetime.now(),
            "operation_type": operation_type
        }
        defaults.update(kwargs)
        return CacheEntry(**defaults)
    
    @staticmethod
    def create_cache_entries(count: int, base_path: str = "/media") -> List[CacheEntry]:
        """Create multiple test cache entries."""
        entries = []
        for i in range(count):
            entry = TestDataBuilder.create_cache_entry(
                file_path=f"{base_path}/file_{i}.mkv",
                cache_path=f"/cache/file_{i}.mkv",
                size=1000000000 + (i * 100000000),  # Varying sizes
                cached_at=datetime.now() - timedelta(hours=i)  # Different times
            )
            entries.append(entry)
        return entries
    
    @staticmethod
    def create_config_dict(environment: str = "test") -> Dict[str, Any]:
        """Create a test configuration dictionary."""
        return {
            "environment": environment,
            "plex_url": "http://localhost:32400",
            "plex_token": "test_token_123456789012345",
            "cache_directory": "/tmp/test_cache",
            "array_directory": "/tmp/test_array",
            "max_cache_size": 50000000000,
            "dry_run": True,
            "log_level": "DEBUG"
        }


class MockFileSystem:
    """Mock file system for testing file operations."""
    
    def __init__(self):
        self.files = {}  # path -> file_info
        self.directories = set()
        self.operation_log = []
    
    def create_file(self, path: str, size: int = 1000000, content: str = None):
        """Create a mock file."""
        self.files[path] = {
            "size": size,
            "content": content or f"mock content for {path}",
            "modified": datetime.now().timestamp(),
            "exists": True
        }
        
        # Ensure parent directory exists
        parent = str(Path(path).parent)
        self.directories.add(parent)
    
    def delete_file(self, path: str):
        """Delete a mock file."""
        if path in self.files:
            self.files[path]["exists"] = False
            self.operation_log.append(("delete", path))
    
    def move_file(self, source: str, destination: str):
        """Move a mock file."""
        if source in self.files and self.files[source]["exists"]:
            self.files[destination] = self.files[source].copy()
            self.files[source]["exists"] = False
            self.operation_log.append(("move", source, destination))
            return True
        return False
    
    def file_exists(self, path: str) -> bool:
        """Check if mock file exists."""
        return path in self.files and self.files[path]["exists"]
    
    def get_file_size(self, path: str) -> int:
        """Get mock file size."""
        if self.file_exists(path):
            return self.files[path]["size"]
        raise FileNotFoundError(f"File not found: {path}")
    
    def get_operation_log(self) -> List[tuple]:
        """Get log of operations performed."""
        return self.operation_log.copy()


class AsyncTestHelper:
    """Helper for testing asynchronous operations."""
    
    @staticmethod
    def wait_for_condition(
        condition: Callable[[], bool],
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition():
                return True
            time.sleep(interval)
        return False
    
    @staticmethod
    def wait_for_value(
        getter: Callable[[], Any],
        expected_value: Any,
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a getter function to return expected value."""
        def condition():
            try:
                return getter() == expected_value
            except Exception:
                return False
        
        return AsyncTestHelper.wait_for_condition(condition, timeout, interval)


class ContainerTestHelper:
    """Helper for testing dependency injection containers."""
    
    @staticmethod
    def assert_service_registered(container: DIContainer, service_type: type):
        """Assert that a service is registered in the container."""
        assert container.is_registered(service_type), \
            f"Service {service_type.__name__} should be registered"
    
    @staticmethod
    def assert_service_resolvable(container: DIContainer, service_type: type):
        """Assert that a service can be resolved from the container."""
        try:
            service = container.resolve(service_type)
            assert service is not None, \
                f"Service {service_type.__name__} should resolve to non-None value"
        except Exception as e:
            assert False, f"Service {service_type.__name__} should be resolvable: {e}"
    
    @staticmethod
    def assert_singleton_behavior(container: DIContainer, service_type: type):
        """Assert that a service exhibits singleton behavior."""
        service1 = container.resolve(service_type)
        service2 = container.resolve(service_type)
        assert service1 is service2, \
            f"Service {service_type.__name__} should be a singleton"
    
    @staticmethod
    def assert_transient_behavior(container: DIContainer, service_type: type):
        """Assert that a service exhibits transient behavior."""
        service1 = container.resolve(service_type)
        service2 = container.resolve(service_type)
        assert service1 is not service2, \
            f"Service {service_type.__name__} should be transient"


class FileTestHelper:
    """Helper for testing file operations."""
    
    @staticmethod
    def create_test_file(path: Path, content: str = "test content", size: Optional[int] = None):
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
    
    @staticmethod
    def create_test_directory_structure(base_path: Path, structure: Dict[str, Any]):
        """Create a test directory structure from a dictionary."""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # It's a directory
                path.mkdir(parents=True, exist_ok=True)
                FileTestHelper.create_test_directory_structure(path, content)
            elif isinstance(content, str):
                # It's a file with string content
                FileTestHelper.create_test_file(path, content)
            elif isinstance(content, int):
                # It's a file with specific size
                FileTestHelper.create_test_file(path, size=content)
    
    @staticmethod
    def assert_file_exists(path: Path, message: str = None):
        """Assert that a file exists."""
        msg = message or f"File should exist: {path}"
        assert path.exists(), msg
    
    @staticmethod
    def assert_file_not_exists(path: Path, message: str = None):
        """Assert that a file does not exist."""
        msg = message or f"File should not exist: {path}"
        assert not path.exists(), msg
    
    @staticmethod
    def assert_file_size(path: Path, expected_size: int):
        """Assert that a file has the expected size."""
        actual_size = path.stat().st_size
        assert actual_size == expected_size, \
            f"File {path} should be {expected_size} bytes, but is {actual_size}"


class RepositoryTestHelper:
    """Helper for testing repository implementations."""
    
    @staticmethod
    def create_test_repository(repo_class, temp_dir: Path) -> Any:
        """Create a test repository instance with temporary storage."""
        test_file = temp_dir / f"test_{repo_class.__name__.lower()}.json"
        return repo_class(data_file=test_file, auto_backup=False)
    
    @staticmethod
    def populate_repository(repository: CacheFileRepository, entries: List[CacheEntry]):
        """Populate a repository with test entries."""
        for entry in entries:
            repository.add_cache_entry(entry)
    
    @staticmethod
    def assert_repository_contains(repository: CacheFileRepository, file_path: str):
        """Assert that repository contains an entry for the given file path."""
        entry = repository.get_cache_entry(file_path)
        assert entry is not None, f"Repository should contain entry for: {file_path}"
    
    @staticmethod
    def assert_repository_count(repository: CacheFileRepository, expected_count: int):
        """Assert that repository contains expected number of entries."""
        entries = repository.list_cache_entries()
        actual_count = len(entries)
        assert actual_count == expected_count, \
            f"Repository should contain {expected_count} entries, but has {actual_count}"


class PerformanceTestHelper:
    """Helper for performance testing and benchmarking."""
    
    @staticmethod
    def benchmark_operation(operation: Callable[[], Any], iterations: int = 100) -> Dict[str, float]:
        """Benchmark an operation and return performance statistics."""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            operation()
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            "mean": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "total": sum(times),
            "iterations": iterations
        }
    
    @staticmethod
    def assert_performance_within_bounds(
        operation: Callable[[], Any],
        max_duration: float,
        iterations: int = 10
    ):
        """Assert that an operation completes within specified time bounds."""
        stats = PerformanceTestHelper.benchmark_operation(operation, iterations)
        
        assert stats["mean"] <= max_duration, \
            f"Operation took {stats['mean']:.3f}s on average, expected <= {max_duration}s"
        
        assert stats["max"] <= max_duration * 2, \
            f"Slowest operation took {stats['max']:.3f}s, expected <= {max_duration * 2}s"


class ConcurrencyTestHelper:
    """Helper for testing concurrent operations."""
    
    @staticmethod
    def run_concurrent_operations(
        operation: Callable[[], Any],
        thread_count: int = 5,
        iterations_per_thread: int = 10
    ) -> Dict[str, Any]:
        """Run an operation concurrently and collect results."""
        results = []
        errors = []
        threads = []
        
        def worker():
            for _ in range(iterations_per_thread):
                try:
                    result = operation()
                    results.append(result)
                except Exception as e:
                    errors.append(e)
        
        # Start threads
        for _ in range(thread_count):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        return {
            "results": results,
            "errors": errors,
            "success_count": len(results),
            "error_count": len(errors),
            "total_operations": thread_count * iterations_per_thread
        }
    
    @staticmethod
    def assert_no_concurrency_errors(concurrent_results: Dict[str, Any]):
        """Assert that concurrent operations completed without errors."""
        error_count = concurrent_results["error_count"]
        assert error_count == 0, \
            f"Expected no concurrency errors, but got {error_count}: {concurrent_results['errors']}"


# Assertion helpers
def assert_command_success(result, message: str = "Command should succeed"):
    """Assert that a command result indicates success."""
    assert result is not None, f"{message}: result should not be None"
    assert hasattr(result, 'success'), f"{message}: result should have 'success' attribute"
    assert result.success, f"{message}: {getattr(result, 'message', 'No message')}"


def assert_command_failure(result, message: str = "Command should fail"):
    """Assert that a command result indicates failure."""
    assert result is not None, f"{message}: result should not be None"
    assert hasattr(result, 'success'), f"{message}: result should have 'success' attribute"
    assert not result.success, f"{message}: command unexpectedly succeeded"


def assert_contains_all(container: List[Any], items: List[Any], message: str = ""):
    """Assert that container contains all specified items."""
    for item in items:
        assert item in container, f"{message}: {item} not found in container"


def assert_eventually(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    message: str = "Condition should eventually be true"
):
    """Assert that a condition eventually becomes true within timeout."""
    success = AsyncTestHelper.wait_for_condition(condition, timeout)
    assert success, f"{message} (timeout after {timeout}s)"


# Context managers for testing
class temporary_environment_variable:
    """Context manager for temporarily setting an environment variable."""
    
    def __init__(self, var_name: str, value: str):
        self.var_name = var_name
        self.value = value
        self.original_value = None
    
    def __enter__(self):
        import os
        self.original_value = os.environ.get(self.var_name)
        os.environ[self.var_name] = self.value
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import os
        if self.original_value is None:
            os.environ.pop(self.var_name, None)
        else:
            os.environ[self.var_name] = self.original_value


class capture_logs:
    """Context manager for capturing log messages during tests."""
    
    def __init__(self, logger_name: str = None, level: str = "DEBUG"):
        self.logger_name = logger_name
        self.level = level
        self.logs = []
        self.handler = None
    
    def __enter__(self):
        import logging
        
        class TestLogHandler(logging.Handler):
            def __init__(self, test_instance):
                super().__init__()
                self.test_instance = test_instance
            
            def emit(self, record):
                self.test_instance.logs.append(self.format(record))
        
        logger = logging.getLogger(self.logger_name) if self.logger_name else logging.getLogger()
        self.handler = TestLogHandler(self)
        self.handler.setLevel(getattr(logging, self.level))
        logger.addHandler(self.handler)
        
        return self.logs
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            import logging
            logger = logging.getLogger(self.logger_name) if self.logger_name else logging.getLogger()
            logger.removeHandler(self.handler)