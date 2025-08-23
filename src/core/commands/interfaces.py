"""
Command Pattern interfaces for PlexCacheUltra.

This module defines the core interfaces for the command pattern implementation,
providing contracts for command execution, undo operations, and command
management systems.

Key interfaces:
- ICommand: Basic command interface with execution
- IUndoableCommand: Commands that support undo operations  
- ICommandExecutor: Service for executing commands with management
- ICommandHistory: Command history tracking and navigation
- ICommandQueue: Command queuing and batch execution
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union, Callable, AsyncIterable
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class CommandStatus(Enum):
    """Status of command execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNDOING = "undoing"
    UNDONE = "undone"
    UNDO_FAILED = "undo_failed"


class CommandPriority(Enum):
    """Command execution priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class CommandResult(BaseModel):
    """
    Result of command execution.
    
    Attributes:
        success: Whether the command executed successfully
        message: Human-readable result message
        data: Additional result data specific to the command
        errors: List of error messages encountered
        warnings: List of warning messages
        files_affected: List of files affected by the operation
        bytes_processed: Number of bytes processed
        execution_time_seconds: Time taken for execution
        timestamp: When the execution completed
        metadata: Additional metadata about the execution
    """
    
    success: bool = Field(description="Whether command executed successfully")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional result data")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    files_affected: List[str] = Field(default_factory=list, description="Files affected by operation")
    bytes_processed: int = Field(default=0, description="Bytes processed")
    execution_time_seconds: Optional[float] = Field(default=None, description="Execution duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('bytes_processed')
    def validate_bytes_processed(cls, v):
        """Ensure bytes_processed is non-negative."""
        if v < 0:
            raise ValueError("bytes_processed must be non-negative")
        return v


class CommandMetadata(BaseModel):
    """
    Metadata for command tracking and management.
    
    Attributes:
        command_id: Unique identifier for the command
        command_type: Type/name of the command
        created_at: When the command was created
        created_by: Who/what created the command
        priority: Command execution priority
        tags: Tags for categorizing commands
        parent_command_id: ID of parent command for composite operations
        retry_count: Number of times command has been retried
        max_retries: Maximum number of retry attempts
        timeout_seconds: Command execution timeout
        dependencies: List of command IDs this command depends on
    """
    
    command_id: UUID = Field(default_factory=uuid4, description="Unique command identifier")
    command_type: str = Field(description="Type/name of the command")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: str = Field(default="system", description="Creator of the command")
    priority: CommandPriority = Field(default=CommandPriority.NORMAL, description="Execution priority")
    tags: List[str] = Field(default_factory=list, description="Command tags")
    parent_command_id: Optional[UUID] = Field(default=None, description="Parent command ID")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(default=None, description="Execution timeout")
    dependencies: List[UUID] = Field(default_factory=list, description="Dependency command IDs")
    
    @validator('retry_count', 'max_retries')
    def validate_retry_counts(cls, v):
        """Ensure retry counts are non-negative."""
        if v < 0:
            raise ValueError("Retry counts must be non-negative")
        return v

    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Ensure timeout is positive if specified."""
        if v is not None and v <= 0:
            raise ValueError("timeout_seconds must be positive")
        return v


class CommandContext(BaseModel):
    """
    Execution context for commands.
    
    Provides runtime context information and services needed
    for command execution, including service providers and
    execution settings.
    
    Attributes:
        dry_run: Whether to execute in dry-run mode
        user_id: User executing the command
        session_id: Execution session identifier
        environment: Execution environment information
        services: Service provider for dependency resolution
        progress_callback: Optional callback for progress updates
        cancellation_token: Token for checking cancellation requests
        execution_settings: Additional execution configuration
    """
    
    dry_run: bool = Field(default=False, description="Dry-run mode execution")
    user_id: Optional[str] = Field(default=None, description="Executing user ID")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    environment: Dict[str, Any] = Field(default_factory=dict, description="Environment info")
    services: Optional[Any] = Field(default=None, description="Service provider")  # IServiceProvider
    progress_callback: Optional[Callable[[float, str], None]] = Field(default=None, description="Progress callback")
    cancellation_token: Optional[Any] = Field(default=None, description="Cancellation token")
    execution_settings: Dict[str, Any] = Field(default_factory=dict, description="Execution settings")
    
    class Config:
        arbitrary_types_allowed = True


