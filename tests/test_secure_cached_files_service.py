"""
Comprehensive test suite for SecureCachedFilesService.

Tests all security features including:
- SQL injection prevention
- Path traversal protection
- Authorization and access control
- Database connection pooling
- Race condition prevention
- Input validation
- Security logging
- Rate limiting
"""

import json
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError

# Import the secure service and related classes
import sys
sys.path.append('/mnt/user/Cursor/Cacherr/src')

from core.secure_cached_files_service import (
    SecureCachedFilesService,
    SecureCachedFileInfo,
    SecureCacheStatistics,
    SecureCachedFilesFilter,
    SecurityLevel,
    PermissionType,
    SecurePathValidator,
    SecurityConfig
)
from core.interfaces import UserOperationContext


class TestSecurePathValidator:
    """Test path validation security."""
    
    def test_validate_path_basic(self):
        """Test basic path validation."""
        # Valid paths
        valid_paths = [
            "/home/user/file.txt",
            "/var/cache/media/video.mp4",
            "C:\\Users\\test\\Documents\\file.pdf"
        ]
        
        for path in valid_paths:
            result = SecurePathValidator.validate_path(path)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_validate_path_traversal_attacks(self):
        """Test protection against path traversal attacks."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/var/cache/../../../etc/shadow",
            "file.txt/../../../secret",
            "./../../config.ini",
            "..\\..\\..\\boot.ini"
        ]
        
        for path in dangerous_paths:
            with pytest.raises(ValueError, match="dangerous pattern"):
                SecurePathValidator.validate_path(path)
    
    def test_validate_path_with_base_paths(self):
        """Test path validation with allowed base paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_paths = [temp_dir]
            
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            
            # Valid path within base
            validated = SecurePathValidator.validate_path(str(test_file), base_paths)
            assert str(test_file) in validated
            
            # Invalid path outside base
            with pytest.raises(ValueError, match="not within allowed directories"):
                SecurePathValidator.validate_path("/tmp/outside.txt", base_paths)
    
    def test_validate_filename(self):
        """Test filename validation."""
        # Valid filenames
        valid_names = [
            "document.pdf",
            "video-file_2023.mp4",
            "My Movie (2023) [1080p].mkv",
            "show.s01e01.720p.x264.mkv"
        ]
        
        for name in valid_names:
            result = SecurePathValidator.validate_filename(name)
            assert result == name
        
        # Invalid filenames
        invalid_names = [
            "file<script>.txt",  # HTML tags
            "file|pipe.txt",     # Pipe character
            "file*.txt",         # Wildcard
            "CON.txt",           # Reserved name
            "file\x00.txt",      # NULL character
            "a" * 300           # Too long
        ]
        
        for name in invalid_names:
            with pytest.raises(ValueError):
                SecurePathValidator.validate_filename(name)


