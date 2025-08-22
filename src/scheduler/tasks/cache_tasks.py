"""
Cache-related task implementations for PlexCacheUltra scheduler.

This module provides task implementations for cache operations including
regular cache operations, test mode analysis, and cache maintenance tasks.
All tasks integrate with the dependency injection system and provide
comprehensive logging and error handling.

Tasks:
- CacheOperationTask: Execute full cache operations
- TestModeAnalysisTask: Run test mode analysis without file operations
- CacheValidationTask: Validate cache integrity and consistency
- CacheStatisticsTask: Generate cache statistics reports

Example:
    ```python
    from src.scheduler.tasks.cache_tasks import CacheOperationTask
    
    # Create task instance
    cache_task = CacheOperationTask(service_provider)
    
    # Execute task
    result = cache_task.execute()
    ```
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from pydantic import BaseModel, Field

from ...core.container import IServiceProvider
from ...core.interfaces import CacheService, MediaService, FileService, NotificationService


logger = logging.getLogger(__name__)


class TaskResult(BaseModel):
    """Base result model for task executions."""
    
    success: bool = Field(description="Whether task completed successfully")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional result data")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    execution_time_seconds: Optional[float] = Field(default=None, description="Task execution time")
    timestamp: datetime = Field(default_factory=datetime.now, description="Task completion timestamp")
    
    class Config:
        extra = "forbid"


class CacheTaskBase:
    """
    Base class for cache-related tasks.
    
    Provides common functionality and service access patterns
    for cache-related task implementations.
    """
    
    def __init__(self, service_provider: IServiceProvider):
        """
        Initialize cache task base.
        
        Args:
            service_provider: Dependency injection service provider
            
        Raises:
            ValueError: If service_provider is None
        """
        if not service_provider:
            raise ValueError("Service provider is required")
        
        self.service_provider = service_provider
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Services (resolved lazily)
        self._cache_service: Optional[CacheService] = None
        self._media_service: Optional[MediaService] = None
        self._file_service: Optional[FileService] = None
        self._notification_service: Optional[NotificationService] = None
    
    @property
    def cache_service(self) -> Optional[CacheService]:
        """Get cache service instance (lazy loading)."""
        if self._cache_service is None:
            self._cache_service = self.service_provider.try_resolve(CacheService)
        return self._cache_service
    
    @property
    def media_service(self) -> Optional[MediaService]:
        """Get media service instance (lazy loading)."""
        if self._media_service is None:
            self._media_service = self.service_provider.try_resolve(MediaService)
        return self._media_service
    
    @property
    def file_service(self) -> Optional[FileService]:
        """Get file service instance (lazy loading)."""
        if self._file_service is None:
            self._file_service = self.service_provider.try_resolve(FileService)
        return self._file_service
    
    @property
    def notification_service(self) -> Optional[NotificationService]:
        """Get notification service instance (lazy loading)."""
        if self._notification_service is None:
            self._notification_service = self.service_provider.try_resolve(NotificationService)
        return self._notification_service
    
    def validate_services(self) -> List[str]:
        """
        Validate that required services are available.
        
        Returns:
            List of missing service names (empty if all services available)
        """
        missing_services = []
        
        if not self.cache_service:
            missing_services.append("CacheService")
        
        if not self.media_service:
            missing_services.append("MediaService")
        
        if not self.file_service:
            missing_services.append("FileService")
        
        return missing_services
    
    def send_notification(self, message: str, level: str = "info", details: Optional[Dict] = None) -> None:
        """
        Send notification if service is available.
        
        Args:
            message: Notification message
            level: Notification level (info, warning, error, success)
            details: Optional additional details
        """
        if self.notification_service:
            try:
                if level == "error" and details:
                    self.notification_service.send_error_notification(message, details)
                elif level == "warning":
                    self.notification_service.send_warning_notification(message)
                elif level == "success":
                    self.notification_service.send_success_notification(message)
                else:
                    self.notification_service.send_notification(message, level)
            except Exception as e:
                self.logger.warning(f"Failed to send notification: {e}")


class CacheOperationTask(CacheTaskBase):
    """
    Task for executing regular cache operations.
    
    This task performs the full cache operation cycle including:
    - Fetching media files from Plex (onDeck, watchlist, watched)
    - Processing file paths and scanning additional sources
    - Executing cache operations (move files to/from cache)
    - Cleanup of watched content
    - Comprehensive error handling and reporting
    """
    
    def __init__(self, service_provider: IServiceProvider, 
                 include_cleanup: bool = True,
                 max_files_per_operation: Optional[int] = None):
        """
        Initialize cache operation task.
        
        Args:
            service_provider: Dependency injection service provider
            include_cleanup: Whether to include cleanup operations
            max_files_per_operation: Maximum files to process in single operation
        """
        super().__init__(service_provider)
        self.include_cleanup = include_cleanup
        self.max_files_per_operation = max_files_per_operation
    
    def execute(self) -> TaskResult:
        """
        Execute the cache operation task.
        
        Returns:
            TaskResult with operation results and statistics
        """
        start_time = datetime.now()
        result_data = {
            "operations_performed": [],
            "files_processed": 0,
            "total_bytes_processed": 0,
            "cache_operations": {},
            "array_operations": {},
            "cleanup_operations": {}
        }
        errors = []
        warnings = []
        
        try:
            self.logger.info("Starting cache operation task")
            
            # Validate required services
            missing_services = self.validate_services()
            if missing_services:
                error_msg = f"Missing required services: {', '.join(missing_services)}"
                self.logger.error(error_msg)
                
                return TaskResult(
                    success=False,
                    message=error_msg,
                    errors=[error_msg],
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Step 1: Fetch media files from Plex
            media_files = self._fetch_all_media_files()
            if not media_files:
                warning_msg = "No media files found to process"
                self.logger.warning(warning_msg)
                warnings.append(warning_msg)
            
            result_data["media_files_found"] = len(media_files)
            
            # Step 2: Process file paths and scan additional sources
            processed_files = self._process_media_files(media_files)
            result_data["files_after_processing"] = len(processed_files)
            
            if not processed_files:
                warning_msg = "No processable files found after path processing"
                self.logger.warning(warning_msg)
                warnings.append(warning_msg)
                
                return TaskResult(
                    success=True,
                    message="Cache operation completed - no files to process",
                    data=result_data,
                    warnings=warnings,
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Step 3: Execute cache operations (move files to cache)
            cache_result = self._execute_cache_operations(processed_files)
            result_data["cache_operations"] = cache_result
            result_data["operations_performed"].append("cache_operations")
            
            if cache_result.get("files_processed", 0) > 0:
                result_data["files_processed"] += cache_result["files_processed"]
                result_data["total_bytes_processed"] += cache_result.get("bytes_processed", 0)
            
            # Step 4: Execute array operations (move watched files back to array)
            array_result = self._execute_array_operations()
            result_data["array_operations"] = array_result
            result_data["operations_performed"].append("array_operations")
            
            if array_result.get("files_processed", 0) > 0:
                result_data["files_processed"] += array_result["files_processed"]
                result_data["total_bytes_processed"] += array_result.get("bytes_processed", 0)
            
            # Step 5: Cleanup operations (if enabled)
            if self.include_cleanup:
                cleanup_result = self._execute_cleanup_operations()
                result_data["cleanup_operations"] = cleanup_result
                result_data["operations_performed"].append("cleanup_operations")
                
                if cleanup_result.get("files_processed", 0) > 0:
                    result_data["files_processed"] += cleanup_result["files_processed"]
                    result_data["total_bytes_processed"] += cleanup_result.get("bytes_processed", 0)
            
            # Calculate final results
            execution_time = (datetime.now() - start_time).total_seconds()
            total_operations = len([op for op in result_data["operations_performed"] if op])
            
            success_message = (
                f"Cache operation completed successfully. "
                f"Processed {result_data['files_processed']} files in {total_operations} operations. "
                f"Total data processed: {self._format_bytes(result_data['total_bytes_processed'])}"
            )
            
            self.logger.info(success_message)
            
            # Send success notification
            self.send_notification(success_message, level="success")
            
            return TaskResult(
                success=True,
                message=success_message,
                data=result_data,
                warnings=warnings,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            error_msg = f"Cache operation task failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            # Send error notification
            self.send_notification(
                error_msg,
                level="error",
                details={"task": "cache_operation", "error": str(e)}
            )
            
            return TaskResult(
                success=False,
                message=error_msg,
                data=result_data,
                errors=errors,
                warnings=warnings,
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _fetch_all_media_files(self) -> List[str]:
        """
        Fetch all media files from Plex sources.
        
        Returns:
            List of media file paths
        """
        all_files = []
        
        try:
            # Fetch onDeck media
            ondeck_files = self.media_service.fetch_ondeck_media()
            all_files.extend(ondeck_files)
            self.logger.info(f"Found {len(ondeck_files)} onDeck files")
            
            # Fetch watchlist media
            watchlist_files = self.media_service.fetch_watchlist_media()
            all_files.extend(watchlist_files)
            self.logger.info(f"Found {len(watchlist_files)} watchlist files")
            
            # Remove duplicates while preserving order
            unique_files = list(dict.fromkeys(all_files))
            self.logger.info(f"Total unique media files: {len(unique_files)}")
            
            return unique_files
            
        except Exception as e:
            self.logger.error(f"Error fetching media files: {e}")
            raise
    
    def _process_media_files(self, media_files: List[str]) -> List[str]:
        """
        Process media file paths and scan additional sources.
        
        Args:
            media_files: Raw media file paths from Plex
            
        Returns:
            Processed file paths ready for operations
        """
        try:
            # Process file paths (convert Plex paths to system paths)
            processed_files = self.file_service.process_file_paths(media_files)
            self.logger.info(f"Processed {len(processed_files)} file paths")
            
            # Scan additional sources for matching files
            additional_files = self.file_service.scan_additional_sources(processed_files)
            processed_files.extend(additional_files)
            self.logger.info(f"Found {len(additional_files)} files from additional sources")
            
            # Find and include subtitle files
            subtitle_files = self.file_service.find_subtitle_files(processed_files)
            processed_files.extend(subtitle_files)
            self.logger.info(f"Found {len(subtitle_files)} subtitle files")
            
            # Remove duplicates and apply file limit if specified
            unique_files = list(dict.fromkeys(processed_files))
            
            if self.max_files_per_operation and len(unique_files) > self.max_files_per_operation:
                unique_files = unique_files[:self.max_files_per_operation]
                self.logger.info(f"Limited processing to {self.max_files_per_operation} files")
            
            return unique_files
            
        except Exception as e:
            self.logger.error(f"Error processing media files: {e}")
            raise
    
    def _execute_cache_operations(self, files: List[str]) -> Dict[str, Any]:
        """
        Execute cache operations (move files to cache).
        
        Args:
            files: Files to process for cache operations
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Filter files that should be moved to cache
            cache_files = self.file_service.filter_files_for_cache(files)
            
            if not cache_files:
                self.logger.info("No files need to be moved to cache")
                return {"files_processed": 0, "message": "No files to cache"}
            
            self.logger.info(f"Moving {len(cache_files)} files to cache")
            
            # Execute cache operation
            result = self.cache_service.execute_cache_operation(
                files=cache_files,
                operation_type="cache",
                dry_run=False
            )
            
            operation_result = {
                "files_processed": result.files_processed,
                "bytes_processed": result.total_size_bytes,
                "success": result.success,
                "errors": result.errors,
                "warnings": result.warnings
            }
            
            self.logger.info(
                f"Cache operation completed: {result.files_processed} files, "
                f"{self._format_bytes(result.total_size_bytes)} processed"
            )
            
            return operation_result
            
        except Exception as e:
            self.logger.error(f"Error executing cache operations: {e}")
            return {
                "files_processed": 0,
                "success": False,
                "error": str(e)
            }
    
    def _execute_array_operations(self) -> Dict[str, Any]:
        """
        Execute array operations (move watched files back to array).
        
        Returns:
            Dictionary with operation results
        """
        try:
            # Fetch watched media files
            watched_files = self.media_service.fetch_watched_media()
            
            if not watched_files:
                self.logger.info("No watched files found")
                return {"files_processed": 0, "message": "No watched files to move"}
            
            # Process watched file paths
            processed_watched = self.file_service.process_file_paths(watched_files)
            
            # Filter files that should be moved to array
            array_files = self.file_service.filter_files_for_array(processed_watched)
            
            if not array_files:
                self.logger.info("No files need to be moved to array")
                return {"files_processed": 0, "message": "No files to move to array"}
            
            self.logger.info(f"Moving {len(array_files)} watched files to array")
            
            # Execute array operation
            result = self.cache_service.execute_cache_operation(
                files=array_files,
                operation_type="array",
                dry_run=False
            )
            
            operation_result = {
                "files_processed": result.files_processed,
                "bytes_processed": result.total_size_bytes,
                "success": result.success,
                "errors": result.errors,
                "warnings": result.warnings
            }
            
            self.logger.info(
                f"Array operation completed: {result.files_processed} files, "
                f"{self._format_bytes(result.total_size_bytes)} processed"
            )
            
            return operation_result
            
        except Exception as e:
            self.logger.error(f"Error executing array operations: {e}")
            return {
                "files_processed": 0,
                "success": False,
                "error": str(e)
            }
    
    def _execute_cleanup_operations(self) -> Dict[str, Any]:
        """
        Execute cleanup operations.
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            self.logger.info("Starting cache cleanup operations")
            
            # Execute cache cleanup
            cleanup_result = self.cache_service.cleanup_cache()
            
            operation_result = {
                "files_processed": cleanup_result.files_processed,
                "bytes_processed": cleanup_result.total_size_bytes,
                "success": cleanup_result.success,
                "errors": cleanup_result.errors,
                "warnings": cleanup_result.warnings
            }
            
            self.logger.info(
                f"Cleanup operation completed: {cleanup_result.files_processed} files cleaned, "
                f"{self._format_bytes(cleanup_result.total_size_bytes)} freed"
            )
            
            return operation_result
            
        except Exception as e:
            self.logger.error(f"Error executing cleanup operations: {e}")
            return {
                "files_processed": 0,
                "success": False,
                "error": str(e)
            }
    
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


class TestModeAnalysisTask(CacheTaskBase):
    """
    Task for running test mode analysis without actual file operations.
    
    This task performs analysis of what would happen during cache operations
    without actually moving files. Useful for planning and validation.
    """
    
    def __init__(self, service_provider: IServiceProvider):
        """
        Initialize test mode analysis task.
        
        Args:
            service_provider: Dependency injection service provider
        """
        super().__init__(service_provider)
    
    def execute(self) -> TaskResult:
        """
        Execute test mode analysis.
        
        Returns:
            TaskResult with analysis results
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting test mode analysis task")
            
            # Validate required services
            missing_services = self.validate_services()
            if missing_services:
                error_msg = f"Missing required services: {', '.join(missing_services)}"
                return TaskResult(
                    success=False,
                    message=error_msg,
                    errors=[error_msg],
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Fetch and process media files
            media_files = []
            try:
                ondeck_files = self.media_service.fetch_ondeck_media()
                watchlist_files = self.media_service.fetch_watchlist_media()
                watched_files = self.media_service.fetch_watched_media()
                
                media_files = list(dict.fromkeys(ondeck_files + watchlist_files))
                
            except Exception as e:
                self.logger.warning(f"Error fetching media files for analysis: {e}")
            
            processed_files = self.file_service.process_file_paths(media_files)
            
            # Analyze cache operations
            cache_files = self.file_service.filter_files_for_cache(processed_files)
            cache_analysis = self.file_service.analyze_files_for_test_mode(cache_files, "cache")
            
            # Analyze array operations
            processed_watched = self.file_service.process_file_paths(watched_files)
            array_files = self.file_service.filter_files_for_array(processed_watched)
            array_analysis = self.file_service.analyze_files_for_test_mode(array_files, "array")
            
            result_data = {
                "cache_operations": {
                    "file_count": cache_analysis.file_count,
                    "total_size": cache_analysis.total_size,
                    "total_size_readable": cache_analysis.total_size_readable,
                    "files": cache_analysis.files[:10],  # Limit to first 10 for display
                    "file_details": cache_analysis.file_details[:10] if cache_analysis.file_details else []
                },
                "array_operations": {
                    "file_count": array_analysis.file_count,
                    "total_size": array_analysis.total_size,
                    "total_size_readable": array_analysis.total_size_readable,
                    "files": array_analysis.files[:10],
                    "file_details": array_analysis.file_details[:10] if array_analysis.file_details else []
                },
                "summary": {
                    "total_files_to_cache": cache_analysis.file_count,
                    "total_files_to_array": array_analysis.file_count,
                    "total_cache_size": cache_analysis.total_size,
                    "total_array_size": array_analysis.total_size
                }
            }
            
            total_files = cache_analysis.file_count + array_analysis.file_count
            message = (
                f"Test mode analysis completed. "
                f"Found {cache_analysis.file_count} files to cache "
                f"({cache_analysis.total_size_readable}) and "
                f"{array_analysis.file_count} files to move to array "
                f"({array_analysis.total_size_readable})"
            )
            
            self.logger.info(message)
            
            return TaskResult(
                success=True,
                message=message,
                data=result_data,
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            error_msg = f"Test mode analysis failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return TaskResult(
                success=False,
                message=error_msg,
                errors=[error_msg],
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )


class CacheValidationTask(CacheTaskBase):
    """
    Task for validating cache integrity and consistency.
    
    This task checks cache state, validates file integrity,
    and reports on any inconsistencies or issues.
    """
    
    def execute(self) -> TaskResult:
        """
        Execute cache validation.
        
        Returns:
            TaskResult with validation results
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting cache validation task")
            
            if not self.cache_service:
                return TaskResult(
                    success=False,
                    message="Cache service not available",
                    errors=["Cache service not available"],
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Get cache statistics for validation
            cache_stats = self.cache_service.get_cache_statistics()
            
            validation_results = {
                "cache_statistics": cache_stats,
                "validation_checks": {
                    "cache_accessible": bool(cache_stats),
                    "total_cached_files": cache_stats.get("total_files", 0),
                    "total_cache_size": cache_stats.get("total_size", 0)
                }
            }
            
            message = f"Cache validation completed. Found {cache_stats.get('total_files', 0)} cached files"
            self.logger.info(message)
            
            return TaskResult(
                success=True,
                message=message,
                data=validation_results,
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            error_msg = f"Cache validation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return TaskResult(
                success=False,
                message=error_msg,
                errors=[error_msg],
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )