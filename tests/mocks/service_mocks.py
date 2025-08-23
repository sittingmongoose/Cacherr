"""
Mock implementations of core service interfaces.

This module provides comprehensive mock implementations that can be used
in testing to provide predictable behavior and avoid external dependencies.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from unittest.mock import Mock

from src.core.interfaces import (
    MediaService, FileService, CacheService, NotificationService,
    CacheOperationResult, TestModeAnalysis
)
from src.core.repositories import CacheEntry


class MockMediaService(MediaService):
    """Mock implementation of MediaService for testing."""
    
    def __init__(self, simulation_mode: str = "success"):
        """
        Initialize mock media service.
        
        Args:
            simulation_mode: Mode for simulating different behaviors
                - "success": All operations succeed
                - "failure": All operations fail
                - "mixed": Alternating success/failure
        """
        self.simulation_mode = simulation_mode
        self.call_count = 0
        self.media_database = {
            "/media/movies/test_movie.mkv": {
                "title": "Test Movie",
                "year": 2021,
                "duration": 7200000,  # 2 hours in ms
                "size": 2000000000,   # 2GB
                "format": "mkv",
                "codec": "h264",
                "resolution": "1920x1080"
            },
            "/media/tv/test_show_s01e01.mkv": {
                "title": "Test Show",
                "season": 1,
                "episode": 1,
                "duration": 2700000,  # 45 minutes in ms
                "size": 800000000,    # 800MB
                "format": "mkv",
                "codec": "h265",
                "resolution": "1920x1080"
            }
        }
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Get media information for a file."""
        self.call_count += 1
        
        if self._should_fail():
            raise RuntimeError(f"Mock media service failure for {file_path}")
        
        # Return mock data if available, otherwise generate
        if file_path in self.media_database:
            return self.media_database[file_path].copy()
        
        # Generate mock data based on file path
        return {
            "title": Path(file_path).stem,
            "duration": 7200000,  # 2 hours default
            "size": 1500000000,   # 1.5GB default
            "format": Path(file_path).suffix[1:],  # Remove dot
            "codec": "h264",
            "resolution": "1920x1080",
            "bitrate": 8000000
        }
    
    def is_media_file(self, file_path: str) -> bool:
        """Check if file is a media file."""
        self.call_count += 1
        
        if self._should_fail():
            return False
        
        media_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.m4v'}
        return Path(file_path).suffix.lower() in media_extensions
    
    def validate_media_file(self, file_path: str) -> bool:
        """Validate media file integrity."""
        self.call_count += 1
        
        if self._should_fail():
            return False
        
        # Mock validation - succeed for known files
        return file_path in self.media_database or self.is_media_file(file_path)
    
    def get_media_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get detailed media metadata."""
        self.call_count += 1
        
        if self._should_fail():
            raise RuntimeError(f"Failed to get metadata for {file_path}")
        
        base_info = self.get_media_info(file_path)
        base_info.update({
            "created_date": datetime.now().isoformat(),
            "modified_date": datetime.now().isoformat(),
            "audio_tracks": [
                {"language": "en", "codec": "aac", "channels": 6},
                {"language": "es", "codec": "ac3", "channels": 6}
            ],
            "subtitle_tracks": [
                {"language": "en", "type": "srt"},
                {"language": "es", "type": "srt"}
            ]
        })
        return base_info
    
    def _should_fail(self) -> bool:
        """Determine if current operation should fail based on simulation mode."""
        if self.simulation_mode == "failure":
            return True
        elif self.simulation_mode == "mixed":
            return self.call_count % 2 == 0
        return False


class MockFileService(FileService):
    """Mock implementation of FileService for testing."""
    
    def __init__(self, simulation_mode: str = "success"):
        """
        Initialize mock file service.
        
        Args:
            simulation_mode: Mode for simulating different behaviors
        """
        self.simulation_mode = simulation_mode
        self.call_count = 0
        self.file_system = {}  # Mock file system state
        self.operations_log = []  # Log of operations performed
        
        # Pre-populate with some test files
        self._setup_test_files()
    
    def _setup_test_files(self):
        """Set up initial test files in mock file system."""
        test_files = {
            "/media/movies/test_movie.mkv": {
                "size": 2000000000,
                "modified_time": 1640995200,  # 2022-01-01
                "exists": True,
                "permissions": "rw-r--r--"
            },
            "/cache/test_movie.mkv": {
                "size": 2000000000,
                "modified_time": 1641081600,  # 2022-01-02
                "exists": False,  # Will be created by operations
                "permissions": "rw-r--r--"
            },
            "/array/restored_movie.mkv": {
                "size": 1500000000,
                "modified_time": 1641168000,  # 2022-01-03
                "exists": False,
                "permissions": "rw-r--r--"
            }
        }
        self.file_system.update(test_files)
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        self.call_count += 1
        self._log_operation("file_exists", {"path": file_path})
        
        if self._should_fail():
            raise OSError(f"Mock file service error checking {file_path}")
        
        return self.file_system.get(file_path, {}).get("exists", False)
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        self.call_count += 1
        self._log_operation("get_file_size", {"path": file_path})
        
        if self._should_fail():
            raise OSError(f"Mock error getting size of {file_path}")
        
        if not self.file_exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return self.file_system[file_path]["size"]
    
    def get_file_modified_time(self, file_path: str) -> float:
        """Get file modification time as timestamp."""
        self.call_count += 1
        self._log_operation("get_file_modified_time", {"path": file_path})
        
        if self._should_fail():
            raise OSError(f"Mock error getting modified time of {file_path}")
        
        if not self.file_exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return self.file_system[file_path]["modified_time"]
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy file from source to destination."""
        self.call_count += 1
        self._log_operation("copy_file", {
            "source": source_path,
            "destination": destination_path
        })
        
        if self._should_fail():
            return False
        
        if not self.file_exists(source_path):
            return False
        
        # Copy file in mock file system
        source_info = self.file_system[source_path].copy()
        self.file_system[destination_path] = source_info
        self.file_system[destination_path]["exists"] = True
        self.file_system[destination_path]["modified_time"] = datetime.now().timestamp()
        
        return True
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """Move file from source to destination."""
        self.call_count += 1
        self._log_operation("move_file", {
            "source": source_path,
            "destination": destination_path
        })
        
        if self._should_fail():
            return False
        
        if not self.copy_file(source_path, destination_path):
            return False
        
        # Remove source file
        if source_path in self.file_system:
            self.file_system[source_path]["exists"] = False
        
        return True
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file."""
        self.call_count += 1
        self._log_operation("delete_file", {"path": file_path})
        
        if self._should_fail():
            return False
        
        if file_path in self.file_system:
            self.file_system[file_path]["exists"] = False
            return True
        
        return False
    
    def create_directory(self, directory_path: str) -> bool:
        """Create directory."""
        self.call_count += 1
        self._log_operation("create_directory", {"path": directory_path})
        
        if self._should_fail():
            return False
        
        # Mark directory as existing in mock file system
        self.file_system[directory_path] = {
            "exists": True,
            "is_directory": True,
            "created_time": datetime.now().timestamp()
        }
        
        return True
    
    def get_available_space(self, path: str) -> int:
        """Get available space in bytes for given path."""
        self.call_count += 1
        self._log_operation("get_available_space", {"path": path})
        
        if self._should_fail():
            raise OSError(f"Mock error getting available space for {path}")
        
        # Return mock available space based on path
        if "/cache" in path:
            return 50000000000  # 50GB available in cache
        elif "/array" in path:
            return 500000000000  # 500GB available in array
        else:
            return 100000000000  # 100GB default
    
    def _log_operation(self, operation: str, params: Dict[str, Any]):
        """Log file operation for testing verification."""
        self.operations_log.append({
            "operation": operation,
            "params": params,
            "timestamp": datetime.now(),
            "call_count": self.call_count
        })
    
    def _should_fail(self) -> bool:
        """Determine if current operation should fail."""
        if self.simulation_mode == "failure":
            return True
        elif self.simulation_mode == "mixed":
            return self.call_count % 3 == 0  # Fail every 3rd operation
        return False
    
    def get_operations_log(self) -> List[Dict[str, Any]]:
        """Get log of all operations performed."""
        return self.operations_log.copy()


class MockCacheService(CacheService):
    """Mock implementation of CacheService for testing."""
    
    def __init__(self, simulation_mode: str = "success"):
        """Initialize mock cache service."""
        self.simulation_mode = simulation_mode
        self.call_count = 0
        self.cached_files = {}  # Track cached files
        self.cache_statistics = {
            "total_files": 0,
            "total_size": 0,
            "free_space": 50000000000,  # 50GB
            "cache_hit_rate": 0.85
        }
    
    def cache_file(self, file_path: str, cache_path: str, 
                   operation_type: str = "move") -> CacheOperationResult:
        """Cache a file."""
        self.call_count += 1
        
        if self._should_fail():
            return CacheOperationResult(
                success=False,
                message=f"Mock cache operation failed for {file_path}",
                operation_type=operation_type,
                file_path=file_path,
                error_details="Simulated cache service failure"
            )
        
        # Simulate successful caching
        file_size = 1500000000  # Mock 1.5GB file size
        
        self.cached_files[file_path] = {
            "cache_path": cache_path,
            "operation_type": operation_type,
            "size": file_size,
            "cached_at": datetime.now(),
            "access_count": 0
        }
        
        # Update statistics
        self.cache_statistics["total_files"] += 1
        self.cache_statistics["total_size"] += file_size
        self.cache_statistics["free_space"] -= file_size
        
        return CacheOperationResult(
            success=True,
            message=f"File successfully cached: {file_path}",
            operation_type=operation_type,
            file_path=file_path,
            cache_path=cache_path,
            size=file_size,
            duration_seconds=2.5  # Mock operation time
        )
    
    def restore_file(self, file_path: str, restore_path: str,
                     operation_type: str = "move") -> CacheOperationResult:
        """Restore a file from cache."""
        self.call_count += 1
        
        if self._should_fail():
            return CacheOperationResult(
                success=False,
                message=f"Mock restore operation failed for {file_path}",
                operation_type=operation_type,
                file_path=file_path,
                error_details="Simulated restore failure"
            )
        
        if file_path not in self.cached_files:
            return CacheOperationResult(
                success=False,
                message=f"File not found in cache: {file_path}",
                operation_type=operation_type,
                file_path=file_path,
                error_details="File not in cache"
            )
        
        cached_info = self.cached_files[file_path]
        file_size = cached_info["size"]
        
        # Remove from cache if move operation
        if operation_type == "move":
            del self.cached_files[file_path]
            self.cache_statistics["total_files"] -= 1
            self.cache_statistics["total_size"] -= file_size
            self.cache_statistics["free_space"] += file_size
        else:
            # Just increment access count for copy
            cached_info["access_count"] += 1
        
        return CacheOperationResult(
            success=True,
            message=f"File successfully restored: {file_path}",
            operation_type=operation_type,
            file_path=file_path,
            cache_path=restore_path,
            size=file_size,
            duration_seconds=1.8
        )
    
    def is_file_cached(self, file_path: str) -> bool:
        """Check if file is in cache."""
        self.call_count += 1
        
        if self._should_fail():
            return False
        
        return file_path in self.cached_files
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information."""
        self.call_count += 1
        
        if self._should_fail():
            return {}
        
        status = self.cache_statistics.copy()
        status.update({
            "cache_utilization": (status["total_size"] / (status["total_size"] + status["free_space"])) if status["total_size"] > 0 else 0,
            "cached_files_list": list(self.cached_files.keys()),
            "last_updated": datetime.now().isoformat()
        })
        
        return status
    
    def analyze_test_mode(self, directory: str) -> TestModeAnalysis:
        """Analyze directory for test mode operation."""
        self.call_count += 1
        
        if self._should_fail():
            return TestModeAnalysis(
                success=False,
                message="Mock test mode analysis failed",
                total_files=0,
                total_size=0,
                files_to_cache=[],
                files_to_restore=[],
                error_details="Simulated analysis failure"
            )
        
        # Generate mock analysis results
        mock_files = [
            f"{directory}/movie_1.mkv",
            f"{directory}/movie_2.mp4",
            f"{directory}/tv_show_s01e01.mkv"
        ]
        
        files_to_cache = mock_files[:2]  # First 2 files
        files_to_restore = mock_files[2:] if len(mock_files) > 2 else []
        
        return TestModeAnalysis(
            success=True,
            message=f"Test mode analysis complete for {directory}",
            total_files=len(mock_files),
            total_size=4500000000,  # Mock total size
            files_to_cache=files_to_cache,
            files_to_restore=files_to_restore,
            estimated_cache_savings=1500000000,  # Mock savings
            estimated_restore_time=300  # 5 minutes
        )
    
    def _should_fail(self) -> bool:
        """Determine if operation should fail."""
        if self.simulation_mode == "failure":
            return True
        elif self.simulation_mode == "mixed":
            return self.call_count % 4 == 0  # Fail every 4th operation
        return False


