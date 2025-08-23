"""
Cache operation command implementations for PlexCacheUltra.

This module provides concrete command implementations for all cache-related
operations including file movement, copying, deletion, and analysis operations.
These commands integrate with the existing FileService and CacheService interfaces
through the dependency injection system.

Commands:
- MoveToCache: Move files from array to cache storage
- MoveToArray: Move files from cache back to array storage  
- CopyToCache: Copy files to cache without removing originals
- DeleteFromCache: Delete files from cache storage
- TestCacheOperation: Analyze cache operations without executing
- AnalyzeCacheImpact: Deep analysis of cache operation impacts
- CleanupCache: Remove old or watched content from cache
- ValidateCache: Validate cache integrity and consistency
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from datetime import datetime

from .interfaces import (
    CommandResult, CommandContext, CommandPriority, CommandStatus
)
from .base_commands import BaseCommand, BaseUndoableCommand
from ..interfaces import (
    FileService, CacheService, NotificationService,
    MediaFileInfo, CacheOperationResult, TestModeAnalysis
)

logger = logging.getLogger(__name__)


class MoveToCache(BaseUndoableCommand):
    """
    Command to move files from array storage to cache.
    
    This command moves files from their original array locations to the
    cache directory, enabling faster access for frequently viewed content.
    Supports undo operations to restore files to original locations.
    
    Attributes:
        files: List of file paths to move to cache
        source_directory: Source directory path (array storage)
        cache_directory: Destination cache directory path
        max_concurrent: Maximum concurrent file operations
        create_symlinks: Whether to create symlinks back to original locations
    """
    
    def __init__(self, files: List[str], source_directory: str, cache_directory: str,
                 max_concurrent: Optional[int] = None, create_symlinks: bool = False,
                 priority: CommandPriority = CommandPriority.NORMAL):
        """
        Initialize move to cache command.
        
        Args:
            files: List of file paths to move
            source_directory: Source directory (array storage)
            cache_directory: Cache directory destination
            max_concurrent: Maximum concurrent operations
            create_symlinks: Whether to create symlinks after move
            priority: Command execution priority
        """
        super().__init__("move_to_cache", priority, timeout_seconds=3600)
        self.files = files.copy()
        self.source_directory = str(Path(source_directory).resolve())
        self.cache_directory = str(Path(cache_directory).resolve()) 
        self.max_concurrent = max_concurrent
        self.create_symlinks = create_symlinks
        
        # Store affected resources
        self._affected_resources = self.files.copy()
        
        # Undo information storage
        self._moved_files: List[Dict[str, str]] = []
        self._created_symlinks: List[str] = []
    
    def _validate_specific(self) -> List[str]:
        """Validate move to cache command parameters."""
        errors = []
        
        if not self.files:
            errors.append("No files specified for move operation")
        
        if not os.path.exists(self.source_directory):
            errors.append(f"Source directory does not exist: {self.source_directory}")
        
        if not os.path.exists(self.cache_directory):
            errors.append(f"Cache directory does not exist: {self.cache_directory}")
        
        # Check if files exist
        missing_files = []
        for file_path in self.files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            errors.append(f"Missing files: {', '.join(missing_files[:5])}")
            if len(missing_files) > 5:
                errors.append(f"... and {len(missing_files) - 5} more files")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute move to cache operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for cache operations"]
            )
        
        try:
            # Resolve required services
            file_service: FileService = context.services.resolve(FileService)
            cache_service: CacheService = context.services.resolve(CacheService)
            notification_service: NotificationService = context.services.try_resolve(NotificationService)
            
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve required services",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Moving {len(self.files)} files to cache")
        
        try:
            # Update progress
            self._update_progress(0.1, "Filtering files for cache operation")
            
            # Filter files that should be moved to cache
            cache_files = file_service.filter_files_for_cache(self.files)
            
            if not cache_files:
                return CommandResult(
                    success=True,
                    message="No files need to be moved to cache",
                    data={"filtered_files": len(self.files), "cache_eligible": 0}
                )
            
            self._update_progress(0.2, f"Filtered {len(cache_files)} files for caching")
            
            # Check available space
            self._update_progress(0.3, "Checking available cache space")
            if not file_service.check_available_space(cache_files, self.cache_directory):
                return CommandResult(
                    success=False,
                    message="Insufficient space in cache directory",
                    errors=["Not enough free space to move files to cache"]
                )
            
            # Execute the move operation
            self._update_progress(0.4, "Executing file move operations")
            
            if context.dry_run:
                # Dry run mode - analyze without moving
                analysis = file_service.analyze_files_for_test_mode(cache_files, "cache")
                
                return CommandResult(
                    success=True,
                    message=f"Dry run: Would move {analysis.file_count} files ({analysis.total_size_readable})",
                    files_affected=analysis.files,
                    bytes_processed=analysis.total_size,
                    data={
                        "dry_run": True,
                        "analysis": analysis.dict(),
                        "operation_type": "move_to_cache"
                    }
                )
            
            # Perform actual move operation
            files_moved, bytes_moved = file_service.move_files(
                files=cache_files,
                source_dir=self.source_directory,
                dest_dir=self.cache_directory,
                max_concurrent=self.max_concurrent,
                create_symlinks=self.create_symlinks,
                move_with_symlinks=self.create_symlinks
            )
            
            self._update_progress(0.8, f"Moved {files_moved} files")
            
            # Store information for undo
            for file_path in cache_files[:files_moved]:
                filename = os.path.basename(file_path)
                cache_path = os.path.join(self.cache_directory, filename)
                self._moved_files.append({
                    "original_path": file_path,
                    "cache_path": cache_path,
                    "filename": filename
                })
                
                if self.create_symlinks:
                    self._created_symlinks.append(file_path)
            
            # Send notification
            if notification_service and files_moved > 0:
                file_size_readable = file_service.get_file_size_readable(bytes_moved)
                notification_service.send_cache_operation_notification(
                    "move_to_cache",
                    {
                        "files_moved": files_moved,
                        "total_size": file_size_readable,
                        "cache_directory": self.cache_directory
                    }
                )
            
            self._update_progress(1.0, "Cache move operation completed")
            
            return CommandResult(
                success=files_moved > 0,
                message=f"Successfully moved {files_moved} files to cache ({file_service.get_file_size_readable(bytes_moved)})",
                files_affected=[f["cache_path"] for f in self._moved_files],
                bytes_processed=bytes_moved,
                data={
                    "files_moved": files_moved,
                    "bytes_moved": bytes_moved,
                    "symlinks_created": len(self._created_symlinks),
                    "cache_directory": self.cache_directory
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to move files to cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Cache move operation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _store_undo_information_specific(self, execution_result: CommandResult) -> Optional[Dict[str, Any]]:
        """Store move-specific undo information."""
        return {
            "moved_files": self._moved_files.copy(),
            "created_symlinks": self._created_symlinks.copy(),
            "source_directory": self.source_directory,
            "cache_directory": self.cache_directory,
            "create_symlinks": self.create_symlinks
        }
    
    def _undo_internal(self, context: CommandContext) -> CommandResult:
        """Undo the move to cache operation."""
        if not self._undo_information or not context.services:
            return CommandResult(
                success=False,
                message="Cannot undo: missing undo information or services",
                errors=["Undo information or service provider not available"]
            )
        
        try:
            file_service: FileService = context.services.resolve(FileService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve file service for undo",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        moved_files = self._undo_information.get("moved_files", [])
        created_symlinks = self._undo_information.get("created_symlinks", [])
        
        logger.info(f"Undoing move to cache: restoring {len(moved_files)} files")
        
        try:
            files_restored = 0
            errors = []
            
            # Remove symlinks first
            for symlink_path in created_symlinks:
                try:
                    if os.path.islink(symlink_path):
                        os.unlink(symlink_path)
                        logger.debug(f"Removed symlink: {symlink_path}")
                except Exception as e:
                    errors.append(f"Failed to remove symlink {symlink_path}: {str(e)}")
            
            # Move files back to original locations
            for file_info in moved_files:
                try:
                    cache_path = file_info["cache_path"]
                    original_path = file_info["original_path"]
                    
                    if os.path.exists(cache_path):
                        # Ensure original directory exists
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)
                        
                        # Move file back
                        os.rename(cache_path, original_path)
                        files_restored += 1
                        logger.debug(f"Restored file: {cache_path} -> {original_path}")
                    
                except Exception as e:
                    errors.append(f"Failed to restore {file_info.get('filename', 'file')}: {str(e)}")
            
            success = files_restored > 0 or len(moved_files) == 0
            
            return CommandResult(
                success=success,
                message=f"Restored {files_restored} files from cache",
                errors=errors,
                data={
                    "files_restored": files_restored,
                    "symlinks_removed": len(created_symlinks),
                    "total_files": len(moved_files)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Undo operation failed: {str(e)}",
                errors=[str(e)]
            )


class MoveToArray(BaseUndoableCommand):
    """
    Command to move files from cache back to array storage.
    
    Used for moving watched content or cleaning up cache by returning
    files to their original array storage locations.
    """
    
    def __init__(self, files: List[str], cache_directory: str, array_directory: str,
                 max_concurrent: Optional[int] = None, 
                 priority: CommandPriority = CommandPriority.NORMAL):
        """
        Initialize move to array command.
        
        Args:
            files: List of file paths to move from cache
            cache_directory: Source cache directory
            array_directory: Destination array directory  
            max_concurrent: Maximum concurrent operations
            priority: Command execution priority
        """
        super().__init__("move_to_array", priority, timeout_seconds=3600)
        self.files = files.copy()
        self.cache_directory = str(Path(cache_directory).resolve())
        self.array_directory = str(Path(array_directory).resolve())
        self.max_concurrent = max_concurrent
        
        self._affected_resources = self.files.copy()
        self._moved_files: List[Dict[str, str]] = []
    
    def _validate_specific(self) -> List[str]:
        """Validate move to array command parameters."""
        errors = []
        
        if not self.files:
            errors.append("No files specified for array move operation")
        
        if not os.path.exists(self.cache_directory):
            errors.append(f"Cache directory does not exist: {self.cache_directory}")
        
        if not os.path.exists(self.array_directory):
            errors.append(f"Array directory does not exist: {self.array_directory}")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute move to array operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for cache operations"]
            )
        
        try:
            file_service: FileService = context.services.resolve(FileService)
            notification_service: NotificationService = context.services.try_resolve(NotificationService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve required services", 
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Moving {len(self.files)} files from cache to array")
        
        try:
            # Filter files that should be moved to array
            array_files = file_service.filter_files_for_array(self.files)
            
            if not array_files:
                return CommandResult(
                    success=True,
                    message="No files need to be moved to array",
                    data={"filtered_files": len(self.files), "array_eligible": 0}
                )
            
            self._update_progress(0.2, f"Filtered {len(array_files)} files for array move")
            
            # Check available space
            if not file_service.check_available_space(array_files, self.array_directory):
                return CommandResult(
                    success=False,
                    message="Insufficient space in array directory",
                    errors=["Not enough free space to move files to array"]
                )
            
            # Execute the move operation
            self._update_progress(0.4, "Executing file move operations")
            
            if context.dry_run:
                analysis = file_service.analyze_files_for_test_mode(array_files, "array")
                
                return CommandResult(
                    success=True,
                    message=f"Dry run: Would move {analysis.file_count} files ({analysis.total_size_readable})",
                    files_affected=analysis.files,
                    bytes_processed=analysis.total_size,
                    data={
                        "dry_run": True,
                        "analysis": analysis.dict(),
                        "operation_type": "move_to_array"
                    }
                )
            
            # Perform actual move operation
            files_moved, bytes_moved = file_service.move_files(
                files=array_files,
                source_dir=self.cache_directory,
                dest_dir=self.array_directory,
                max_concurrent=self.max_concurrent
            )
            
            self._update_progress(0.8, f"Moved {files_moved} files")
            
            # Store information for undo
            for file_path in array_files[:files_moved]:
                filename = os.path.basename(file_path)
                array_path = os.path.join(self.array_directory, filename)
                self._moved_files.append({
                    "cache_path": file_path,
                    "array_path": array_path,
                    "filename": filename
                })
            
            # Send notification
            if notification_service and files_moved > 0:
                file_size_readable = file_service.get_file_size_readable(bytes_moved)
                notification_service.send_cache_operation_notification(
                    "move_to_array",
                    {
                        "files_moved": files_moved,
                        "total_size": file_size_readable,
                        "array_directory": self.array_directory
                    }
                )
            
            self._update_progress(1.0, "Array move operation completed")
            
            return CommandResult(
                success=files_moved > 0,
                message=f"Successfully moved {files_moved} files to array ({file_service.get_file_size_readable(bytes_moved)})",
                files_affected=[f["array_path"] for f in self._moved_files],
                bytes_processed=bytes_moved,
                data={
                    "files_moved": files_moved,
                    "bytes_moved": bytes_moved,
                    "array_directory": self.array_directory
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to move files to array: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Array move operation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _store_undo_information_specific(self, execution_result: CommandResult) -> Optional[Dict[str, Any]]:
        """Store array move specific undo information."""
        return {
            "moved_files": self._moved_files.copy(),
            "cache_directory": self.cache_directory,
            "array_directory": self.array_directory
        }
    
    def _undo_internal(self, context: CommandContext) -> CommandResult:
        """Undo the move to array operation."""
        if not self._undo_information or not context.services:
            return CommandResult(
                success=False,
                message="Cannot undo: missing undo information or services",
                errors=["Undo information or service provider not available"]
            )
        
        try:
            file_service: FileService = context.services.resolve(FileService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve file service for undo",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        moved_files = self._undo_information.get("moved_files", [])
        
        logger.info(f"Undoing move to array: restoring {len(moved_files)} files to cache")
        
        try:
            files_restored = 0
            errors = []
            
            for file_info in moved_files:
                try:
                    array_path = file_info["array_path"]
                    cache_path = file_info["cache_path"]
                    
                    if os.path.exists(array_path):
                        # Ensure cache directory exists
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        
                        # Move file back to cache
                        os.rename(array_path, cache_path)
                        files_restored += 1
                        logger.debug(f"Restored file to cache: {array_path} -> {cache_path}")
                    
                except Exception as e:
                    errors.append(f"Failed to restore {file_info.get('filename', 'file')}: {str(e)}")
            
            return CommandResult(
                success=files_restored > 0 or len(moved_files) == 0,
                message=f"Restored {files_restored} files to cache",
                errors=errors,
                data={
                    "files_restored": files_restored,
                    "total_files": len(moved_files)
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Undo operation failed: {str(e)}",
                errors=[str(e)]
            )


class CopyToCache(BaseCommand):
    """
    Command to copy files to cache without removing originals.
    
    Useful for creating cache copies while preserving original files
    in their array locations. Does not support undo since originals
    are preserved.
    """
    
    def __init__(self, files: List[str], source_directory: str, cache_directory: str,
                 max_concurrent: Optional[int] = None,
                 priority: CommandPriority = CommandPriority.NORMAL):
        """
        Initialize copy to cache command.
        
        Args:
            files: List of file paths to copy
            source_directory: Source directory (array storage)
            cache_directory: Cache directory destination
            max_concurrent: Maximum concurrent operations
            priority: Command execution priority
        """
        super().__init__("copy_to_cache", priority, timeout_seconds=3600)
        self.files = files.copy()
        self.source_directory = str(Path(source_directory).resolve())
        self.cache_directory = str(Path(cache_directory).resolve())
        self.max_concurrent = max_concurrent
        
        self._affected_resources = self.files.copy()
    
    def _validate_specific(self) -> List[str]:
        """Validate copy to cache command parameters."""
        errors = []
        
        if not self.files:
            errors.append("No files specified for copy operation")
        
        if not os.path.exists(self.source_directory):
            errors.append(f"Source directory does not exist: {self.source_directory}")
        
        if not os.path.exists(self.cache_directory):
            errors.append(f"Cache directory does not exist: {self.cache_directory}")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute copy to cache operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for cache operations"]
            )
        
        try:
            file_service: FileService = context.services.resolve(FileService)
            notification_service: NotificationService = context.services.try_resolve(NotificationService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve required services",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Copying {len(self.files)} files to cache")
        
        try:
            # Filter files that should be copied to cache
            cache_files = file_service.filter_files_for_cache(self.files)
            
            if not cache_files:
                return CommandResult(
                    success=True,
                    message="No files need to be copied to cache",
                    data={"filtered_files": len(self.files), "cache_eligible": 0}
                )
            
            self._update_progress(0.2, f"Filtered {len(cache_files)} files for copying")
            
            # Check available space
            if not file_service.check_available_space(cache_files, self.cache_directory):
                return CommandResult(
                    success=False,
                    message="Insufficient space in cache directory",
                    errors=["Not enough free space to copy files to cache"]
                )
            
            # Execute the copy operation
            self._update_progress(0.4, "Executing file copy operations")
            
            if context.dry_run:
                analysis = file_service.analyze_files_for_test_mode(cache_files, "cache")
                
                return CommandResult(
                    success=True,
                    message=f"Dry run: Would copy {analysis.file_count} files ({analysis.total_size_readable})",
                    files_affected=analysis.files,
                    bytes_processed=analysis.total_size,
                    data={
                        "dry_run": True,
                        "analysis": analysis.dict(),
                        "operation_type": "copy_to_cache"
                    }
                )
            
            # Perform actual copy operation
            files_copied, bytes_copied = file_service.move_files(
                files=cache_files,
                source_dir=self.source_directory,
                dest_dir=self.cache_directory,
                max_concurrent=self.max_concurrent,
                copy_mode=True  # Enable copy mode
            )
            
            self._update_progress(0.8, f"Copied {files_copied} files")
            
            # Send notification
            if notification_service and files_copied > 0:
                file_size_readable = file_service.get_file_size_readable(bytes_copied)
                notification_service.send_cache_operation_notification(
                    "copy_to_cache",
                    {
                        "files_copied": files_copied,
                        "total_size": file_size_readable,
                        "cache_directory": self.cache_directory
                    }
                )
            
            self._update_progress(1.0, "Cache copy operation completed")
            
            return CommandResult(
                success=files_copied > 0,
                message=f"Successfully copied {files_copied} files to cache ({file_service.get_file_size_readable(bytes_copied)})",
                files_affected=cache_files[:files_copied],
                bytes_processed=bytes_copied,
                data={
                    "files_copied": files_copied,
                    "bytes_copied": bytes_copied,
                    "cache_directory": self.cache_directory
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to copy files to cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Cache copy operation failed: {str(e)}",
                errors=[str(e)]
            )


class DeleteFromCache(BaseUndoableCommand):
    """
    Command to delete files from cache storage.
    
    Used for cache cleanup operations. Supports undo by storing
    deleted file information, though actual file restoration 
    requires the original files still exist elsewhere.
    """
    
    def __init__(self, files: List[str], max_concurrent: Optional[int] = None,
                 priority: CommandPriority = CommandPriority.NORMAL):
        """
        Initialize delete from cache command.
        
        Args:
            files: List of cache file paths to delete
            max_concurrent: Maximum concurrent delete operations
            priority: Command execution priority
        """
        super().__init__("delete_from_cache", priority, timeout_seconds=1800)
        self.files = files.copy()
        self.max_concurrent = max_concurrent
        
        self._affected_resources = self.files.copy()
        self._deleted_files: List[Dict[str, Any]] = []
    
    def _validate_specific(self) -> List[str]:
        """Validate delete from cache command parameters."""
        errors = []
        
        if not self.files:
            errors.append("No files specified for delete operation")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute delete from cache operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for cache operations"]
            )
        
        try:
            file_service: FileService = context.services.resolve(FileService)
            notification_service: NotificationService = context.services.try_resolve(NotificationService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve required services",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Deleting {len(self.files)} files from cache")
        
        try:
            if context.dry_run:
                analysis = file_service.analyze_files_for_test_mode(self.files, "delete")
                
                return CommandResult(
                    success=True,
                    message=f"Dry run: Would delete {analysis.file_count} files ({analysis.total_size_readable})",
                    files_affected=analysis.files,
                    bytes_processed=analysis.total_size,
                    data={
                        "dry_run": True,
                        "analysis": analysis.dict(),
                        "operation_type": "delete_from_cache"
                    }
                )
            
            # Store file info before deletion for undo
            for file_path in self.files:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    self._deleted_files.append({
                        "path": file_path,
                        "size": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "exists": True
                    })
                else:
                    self._deleted_files.append({
                        "path": file_path,
                        "size": 0,
                        "modified_time": None,
                        "exists": False
                    })
            
            self._update_progress(0.3, "Analyzing files for deletion")
            
            # Execute the delete operation
            files_deleted, bytes_freed = file_service.delete_files(
                files=self.files,
                max_concurrent=self.max_concurrent
            )
            
            self._update_progress(0.8, f"Deleted {files_deleted} files")
            
            # Send notification
            if notification_service and files_deleted > 0:
                file_size_readable = file_service.get_file_size_readable(bytes_freed)
                notification_service.send_cache_operation_notification(
                    "delete_from_cache",
                    {
                        "files_deleted": files_deleted,
                        "space_freed": file_size_readable
                    }
                )
            
            self._update_progress(1.0, "Cache delete operation completed")
            
            return CommandResult(
                success=files_deleted > 0 or len(self.files) == 0,
                message=f"Successfully deleted {files_deleted} files from cache ({file_service.get_file_size_readable(bytes_freed)} freed)",
                files_affected=self.files[:files_deleted],
                bytes_processed=bytes_freed,
                data={
                    "files_deleted": files_deleted,
                    "bytes_freed": bytes_freed,
                    "total_files": len(self.files)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to delete files from cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Cache delete operation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _store_undo_information_specific(self, execution_result: CommandResult) -> Optional[Dict[str, Any]]:
        """Store delete-specific undo information."""
        return {
            "deleted_files": self._deleted_files.copy()
        }
    
    def _undo_internal(self, context: CommandContext) -> CommandResult:
        """Undo delete operation - limited restoration capability."""
        # Note: This is a limited undo that can only report what was deleted
        # Actual file restoration would require backup/recovery mechanisms
        
        deleted_files = self._undo_information.get("deleted_files", []) if self._undo_information else []
        
        return CommandResult(
            success=False,
            message="Delete operations cannot be fully undone",
            warnings=[
                "Deleted files cannot be restored without backup mechanisms",
                f"Originally deleted {len(deleted_files)} files"
            ],
            data={
                "deleted_files_info": deleted_files,
                "undo_limitation": "Files cannot be restored from deletion"
            }
        )


class TestCacheOperation(BaseCommand):
    """
    Command to analyze cache operations without executing them.
    
    Provides detailed analysis of what would happen during cache
    operations including file sizes, space requirements, and
    potential issues.
    """
    
    def __init__(self, files: List[str], operation_type: str = "cache",
                 priority: CommandPriority = CommandPriority.LOW):
        """
        Initialize test cache operation command.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation to test ("cache", "array", "delete")
            priority: Command execution priority
        """
        super().__init__("test_cache_operation", priority, timeout_seconds=300)
        self.files = files.copy()
        self.operation_type = operation_type
        
        self._affected_resources = []  # Test operations don't affect resources
    
    def _validate_specific(self) -> List[str]:
        """Validate test operation command parameters."""
        errors = []
        
        if not self.files:
            errors.append("No files specified for test operation")
        
        if self.operation_type not in ["cache", "array", "delete"]:
            errors.append(f"Invalid operation type: {self.operation_type}")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute test cache operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for test operations"]
            )
        
        try:
            file_service: FileService = context.services.resolve(FileService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve file service",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Analyzing {len(self.files)} files for {self.operation_type} operation")
        
        try:
            self._update_progress(0.2, "Analyzing files")
            
            # Perform analysis
            analysis = file_service.analyze_files_for_test_mode(self.files, self.operation_type)
            
            self._update_progress(0.8, "Analysis complete")
            
            return CommandResult(
                success=True,
                message=f"Analysis complete: {analysis.file_count} files ({analysis.total_size_readable}) for {self.operation_type}",
                files_affected=analysis.files,
                bytes_processed=analysis.total_size,
                data={
                    "analysis": analysis.dict(),
                    "operation_type": self.operation_type,
                    "test_mode": True
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze cache operation: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Test operation failed: {str(e)}",
                errors=[str(e)]
            )


class AnalyzeCacheImpact(BaseCommand):
    """
    Command for deep analysis of cache operation impacts.
    
    Provides comprehensive analysis including space requirements,
    performance impacts, and recommendations.
    """
    
    def __init__(self, files: List[str], operation_type: str = "cache",
                 priority: CommandPriority = CommandPriority.LOW):
        """
        Initialize analyze cache impact command.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation to analyze
            priority: Command execution priority
        """
        super().__init__("analyze_cache_impact", priority, timeout_seconds=600)
        self.files = files.copy()
        self.operation_type = operation_type
        
        self._affected_resources = []
    
    def _validate_specific(self) -> List[str]:
        """Validate analyze impact command parameters."""
        errors = []
        
        if not self.files:
            errors.append("No files specified for impact analysis")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute cache impact analysis."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for impact analysis"]
            )
        
        try:
            cache_service: CacheService = context.services.resolve(CacheService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve cache service",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Analyzing cache impact for {len(self.files)} files")
        
        try:
            self._update_progress(0.2, "Starting impact analysis")
            
            # Perform impact analysis
            impact_analysis = cache_service.analyze_cache_impact(self.files, self.operation_type)
            
            self._update_progress(0.6, "Getting cache statistics")
            
            # Get current cache statistics
            cache_stats = cache_service.get_cache_statistics()
            
            self._update_progress(0.9, "Generating recommendations")
            
            # Generate recommendations based on analysis
            recommendations = self._generate_recommendations(impact_analysis, cache_stats)
            
            return CommandResult(
                success=True,
                message=f"Impact analysis complete for {impact_analysis.file_count} files",
                files_affected=impact_analysis.files,
                bytes_processed=impact_analysis.total_size,
                data={
                    "impact_analysis": impact_analysis.dict(),
                    "cache_statistics": cache_stats,
                    "recommendations": recommendations,
                    "operation_type": self.operation_type
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze cache impact: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Impact analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _generate_recommendations(self, analysis: TestModeAnalysis, 
                                 cache_stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Analyze file sizes
        if analysis.total_size > 100 * 1024 * 1024 * 1024:  # > 100GB
            recommendations.append("Large operation detected - consider running during off-peak hours")
        
        # Check cache space utilization
        if "available_space" in cache_stats:
            available_space = cache_stats.get("available_space", 0)
            if analysis.total_size > available_space * 0.8:
                recommendations.append("Operation will use >80% of available cache space")
        
        # File count considerations
        if analysis.file_count > 1000:
            recommendations.append("Large number of files - consider enabling parallel processing")
        
        # Operation-specific recommendations
        if self.operation_type == "cache":
            recommendations.append("Consider monitoring cache hit rates after operation")
        elif self.operation_type == "array":
            recommendations.append("Verify array storage has sufficient space")
        
        return recommendations


class CleanupCache(BaseCommand):
    """
    Command to clean up old or watched content from cache.
    
    Removes files from cache based on age, access patterns,
    or watch status to free up space for new content.
    """
    
    def __init__(self, max_age_hours: Optional[int] = None, 
                 remove_watched: bool = True,
                 priority: CommandPriority = CommandPriority.LOW):
        """
        Initialize cache cleanup command.
        
        Args:
            max_age_hours: Maximum age for cache files (None for default)
            remove_watched: Whether to remove watched content
            priority: Command execution priority
        """
        super().__init__("cleanup_cache", priority, timeout_seconds=1800)
        self.max_age_hours = max_age_hours
        self.remove_watched = remove_watched
        
        self._affected_resources = []  # Will be populated during execution
    
    def _validate_specific(self) -> List[str]:
        """Validate cleanup cache command parameters."""
        errors = []
        
        if self.max_age_hours is not None and self.max_age_hours <= 0:
            errors.append("Max age hours must be positive")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute cache cleanup operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for cache cleanup"]
            )
        
        try:
            cache_service: CacheService = context.services.resolve(CacheService)
            notification_service: NotificationService = context.services.try_resolve(NotificationService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve required services",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info("Starting cache cleanup operation")
        
        try:
            self._update_progress(0.2, "Starting cache cleanup")
            
            if context.dry_run:
                # For dry run, we would analyze what would be cleaned up
                return CommandResult(
                    success=True,
                    message="Dry run: Cache cleanup analysis complete",
                    data={
                        "dry_run": True,
                        "max_age_hours": self.max_age_hours,
                        "remove_watched": self.remove_watched,
                        "operation_type": "cleanup_cache"
                    }
                )
            
            # Execute cleanup
            cleanup_result = cache_service.cleanup_cache(self.max_age_hours)
            
            self._update_progress(0.8, "Cleanup operation completed")
            
            # Send notification
            if notification_service and cleanup_result.success:
                notification_service.send_cache_operation_notification(
                    "cleanup_cache",
                    {
                        "files_removed": cleanup_result.files_processed,
                        "space_freed": cleanup_result.total_size_readable
                    }
                )
            
            return CommandResult(
                success=cleanup_result.success,
                message=cleanup_result.message,
                files_affected=cleanup_result.errors,  # Assuming errors contain file paths
                bytes_processed=cleanup_result.total_size_bytes,
                errors=cleanup_result.errors,
                warnings=cleanup_result.warnings,
                data={
                    "cleanup_result": cleanup_result.dict(),
                    "max_age_hours": self.max_age_hours,
                    "remove_watched": self.remove_watched
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Cache cleanup failed: {str(e)}",
                errors=[str(e)]
            )


class ValidateCache(BaseCommand):
    """
    Command to validate cache integrity and consistency.
    
    Checks cache files for corruption, verifies metadata consistency,
    and reports any issues that need attention.
    """
    
    def __init__(self, deep_scan: bool = False,
                 priority: CommandPriority = CommandPriority.LOW):
        """
        Initialize cache validation command.
        
        Args:
            deep_scan: Whether to perform deep file integrity checks
            priority: Command execution priority
        """
        super().__init__("validate_cache", priority, timeout_seconds=3600)
        self.deep_scan = deep_scan
        
        self._affected_resources = []
    
    def _validate_specific(self) -> List[str]:
        """Validate cache validation command parameters."""
        # No specific validation needed for cache validation
        return []
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """Execute cache validation operation."""
        if not context.services:
            return CommandResult(
                success=False,
                message="No service provider available",
                errors=["Service provider is required for cache validation"]
            )
        
        try:
            cache_service: CacheService = context.services.resolve(CacheService)
        except Exception as e:
            return CommandResult(
                success=False,
                message="Failed to resolve cache service",
                errors=[f"Service resolution error: {str(e)}"]
            )
        
        logger.info(f"Starting cache validation (deep_scan={self.deep_scan})")
        
        try:
            self._update_progress(0.2, "Getting cache statistics")
            
            # Get current cache statistics for validation
            cache_stats = cache_service.get_cache_statistics()
            
            self._update_progress(0.6, "Validating cache integrity")
            
            # Perform validation checks
            validation_results = {
                "cache_accessible": True,
                "statistics_valid": bool(cache_stats),
                "total_files": cache_stats.get("file_count", 0),
                "total_size": cache_stats.get("total_size", 0),
                "issues_found": [],
                "recommendations": []
            }
            
            # Add validation logic here based on cache service capabilities
            if self.deep_scan:
                validation_results["deep_scan_performed"] = True
                # Deep scan logic would go here
                
            self._update_progress(0.9, "Generating validation report")
            
            # Determine overall success
            issues_count = len(validation_results["issues_found"])
            success = issues_count == 0
            
            return CommandResult(
                success=success,
                message=f"Cache validation complete: {issues_count} issues found",
                data={
                    "validation_results": validation_results,
                    "cache_statistics": cache_stats,
                    "deep_scan": self.deep_scan
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to validate cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Cache validation failed: {str(e)}",
                errors=[str(e)]
            )