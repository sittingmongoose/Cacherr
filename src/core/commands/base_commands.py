"""
Base command implementations for PlexCacheUltra.

This module provides base implementations for the command pattern interfaces,
offering common functionality that specific command implementations can inherit.
These base classes handle common patterns like validation, progress tracking,
and error handling.

Classes:
- BaseCommand: Basic command implementation with common functionality
- BaseUndoableCommand: Base for commands that support undo operations
- CompositeCacheCommand: Command that combines multiple cache operations
"""

import logging
import time
from abc import abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from uuid import UUID

from .interfaces import (
    ICommand, IUndoableCommand, CommandResult, CommandStatus, 
    CommandMetadata, CommandContext, CommandPriority,
    CommandExecutionError, CommandValidationError
)

logger = logging.getLogger(__name__)


class BaseCommand(ICommand):
    """
    Base implementation for commands with common functionality.
    
    Provides standard implementations for metadata management,
    validation patterns, progress tracking, and error handling.
    Subclasses need to implement the core execution logic.
    
    Attributes:
        _metadata: Command metadata information
        _status: Current command execution status
        _progress: Current execution progress (0.0 to 1.0)
        _validation_errors: List of validation errors
        _start_time: Command execution start time
        _end_time: Command execution end time
    """
    
    def __init__(self, command_type: str, priority: CommandPriority = CommandPriority.NORMAL,
                 timeout_seconds: Optional[int] = None, max_retries: int = 3,
                 tags: Optional[List[str]] = None):
        """
        Initialize base command.
        
        Args:
            command_type: Type identifier for the command
            priority: Execution priority
            timeout_seconds: Maximum execution time
            max_retries: Maximum retry attempts
            tags: Optional tags for categorization
        """
        self._metadata = CommandMetadata(
            command_type=command_type,
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            tags=tags or []
        )
        self._status = CommandStatus.PENDING
        self._progress = 0.0
        self._validation_errors: List[str] = []
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._affected_resources: List[str] = []
        
        logger.debug(f"Created command {self._metadata.command_type} with ID {self._metadata.command_id}")
    
    @property
    def metadata(self) -> CommandMetadata:
        """Get command metadata."""
        return self._metadata
    
    @property 
    def status(self) -> CommandStatus:
        """Get current command status."""
        return self._status
    
    def get_progress(self) -> float:
        """Get current execution progress."""
        return self._progress
    
    def can_execute(self, context: CommandContext) -> bool:
        """
        Check if command can be executed.
        
        Base implementation checks validation and status.
        Subclasses can override for additional checks.
        
        Args:
            context: Execution context
            
        Returns:
            True if command can be executed
        """
        if self._status not in [CommandStatus.PENDING, CommandStatus.FAILED]:
            return False
        
        validation_errors = self.validate()
        if validation_errors:
            logger.warning(f"Command {self.metadata.command_type} validation failed: {validation_errors}")
            return False
        
        return True
    
    def validate(self) -> List[str]:
        """
        Validate command parameters and state.
        
        Base implementation checks basic metadata validity.
        Subclasses should override to add specific validation.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not self._metadata.command_type:
            errors.append("Command type is required")
        
        if self._metadata.timeout_seconds is not None and self._metadata.timeout_seconds <= 0:
            errors.append("Timeout must be positive")
        
        if self._metadata.max_retries < 0:
            errors.append("Max retries must be non-negative")
        
        # Add subclass-specific validation
        errors.extend(self._validate_specific())
        
        self._validation_errors = errors
        return errors
    
    @abstractmethod
    def _validate_specific(self) -> List[str]:
        """
        Perform command-specific validation.
        
        Returns:
            List of validation error messages
        """
        pass
    
    def execute(self, context: CommandContext) -> CommandResult:
        """
        Execute the command with proper lifecycle management.
        
        Handles status tracking, progress updates, timing, and error handling.
        Subclasses implement _execute_internal for the actual operation.
        
        Args:
            context: Execution context
            
        Returns:
            CommandResult with execution details
        """
        if not self.can_execute(context):
            validation_errors = self.validate()
            raise CommandValidationError(self, validation_errors)
        
        self._status = CommandStatus.EXECUTING
        self._start_time = datetime.utcnow()
        self._progress = 0.0
        
        logger.info(f"Executing command {self.metadata.command_type} (ID: {self.metadata.command_id})")
        
        try:
            # Execute the command-specific logic
            result = self._execute_internal(context)
            
            # Update progress and status
            self._progress = 1.0
            self._status = CommandStatus.COMPLETED if result.success else CommandStatus.FAILED
            self._end_time = datetime.utcnow()
            
            # Calculate execution time
            if self._start_time and self._end_time:
                execution_time = (self._end_time - self._start_time).total_seconds()
                result.execution_time_seconds = execution_time
            
            # Update result with command metadata
            result.metadata.update({
                "command_id": str(self.metadata.command_id),
                "command_type": self.metadata.command_type,
                "status": self._status.value,
                "retry_count": self.metadata.retry_count
            })
            
            logger.info(
                f"Command {self.metadata.command_type} completed "
                f"({'success' if result.success else 'failed'}) "
                f"in {result.execution_time_seconds:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self._status = CommandStatus.FAILED
            self._end_time = datetime.utcnow()
            
            logger.error(
                f"Command {self.metadata.command_type} failed: {str(e)}", 
                exc_info=True
            )
            
            # Return failed result
            return CommandResult(
                success=False,
                message=f"Command execution failed: {str(e)}",
                errors=[str(e)],
                execution_time_seconds=(
                    (self._end_time - self._start_time).total_seconds()
                    if self._start_time else None
                ),
                metadata={
                    "command_id": str(self.metadata.command_id),
                    "command_type": self.metadata.command_type,
                    "status": self._status.value,
                    "exception_type": type(e).__name__
                }
            )
    
    @abstractmethod
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """
        Execute the command-specific logic.
        
        Subclasses must implement this method to provide the actual
        command execution behavior.
        
        Args:
            context: Execution context
            
        Returns:
            CommandResult with execution details
        """
        pass
    
    def get_affected_resources(self) -> List[str]:
        """
        Get resources that will be affected by this command.
        
        Base implementation returns stored resources.
        Subclasses can override for dynamic resource discovery.
        
        Returns:
            List of resource identifiers
        """
        return self._affected_resources.copy()
    
    def estimate_execution_time(self) -> Optional[float]:
        """
        Estimate command execution time.
        
        Base implementation returns None (unknown).
        Subclasses can override with specific estimation logic.
        
        Returns:
            Estimated execution time in seconds, or None
        """
        return None
    
    def _update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """
        Update command execution progress.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional progress message
        """
        self._progress = max(0.0, min(1.0, progress))
        
        if message:
            logger.debug(f"Command {self.metadata.command_type} progress: {progress:.1%} - {message}")
    
    def _add_affected_resource(self, resource: str) -> None:
        """
        Add a resource to the affected resources list.
        
        Args:
            resource: Resource identifier to add
        """
        if resource and resource not in self._affected_resources:
            self._affected_resources.append(resource)


class BaseUndoableCommand(BaseCommand, IUndoableCommand):
    """
    Base implementation for undoable commands.
    
    Extends BaseCommand to provide undo functionality with
    proper state management and validation.
    
    Attributes:
        _undo_information: Data needed to undo the command
        _undo_executed: Whether undo has been executed
    """
    
    def __init__(self, command_type: str, priority: CommandPriority = CommandPriority.NORMAL,
                 timeout_seconds: Optional[int] = None, max_retries: int = 3,
                 tags: Optional[List[str]] = None):
        """
        Initialize base undoable command.
        
        Args:
            command_type: Type identifier for the command
            priority: Execution priority
            timeout_seconds: Maximum execution time
            max_retries: Maximum retry attempts
            tags: Optional tags for categorization
        """
        super().__init__(command_type, priority, timeout_seconds, max_retries, tags)
        self._undo_information: Optional[Dict[str, Any]] = None
        self._undo_executed = False
    
    @property
    def can_undo(self) -> bool:
        """
        Check if command can be undone.
        
        Base implementation checks if command was successfully executed
        and undo hasn't been performed yet.
        
        Returns:
            True if command can be undone
        """
        return (
            self._status == CommandStatus.COMPLETED and
            not self._undo_executed and
            self._undo_information is not None
        )
    
    @property
    def undo_information(self) -> Optional[Dict[str, Any]]:
        """Get undo information."""
        return self._undo_information.copy() if self._undo_information else None
    
    def store_undo_information(self, execution_result: CommandResult) -> None:
        """
        Store information needed for undo operation.
        
        Base implementation stores basic execution data.
        Subclasses should override to store command-specific undo data.
        
        Args:
            execution_result: Result of the original execution
        """
        self._undo_information = {
            "execution_result": execution_result.dict(),
            "execution_time": self._end_time.isoformat() if self._end_time else None,
            "affected_resources": self.get_affected_resources(),
            "command_metadata": self.metadata.dict()
        }
        
        # Store command-specific undo information
        command_specific_undo = self._store_undo_information_specific(execution_result)
        if command_specific_undo:
            self._undo_information.update(command_specific_undo)
        
        logger.debug(f"Stored undo information for command {self.metadata.command_type}")
    
    @abstractmethod
    def _store_undo_information_specific(self, execution_result: CommandResult) -> Optional[Dict[str, Any]]:
        """
        Store command-specific undo information.
        
        Args:
            execution_result: Result of the original execution
            
        Returns:
            Dictionary with command-specific undo data, or None
        """
        pass
    
    def undo(self, context: CommandContext) -> CommandResult:
        """
        Undo the effects of the command.
        
        Handles undo lifecycle management and delegates to
        subclass-specific undo logic.
        
        Args:
            context: Execution context for undo operation
            
        Returns:
            CommandResult with undo operation details
        """
        if not self.can_undo:
            return CommandResult(
                success=False,
                message="Command cannot be undone",
                errors=["Command is not in a state that supports undo"],
                metadata={"command_id": str(self.metadata.command_id)}
            )
        
        self._status = CommandStatus.UNDOING
        undo_start_time = datetime.utcnow()
        
        logger.info(f"Undoing command {self.metadata.command_type} (ID: {self.metadata.command_id})")
        
        try:
            # Execute undo-specific logic
            result = self._undo_internal(context)
            
            if result.success:
                self._status = CommandStatus.UNDONE
                self._undo_executed = True
                logger.info(f"Successfully undid command {self.metadata.command_type}")
            else:
                self._status = CommandStatus.UNDO_FAILED
                logger.error(f"Failed to undo command {self.metadata.command_type}")
            
            # Calculate undo execution time
            undo_end_time = datetime.utcnow()
            undo_time = (undo_end_time - undo_start_time).total_seconds()
            result.execution_time_seconds = undo_time
            
            # Update result metadata
            result.metadata.update({
                "command_id": str(self.metadata.command_id),
                "command_type": self.metadata.command_type,
                "operation": "undo",
                "status": self._status.value
            })
            
            return result
            
        except Exception as e:
            self._status = CommandStatus.UNDO_FAILED
            
            logger.error(f"Undo failed for command {self.metadata.command_type}: {str(e)}", exc_info=True)
            
            return CommandResult(
                success=False,
                message=f"Undo operation failed: {str(e)}",
                errors=[str(e)],
                execution_time_seconds=(datetime.utcnow() - undo_start_time).total_seconds(),
                metadata={
                    "command_id": str(self.metadata.command_id),
                    "command_type": self.metadata.command_type,
                    "operation": "undo",
                    "status": self._status.value,
                    "exception_type": type(e).__name__
                }
            )
    
    @abstractmethod
    def _undo_internal(self, context: CommandContext) -> CommandResult:
        """
        Execute the command-specific undo logic.
        
        Subclasses must implement this method to provide the actual
        undo behavior using the stored undo information.
        
        Args:
            context: Execution context for undo operation
            
        Returns:
            CommandResult with undo execution details
        """
        pass


class CompositeCacheCommand(BaseCommand):
    """
    Composite command that combines multiple cache operations.
    
    Allows grouping related cache operations into a single command
    that can be executed as a unit with proper error handling and
    rollback capabilities.
    
    Attributes:
        _commands: List of child commands to execute
        _stop_on_failure: Whether to stop execution on first failure
        _executed_commands: List of successfully executed commands
    """
    
    def __init__(self, commands: List[ICommand], command_type: str = "composite_cache_operation",
                 stop_on_failure: bool = True, priority: CommandPriority = CommandPriority.NORMAL):
        """
        Initialize composite cache command.
        
        Args:
            commands: List of commands to execute
            command_type: Type identifier for this composite command
            stop_on_failure: Whether to stop on first command failure
            priority: Execution priority
        """
        super().__init__(command_type, priority)
        self._commands = commands.copy()
        self._stop_on_failure = stop_on_failure
        self._executed_commands: List[ICommand] = []
        
        # Aggregate affected resources from child commands
        for command in self._commands:
            self._affected_resources.extend(command.get_affected_resources())
    
    def _validate_specific(self) -> List[str]:
        """
        Validate composite command and all child commands.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not self._commands:
            errors.append("Composite command must contain at least one child command")
        
        # Validate each child command
        for i, command in enumerate(self._commands):
            command_errors = command.validate()
            for error in command_errors:
                errors.append(f"Command {i} ({command.metadata.command_type}): {error}")
        
        return errors
    
    def _execute_internal(self, context: CommandContext) -> CommandResult:
        """
        Execute all child commands in sequence.
        
        Args:
            context: Execution context
            
        Returns:
            CommandResult with composite execution details
        """
        results = []
        total_files_affected = []
        total_bytes_processed = 0
        all_errors = []
        all_warnings = []
        
        logger.info(f"Executing composite command with {len(self._commands)} child commands")
        
        for i, command in enumerate(self._commands):
            try:
                # Update progress
                progress = i / len(self._commands)
                self._update_progress(progress, f"Executing command {i+1}/{len(self._commands)}")
                
                # Execute child command
                result = command.execute(context)
                results.append(result)
                
                # Track successful executions
                if result.success:
                    self._executed_commands.append(command)
                    total_files_affected.extend(result.files_affected)
                    total_bytes_processed += result.bytes_processed
                else:
                    all_errors.extend(result.errors)
                
                all_warnings.extend(result.warnings)
                
                # Stop on failure if configured
                if not result.success and self._stop_on_failure:
                    logger.warning(f"Composite command stopping due to failure in command {i+1}")
                    break
                    
            except Exception as e:
                error_msg = f"Child command {i+1} failed: {str(e)}"
                all_errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                
                if self._stop_on_failure:
                    break
        
        # Calculate overall success
        successful_commands = len(self._executed_commands)
        total_commands = len(self._commands)
        success_rate = successful_commands / total_commands if total_commands > 0 else 0
        overall_success = success_rate > 0.5 or (success_rate == 1.0 and not all_errors)
        
        return CommandResult(
            success=overall_success,
            message=f"Composite command completed: {successful_commands}/{total_commands} commands successful",
            files_affected=total_files_affected,
            bytes_processed=total_bytes_processed,
            errors=all_errors,
            warnings=all_warnings,
            data={
                "child_results": [r.dict() for r in results],
                "success_rate": success_rate,
                "successful_commands": successful_commands,
                "total_commands": total_commands
            }
        )
    
    def estimate_execution_time(self) -> Optional[float]:
        """
        Estimate execution time based on child commands.
        
        Returns:
            Sum of child command execution estimates, or None if unknown
        """
        total_time = 0.0
        has_estimates = False
        
        for command in self._commands:
            estimate = command.estimate_execution_time()
            if estimate is not None:
                total_time += estimate
                has_estimates = True
        
        return total_time if has_estimates else None
    
    def get_child_commands(self) -> List[ICommand]:
        """
        Get list of child commands.
        
        Returns:
            Copy of child commands list
        """
        return self._commands.copy()
    
    def get_executed_commands(self) -> List[ICommand]:
        """
        Get list of successfully executed commands.
        
        Returns:
            Copy of executed commands list
        """
        return self._executed_commands.copy()