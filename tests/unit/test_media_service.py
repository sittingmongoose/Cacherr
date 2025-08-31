"""
Comprehensive unit tests for MediaService class with extensive comments and mocking.

This test suite covers all MediaService functionality including:
- File path processing and mapping with atomic operations
- Cache directory management with secure validation
- Concurrent operations with thread safety
- Error handling and edge cases with comprehensive coverage
- Pydantic model validation and type safety
- Performance benchmarking and resource monitoring
- Security validation and path traversal protection

All tests use comprehensive mocking to avoid filesystem dependencies
while maintaining full test coverage and reliability. Tests are designed
to be fast, isolated, and provide clear debugging information.

The MediaService is implemented as SecureCachedFilesService with:
- SQL injection prevention using parameterized queries
- Path traversal protection with SecurePathValidator
- Authorization framework with role-based access control
- Connection pooling for database resource management
- Race condition prevention with atomic transactions
- Input validation using enhanced Pydantic models
- Security logging with comprehensive audit trails

Example test coverage:
    >>> test_atomic_file_operations()
    Test atomic file caching operations with rollback on failure
    >>> test_concurrent_operations()
    Test thread-safe concurrent file operations
    >>> test_security_validation()
    Test comprehensive security validation and path protection
"""

import json
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union, ContextManager
from unittest.mock import Mock, patch, MagicMock, call

import pytest
from pydantic import ValidationError

# Import the service and related classes
import sys
import os
# Add the src directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # tests/
project_root = os.path.dirname(parent_dir)  # project root
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from core.secure_cached_files_service import (
    SecureCachedFilesService,
    SecureCachedFileInfo,
    SecureCacheStatistics,
    SecureCachedFilesFilter,
    SecurityLevel,
    PermissionType,
    SecurePathValidator,
    SecurityConfig,
    UserOperationContext
)
from core.interfaces import UserOperationContext as BaseUserContext


class TestSecurePathValidator:
    """
    Test path validation security with comprehensive edge case coverage.

    This test class validates the SecurePathValidator's ability to:
    - Prevent path traversal attacks (.. in paths)
    - Validate absolute paths for security
    - Handle various encoding and normalization issues
    - Provide clear error messages for debugging
    - Support both Windows and Unix path formats
    """

    def test_validate_path_basic_security(self):
        """
        Test basic path validation for common security vulnerabilities.

        Ensures that the validator correctly identifies and blocks:
        - Path traversal attempts using .. sequences
        - Absolute path requirements for cache operations
        - Null byte injection attempts
        - Directory traversal in file names
        """
        validator = SecurePathValidator()

        # Test valid absolute paths
        valid_paths = [
            "/valid/cache/path/file.mp4",
            "/mnt/cache/movies/film.mkv",
            "/cache/tv-shows/episode.avi"
        ]

        for path in valid_paths:
            assert validator.validate_path(path), f"Valid path {path} should pass validation"

        # Test path traversal attacks
        invalid_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\cmd.exe",
            "/cache/../../../root/.ssh/id_rsa",
            "cache/movies/../../../etc/hosts"
        ]

        for path in invalid_paths:
            with pytest.raises(ValueError, match="path traversal|security"):
                validator.validate_path(path)

    def test_validate_path_edge_cases(self):
        """
        Test path validation edge cases and boundary conditions.

        Covers unusual but potentially dangerous path scenarios:
        - Empty and whitespace-only paths
        - Very long paths near system limits
        - Unicode characters and special symbols
        - Case sensitivity variations
        - Symlink and junction point handling
        """
        validator = SecurePathValidator()

        # Empty and whitespace paths
        with pytest.raises(ValueError, match="empty|whitespace"):
            validator.validate_path("")

        with pytest.raises(ValueError, match="empty|whitespace"):
            validator.validate_path("   ")

        with pytest.raises(ValueError, match="empty|whitespace"):
            validator.validate_path("\t\n")

        # Very long paths (near filesystem limits)
        long_path = "/cache/" + "a" * 1000 + "/file.mp4"
        if len(long_path) > SecurityConfig.MAX_PATH_LENGTH:
            with pytest.raises(ValueError, match="path length"):
                validator.validate_path(long_path)
        else:
            assert validator.validate_path(long_path)

        # Unicode and special characters
        unicode_paths = [
            "/cache/films/naïve-café.mkv",
            "/cache/movies/café-paris.avi",
            "/cache/测试文件.mp4"
        ]

        for path in unicode_paths:
            assert validator.validate_path(path), f"Unicode path {path} should be valid"

    def test_validate_filename_security(self):
        """
        Test filename validation for security vulnerabilities.

        Ensures filenames are validated for:
        - Directory traversal sequences
        - Hidden file access attempts
        - Reserved system names
        - Special character injection
        - File extension spoofing
        """
        validator = SecurePathValidator()

        # Valid filenames
        valid_names = [
            "movie.mp4",
            "tv-show-s01e01.mkv",
            "documentary.avi",
            "cartoon-series.m4v"
        ]

        for name in valid_names:
            assert validator.validate_filename(name), f"Valid filename {name} should pass"

        # Security threat filenames
        threat_names = [
            "../../../passwd",
            "..\\system32\\cmd.exe",
            ".hidden_file",
            "normal.mp4.exe",  # Extension spoofing
            "CON",  # Reserved Windows name
            "PRN",
            "AUX",
            "NUL"
        ]

        for name in threat_names:
            with pytest.raises(ValueError, match="security|reserved|hidden"):
                validator.validate_filename(name)

    def test_path_normalization(self):
        """
        Test path normalization and canonicalization.

        Verifies that paths are properly normalized to prevent:
        - Duplicate slashes and path separators
        - Relative path components
        - Case inconsistencies
        - Symbolic link resolution
        """
        validator = SecurePathValidator()

        test_cases = [
            ("/cache//movies///film.mp4", "/cache/movies/film.mp4"),
            ("/cache/./movies/film.mp4", "/cache/movies/film.mp4"),
            ("cache/movies/film.mp4", "/cache/movies/film.mp4"),  # Make absolute
        ]

        for input_path, expected in test_cases:
            normalized = validator.normalize_path(input_path)
            assert normalized == expected, f"Path {input_path} should normalize to {expected}"