class ICommand(ABC):
    """
    Basic command interface.
    
    Defines the fundamental contract for all commands in the system.
    Commands encapsulate operations as objects, enabling queuing,
    logging, and management of operations.
    """

    @property
    @abstractmethod
    def metadata(self) -> CommandMetadata:
        """Get command metadata."""
        pass

    @property
    @abstractmethod
    def status(self) -> CommandStatus:
        """Get current command status."""
        pass

    @abstractmethod
    def can_execute(self, context: CommandContext) -> bool:
        """
        Check if the command can be executed in the given context.
        
        Args:
            context: Execution context
            
        Returns:
            True if command can be executed, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, context: CommandContext) -> CommandResult:
        """
        Execute the command.
        
        Args:
            context: Execution context providing services and settings
            
        Returns:
            CommandResult with execution details and outcomes
            
        Raises:
            CommandExecutionError: When command execution fails
            ValidationError: When command parameters are invalid
        """
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """
        Validate command parameters and state.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    @abstractmethod
    def get_affected_resources(self) -> List[str]:
        """
        Get list of resources that will be affected by this command.
        
        Returns:
            List of resource identifiers (file paths, IDs, etc.)
        """
        pass

    @abstractmethod
    def estimate_execution_time(self) -> Optional[float]:
        """
        Estimate command execution time in seconds.
        
        Returns:
            Estimated execution time in seconds, or None if unknown
        """
        pass

    @abstractmethod
    def get_progress(self) -> float:
        """
        Get current execution progress.
        
        Returns:
            Progress as a float between 0.0 and 1.0
        """
        pass


class IUndoableCommand(ICommand):
    """
    Interface for commands that support undo operations.
    
    Extends the basic command interface to support undoing
    operations, enabling rollback capabilities for critical
    operations like file movements.
    """

    @property
    @abstractmethod
    def can_undo(self) -> bool:
        """Check if the command can be undone."""
        pass

    @property
    @abstractmethod
    def undo_information(self) -> Optional[Dict[str, Any]]:
        """Get information needed to undo the command."""
        pass

    @abstractmethod
    def undo(self, context: CommandContext) -> CommandResult:
        """
        Undo the effects of the command.
        
        Args:
            context: Execution context for undo operation
            
        Returns:
            CommandResult with undo operation details
            
        Raises:
            UndoNotSupportedError: When undo is not supported or possible
            UndoExecutionError: When undo operation fails
        """
        pass

    @abstractmethod
    def store_undo_information(self, execution_result: CommandResult) -> None:
        """
        Store information needed for undo operation.
        
        Called after successful execution to capture state
        needed for potential undo operations.
        
        Args:
            execution_result: Result of the original execution
        """
        pass


class ICommandExecutor(ABC):
    """
    Interface for command execution management.
    
    Provides services for executing commands with proper
    lifecycle management, error handling, and monitoring.
    """

    @abstractmethod
    def execute_command(self, command: ICommand, context: Optional[CommandContext] = None) -> CommandResult:
        """
        Execute a single command.
        
        Args:
            command: Command to execute
            context: Optional execution context
            
        Returns:
            CommandResult with execution details
        """
        pass

    @abstractmethod
    def execute_commands(self, commands: List[ICommand], 
                        context: Optional[CommandContext] = None,
                        parallel: bool = False) -> List[CommandResult]:
        """
        Execute multiple commands.
        
        Args:
            commands: Commands to execute
            context: Optional execution context
            parallel: Whether to execute commands in parallel
            
        Returns:
            List of CommandResult objects
        """
        pass

    @abstractmethod
    def can_execute_command(self, command: ICommand, context: Optional[CommandContext] = None) -> bool:
        """
        Check if a command can be executed.
        
        Args:
            command: Command to check
            context: Optional execution context
            
        Returns:
            True if command can be executed
        """
        pass

    @abstractmethod
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get command execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        pass


