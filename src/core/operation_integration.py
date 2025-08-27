"""
Integration layer for updating existing operation handlers to use commands.

This module provides adapter classes and integration utilities to gradually
migrate existing PlexCacheUltra operations to use the new command pattern
while maintaining backward compatibility.

Classes:
- OperationCommandAdapter: Adapter for existing operations to commands
- CacheOperationHandler: Updated handler using commands
- LegacyOperationBridge: Bridge for legacy code compatibility
"""

import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

from .command_service import CommandService
from .commands.interfaces import ICommand, CommandContext, CommandResult, CommandPriority
from .commands.cache_commands import MoveToCache, MoveToArray, CopyToCache, DeleteFromCache, TestCacheOperation
from .interfaces import CacheOperationResult, TestModeAnalysis

logger = logging.getLogger(__name__)


class OperationCommandAdapter:
    """
    Adapter to convert existing operation results to command results.
    
    Provides a bridge between legacy operation interfaces and the new
    command pattern, enabling gradual migration while preserving
    existing functionality.
    """
    
    @staticmethod
    def cache_operation_to_command_result(cache_result: CacheOperationResult,
                                        command_type: str) -> CommandResult:
        """
        Convert CacheOperationResult to CommandResult.
        
        Args:
            cache_result: Legacy cache operation result
            command_type: Type of command that produced this result
            
        Returns:
            CommandResult equivalent
        """
        return CommandResult(
            success=cache_result.success,
            message=f"{command_type}: {cache_result.total_size_readable} processed",
            files_affected=[],  # Would need to be provided separately
            bytes_processed=cache_result.total_size_bytes,
            errors=cache_result.errors.copy(),
            warnings=cache_result.warnings.copy(),
            data={
                "files_processed": cache_result.files_processed,
                "operation_type": cache_result.operation_type,
                "legacy_result": cache_result.model_dump()
            }
        )
    
    @staticmethod
    def test_analysis_to_command_result(test_analysis: TestModeAnalysis) -> CommandResult:
        """
        Convert TestModeAnalysis to CommandResult.
        
        Args:
            test_analysis: Legacy test mode analysis
            
        Returns:
            CommandResult equivalent
        """
        return CommandResult(
            success=True,
            message=f"Analysis: {test_analysis.file_count} files ({test_analysis.total_size_readable})",
            files_affected=test_analysis.files.copy(),
            bytes_processed=test_analysis.total_size,
            data={
                "analysis": test_analysis.model_dump(),
                "test_mode": True,
                "operation_type": test_analysis.operation_type
            }
        )


