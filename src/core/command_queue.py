"""
Command queue implementation for Cacherr.

This module provides a comprehensive command queue system for managing
command execution with priority handling, dependency resolution, and
concurrent processing capabilities.

Classes:
- CommandQueueEntry: Internal representation of queued commands
- CommandQueue: Thread-safe priority queue for commands
- CommandExecutionManager: High-level command execution coordination
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set, Callable
from uuid import UUID, uuid4
from queue import PriorityQueue, Empty
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field

from pydantic import BaseModel

from .commands.interfaces import (
    ICommand, ICommandQueue, ICommandExecutor, CommandResult, CommandStatus,
    CommandPriority, CommandContext, CommandExecutionError, CommandTimeoutError,
    CommandCancelledError
)

logger = logging.getLogger(__name__)


@dataclass
class CommandQueueEntry:
    """
    Internal representation of a queued command.
    
    Attributes:
        priority: Command execution priority (higher values = higher priority)
        queue_time: When the command was queued
        command: The command to execute
        queue_id: Unique identifier for this queue entry
        dependencies: Set of command IDs this command depends on
        retry_count: Number of times this command has been retried
        last_error: Last error message if command failed
    """
    priority: int
    queue_time: datetime
    command: ICommand
    queue_id: UUID = field(default_factory=uuid4)
    dependencies: Set[UUID] = field(default_factory=set)
    retry_count: int = 0
    last_error: Optional[str] = None
    
    def __lt__(self, other: 'CommandQueueEntry') -> bool:
        """Compare entries for priority queue ordering."""
        # Higher priority values come first
        if self.priority != other.priority:
            return self.priority > other.priority
        # Earlier queue times come first for same priority
        return self.queue_time < other.queue_time


class CommandQueueStatus(BaseModel):
    """Status information for the command queue."""
    
    total_queued: int
    pending_commands: int
    executing_commands: int
    completed_commands: int
    failed_commands: int
    cancelled_commands: int
    is_paused: bool
    is_processing: bool
    average_execution_time: Optional[float]
    queue_start_time: Optional[datetime]
    last_activity_time: Optional[datetime]


class CommandQueue(ICommandQueue):
    """
    Thread-safe priority queue for command management.
    
    Provides a priority-based queue with dependency resolution,
    cancellation support, and comprehensive status tracking.
    
    Attributes:
        max_size: Maximum queue size (0 for unlimited)
        default_priority: Default priority for commands without explicit priority
    """
    
    def __init__(self, max_size: int = 0, 
                 default_priority: CommandPriority = CommandPriority.NORMAL):
        """
        Initialize command queue.
        
        Args:
            max_size: Maximum queue size (0 for unlimited)
            default_priority: Default priority for commands
        """
        self._queue = PriorityQueue(maxsize=max_size)
        self._lock = threading.RLock()
        self._paused = False
        self._processing = False
        
        # Command tracking
        self._queued_commands: Dict[UUID, CommandQueueEntry] = {}
        self._executing_commands: Dict[UUID, CommandQueueEntry] = {}
        self._completed_commands: Dict[UUID, CommandQueueEntry] = {}
        self._cancelled_commands: Set[UUID] = set()
        
        # Dependency tracking
        self._dependency_graph: Dict[UUID, Set[UUID]] = {}
        self._reverse_dependencies: Dict[UUID, Set[UUID]] = {}
        
        # Statistics
        self._queue_start_time: Optional[datetime] = None
        self._last_activity_time: Optional[datetime] = None
        self._execution_times: List[float] = []
        self._max_execution_history = 100
        
        self.default_priority = default_priority
        
        logger.info("CommandQueue initialized")
    
    def enqueue_command(self, command: ICommand, 
                       priority: Optional[CommandPriority] = None) -> UUID:
        """
        Add a command to the execution queue.
        
        Args:
            command: Command to queue
            priority: Optional priority override
            
        Returns:
            Unique queue entry identifier
            
        Raises:
            ValueError: If queue is full or command is invalid
        """
        if not command:
            raise ValueError("Command cannot be None")
        
        # Use command's priority or override
        cmd_priority = priority or command.metadata.priority
        priority_value = cmd_priority.value
        
        # Create queue entry
        entry = CommandQueueEntry(
            priority=priority_value,
            queue_time=datetime.utcnow(),
            command=command,
            dependencies=set(command.metadata.dependencies)
        )
        
        with self._lock:
            try:
                # Check if queue is full
                if self._queue.full():
                    raise ValueError("Command queue is full")
                
                # Add to queue
                self._queue.put_nowait(entry)
                
                # Track the command
                self._queued_commands[entry.queue_id] = entry
                
                # Update dependency graph
                if entry.dependencies:
                    self._dependency_graph[entry.queue_id] = entry.dependencies.copy()
                    for dep_id in entry.dependencies:
                        if dep_id not in self._reverse_dependencies:
                            self._reverse_dependencies[dep_id] = set()
                        self._reverse_dependencies[dep_id].add(entry.queue_id)
                
                # Update statistics
                if not self._queue_start_time:
                    self._queue_start_time = datetime.utcnow()
                self._last_activity_time = datetime.utcnow()
                
                logger.debug(f"Enqueued command {command.metadata.command_type} "
                           f"with priority {cmd_priority.name} (ID: {entry.queue_id})")
                
                return entry.queue_id
                
            except Exception as e:
                logger.error(f"Failed to enqueue command: {str(e)}")
                raise
    
    def dequeue_command(self, timeout_seconds: Optional[float] = None) -> Optional[ICommand]:
        """
        Get the next command from the queue.
        
        Args:
            timeout_seconds: Maximum time to wait for a command
            
        Returns:
            Next command to execute, or None if timeout/empty/paused
        """
        if self._paused:
            return None
        
        try:
            # Get next entry from priority queue
            entry = self._queue.get(timeout=timeout_seconds)
            
            with self._lock:
                # Check if command was cancelled
                if entry.queue_id in self._cancelled_commands:
                    self._cancelled_commands.discard(entry.queue_id)
                    self._queued_commands.pop(entry.queue_id, None)
                    logger.debug(f"Skipping cancelled command {entry.queue_id}")
                    return None
                
                # Check dependencies
                if not self._are_dependencies_satisfied(entry.queue_id):
                    # Re-queue the command for later
                    self._queue.put_nowait(entry)
                    logger.debug(f"Re-queuing command {entry.queue_id} due to unsatisfied dependencies")
                    return None
                
                # Move from queued to executing
                self._queued_commands.pop(entry.queue_id, None)
                self._executing_commands[entry.queue_id] = entry
                
                self._last_activity_time = datetime.utcnow()
                
                logger.debug(f"Dequeued command {entry.command.metadata.command_type} "
                           f"(ID: {entry.queue_id})")
                
                return entry.command
                
        except Empty:
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue command: {str(e)}")
            return None
    
    def peek_next_command(self) -> Optional[ICommand]:
        """
        Peek at the next command without removing it.
        
        Returns:
            Next command or None if queue is empty
        """
        if self._paused or self._queue.empty():
            return None
        
        try:
            # This is a bit tricky since PriorityQueue doesn't have peek
            # We'll need to get and put back
            entry = self._queue.get_nowait()
            self._queue.put_nowait(entry)
            
            # Check if command is cancelled
            if entry.queue_id in self._cancelled_commands:
                return None
            
            return entry.command
            
        except Empty:
            return None
        except Exception as e:
            logger.error(f"Failed to peek at next command: {str(e)}")
            return None
    
    def cancel_command(self, command_id: UUID) -> bool:
        """
        Cancel a queued command.
        
        Args:
            command_id: ID of command to cancel (queue_id or command metadata ID)
            
        Returns:
            True if command was cancelled, False if not found or executing
        """
        with self._lock:
            # Check if it's a queued command (by queue_id)
            if command_id in self._queued_commands:
                self._cancelled_commands.add(command_id)
                logger.info(f"Cancelled queued command {command_id}")
                return True
            
            # Check if it's a command by metadata ID
            for queue_id, entry in self._queued_commands.items():
                if entry.command.metadata.command_id == command_id:
                    self._cancelled_commands.add(queue_id)
                    logger.info(f"Cancelled queued command by metadata ID {command_id}")
                    return True
            
            # Can't cancel executing commands (would need different mechanism)
            if command_id in self._executing_commands:
                logger.warning(f"Cannot cancel executing command {command_id}")
                return False
            
            logger.debug(f"Command {command_id} not found for cancellation")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status and statistics.
        
        Returns:
            Dictionary with queue status information
        """
        with self._lock:
            # Calculate average execution time
            avg_execution_time = None
            if self._execution_times:
                avg_execution_time = sum(self._execution_times) / len(self._execution_times)
            
            status = CommandQueueStatus(
                total_queued=len(self._queued_commands),
                pending_commands=self._queue.qsize(),
                executing_commands=len(self._executing_commands),
                completed_commands=len(self._completed_commands),
                failed_commands=sum(1 for e in self._completed_commands.values() 
                                   if e.last_error is not None),
                cancelled_commands=len(self._cancelled_commands),
                is_paused=self._paused,
                is_processing=self._processing,
                average_execution_time=avg_execution_time,
                queue_start_time=self._queue_start_time,
                last_activity_time=self._last_activity_time
            )
            
            return status.model_dump()
    
    def get_queued_commands(self, limit: Optional[int] = None) -> List[ICommand]:
        """
        Get list of queued commands.
        
        Args:
            limit: Maximum number of commands to return
            
        Returns:
            List of queued commands
        """
        with self._lock:
            commands = [entry.command for entry in self._queued_commands.values()]
            
            # Sort by priority and queue time
            commands.sort(key=lambda c: (
                -c.metadata.priority.value,  # Higher priority first
                c.metadata.created_at  # Earlier created first
            ))
            
            if limit:
                commands = commands[:limit]
            
            return commands
    
    def clear_queue(self, command_type_filter: Optional[str] = None) -> int:
        """
        Clear the command queue.
        
        Args:
            command_type_filter: Only clear commands of this type
            
        Returns:
            Number of commands cleared
        """
        cleared_count = 0
        
        with self._lock:
            if not command_type_filter:
                # Clear everything
                cleared_count = len(self._queued_commands)
                
                # Clear the priority queue
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                    except Empty:
                        break
                
                # Clear tracking dictionaries
                self._queued_commands.clear()
                self._dependency_graph.clear()
                self._reverse_dependencies.clear()
                self._cancelled_commands.clear()
                
            else:
                # Clear specific command types
                entries_to_remove = []
                
                for queue_id, entry in self._queued_commands.items():
                    if entry.command.metadata.command_type == command_type_filter:
                        entries_to_remove.append(queue_id)
                
                for queue_id in entries_to_remove:
                    self._queued_commands.pop(queue_id, None)
                    self._dependency_graph.pop(queue_id, None)
                    
                    # Remove from reverse dependencies
                    for dep_set in self._reverse_dependencies.values():
                        dep_set.discard(queue_id)
                    
                    cleared_count += 1
                
                # Mark filtered commands as cancelled
                self._cancelled_commands.update(entries_to_remove)
            
            logger.info(f"Cleared {cleared_count} commands from queue")
            return cleared_count
    
    def pause_queue(self) -> None:
        """Pause queue processing."""
        with self._lock:
            self._paused = True
            logger.info("Command queue paused")
    
    def resume_queue(self) -> None:
        """Resume queue processing."""
        with self._lock:
            self._paused = False
            logger.info("Command queue resumed")
    
    @property
    def is_paused(self) -> bool:
        """Check if queue processing is paused."""
        return self._paused
    
    @property
    def size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def _are_dependencies_satisfied(self, command_id: UUID) -> bool:
        """
        Check if all dependencies for a command are satisfied.
        
        Args:
            command_id: ID of command to check
            
        Returns:
            True if all dependencies are satisfied
        """
        dependencies = self._dependency_graph.get(command_id, set())
        
        for dep_id in dependencies:
            # Check if dependency is completed
            if dep_id not in self._completed_commands:
                return False
        
        return True
    
    def _mark_command_completed(self, queue_id: UUID, execution_time: Optional[float] = None,
                               error: Optional[str] = None) -> None:
        """
        Mark a command as completed.
        
        Args:
            queue_id: Queue ID of completed command
            execution_time: Time taken to execute the command
            error: Error message if command failed
        """
        with self._lock:
            entry = self._executing_commands.pop(queue_id, None)
            if entry:
                entry.last_error = error
                self._completed_commands[queue_id] = entry
                
                # Track execution time
                if execution_time is not None:
                    self._execution_times.append(execution_time)
                    # Keep only recent execution times
                    if len(self._execution_times) > self._max_execution_history:
                        self._execution_times = self._execution_times[-self._max_execution_history:]
                
                # Clean up dependency graph
                self._dependency_graph.pop(queue_id, None)
                
                # Notify dependent commands (they might be ready to execute now)
                dependent_commands = self._reverse_dependencies.pop(queue_id, set())
                logger.debug(f"Command {queue_id} completed, potentially unblocking {len(dependent_commands)} commands")
                
                self._last_activity_time = datetime.utcnow()