class MockNotificationService(NotificationService):
    """Mock implementation of NotificationService for testing."""
    
    def __init__(self, simulation_mode: str = "success", enabled: bool = True):
        """Initialize mock notification service."""
        self.simulation_mode = simulation_mode
        self.call_count = 0
        self.enabled = enabled
        self.sent_notifications = []  # Track sent notifications
    
    def send_notification(self, message: str, title: str = "PlexCacheUltra",
                         priority: str = "normal", **kwargs) -> bool:
        """Send a notification."""
        self.call_count += 1
        
        notification = {
            "message": message,
            "title": title,
            "priority": priority,
            "timestamp": datetime.now(),
            "kwargs": kwargs
        }
        
        if not self.enabled:
            notification["status"] = "disabled"
            self.sent_notifications.append(notification)
            return False
        
        if self._should_fail():
            notification["status"] = "failed"
            notification["error"] = "Mock notification service failure"
            self.sent_notifications.append(notification)
            return False
        
        notification["status"] = "sent"
        self.sent_notifications.append(notification)
        return True
    
    def send_test_notification(self) -> bool:
        """Send a test notification."""
        return self.send_notification(
            message="This is a test notification from PlexCacheUltra",
            title="Test Notification",
            priority="low"
        )
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.enabled
    
    def get_notification_history(self) -> List[Dict[str, Any]]:
        """Get history of sent notifications."""
        return self.sent_notifications.copy()
    
    def enable_notifications(self):
        """Enable notifications."""
        self.enabled = True
    
    def disable_notifications(self):
        """Disable notifications."""
        self.enabled = False
    
    def _should_fail(self) -> bool:
        """Determine if operation should fail."""
        if self.simulation_mode == "failure":
            return True
        elif self.simulation_mode == "mixed":
            return self.call_count % 5 == 0  # Fail every 5th operation
        return False


# Factory functions for creating mock services
def create_mock_media_service(mode: str = "success") -> MockMediaService:
    """Create a mock media service with specified behavior mode."""
    return MockMediaService(simulation_mode=mode)


def create_mock_file_service(mode: str = "success") -> MockFileService:
    """Create a mock file service with specified behavior mode."""
    return MockFileService(simulation_mode=mode)


def create_mock_cache_service(mode: str = "success") -> MockCacheService:
    """Create a mock cache service with specified behavior mode."""
    return MockCacheService(simulation_mode=mode)


def create_mock_notification_service(mode: str = "success", enabled: bool = True) -> MockNotificationService:
    """Create a mock notification service with specified behavior mode."""
    return MockNotificationService(simulation_mode=mode, enabled=enabled)


def create_mock_service_suite(mode: str = "success") -> Dict[str, Any]:
    """Create a complete suite of mock services for testing."""
    return {
        "media_service": create_mock_media_service(mode),
        "file_service": create_mock_file_service(mode),
        "cache_service": create_mock_cache_service(mode),
        "notification_service": create_mock_notification_service(mode)
    }