class CacheOperationHandler:
    """
    Updated cache operation handler using the command pattern.
    
    Replaces direct cache operations with command-based operations,
    providing better error handling, logging, monitoring, and undo capabilities.
    """
    
    def __init__(self, command_service: CommandService):
        """
        Initialize cache operation handler.
        
        Args:
            command_service: Command service for executing operations
        """
        self.command_service = command_service
        logger.info("CacheOperationHandler initialized with command pattern")
    
    def move_files_to_cache(self, files: List[str],
                           source_directory: str,
                           cache_directory: str,
                           max_concurrent: Optional[int] = None,
                           create_symlinks: bool = False,
                           dry_run: bool = False,
                           priority: CommandPriority = CommandPriority.NORMAL) -> CommandResult:
        """
        Move files to cache using command pattern.
        
        Args:
            files: List of file paths to move
            source_directory: Source directory (array storage)
            cache_directory: Cache directory destination
            max_concurrent: Maximum concurrent operations
            create_symlinks: Whether to create symlinks after move
            dry_run: Whether to run in test mode
            priority: Command execution priority
            
        Returns:
            CommandResult with operation details
        """
        logger.info(f"Moving {len(files)} files to cache using command pattern")
        
        try:
            # Create move to cache command
            command = self.command_service.create_cache_command(
                "move_to_cache",
                files=files,
                source_directory=source_directory,
                cache_directory=cache_directory,
                max_concurrent=max_concurrent,
                create_symlinks=create_symlinks,
                priority=priority
            )
            
            # Create execution context
            context = CommandContext(
                dry_run=dry_run,
                services=self.command_service.service_provider,
                execution_settings={"operation_type": "move_to_cache"}
            )
            
            # Execute command
            result = self.command_service.execute_command(command, context)
            
            logger.info(f"Move to cache command completed: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to move files to cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Move to cache failed: {str(e)}",
                errors=[str(e)]
            )
    
    def move_files_to_array(self, files: List[str],
                           cache_directory: str,
                           array_directory: str,
                           max_concurrent: Optional[int] = None,
                           dry_run: bool = False,
                           priority: CommandPriority = CommandPriority.NORMAL) -> CommandResult:
        """
        Move files from cache to array using command pattern.
        
        Args:
            files: List of file paths to move from cache
            cache_directory: Source cache directory
            array_directory: Destination array directory
            max_concurrent: Maximum concurrent operations
            dry_run: Whether to run in test mode
            priority: Command execution priority
            
        Returns:
            CommandResult with operation details
        """
        logger.info(f"Moving {len(files)} files to array using command pattern")
        
        try:
            # Create move to array command
            command = self.command_service.create_cache_command(
                "move_to_array",
                files=files,
                cache_directory=cache_directory,
                array_directory=array_directory,
                max_concurrent=max_concurrent,
                priority=priority
            )
            
            # Create execution context
            context = CommandContext(
                dry_run=dry_run,
                services=self.command_service.service_provider,
                execution_settings={"operation_type": "move_to_array"}
            )
            
            # Execute command
            result = self.command_service.execute_command(command, context)
            
            logger.info(f"Move to array command completed: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to move files to array: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Move to array failed: {str(e)}",
                errors=[str(e)]
            )
    
    def copy_files_to_cache(self, files: List[str],
                           source_directory: str,
                           cache_directory: str,
                           max_concurrent: Optional[int] = None,
                           dry_run: bool = False,
                           priority: CommandPriority = CommandPriority.NORMAL) -> CommandResult:
        """
        Copy files to cache using command pattern.
        
        Args:
            files: List of file paths to copy
            source_directory: Source directory
            cache_directory: Cache directory destination
            max_concurrent: Maximum concurrent operations
            dry_run: Whether to run in test mode
            priority: Command execution priority
            
        Returns:
            CommandResult with operation details
        """
        logger.info(f"Copying {len(files)} files to cache using command pattern")
        
        try:
            # Create copy to cache command
            command = self.command_service.create_cache_command(
                "copy_to_cache",
                files=files,
                source_directory=source_directory,
                cache_directory=cache_directory,
                max_concurrent=max_concurrent,
                priority=priority
            )
            
            # Create execution context
            context = CommandContext(
                dry_run=dry_run,
                services=self.command_service.service_provider,
                execution_settings={"operation_type": "copy_to_cache"}
            )
            
            # Execute command
            result = self.command_service.execute_command(command, context)
            
            logger.info(f"Copy to cache command completed: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to copy files to cache: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Copy to cache failed: {str(e)}",
                errors=[str(e)]
            )
    
    def delete_cache_files(self, files: List[str],
                          max_concurrent: Optional[int] = None,
                          dry_run: bool = False,
                          priority: CommandPriority = CommandPriority.NORMAL) -> CommandResult:
        """
        Delete files from cache using command pattern.
        
        Args:
            files: List of cache file paths to delete
            max_concurrent: Maximum concurrent operations
            dry_run: Whether to run in test mode
            priority: Command execution priority
            
        Returns:
            CommandResult with operation details
        """
        logger.info(f"Deleting {len(files)} files from cache using command pattern")
        
        try:
            # Create delete from cache command
            command = self.command_service.create_cache_command(
                "delete_from_cache",
                files=files,
                max_concurrent=max_concurrent,
                priority=priority
            )
            
            # Create execution context
            context = CommandContext(
                dry_run=dry_run,
                services=self.command_service.service_provider,
                execution_settings={"operation_type": "delete_from_cache"}
            )
            
            # Execute command
            result = self.command_service.execute_command(command, context)
            
            logger.info(f"Delete from cache command completed: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete cache files: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Delete cache files failed: {str(e)}",
                errors=[str(e)]
            )
    
    def test_cache_operation(self, files: List[str],
                            operation_type: str = "cache") -> CommandResult:
        """
        Test cache operation without executing using command pattern.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation to test
            
        Returns:
            CommandResult with analysis details
        """
        logger.info(f"Testing {operation_type} operation on {len(files)} files")
        
        try:
            # Create test cache operation command
            command = self.command_service.create_cache_command(
                "test_cache_operation",
                files=files,
                operation_type=operation_type,
                priority=CommandPriority.LOW
            )
            
            # Create execution context (always dry run for test operations)
            context = CommandContext(
                dry_run=True,
                services=self.command_service.service_provider,
                execution_settings={"operation_type": "test"}
            )
            
            # Execute command
            result = self.command_service.execute_command(command, context)
            
            logger.info(f"Test cache operation completed: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to test cache operation: {str(e)}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Test cache operation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def batch_cache_operations(self, operations: List[Dict[str, Any]],
                              dry_run: bool = False) -> List[CommandResult]:
        """
        Execute multiple cache operations in batch.
        
        Args:
            operations: List of operation specifications
            dry_run: Whether to run in test mode
            
        Returns:
            List of CommandResult objects
            
        Example operations format:
            [
                {
                    "type": "move_to_cache",
                    "files": [...],
                    "source_directory": "...",
                    "cache_directory": "...",
                    "priority": "high"
                },
                {
                    "type": "cleanup_cache",
                    "max_age_hours": 168
                }
            ]
        """
        logger.info(f"Executing batch of {len(operations)} cache operations")
        
        results = []
        
        for i, op in enumerate(operations):
            try:
                op_type = op.pop("type", "unknown")
                priority_str = op.pop("priority", "normal")
                
                # Convert priority string to enum
                priority_map = {
                    "low": CommandPriority.LOW,
                    "normal": CommandPriority.NORMAL,
                    "high": CommandPriority.HIGH,
                    "critical": CommandPriority.CRITICAL
                }
                priority = priority_map.get(priority_str.lower(), CommandPriority.NORMAL)
                
                # Create command
                command = self.command_service.create_cache_command(op_type, priority=priority, **op)
                
                # Create execution context
                context = CommandContext(
                    dry_run=dry_run,
                    services=self.command_service.service_provider,
                    execution_settings={
                        "operation_type": "batch",
                        "batch_index": i,
                        "batch_size": len(operations)
                    }
                )
                
                # Execute command
                result = self.command_service.execute_command(command, context)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch operation {i} failed: {str(e)}")
                error_result = CommandResult(
                    success=False,
                    message=f"Batch operation {i} failed: {str(e)}",
                    errors=[str(e)],
                    metadata={"batch_index": i}
                )
                results.append(error_result)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch operations completed: {successful}/{len(operations)} successful")
        
        return results