class CommandExecutionManager(ICommandExecutor):
    """
    High-level command execution management with concurrency support.
    
    Coordinates command execution with the queue system, providing
    features like retry logic, timeout handling, and progress tracking.
    
    Attributes:
        command_queue: Command queue for managing execution order
        max_concurrent_commands: Maximum concurrent command execution
        default_timeout: Default timeout for command execution
        service_provider: Service provider for command execution context
    """
    
    def __init__(self, command_queue: CommandQueue,
                 max_concurrent_commands: int = 4,
                 default_timeout: Optional[int] = None,
                 service_provider: Optional[Any] = None):
        """
        Initialize command execution manager.
        
        Args:
            command_queue: Command queue for execution management
            max_concurrent_commands: Maximum concurrent executions
            default_timeout: Default command timeout in seconds
            service_provider: Service provider for dependency injection
        """
        self.command_queue = command_queue
        self.max_concurrent_commands = max_concurrent_commands
        self.default_timeout = default_timeout
        self.service_provider = service_provider
        
        # Execution tracking
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_commands)
        self._active_executions: Dict[UUID, Future] = {}
        self._execution_stats = {
            "total_executed": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cancelled_executions": 0,
            "timeout_executions": 0,
            "retry_executions": 0
        }
        
        # Thread safety
        self._lock = threading.RLock()
        self._shutdown = False
        
        logger.info(f"CommandExecutionManager initialized with {max_concurrent_commands} max concurrent commands")
    
    def execute_command(self, command: ICommand, 
                       context: Optional[CommandContext] = None) -> CommandResult:
        """
        Execute a single command.
        
        Args:
            command: Command to execute
            context: Optional execution context
            
        Returns:
            CommandResult with execution details
        """
        if self._shutdown:
            return CommandResult(
                success=False,
                message="Command execution manager is shutdown",
                errors=["Execution manager is not accepting new commands"]
            )
        
        # Create execution context
        exec_context = context or CommandContext(
            services=self.service_provider,
            dry_run=False
        )
        
        # Validate command before execution
        validation_errors = command.validate()
        if validation_errors:
            return CommandResult(
                success=False,
                message="Command validation failed",
                errors=validation_errors
            )
        
        # Check if command can execute
        if not command.can_execute(exec_context):
            return CommandResult(
                success=False,
                message="Command cannot be executed in current context",
                errors=["Command pre-execution check failed"]
            )
        
        logger.info(f"Executing command {command.metadata.command_type} "
                   f"(ID: {command.metadata.command_id})")
        
        start_time = time.time()
        
        try:
            # Execute the command
            result = command.execute(exec_context)
            
            # Update statistics
            execution_time = time.time() - start_time
            self._update_execution_stats(result.success, execution_time)
            
            logger.info(f"Command {command.metadata.command_type} completed "
                       f"({'success' if result.success else 'failed'}) "
                       f"in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_execution_stats(False, execution_time)
            
            logger.error(f"Command {command.metadata.command_type} failed with exception: {str(e)}", 
                        exc_info=True)
            
            return CommandResult(
                success=False,
                message=f"Command execution failed: {str(e)}",
                errors=[str(e)],
                execution_time_seconds=execution_time,
                metadata={
                    "command_id": str(command.metadata.command_id),
                    "exception_type": type(e).__name__
                }
            )
    
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
        if not commands:
            return []
        
        if self._shutdown:
            error_result = CommandResult(
                success=False,
                message="Command execution manager is shutdown",
                errors=["Execution manager is not accepting new commands"]
            )
            return [error_result] * len(commands)
        
        logger.info(f"Executing {len(commands)} commands "
                   f"({'parallel' if parallel else 'sequential'})")
        
        if parallel:
            return self._execute_commands_parallel(commands, context)
        else:
            return self._execute_commands_sequential(commands, context)
    
    def _execute_commands_sequential(self, commands: List[ICommand],
                                   context: Optional[CommandContext]) -> List[CommandResult]:
        """Execute commands sequentially."""
        results = []
        
        for i, command in enumerate(commands):
            logger.debug(f"Executing command {i+1}/{len(commands)}: {command.metadata.command_type}")
            
            result = self.execute_command(command, context)
            results.append(result)
            
            # Stop on failure if configured
            if not result.success and context and context.execution_settings.get("stop_on_failure", False):
                logger.warning(f"Stopping command execution due to failure in command {i+1}")
                break
        
        return results
    
    def _execute_commands_parallel(self, commands: List[ICommand],
                                  context: Optional[CommandContext]) -> List[CommandResult]:
        """Execute commands in parallel."""
        results = [None] * len(commands)
        futures = {}
        
        # Submit all commands for execution
        for i, command in enumerate(commands):
            future = self._executor.submit(self.execute_command, command, context)
            futures[future] = i
        
        # Collect results as they complete
        for future in as_completed(futures):
            index = futures[future]
            try:
                result = future.result()
                results[index] = result
            except Exception as e:
                logger.error(f"Parallel command execution failed: {str(e)}")
                results[index] = CommandResult(
                    success=False,
                    message=f"Parallel execution failed: {str(e)}",
                    errors=[str(e)]
                )
        
        return results
    
    def can_execute_command(self, command: ICommand, 
                           context: Optional[CommandContext] = None) -> bool:
        """
        Check if a command can be executed.
        
        Args:
            command: Command to check
            context: Optional execution context
            
        Returns:
            True if command can be executed
        """
        if self._shutdown:
            return False
        
        exec_context = context or CommandContext(services=self.service_provider)
        
        # Check command validation
        validation_errors = command.validate()
        if validation_errors:
            return False
        
        # Check command pre-execution conditions
        return command.can_execute(exec_context)
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get command execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        with self._lock:
            stats = self._execution_stats.copy()
            stats.update({
                "active_executions": len(self._active_executions),
                "max_concurrent_commands": self.max_concurrent_commands,
                "queue_size": self.command_queue.size,
                "queue_status": self.command_queue.get_queue_status()
            })
            
            return stats
    
    def _update_execution_stats(self, success: bool, execution_time: float) -> None:
        """Update execution statistics."""
        with self._lock:
            self._execution_stats["total_executed"] += 1
            
            if success:
                self._execution_stats["successful_executions"] += 1
            else:
                self._execution_stats["failed_executions"] += 1
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """
        Shutdown the execution manager.
        
        Args:
            wait: Whether to wait for active executions to complete
            timeout: Maximum time to wait for shutdown
        """
        logger.info("Shutting down CommandExecutionManager...")
        
        self._shutdown = True
        
        if wait:
            try:
                self._executor.shutdown(wait=True, timeout=timeout)
            except TypeError:
                # Fallback for Python < 3.9 which doesn't support timeout parameter
                self._executor.shutdown(wait=True)
        else:
            self._executor.shutdown(wait=False)
        
        logger.info("CommandExecutionManager shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic shutdown."""
        self.shutdown()