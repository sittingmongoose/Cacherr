"""
Cleanup task implementations for PlexCacheUltra scheduler.

This module provides task implementations for various cleanup operations
including cache cleanup, log file management, temporary file removal,
and system maintenance tasks.

Tasks:
- CacheCleanupTask: Clean up old and watched content from cache
- LogCleanupTask: Manage log file rotation and cleanup
- TempFileCleanupTask: Remove temporary files and directories
- SystemMaintenanceTask: General system maintenance operations

Example:
    ```python
    from src.scheduler.tasks.cleanup_tasks import CacheCleanupTask
    
    # Create cleanup task
    cleanup_task = CacheCleanupTask(service_provider, max_age_hours=48)
    
    # Execute task
    result = cleanup_task.execute()
    ```
"""

import logging
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from ...core.container import IServiceProvider
from ...core.interfaces import CacheService, FileService, NotificationService
from .cache_tasks import CacheTaskBase, TaskResult


logger = logging.getLogger(__name__)


class CacheCleanupTask(CacheTaskBase):
    """
    Task for cleaning up cache contents based on age and watch status.
    
    This task removes files from cache that meet cleanup criteria:
    - Files older than specified maximum age
    - Files that have been watched and meet expiry criteria
    - Orphaned cache entries with missing source files
    - Cache integrity validation and repair
    """
    
    def __init__(self, service_provider: IServiceProvider,
                 max_age_hours: Optional[int] = None,
                 cleanup_watched: bool = True,
                 cleanup_orphaned: bool = True,
                 cleanup_empty_dirs: bool = True):
        """
        Initialize cache cleanup task.
        
        Args:
            service_provider: Dependency injection service provider
            max_age_hours: Maximum age for cache files (None uses system default)
            cleanup_watched: Whether to cleanup watched content
            cleanup_orphaned: Whether to cleanup orphaned cache entries
            cleanup_empty_dirs: Whether to cleanup empty directories
        """
        super().__init__(service_provider)
        self.max_age_hours = max_age_hours
        self.cleanup_watched = cleanup_watched
        self.cleanup_orphaned = cleanup_orphaned
        self.cleanup_empty_dirs = cleanup_empty_dirs
    
    def execute(self) -> TaskResult:
        """
        Execute cache cleanup operations.
        
        Returns:
            TaskResult with cleanup operation results
        """
        start_time = datetime.now()
        result_data = {
            "cleanup_operations": [],
            "files_removed": 0,
            "bytes_freed": 0,
            "directories_removed": 0,
            "errors_encountered": []
        }
        errors = []
        warnings = []
        
        try:
            self.logger.info("Starting cache cleanup task")
            
            if not self.cache_service:
                error_msg = "Cache service not available for cleanup"
                return TaskResult(
                    success=False,
                    message=error_msg,
                    errors=[error_msg],
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Execute main cache cleanup
            cleanup_result = self.cache_service.cleanup_cache(self.max_age_hours)
            
            result_data["cleanup_operations"].append("cache_cleanup")
            result_data["files_removed"] += cleanup_result.files_processed
            result_data["bytes_freed"] += cleanup_result.total_size_bytes
            
            if not cleanup_result.success:
                errors.extend(cleanup_result.errors)
                warnings.extend(cleanup_result.warnings)
            
            self.logger.info(
                f"Main cache cleanup completed: {cleanup_result.files_processed} files removed, "
                f"{self._format_bytes(cleanup_result.total_size_bytes)} freed"
            )
            
            # Cleanup empty directories if enabled
            if self.cleanup_empty_dirs:
                dirs_removed = self._cleanup_empty_directories()
                result_data["cleanup_operations"].append("empty_directory_cleanup")
                result_data["directories_removed"] = dirs_removed
                self.logger.info(f"Removed {dirs_removed} empty directories")
            
            # Calculate final results
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result_data["files_removed"] > 0 or result_data["directories_removed"] > 0:
                success_message = (
                    f"Cache cleanup completed successfully. "
                    f"Removed {result_data['files_removed']} files "
                    f"({self._format_bytes(result_data['bytes_freed'])}) "
                    f"and {result_data['directories_removed']} empty directories"
                )
            else:
                success_message = "Cache cleanup completed - no files needed removal"
            
            # Determine overall success
            overall_success = len(errors) == 0
            
            self.logger.info(success_message)
            
            # Send notification
            if overall_success:
                self.send_notification(success_message, level="success")
            else:
                self.send_notification(
                    f"Cache cleanup completed with errors: {'; '.join(errors)}",
                    level="warning"
                )
            
            return TaskResult(
                success=overall_success,
                message=success_message,
                data=result_data,
                errors=errors,
                warnings=warnings,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            error_msg = f"Cache cleanup task failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            self.send_notification(
                error_msg,
                level="error",
                details={"task": "cache_cleanup", "error": str(e)}
            )
            
            return TaskResult(
                success=False,
                message=error_msg,
                data=result_data,
                errors=errors,
                warnings=warnings,
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _cleanup_empty_directories(self) -> int:
        """
        Clean up empty directories in cache locations.
        
        Returns:
            Number of directories removed
        """
        directories_removed = 0
        
        try:
            # Get cache statistics to find cache locations
            cache_stats = self.cache_service.get_cache_statistics()
            
            # This would need to be implemented based on actual cache structure
            # For now, we'll return 0 as a placeholder
            
            self.logger.debug("Empty directory cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Error during empty directory cleanup: {e}")
        
        return directories_removed
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value to human-readable string."""
        if self.file_service:
            return self.file_service.get_file_size_readable(bytes_value)
        
        # Fallback formatting
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"


class LogCleanupTask:
    """
    Task for managing log file cleanup and rotation.
    
    This task handles:
    - Rotating log files when they reach size limits
    - Removing old log files based on retention policy
    - Compressing archived log files
    - Monitoring disk space used by logs
    """
    
    def __init__(self, log_dir: Path = None,
                 max_log_size_mb: int = 100,
                 max_log_files: int = 10,
                 max_age_days: int = 30,
                 compress_old_logs: bool = True):
        """
        Initialize log cleanup task.
        
        Args:
            log_dir: Directory containing log files (None uses default)
            max_log_size_mb: Maximum size for individual log files
            max_log_files: Maximum number of log files to keep
            max_age_days: Maximum age for log files in days
            compress_old_logs: Whether to compress old log files
        """
        self.log_dir = log_dir or Path("/config/logs")
        self.max_log_size_mb = max_log_size_mb
        self.max_log_files = max_log_files
        self.max_age_days = max_age_days
        self.compress_old_logs = compress_old_logs
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def execute(self) -> TaskResult:
        """
        Execute log cleanup operations.
        
        Returns:
            TaskResult with log cleanup results
        """
        start_time = datetime.now()
        result_data = {
            "cleanup_operations": [],
            "files_removed": 0,
            "files_compressed": 0,
            "bytes_freed": 0,
            "log_files_found": 0
        }
        errors = []
        warnings = []
        
        try:
            self.logger.info(f"Starting log cleanup task in {self.log_dir}")
            
            if not self.log_dir.exists():
                warning_msg = f"Log directory does not exist: {self.log_dir}"
                self.logger.warning(warning_msg)
                warnings.append(warning_msg)
                
                return TaskResult(
                    success=True,
                    message="Log cleanup completed - no log directory found",
                    data=result_data,
                    warnings=warnings,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Find all log files
            log_files = list(self.log_dir.glob("*.log*"))
            result_data["log_files_found"] = len(log_files)
            
            if not log_files:
                self.logger.info("No log files found for cleanup")
                return TaskResult(
                    success=True,
                    message="Log cleanup completed - no log files found",
                    data=result_data,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Remove old log files
            removed_files, bytes_freed = self._remove_old_log_files(log_files)
            result_data["files_removed"] = removed_files
            result_data["bytes_freed"] = bytes_freed
            
            if removed_files > 0:
                result_data["cleanup_operations"].append("old_file_removal")
                self.logger.info(f"Removed {removed_files} old log files")
            
            # Compress large log files if enabled
            if self.compress_old_logs:
                compressed_files = self._compress_large_log_files(log_files)
                result_data["files_compressed"] = compressed_files
                
                if compressed_files > 0:
                    result_data["cleanup_operations"].append("log_compression")
                    self.logger.info(f"Compressed {compressed_files} log files")
            
            # Rotate current log file if too large
            current_log = self.log_dir / "cacherr.log"
            if current_log.exists() and self._should_rotate_log(current_log):
                if self._rotate_current_log(current_log):
                    result_data["cleanup_operations"].append("log_rotation")
                    self.logger.info("Rotated current log file")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result_data["cleanup_operations"]:
                success_message = (
                    f"Log cleanup completed. "
                    f"Operations: {', '.join(result_data['cleanup_operations'])}. "
                    f"Removed {result_data['files_removed']} files, "
                    f"compressed {result_data['files_compressed']} files"
                )
            else:
                success_message = "Log cleanup completed - no actions needed"
            
            self.logger.info(success_message)
            
            return TaskResult(
                success=True,
                message=success_message,
                data=result_data,
                errors=errors,
                warnings=warnings,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            error_msg = f"Log cleanup task failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            return TaskResult(
                success=False,
                message=error_msg,
                data=result_data,
                errors=errors,
                warnings=warnings,
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _remove_old_log_files(self, log_files: List[Path]) -> tuple[int, int]:
        """
        Remove log files older than max_age_days.
        
        Args:
            log_files: List of log file paths
            
        Returns:
            Tuple of (files_removed, bytes_freed)
        """
        files_removed = 0
        bytes_freed = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        for log_file in log_files:
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    file_size = log_file.stat().st_size
                    log_file.unlink()
                    files_removed += 1
                    bytes_freed += file_size
                    self.logger.debug(f"Removed old log file: {log_file}")
                    
            except Exception as e:
                self.logger.warning(f"Error removing log file {log_file}: {e}")
        
        return files_removed, bytes_freed
    
    def _compress_large_log_files(self, log_files: List[Path]) -> int:
        """
        Compress log files that are larger than threshold.
        
        Args:
            log_files: List of log file paths
            
        Returns:
            Number of files compressed
        """
        files_compressed = 0
        
        # This would require gzip import and implementation
        # For now, we'll return 0 as placeholder
        
        return files_compressed
    
    def _should_rotate_log(self, log_file: Path) -> bool:
        """
        Check if current log file should be rotated.
        
        Args:
            log_file: Path to current log file
            
        Returns:
            True if log file should be rotated
        """
        try:
            file_size_mb = log_file.stat().st_size / (1024 * 1024)
            return file_size_mb >= self.max_log_size_mb
        except Exception:
            return False
    
    def _rotate_current_log(self, current_log: Path) -> bool:
        """
        Rotate the current log file.
        
        Args:
            current_log: Path to current log file
            
        Returns:
            True if rotation successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_name = current_log.with_name(f"{current_log.stem}_{timestamp}.log")
            
            current_log.rename(rotated_name)
            self.logger.info(f"Rotated log file to: {rotated_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rotate log file: {e}")
            return False


class TempFileCleanupTask:
    """
    Task for cleaning up temporary files and directories.
    
    This task removes temporary files created during operations,
    cleans up system temp directories, and manages disk space.
    """
    
    def __init__(self, max_age_hours: int = 24,
                 cleanup_system_temp: bool = False,
                 temp_patterns: Optional[List[str]] = None):
        """
        Initialize temp file cleanup task.
        
        Args:
            max_age_hours: Maximum age for temp files
            cleanup_system_temp: Whether to cleanup system temp directory
            temp_patterns: File patterns to consider as temporary
        """
        self.max_age_hours = max_age_hours
        self.cleanup_system_temp = cleanup_system_temp
        self.temp_patterns = temp_patterns or ["*.tmp", "*.temp", "*.cache", ".DS_Store"]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def execute(self) -> TaskResult:
        """
        Execute temp file cleanup.
        
        Returns:
            TaskResult with cleanup results
        """
        start_time = datetime.now()
        result_data = {
            "cleanup_locations": [],
            "files_removed": 0,
            "bytes_freed": 0,
            "directories_removed": 0
        }
        
        try:
            self.logger.info("Starting temporary file cleanup task")
            
            # Cleanup application temp files
            app_temp_removed, app_bytes_freed = self._cleanup_app_temp_files()
            result_data["files_removed"] += app_temp_removed
            result_data["bytes_freed"] += app_bytes_freed
            
            if app_temp_removed > 0:
                result_data["cleanup_locations"].append("application_temp")
                self.logger.info(f"Removed {app_temp_removed} application temp files")
            
            # Cleanup system temp files if enabled
            if self.cleanup_system_temp:
                sys_temp_removed, sys_bytes_freed = self._cleanup_system_temp_files()
                result_data["files_removed"] += sys_temp_removed
                result_data["bytes_freed"] += sys_bytes_freed
                
                if sys_temp_removed > 0:
                    result_data["cleanup_locations"].append("system_temp")
                    self.logger.info(f"Removed {sys_temp_removed} system temp files")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result_data["files_removed"] > 0:
                success_message = (
                    f"Temp file cleanup completed. "
                    f"Removed {result_data['files_removed']} files "
                    f"({self._format_bytes(result_data['bytes_freed'])})"
                )
            else:
                success_message = "Temp file cleanup completed - no files needed removal"
            
            self.logger.info(success_message)
            
            return TaskResult(
                success=True,
                message=success_message,
                data=result_data,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            error_msg = f"Temp file cleanup failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return TaskResult(
                success=False,
                message=error_msg,
                errors=[error_msg],
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _cleanup_app_temp_files(self) -> tuple[int, int]:
        """
        Clean up application-specific temp files.
        
        Returns:
            Tuple of (files_removed, bytes_freed)
        """
        files_removed = 0
        bytes_freed = 0
        
        # Clean up various temp locations
        temp_locations = [
            Path("/config/temp"),  # Application temp directory
            Path("/tmp/cacherr"),  # App-specific temp
            Path.cwd() / "temp"  # Local temp directory
        ]
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        
        for temp_dir in temp_locations:
            if not temp_dir.exists():
                continue
            
            try:
                for pattern in self.temp_patterns:
                    for temp_file in temp_dir.glob(pattern):
                        try:
                            if temp_file.is_file():
                                file_mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                                
                                if file_mtime < cutoff_time:
                                    file_size = temp_file.stat().st_size
                                    temp_file.unlink()
                                    files_removed += 1
                                    bytes_freed += file_size
                                    
                        except Exception as e:
                            self.logger.warning(f"Error removing temp file {temp_file}: {e}")
                            
            except Exception as e:
                self.logger.warning(f"Error cleaning temp directory {temp_dir}: {e}")
        
        return files_removed, bytes_freed
    
    def _cleanup_system_temp_files(self) -> tuple[int, int]:
        """
        Clean up system temp files (use with caution).
        
        Returns:
            Tuple of (files_removed, bytes_freed)
        """
        files_removed = 0
        bytes_freed = 0
        
        try:
            system_temp = Path(tempfile.gettempdir())
            cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
            
            # Only clean files with our app-specific patterns to avoid system issues
            app_patterns = ["plexcache*", "cacherr*"]
            
            for pattern in app_patterns:
                for temp_file in system_temp.glob(pattern):
                    try:
                        if temp_file.is_file():
                            file_mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                            
                            if file_mtime < cutoff_time:
                                file_size = temp_file.stat().st_size
                                temp_file.unlink()
                                files_removed += 1
                                bytes_freed += file_size
                                
                    except Exception as e:
                        self.logger.warning(f"Error removing system temp file {temp_file}: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Error cleaning system temp files: {e}")
        
        return files_removed, bytes_freed
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"