class LegacyOperationBridge:
    """
    Bridge for maintaining compatibility with legacy operation code.
    
    Provides methods that match the legacy interfaces while internally
    using the new command pattern. This allows for gradual migration
    of existing code without breaking changes.
    """
    
    def __init__(self, cache_operation_handler: CacheOperationHandler):
        """
        Initialize legacy operation bridge.
        
        Args:
            cache_operation_handler: Command-based operation handler
        """
        self.handler = cache_operation_handler
        logger.info("LegacyOperationBridge initialized")
    
    def execute_cache_operation(self, files: List[str], operation_type: str,
                               dry_run: bool = False) -> CacheOperationResult:
        """
        Legacy-compatible cache operation execution.
        
        Args:
            files: Files to process
            operation_type: Type of operation ("cache", "array", "delete")
            dry_run: Whether to run in test mode
            
        Returns:
            CacheOperationResult for compatibility
        """
        try:
            # Map operation types to command methods
            if operation_type == "cache":
                result = self.handler.test_cache_operation(files, "cache") if dry_run else None
                # Would need actual cache/array directories from config
                if not dry_run:
                    result = self.handler.move_files_to_cache(
                        files=files,
                        source_directory="/array",  # Would come from config
                        cache_directory="/cache",   # Would come from config
                        dry_run=dry_run
                    )
            elif operation_type == "array":
                result = self.handler.test_cache_operation(files, "array") if dry_run else None
                if not dry_run:
                    result = self.handler.move_files_to_array(
                        files=files,
                        cache_directory="/cache",  # Would come from config
                        array_directory="/array",  # Would come from config
                        dry_run=dry_run
                    )
            elif operation_type == "delete":
                result = self.handler.delete_cache_files(files, dry_run=dry_run)
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")
            
            if not result:
                result = CommandResult(success=False, message="No result from operation")
            
            # Convert CommandResult back to CacheOperationResult
            return CacheOperationResult(
                success=result.success,
                files_processed=len(result.files_affected),
                total_size_bytes=result.bytes_processed,
                total_size_readable=self._format_file_size(result.bytes_processed),
                operation_type=operation_type,
                errors=result.errors,
                warnings=result.warnings
            )
            
        except Exception as e:
            logger.error(f"Legacy cache operation failed: {str(e)}")
            return CacheOperationResult(
                success=False,
                files_processed=0,
                total_size_bytes=0,
                total_size_readable="0 B",
                operation_type=operation_type,
                errors=[str(e)]
            )
    
    def analyze_cache_impact(self, files: List[str], operation_type: str = "cache") -> TestModeAnalysis:
        """
        Legacy-compatible cache impact analysis.
        
        Args:
            files: Files to analyze
            operation_type: Type of operation to analyze
            
        Returns:
            TestModeAnalysis for compatibility
        """
        try:
            result = self.handler.test_cache_operation(files, operation_type)
            
            if result.success and result.data and "analysis" in result.data:
                analysis_data = result.data["analysis"]
                return TestModeAnalysis(**analysis_data)
            else:
                # Create a basic analysis from command result
                return TestModeAnalysis(
                    files=result.files_affected,
                    total_size=result.bytes_processed,
                    total_size_readable=self._format_file_size(result.bytes_processed),
                    file_details=[],
                    operation_type=operation_type,
                    file_count=len(result.files_affected)
                )
                
        except Exception as e:
            logger.error(f"Legacy cache analysis failed: {str(e)}")
            return TestModeAnalysis(
                files=[],
                total_size=0,
                total_size_readable="0 B",
                file_details=[],
                operation_type=operation_type,
                file_count=0
            )
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"


# Convenience function for creating the complete operation handler setup
def create_operation_handler(command_service: CommandService) -> CacheOperationHandler:
    """
    Create a complete cache operation handler with command pattern support.
    
    Args:
        command_service: Configured command service
        
    Returns:
        CacheOperationHandler instance
    """
    return CacheOperationHandler(command_service)


def create_legacy_bridge(command_service: CommandService) -> LegacyOperationBridge:
    """
    Create a legacy compatibility bridge for existing code.
    
    Args:
        command_service: Configured command service
        
    Returns:
        LegacyOperationBridge instance
    """
    operation_handler = create_operation_handler(command_service)
    return LegacyOperationBridge(operation_handler)