class ICommandHistory(ABC):
    """
    Interface for command history management.
    
    Provides functionality for tracking executed commands,
    enabling undo/redo operations, and maintaining audit trails.
    """

    @abstractmethod
    def add_command(self, command: ICommand, result: CommandResult) -> None:
        """
        Add a command and its result to history.
        
        Args:
            command: The executed command
            result: The execution result
        """
        pass

    @abstractmethod
    def get_history(self, limit: Optional[int] = None, 
                   offset: int = 0,
                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get command execution history.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            filters: Optional filters to apply
            
        Returns:
            List of history entries
        """
        pass

    @abstractmethod
    def can_undo(self) -> bool:
        """Check if there are commands that can be undone."""
        pass

    @abstractmethod
    def can_redo(self) -> bool:
        """Check if there are commands that can be redone."""
        pass

    @abstractmethod
    def undo_last_command(self, context: Optional[CommandContext] = None) -> Optional[CommandResult]:
        """
        Undo the last executed command.
        
        Args:
            context: Optional execution context
            
        Returns:
            CommandResult if undo was performed, None if nothing to undo
        """
        pass

    @abstractmethod
    def redo_next_command(self, context: Optional[CommandContext] = None) -> Optional[CommandResult]:
        """
        Redo the next command in history.
        
        Args:
            context: Optional execution context
            
        Returns:
            CommandResult if redo was performed, None if nothing to redo
        """
        pass

    @abstractmethod
    def clear_history(self, before_timestamp: Optional[datetime] = None) -> int:
        """
        Clear command history.
        
        Args:
            before_timestamp: Only clear entries before this timestamp
            
        Returns:
            Number of entries cleared
        """
        pass

    @abstractmethod
    def get_command_by_id(self, command_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific command from history by ID.
        
        Args:
            command_id: Command identifier
            
        Returns:
            Command history entry or None if not found
        """
        pass


class ICommandQueue(ABC):
    """
    Interface for command queue management.
    
    Provides functionality for queuing commands, batch execution,
    priority management, and queue monitoring.
    """

    @abstractmethod
    def enqueue_command(self, command: ICommand, priority: Optional[CommandPriority] = None) -> UUID:
        """
        Add a command to the execution queue.
        
        Args:
            command: Command to queue
            priority: Optional priority override
            
        Returns:
            Unique queue entry identifier
        """
        pass

    @abstractmethod
    def dequeue_command(self, timeout_seconds: Optional[float] = None) -> Optional[ICommand]:
        """
        Get the next command from the queue.
        
        Args:
            timeout_seconds: Maximum time to wait for a command
            
        Returns:
            Next command to execute, or None if timeout/empty
        """
        pass

    @abstractmethod
    def peek_next_command(self) -> Optional[ICommand]:
        """
        Peek at the next command without removing it.
        
        Returns:
            Next command or None if queue is empty
        """
        pass

    @abstractmethod
    def cancel_command(self, command_id: UUID) -> bool:
        """
        Cancel a queued command.
        
        Args:
            command_id: ID of command to cancel
            
        Returns:
            True if command was cancelled, False if not found or executing
        """
        pass

    @abstractmethod
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status and statistics.
        
        Returns:
            Dictionary with queue status information
        """
        pass

    @abstractmethod
    def get_queued_commands(self, limit: Optional[int] = None) -> List[ICommand]:
        """
        Get list of queued commands.
        
        Args:
            limit: Maximum number of commands to return
            
        Returns:
            List of queued commands
        """
        pass

    @abstractmethod
    def clear_queue(self, command_type_filter: Optional[str] = None) -> int:
        """
        Clear the command queue.
        
        Args:
            command_type_filter: Only clear commands of this type
            
        Returns:
            Number of commands cleared
        """
        pass

    @abstractmethod
    def pause_queue(self) -> None:
        """Pause queue processing."""
        pass

    @abstractmethod
    def resume_queue(self) -> None:
        """Resume queue processing."""
        pass

    @property
    @abstractmethod
    def is_paused(self) -> bool:
        """Check if queue processing is paused."""
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """Get current queue size."""
        pass


# Exception classes for command operations
class CommandError(Exception):
    """Base exception for command-related errors."""
    pass


class CommandExecutionError(CommandError):
    """Raised when command execution fails."""
    
    def __init__(self, command: ICommand, message: str, inner_exception: Optional[Exception] = None):
        self.command = command
        self.inner_exception = inner_exception
        super().__init__(f"Command '{command.metadata.command_type}' execution failed: {message}")


class UndoNotSupportedError(CommandError):
    """Raised when undo is requested for a command that doesn't support it."""
    pass


class UndoExecutionError(CommandError):
    """Raised when undo operation fails."""
    
    def __init__(self, command: IUndoableCommand, message: str, inner_exception: Optional[Exception] = None):
        self.command = command
        self.inner_exception = inner_exception
        super().__init__(f"Undo for command '{command.metadata.command_type}' failed: {message}")


class CommandValidationError(CommandError):
    """Raised when command validation fails."""
    
    def __init__(self, command: ICommand, validation_errors: List[str]):
        self.command = command
        self.validation_errors = validation_errors
        errors_str = "; ".join(validation_errors)
        super().__init__(f"Command '{command.metadata.command_type}' validation failed: {errors_str}")


class CommandTimeoutError(CommandError):
    """Raised when command execution times out."""
    
    def __init__(self, command: ICommand, timeout_seconds: int):
        self.command = command
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Command '{command.metadata.command_type}' timed out after {timeout_seconds} seconds")


class CommandCancelledError(CommandError):
    """Raised when command execution is cancelled."""
    
    def __init__(self, command: ICommand):
        self.command = command
        super().__init__(f"Command '{command.metadata.command_type}' was cancelled")