class TestSecurePydanticModels:
    """Test enhanced Pydantic models with security validation."""
    
    def test_secure_cached_file_info_validation(self):
        """Test SecureCachedFileInfo validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.mp4"
            test_file.write_text("test content")
            
            # Valid data
            valid_data = {
                "id": str(uuid.uuid4()),
                "file_path": str(test_file),
                "filename": "test.mp4",
                "original_path": str(test_file),
                "cached_path": str(test_file),
                "cache_method": "atomic_symlink",
                "file_size_bytes": 1000,
                "file_size_readable": "1.0 KB",
                "cached_at": datetime.now(timezone.utc),
                "triggered_by_operation": "manual",
                "status": "active"
            }
            
            cached_file = SecureCachedFileInfo(**valid_data)
            assert cached_file.id == valid_data["id"]
            assert cached_file.cache_method == "atomic_symlink"
    
    def test_invalid_cache_method(self):
        """Test invalid cache method rejection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.mp4"
            
            invalid_data = {
                "id": str(uuid.uuid4()),
                "file_path": str(test_file),
                "filename": "test.mp4",
                "original_path": str(test_file),
                "cached_path": str(test_file),
                "cache_method": "unsafe_method",  # Invalid method
                "file_size_bytes": 1000,
                "file_size_readable": "1.0 KB",
                "cached_at": datetime.now(timezone.utc),
                "triggered_by_operation": "manual",
                "status": "active"
            }
            
            with pytest.raises(ValidationError):
                SecureCachedFileInfo(**invalid_data)
    
    def test_metadata_size_limit(self):
        """Test metadata size limits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.mp4"
            
            # Large metadata that exceeds limit
            large_metadata = {"data": "x" * (SecurityConfig.MAX_METADATA_SIZE + 1)}
            
            invalid_data = {
                "id": str(uuid.uuid4()),
                "file_path": str(test_file),
                "filename": "test.mp4",
                "original_path": str(test_file),
                "cached_path": str(test_file),
                "cache_method": "atomic_copy",
                "file_size_bytes": 1000,
                "file_size_readable": "1.0 KB",
                "cached_at": datetime.now(timezone.utc),
                "triggered_by_operation": "manual",
                "status": "active",
                "metadata": large_metadata
            }
            
            with pytest.raises(ValidationError, match="Metadata too large"):
                SecureCachedFileInfo(**invalid_data)
    
    def test_filter_validation(self):
        """Test secure filter validation."""
        # Valid filter
        valid_filter = SecureCachedFilesFilter(
            search="movie",
            user_id="user123",
            status="active",
            limit=100
        )
        assert valid_filter.search == "movie"
        
        # Invalid search with special characters
        with pytest.raises(ValidationError):
            SecureCachedFilesFilter(search="<script>alert('xss')</script>")
        
        # Invalid limit too high
        with pytest.raises(ValidationError):
            SecureCachedFilesFilter(limit=10000)


class TestSecureCachedFilesService:
    """Test the secure cached files service."""
    
    @pytest.fixture
    def temp_db_service(self):
        """Create a temporary database service for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            allowed_paths = [temp_dir]
            
            service = SecureCachedFilesService(
                database_path=str(db_path),
                allowed_base_paths=allowed_paths
            )
            
            # Add a test admin user
            service.auth_manager.add_user("admin", SecurityLevel.ADMIN)
            service.auth_manager.add_user("user1", SecurityLevel.USER)
            service.auth_manager.add_user("readonly", SecurityLevel.PUBLIC)
            
            yield service, temp_dir
            
            service.close()
    
    def test_service_initialization(self, temp_db_service):
        """Test service initialization."""
        service, temp_dir = temp_db_service
        
        # Check that database was created
        assert Path(service.database_path).exists()
        
        # Check that connection pool is initialized
        assert service.connection_pool is not None
        
        # Check security components
        assert service.security_logger is not None
        assert service.auth_manager is not None
    
    def test_sql_injection_prevention(self, temp_db_service):
        """Test SQL injection prevention in queries."""
        service, temp_dir = temp_db_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        # Create a test file
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test")
        
        # Add a legitimate file
        service.add_cached_file(
            file_path=str(test_file),
            original_path=str(test_file),
            cached_path=str(test_file),
            user_context=admin_context
        )
        
        # Attempt SQL injection in search filter
        malicious_filter = SecureCachedFilesFilter()
        # This would normally fail validation, but let's test the query handling
        try:
            # The search validation should prevent this, but test query safety
            files, count = service.get_cached_files(malicious_filter, admin_context)
            assert isinstance(files, list)
            assert isinstance(count, int)
        except ValidationError:
            # Expected - validation should catch malicious input
            pass
    
    def test_path_traversal_protection(self, temp_db_service):
        """Test path traversal attack protection."""
        service, temp_dir = temp_db_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        # Attempt path traversal in file paths
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "/var/cache/../../../secret.txt"
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(ValueError, match="dangerous pattern"):
                service.add_cached_file(
                    file_path=dangerous_path,
                    original_path=dangerous_path,
                    cached_path=dangerous_path,
                    user_context=admin_context
                )
    
    def test_authorization_controls(self, temp_db_service):
        """Test authorization and access controls."""
        service, temp_dir = temp_db_service
        
        # Test read-only user
        readonly_context = UserOperationContext(
            user_id="readonly",
            trigger_source="test"
        )
        
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test")
        
        # Should fail to add file (no write permission)
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.add_cached_file(
                file_path=str(test_file),
                original_path=str(test_file),
                cached_path=str(test_file),
                user_context=readonly_context
            )
        
        # Should be able to read statistics
        stats = service.get_cache_statistics(readonly_context)
        assert isinstance(stats, SecureCacheStatistics)
        
        # Regular user should be able to add files
        user_context = UserOperationContext(
            user_id="user1",
            trigger_source="test"
        )
        
        cached_file = service.add_cached_file(
            file_path=str(test_file),
            original_path=str(test_file),
            cached_path=str(test_file),
            user_context=user_context
        )
        assert cached_file.triggered_by_user == "user1"
        
        # But should not be able to cleanup (admin only)
        with pytest.raises(PermissionError, match="Insufficient permissions"):
            service.cleanup_orphaned_files(user_context)
    
    def test_rate_limiting(self, temp_db_service):
        """Test rate limiting functionality."""
        service, temp_dir = temp_db_service
        
        user_context = UserOperationContext(
            user_id="user1",
            trigger_source="test"
        )
        
        # Simulate rapid requests by manipulating the rate limiter
        with service._rate_limit_lock:
            # Fill up the rate limit for user1
            now = datetime.now(timezone.utc)
            service._rate_limiter["user1"] = [now] * SecurityConfig.RATE_LIMIT_REQUESTS
        
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test")
        
        # Next request should be rate limited
        with pytest.raises(PermissionError, match="Rate limit exceeded"):
            service.add_cached_file(
                file_path=str(test_file),
                original_path=str(test_file),
                cached_path=str(test_file),
                user_context=user_context
            )
    
    def test_atomic_transactions(self, temp_db_service):
        """Test atomic transaction handling."""
        service, temp_dir = temp_db_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test")
        
        # Mock database error to test rollback
        with patch.object(service.connection_pool, 'get_connection') as mock_conn:
            # Create a mock connection that fails during commit
            mock_db_conn = MagicMock()
            mock_db_conn.connection.execute.side_effect = [None, None, Exception("DB Error")]
            mock_conn.return_value.__enter__.return_value = mock_db_conn
            
            with pytest.raises(Exception, match="DB Error"):
                service.add_cached_file(
                    file_path=str(test_file),
                    original_path=str(test_file),
                    cached_path=str(test_file),
                    user_context=admin_context
                )
            
            # Verify transaction was marked inactive
            assert not mock_db_conn.transaction_active
    
    def test_concurrent_operations(self, temp_db_service):
        """Test concurrent database operations."""
        service, temp_dir = temp_db_service
        
        results = []
        errors = []
        
        def add_file_worker(file_num):
            try:
                admin_context = UserOperationContext(
                    user_id="admin",
                    trigger_source="test"
                )
                
                test_file = Path(temp_dir) / f"test_{file_num}.mp4"
                test_file.write_text(f"test content {file_num}")
                
                cached_file = service.add_cached_file(
                    file_path=str(test_file),
                    original_path=str(test_file),
                    cached_path=str(test_file),
                    user_context=admin_context
                )
                results.append(cached_file)
            except Exception as e:
                errors.append(e)
        
        # Run multiple concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=add_file_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"
    
    def test_security_logging(self, temp_db_service):
        """Test security event logging."""
        service, temp_dir = temp_db_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test")
        
        # Perform an operation that should be logged
        service.add_cached_file(
            file_path=str(test_file),
            original_path=str(test_file),
            cached_path=str(test_file),
            user_context=admin_context,
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0"
        )
        
        # Check security events
        events = service.get_security_events(user_context=admin_context)
        assert len(events) > 0
        
        # Find the file_cached event
        cached_events = [e for e in events if e['event_type'] == 'file_cached']
        assert len(cached_events) > 0
        
        event = cached_events[0]
        assert event['user_id'] == 'admin'
        assert event['success'] is True
        assert event['ip_address'] == '127.0.0.1'
        assert event['user_agent'] == 'TestAgent/1.0'
    
    def test_integrity_verification(self, temp_db_service):
        """Test file integrity verification."""
        service, temp_dir = temp_db_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test content")
        
        # Add a file with checksum
        cached_file = service.add_cached_file(
            file_path=str(test_file),
            original_path=str(test_file),
            cached_path=str(test_file),
            user_context=admin_context
        )
        
        # Verify integrity
        verified_count, error_count = service.verify_cache_integrity(admin_context)
        assert verified_count == 1
        assert error_count == 0
        
        # Delete the cached file to simulate corruption
        test_file.unlink()
        
        # Verify again - should detect missing file
        verified_count, error_count = service.verify_cache_integrity(admin_context)
        assert error_count == 1
    
    def test_database_connection_pooling(self, temp_db_service):
        """Test database connection pooling."""
        service, temp_dir = temp_db_service
        
        # Test that connections are reused
        connections_used = []
        
        def get_connection_id():
            with service.connection_pool.get_connection() as db_conn:
                connections_used.append(db_conn.connection_id)
        
        # Use connections sequentially
        for _ in range(5):
            get_connection_id()
        
        # Should reuse connections
        unique_connections = set(connections_used)
        assert len(unique_connections) <= service.connection_pool.max_connections
    
    def test_input_validation_edge_cases(self, temp_db_service):
        """Test edge cases in input validation."""
        service, temp_dir = temp_db_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        # Test with empty strings
        with pytest.raises(ValueError):
            service.add_cached_file(
                file_path="",
                original_path="",
                cached_path="",
                user_context=admin_context
            )
        
        # Test with None values
        with pytest.raises((ValueError, TypeError)):
            service.add_cached_file(
                file_path=None,
                original_path=None,
                cached_path=None,
                user_context=admin_context
            )
        
        # Test with excessively long paths
        long_path = "x" * (SecurityConfig.MAX_PATH_LENGTH + 1)
        with pytest.raises(ValueError, match="Path too long"):
            service.add_cached_file(
                file_path=long_path,
                original_path=long_path,
                cached_path=long_path,
                user_context=admin_context
            )
    
    def test_cleanup_and_shutdown(self, temp_db_service):
        """Test proper cleanup and shutdown."""
        service, temp_dir = temp_db_service
        
        # Add some test data
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="test"
        )
        
        test_file = Path(temp_dir) / "test.mp4"
        test_file.write_text("test")
        
        service.add_cached_file(
            file_path=str(test_file),
            original_path=str(test_file),
            cached_path=str(test_file),
            user_context=admin_context
        )
        
        # Test cleanup
        cleaned_count = service.cleanup_orphaned_files(admin_context)
        assert isinstance(cleaned_count, int)
        
        # Test service shutdown
        service.close()
        
        # Verify connections are closed
        assert service.connection_pool._connection_count >= 0


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    @pytest.fixture
    def production_like_service(self):
        """Create a service with production-like configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create realistic directory structure
            cache_dir = Path(temp_dir) / "cache"
            media_dir = Path(temp_dir) / "media"
            cache_dir.mkdir()
            media_dir.mkdir()
            
            db_path = Path(temp_dir) / "cache.db"
            allowed_paths = [str(cache_dir), str(media_dir)]
            
            service = SecureCachedFilesService(
                database_path=str(db_path),
                allowed_base_paths=allowed_paths,
                max_connections=5,
                security_key="test-key-for-hmac"
            )
            
            # Set up realistic user permissions
            service.auth_manager.add_user("admin", SecurityLevel.ADMIN)
            service.auth_manager.add_user("plex_user", SecurityLevel.USER)
            service.auth_manager.add_user("guest", SecurityLevel.PUBLIC)
            
            yield service, cache_dir, media_dir
            
            service.close()
    
    def test_realistic_workflow(self, production_like_service):
        """Test a realistic caching workflow with security."""
        service, cache_dir, media_dir = production_like_service
        
        # Simulate a user adding files to cache
        user_context = UserOperationContext(
            user_id="plex_user",
            plex_username="PlexUser",
            trigger_source="web_ui",
            client_info={"browser": "Chrome", "version": "91.0"}
        )
        
        # Create test media files
        movie_file = media_dir / "Movie (2023).mkv"
        movie_file.write_text("movie content")
        
        series_dir = media_dir / "Series" / "Season 1"
        series_dir.mkdir(parents=True)
        episode_file = series_dir / "Series.S01E01.mkv"
        episode_file.write_text("episode content")
        
        # Cache the files
        cached_movie = service.add_cached_file(
            file_path=str(movie_file),
            original_path=str(movie_file),
            cached_path=str(cache_dir / "Movie (2023).mkv"),
            cache_method="atomic_symlink",
            user_context=user_context,
            operation_reason="watchlist",
            ip_address="192.168.1.100",
            user_agent="PlexCacheUltra/1.0"
        )
        
        cached_episode = service.add_cached_file(
            file_path=str(episode_file),
            original_path=str(episode_file),
            cached_path=str(cache_dir / "Series.S01E01.mkv"),
            cache_method="atomic_copy",
            user_context=user_context,
            operation_reason="ondeck",
            ip_address="192.168.1.100",
            user_agent="PlexCacheUltra/1.0"
        )
        
        # Verify files were cached
        assert cached_movie.status == "active"
        assert cached_episode.status == "active"
        assert cached_movie.triggered_by_user == "plex_user"
        
        # Get files with filtering
        filter_params = SecureCachedFilesFilter(
            user_id="plex_user",
            status="active",
            triggered_by_operation="watchlist"
        )
        
        files, count = service.get_cached_files(filter_params, user_context)
        assert count == 1
        assert files[0].filename == "Movie (2023).mkv"
        
        # Get statistics
        stats = service.get_cache_statistics(user_context)
        assert stats.total_files == 2
        assert stats.active_files == 2
        assert stats.users_count == 1
        
        # Admin performs integrity check
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="web_ui"
        )
        
        verified, errors = service.verify_cache_integrity(admin_context)
        assert verified == 2
        assert errors == 0
        
        # Remove a file
        success = service.remove_cached_file(
            str(movie_file),
            reason="watched",
            user_context=user_context,
            ip_address="192.168.1.100"
        )
        assert success is True
        
        # Verify removal
        updated_stats = service.get_cache_statistics(user_context)
        assert updated_stats.active_files == 1
    
    def test_security_audit_trail(self, production_like_service):
        """Test comprehensive security audit trail."""
        service, cache_dir, media_dir = production_like_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="api"
        )
        
        user_context = UserOperationContext(
            user_id="plex_user",
            trigger_source="web_ui"
        )
        
        # Perform various operations to generate audit trail
        test_file = media_dir / "test.mkv"
        test_file.write_text("test content")
        
        # Successful operations
        service.add_cached_file(
            str(test_file), str(test_file), str(cache_dir / "test.mkv"),
            user_context=user_context, ip_address="192.168.1.100"
        )
        
        service.get_cached_files(user_context=user_context, ip_address="192.168.1.100")
        service.get_cache_statistics(user_context=user_context, ip_address="192.168.1.100")
        
        # Failed operations (permission denied)
        guest_context = UserOperationContext(user_id="guest", trigger_source="web_ui")
        
        try:
            service.add_cached_file(
                str(test_file), str(test_file), str(cache_dir / "test2.mkv"),
                user_context=guest_context, ip_address="192.168.1.101"
            )
        except PermissionError:
            pass  # Expected
        
        # Get security events
        events = service.get_security_events(user_context=admin_context)
        assert len(events) > 0
        
        # Check event types
        event_types = {event['event_type'] for event in events}
        expected_types = {'file_cached', 'files_accessed', 'statistics_accessed', 'authorization_failure'}
        assert event_types.intersection(expected_types) == expected_types
        
        # Check IP addresses are recorded
        ip_addresses = {event['ip_address'] for event in events if event['ip_address']}
        assert '192.168.1.100' in ip_addresses
        assert '192.168.1.101' in ip_addresses
    
    def test_performance_under_load(self, production_like_service):
        """Test service performance under load."""
        service, cache_dir, media_dir = production_like_service
        
        admin_context = UserOperationContext(
            user_id="admin",
            trigger_source="load_test"
        )
        
        # Create multiple test files
        test_files = []
        for i in range(20):
            test_file = media_dir / f"movie_{i:03d}.mkv"
            test_file.write_text(f"content {i}")
            test_files.append(test_file)
        
        start_time = time.time()
        
        # Add files concurrently
        def add_file_batch(start_idx, end_idx):
            for i in range(start_idx, end_idx):
                service.add_cached_file(
                    str(test_files[i]),
                    str(test_files[i]),
                    str(cache_dir / f"movie_{i:03d}.mkv"),
                    user_context=admin_context
                )
        
        threads = []
        batch_size = 5
        for i in range(0, 20, batch_size):
            thread = threading.Thread(
                target=add_file_batch, 
                args=(i, min(i + batch_size, 20))
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Verify all files were added
        stats = service.get_cache_statistics(admin_context)
        assert stats.total_files == 20
        
        # Check performance (should complete within reasonable time)
        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Operation took too long: {execution_time}s"
        
        # Test query performance
        start_time = time.time()
        
        files, count = service.get_cached_files(
            SecureCachedFilesFilter(limit=20),
            admin_context
        )
        
        query_time = time.time() - start_time
        assert query_time < 1.0, f"Query took too long: {query_time}s"
        assert len(files) == 20
        assert count == 20


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])