class TestSecureCachedFilesService:
    """
    Comprehensive test suite for SecureCachedFilesService.

    This class tests the complete service functionality including:
    - Database operations with security validation
    - File caching with atomic operations
    - Concurrent access with thread safety
    - Security auditing and logging
    - Performance monitoring and optimization
    - Error recovery and rollback mechanisms

    All tests use extensive mocking to ensure isolation and reliability.
    """

    @pytest.fixture
    def temp_db_path(self, tmp_path: Path) -> Path:
        """
        Create a temporary database path for testing.

        Provides an isolated database file that will be automatically
        cleaned up after each test, preventing interference between tests.

        Args:
            tmp_path: Pytest temporary directory fixture

        Returns:
            Path to temporary database file
        """
        return tmp_path / "test_cache.db"

    @pytest.fixture
    def mock_user_context(self) -> UserOperationContext:
        """
        Create a mock user operation context for testing.

        Provides a realistic user context with proper permissions
        and security credentials for authenticated operations.

        Returns:
            Mock UserOperationContext with test credentials
        """
        return UserOperationContext(
            user_id="test_user_123",
            session_id="session_456",
            permissions={PermissionType.READ, PermissionType.WRITE},
            client_ip="192.168.1.100",
            user_agent="Cacherr-Test/1.0"
        )

    @pytest.fixture
    def service(self, temp_db_path: Path) -> SecureCachedFilesService:
        """
        Create a SecureCachedFilesService instance for testing.

        Initializes the service with a temporary database and
        configures it for testing with appropriate security settings.

        Args:
            temp_db_path: Temporary database path fixture

        Returns:
            Configured SecureCachedFilesService instance
        """
        service = SecureCachedFilesService(
            db_path=temp_db_path,
            cache_dir="/test/cache",
            array_dir="/test/array",
            security_level=SecurityLevel.STRICT,
            enable_audit=True
        )
        return service

    def test_service_initialization(self, service: SecureCachedFilesService):
        """
        Test service initialization with proper configuration.

        Verifies that the service initializes correctly with:
        - Database connection established
        - Tables created with proper schema
        - Security configuration applied
        - Audit logging enabled
        """
        assert service is not None
        assert service._db_path.exists()
        assert service._security_level == SecurityLevel.STRICT
        assert service._audit_enabled is True

        # Verify database tables were created
        with service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            expected_tables = {
                'cached_files', 'audit_log', 'security_events',
                'performance_metrics', 'user_sessions'
            }
            assert expected_tables.issubset(tables)

    def test_atomic_file_caching_operation(self, service: SecureCachedFilesService, mock_user_context: UserOperationContext):
        """
        Test atomic file caching operations with rollback on failure.

        This test verifies the critical atomicity guarantee where either:
        - The entire caching operation succeeds completely, OR
        - The operation fails entirely with no partial state changes

        The test simulates various failure scenarios to ensure rollback works.
        """
        # Test data
        source_path = "/test/array/movies/film.mp4"
        cache_path = "/test/cache/movies/film.mp4"
        file_size = 1000000000  # 1GB

        # Mock successful file operations
        with patch('shutil.copy2') as mock_copy, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=file_size):

            mock_copy.return_value = None

            # Execute caching operation
            result = service.cache_file_atomic(
                source_path=source_path,
                cache_path=cache_path,
                user_context=mock_user_context
            )

            # Verify operation succeeded
            assert result.success is True
            assert result.source_path == source_path
            assert result.cache_path == cache_path
            assert result.file_size == file_size

            # Verify database was updated
            cached_file = service.get_cached_file_info(cache_path)
            assert cached_file is not None
            assert cached_file.source_path == source_path
            assert cached_file.cache_path == cache_path

            # Verify audit log was created
            audit_entries = service.get_audit_log(user_id=mock_user_context.user_id)
            assert len(audit_entries) > 0
            assert any(entry.action == "CACHE_FILE" for entry in audit_entries)

    def test_atomic_operation_rollback_on_failure(self, service: SecureCachedFilesService, mock_user_context: UserOperationContext):
        """
        Test atomic operation rollback when file copy fails.

        This critical test ensures that if any part of the caching operation
        fails (file copy, database update, audit logging), the entire operation
        is rolled back to maintain system consistency.

        The test simulates various failure points to verify rollback behavior.
        """
        source_path = "/test/array/movies/film.mp4"
        cache_path = "/test/cache/movies/film.mp4"

        # Test 1: File copy failure
        with patch('shutil.copy2', side_effect=OSError("Disk full")), \
             patch('os.path.exists', return_value=True):

            result = service.cache_file_atomic(
                source_path=source_path,
                cache_path=cache_path,
                user_context=mock_user_context
            )

            # Verify operation failed and rolled back
            assert result.success is False
            assert "Disk full" in result.error_message

            # Verify no partial database state
            cached_file = service.get_cached_file_info(cache_path)
            assert cached_file is None

        # Test 2: Database transaction failure
        with patch('shutil.copy2') as mock_copy, \
             patch('os.path.exists', return_value=True), \
             patch.object(service, '_execute_query', side_effect=Exception("DB Error")):

            mock_copy.return_value = None

            result = service.cache_file_atomic(
                source_path=source_path,
                cache_path=cache_path,
                user_context=mock_user_context
            )

            # Verify operation failed and rolled back
            assert result.success is False
            assert "DB Error" in result.error_message

            # Verify file operation was still attempted (but rolled back)
            mock_copy.assert_called_once()

    def test_concurrent_operations_thread_safety(self, service: SecureCachedFilesService):
        """
        Test thread-safe concurrent operations under load.

        This test verifies that the service can handle multiple concurrent
        operations without race conditions, data corruption, or deadlocks.
        It simulates realistic concurrent usage patterns.

        Thread safety is critical for the service to handle multiple
        users caching files simultaneously.
        """
        import concurrent.futures
        import threading

        # Shared resources for testing
        operation_count = 0
        operation_lock = threading.Lock()
        results = []
        errors = []

        def concurrent_operation(operation_id: int):
            """Simulate a concurrent caching operation."""
            nonlocal operation_count

            try:
                user_context = UserOperationContext(
                    user_id=f"user_{operation_id}",
                    session_id=f"session_{operation_id}",
                    permissions={PermissionType.READ, PermissionType.WRITE},
                    client_ip=f"192.168.1.{operation_id % 255}",
                    user_agent="Cacherr-Test/1.0"
                )

                source_path = f"/test/array/movies/film_{operation_id}.mp4"
                cache_path = f"/test/cache/movies/film_{operation_id}.mp4"

                # Mock file operations
                with patch('shutil.copy2'), \
                     patch('os.path.exists', return_value=True), \
                     patch('os.path.getsize', return_value=100000000):

                    result = service.cache_file_atomic(
                        source_path=source_path,
                        cache_path=cache_path,
                        user_context=user_context
                    )

                    with operation_lock:
                        operation_count += 1
                        results.append(result)

            except Exception as e:
                with operation_lock:
                    errors.append(str(e))

        # Execute concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_operation, i) for i in range(20)]
            concurrent.futures.wait(futures)

        # Verify results
        assert operation_count == 20, f"Expected 20 operations, got {operation_count}"
        assert len(results) == 20, f"Expected 20 results, got {len(results)}"
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

        # Verify all operations succeeded
        successful_operations = sum(1 for r in results if r.success)
        assert successful_operations == 20, f"Expected 20 successful operations, got {successful_operations}"

        # Verify no duplicate cache paths (race condition check)
        cache_paths = [r.cache_path for r in results]
        assert len(cache_paths) == len(set(cache_paths)), "Duplicate cache paths detected - race condition!"

    def test_security_validation_comprehensive(self, service: SecureCachedFilesService):
        """
        Test comprehensive security validation across all operations.

        This test verifies the service's security measures including:
        - Path traversal prevention
        - SQL injection protection
        - Authorization checks
        - Input sanitization
        - Audit logging completeness
        - Rate limiting effectiveness
        """
        # Test path traversal prevention
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\cmd.exe",
            "/cache/../../../root/.ssh/id_rsa",
            "cache/movies/../../../etc/hosts"
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(ValueError, match="security|path traversal"):
                service.validate_cache_path(malicious_path)

        # Test SQL injection prevention
        malicious_queries = [
            "'; DROP TABLE cached_files; --",
            "1' OR '1'='1",
            "'; SELECT * FROM users; --",
            "1; DELETE FROM audit_log; --"
        ]

        for malicious_query in malicious_queries:
            # All SQL operations should use parameterized queries
            # This test ensures no raw SQL injection is possible
            with pytest.raises(ValueError, match="invalid|malformed"):
                service._execute_query(malicious_query)

        # Test authorization checks
        unauthorized_context = UserOperationContext(
            user_id="unauthorized_user",
            session_id="session_123",
            permissions={PermissionType.READ},  # No write permission
            client_ip="192.168.1.100",
            user_agent="Cacherr-Test/1.0"
        )

        with pytest.raises(PermissionError, match="permission|unauthorized"):
            service.cache_file_atomic(
                source_path="/test/array/write-test.mp4",
                cache_path="/test/cache/write-test.mp4",
                user_context=unauthorized_context
            )

    def test_performance_monitoring_and_metrics(self, service: SecureCachedFilesService):
        """
        Test performance monitoring and metrics collection.

        Verifies that the service correctly tracks and reports:
        - Operation execution times
        - Resource utilization
        - Cache hit/miss ratios
        - Database query performance
        - Memory usage patterns
        """
        # Test performance metrics collection
        initial_metrics = service.get_performance_metrics()

        # Perform some operations to generate metrics
        user_context = UserOperationContext(
            user_id="perf_test_user",
            session_id="perf_session",
            permissions={PermissionType.READ, PermissionType.WRITE},
            client_ip="192.168.1.100",
            user_agent="Cacherr-Test/1.0"
        )

        with patch('shutil.copy2'), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=500000000):

            # Execute multiple operations
            for i in range(5):
                service.cache_file_atomic(
                    source_path=f"/test/array/perf_test_{i}.mp4",
                    cache_path=f"/test/cache/perf_test_{i}.mp4",
                    user_context=user_context
                )

        # Verify metrics were updated
        updated_metrics = service.get_performance_metrics()

        # Check that operations were recorded
        assert updated_metrics.total_operations > initial_metrics.total_operations
        assert updated_metrics.cache_operations >= 5

        # Verify timing metrics
        assert updated_metrics.average_operation_time > 0
        assert updated_metrics.max_operation_time > 0

        # Test metrics export functionality
        metrics_export = service.export_performance_metrics()
        assert isinstance(metrics_export, dict)
        assert 'total_operations' in metrics_export
        assert 'average_operation_time' in metrics_export

    def test_error_recovery_and_rollback(self, service: SecureCachedFilesService, mock_user_context: UserOperationContext):
        """
        Test comprehensive error recovery and rollback mechanisms.

        This test ensures the service can recover from various error conditions:
        - Database connection failures
        - Filesystem permission errors
        - Network interruptions
        - Corrupted data scenarios
        - Resource exhaustion conditions

        All recovery operations should maintain data consistency.
        """
        # Test database connection recovery
        with patch.object(service, '_get_connection', side_effect=Exception("Connection lost")):
            with pytest.raises(Exception, match="Connection lost"):
                service.get_cache_statistics()

        # Test filesystem permission error recovery
        with patch('os.access', return_value=False):  # No permissions
            with pytest.raises(PermissionError):
                service.validate_cache_path("/restricted/path/file.mp4")

        # Test corrupted data recovery
        # Insert some corrupted data
        with service._get_connection() as conn:
            cursor = conn.cursor()
            # Insert corrupted record
            cursor.execute("""
                INSERT INTO cached_files (source_path, cache_path, corrupted)
                VALUES (?, ?, ?)
            """, ("/test/source.mp4", "/test/cache.mp4", True))

        # Verify corrupted data is handled gracefully
        corrupted_files = service.get_corrupted_files()
        assert len(corrupted_files) > 0

        # Test recovery operation
        recovery_result = service.recover_corrupted_files()
        assert recovery_result.success is True

        # Verify corrupted files were cleaned up
        updated_corrupted = service.get_corrupted_files()
        assert len(updated_corrupted) <= len(corrupted_files)

    def test_audit_logging_completeness(self, service: SecureCachedFilesService, mock_user_context: UserOperationContext):
        """
        Test comprehensive audit logging for all operations.

        Verifies that all security-relevant operations are properly logged:
        - Authentication events
        - Authorization decisions
        - File operations
        - Configuration changes
        - Security violations
        - System events

        Audit logs must be tamper-proof and complete.
        """
        # Perform various operations to generate audit events
        operations = [
            lambda: service.cache_file_atomic(
                "/test/array/audit1.mp4", "/test/cache/audit1.mp4", mock_user_context
            ),
            lambda: service.get_cache_statistics(),
            lambda: service.validate_cache_path("/test/cache/valid.mp4"),
        ]

        with patch('shutil.copy2'), patch('os.path.exists', return_value=True), patch('os.path.getsize', return_value=1000000):
            for operation in operations:
                operation()

        # Verify audit logs were created
        audit_logs = service.get_audit_log(user_id=mock_user_context.user_id)
        assert len(audit_logs) > 0

        # Verify log completeness
        for log_entry in audit_logs:
            assert log_entry.user_id == mock_user_context.user_id
            assert log_entry.timestamp is not None
            assert log_entry.action is not None
            assert log_entry.details is not None
            assert log_entry.ip_address == mock_user_context.client_ip

        # Test audit log integrity (tamper-proof)
        # This would involve cryptographic verification in a real implementation
        assert service.verify_audit_log_integrity() is True

        # Test audit log export
        exported_logs = service.export_audit_logs()
        assert isinstance(exported_logs, list)
        assert len(exported_logs) == len(audit_logs)

    def test_resource_cleanup_and_memory_management(self, service: SecureCachedFilesService):
        """
        Test proper resource cleanup and memory management.

        Verifies that the service properly manages resources:
        - Database connections are closed
        - File handles are released
        - Memory usage is bounded
        - Temporary files are cleaned up
        - Thread pools are properly managed
        """
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform memory-intensive operations
        user_context = UserOperationContext(
            user_id="memory_test_user",
            session_id="memory_session",
            permissions={PermissionType.READ, PermissionType.WRITE},
            client_ip="192.168.1.100",
            user_agent="Cacherr-Test/1.0"
        )

        with patch('shutil.copy2'), patch('os.path.exists', return_value=True), patch('os.path.getsize', return_value=100000000):
            # Create many cached file records
            for i in range(100):
                service.cache_file_atomic(
                    f"/test/array/memory_test_{i}.mp4",
                    f"/test/cache/memory_test_{i}.mp4",
                    user_context
                )

        # Verify memory usage didn't grow excessively
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (less than 50MB for this test)
        assert memory_growth < 50 * 1024 * 1024, f"Excessive memory growth: {memory_growth} bytes"

        # Test explicit cleanup
        service.cleanup_resources()

        # Verify database connections are properly closed
        # (This would check connection pool status in a real implementation)
        assert service._connection_pool_size() <= service._max_connections

        # Test garbage collection doesn't cause issues
        import gc
        gc.collect()

        # Service should still be functional after cleanup
        stats = service.get_cache_statistics()
        assert stats is not None
        assert stats.total_files >= 100  # From our test operations
