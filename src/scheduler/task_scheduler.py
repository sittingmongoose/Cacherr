"""
Main task scheduler implementation for PlexCacheUltra.

This module provides a comprehensive task scheduling system with support for
recurring tasks, one-time tasks, and complex scheduling patterns. Built with
dependency injection integration and robust error handling.

Features:
- Cron-like scheduling with interval and time-based triggers
- Background thread management with graceful shutdown
- Task execution tracking and result logging
- Error recovery and notification integration
- Thread-safe operations with proper synchronization
- Task dependency management
- Dynamic task registration and modification

Key Classes:
- TaskScheduler: Main scheduler service
- ScheduledTask: Individual task definition
- TaskExecution: Execution result tracking
- SchedulerConfig: Configuration management

Example:
    Basic usage:
    
    ```python
    scheduler = TaskScheduler(container)
    
    # Schedule recurring cache operation
    task = scheduler.add_recurring_task(
        name="cache_operation",
        task_func=lambda: cache_service.execute_cache_operation(),
        interval_hours=6,
        start_immediately=False
    )
    
    scheduler.start()
    ```
    
    Advanced scheduling:
    
    ```python
    # Schedule at specific times
    scheduler.add_cron_task(
        name="daily_cleanup",
        task_func=cleanup_service.daily_cleanup,
        cron_expression="0 2 * * *"  # Daily at 2 AM
    )
    
    # One-time delayed task
    scheduler.add_delayed_task(
        name="startup_validation",
        task_func=validation_service.validate_system,
        delay_seconds=30
    )
    ```
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import traceback
from concurrent.futures import ThreadPoolExecutor, Future

from pydantic import BaseModel, Field, validator
from croniter import croniter

from ..core.container import DIContainer, IServiceProvider
from ..core.interfaces import NotificationService, CacheService


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class SchedulerState(Enum):
    """Scheduler state enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


class TaskType(Enum):
    """Task type enumeration."""
    RECURRING = "recurring"
    CRON = "cron"
    DELAYED = "delayed"
    IMMEDIATE = "immediate"


@dataclass
class TaskExecution:
    """Task execution result tracking."""
    
    task_name: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    def mark_completed(self, result: Any = None) -> None:
        """Mark execution as completed with optional result."""
        self.end_time = datetime.now()
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def mark_failed(self, error: str, traceback_str: Optional[str] = None) -> None:
        """Mark execution as failed with error information."""
        self.end_time = datetime.now()
        self.status = TaskStatus.FAILED
        self.error = error
        self.error_traceback = traceback_str
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def mark_cancelled(self) -> None:
        """Mark execution as cancelled."""
        self.end_time = datetime.now()
        self.status = TaskStatus.CANCELLED
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()


class ScheduledTask(BaseModel):
    """Definition of a scheduled task."""
    
    name: str = Field(description="Unique task name")
    task_type: TaskType = Field(description="Type of task scheduling")
    task_func: Callable = Field(description="Function to execute")
    description: Optional[str] = Field(default=None, description="Task description")
    
    # Recurring task settings
    interval_seconds: Optional[int] = Field(default=None, description="Interval in seconds for recurring tasks")
    
    # Cron task settings
    cron_expression: Optional[str] = Field(default=None, description="Cron expression for cron tasks")
    
    # Delayed task settings
    delay_seconds: Optional[int] = Field(default=None, description="Delay in seconds for delayed tasks")
    
    # General settings
    enabled: bool = Field(default=True, description="Whether task is enabled")
    max_retries: int = Field(default=0, description="Maximum retry attempts on failure")
    retry_delay_seconds: int = Field(default=300, description="Delay between retry attempts")
    timeout_seconds: Optional[int] = Field(default=None, description="Task execution timeout")
    
    # State tracking
    next_run_time: Optional[datetime] = Field(default=None, description="Next scheduled run time")
    last_run_time: Optional[datetime] = Field(default=None, description="Last execution time")
    last_execution_status: Optional[TaskStatus] = Field(default=None, description="Last execution status")
    consecutive_failures: int = Field(default=0, description="Count of consecutive failures")
    total_executions: int = Field(default=0, description="Total number of executions")
    
    # Task dependencies
    depends_on: List[str] = Field(default_factory=list, description="Tasks this task depends on")
    run_after_failure: bool = Field(default=True, description="Whether to run even if dependencies failed")
    
    class Config:
        arbitrary_types_allowed = True
        
    @validator('cron_expression')
    def validate_cron_expression(cls, v, values):
        """Validate cron expression if provided."""
        if v and values.get('task_type') == TaskType.CRON:
            try:
                # Test if cron expression is valid
                croniter(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
        return v
    
    def calculate_next_run_time(self) -> Optional[datetime]:
        """Calculate the next run time based on task type and settings."""
        now = datetime.now()
        
        if not self.enabled:
            return None
        
        if self.task_type == TaskType.IMMEDIATE:
            return now
        
        elif self.task_type == TaskType.DELAYED:
            if self.delay_seconds and not self.last_run_time:
                return now + timedelta(seconds=self.delay_seconds)
            return None  # Delayed tasks run only once
        
        elif self.task_type == TaskType.RECURRING:
            if self.interval_seconds:
                if self.last_run_time:
                    return self.last_run_time + timedelta(seconds=self.interval_seconds)
                else:
                    return now + timedelta(seconds=self.interval_seconds)
            return None
        
        elif self.task_type == TaskType.CRON:
            if self.cron_expression:
                try:
                    cron = croniter(self.cron_expression, now)
                    return cron.get_next(datetime)
                except Exception as e:
                    logger.error(f"Failed to calculate next cron run time for {self.name}: {e}")
                    return None
            return None
        
        return None
    
    def should_run_now(self) -> bool:
        """Check if task should run now."""
        if not self.enabled:
            return False
        
        if not self.next_run_time:
            self.next_run_time = self.calculate_next_run_time()
            return False
        
        return datetime.now() >= self.next_run_time
    
    def update_after_execution(self, status: TaskStatus) -> None:
        """Update task state after execution."""
        self.last_run_time = datetime.now()
        self.last_execution_status = status
        self.total_executions += 1
        
        if status == TaskStatus.FAILED:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        # Calculate next run time
        if self.task_type in [TaskType.RECURRING, TaskType.CRON]:
            self.next_run_time = self.calculate_next_run_time()
        else:
            self.next_run_time = None  # One-time tasks don't reschedule


class SchedulerConfig(BaseModel):
    """Configuration for the task scheduler."""
    
    max_worker_threads: int = Field(default=4, description="Maximum worker threads for task execution")
    task_execution_timeout: int = Field(default=3600, description="Default task execution timeout in seconds")
    scheduler_loop_interval: int = Field(default=60, description="Scheduler loop interval in seconds")
    max_task_history: int = Field(default=1000, description="Maximum number of task executions to keep in history")
    enable_task_notifications: bool = Field(default=True, description="Enable task execution notifications")
    notification_on_failure_only: bool = Field(default=True, description="Send notifications only on task failures")
    retry_failed_tasks: bool = Field(default=True, description="Automatically retry failed tasks")
    cleanup_completed_tasks: bool = Field(default=True, description="Remove completed one-time tasks")
    
    class Config:
        extra = "forbid"


class TaskScheduler:
    """
    Main task scheduler service for PlexCacheUltra.
    
    Provides comprehensive task scheduling functionality with support for
    various scheduling patterns, error handling, and integration with
    the dependency injection system.
    """
    
    def __init__(self, service_provider: IServiceProvider, config: Optional[SchedulerConfig] = None):
        """
        Initialize the task scheduler.
        
        Args:
            service_provider: Dependency injection service provider
            config: Scheduler configuration (uses defaults if None)
            
        Raises:
            ValueError: If service_provider is None
        """
        if not service_provider:
            raise ValueError("Service provider is required")
        
        self.service_provider = service_provider
        self.config = config or SchedulerConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State management
        self.state = SchedulerState.STOPPED
        self.tasks: Dict[str, ScheduledTask] = {}
        self.executions: List[TaskExecution] = []
        self.execution_futures: Dict[str, Future] = {}
        
        # Threading
        self.scheduler_thread: Optional[threading.Thread] = None
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.shutdown_event = threading.Event()
        self.state_lock = threading.RLock()
        
        # Services (resolved lazily)
        self._notification_service: Optional[NotificationService] = None
        self._cache_service: Optional[CacheService] = None
        
        self.logger.info("TaskScheduler initialized")
    
    @property
    def notification_service(self) -> Optional[NotificationService]:
        """Get notification service instance (lazy loading)."""
        if self._notification_service is None:
            self._notification_service = self.service_provider.try_resolve(NotificationService)
        return self._notification_service
    
    @property
    def cache_service(self) -> Optional[CacheService]:
        """Get cache service instance (lazy loading)."""
        if self._cache_service is None:
            self._cache_service = self.service_provider.try_resolve(CacheService)
        return self._cache_service
    
    def start(self) -> bool:
        """
        Start the task scheduler.
        
        Returns:
            True if scheduler started successfully, False otherwise
        """
        with self.state_lock:
            if self.state != SchedulerState.STOPPED:
                self.logger.warning(f"Cannot start scheduler in state: {self.state}")
                return False
            
            self.state = SchedulerState.STARTING
            self.shutdown_event.clear()
        
        try:
            # Initialize thread pool
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.config.max_worker_threads,
                thread_name_prefix="TaskScheduler"
            )
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="TaskScheduler-Main",
                daemon=True
            )
            self.scheduler_thread.start()
            
            with self.state_lock:
                self.state = SchedulerState.RUNNING
            
            self.logger.info("Task scheduler started successfully")
            
            # Send startup notification
            if self.config.enable_task_notifications and self.notification_service:
                self.notification_service.send_notification(
                    "Task scheduler started successfully",
                    level="success"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start task scheduler: {e}")
            with self.state_lock:
                self.state = SchedulerState.STOPPED
            return False
    
    def stop(self, timeout_seconds: int = 30) -> bool:
        """
        Stop the task scheduler gracefully.
        
        Args:
            timeout_seconds: Maximum time to wait for graceful shutdown
            
        Returns:
            True if scheduler stopped successfully, False otherwise
        """
        with self.state_lock:
            if self.state == SchedulerState.STOPPED:
                return True
            
            self.state = SchedulerState.STOPPING
        
        try:
            self.logger.info("Stopping task scheduler...")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Cancel running tasks
            for execution_id, future in list(self.execution_futures.items()):
                if not future.done():
                    future.cancel()
                    self.logger.info(f"Cancelled task execution: {execution_id}")
            
            # Wait for scheduler thread to finish
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=timeout_seconds)
            
            # Shutdown thread pool
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True, timeout=timeout_seconds)
            
            with self.state_lock:
                self.state = SchedulerState.STOPPED
            
            self.logger.info("Task scheduler stopped successfully")
            
            # Send shutdown notification
            if self.config.enable_task_notifications and self.notification_service:
                self.notification_service.send_notification(
                    "Task scheduler stopped",
                    level="info"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during scheduler shutdown: {e}")
            with self.state_lock:
                self.state = SchedulerState.STOPPED
            return False
    
    def add_task(self, task: ScheduledTask) -> bool:
        """
        Add a task to the scheduler.
        
        Args:
            task: Task to add
            
        Returns:
            True if task added successfully, False otherwise
        """
        if task.name in self.tasks:
            self.logger.warning(f"Task with name '{task.name}' already exists")
            return False
        
        try:
            # Calculate initial next run time
            task.next_run_time = task.calculate_next_run_time()
            
            self.tasks[task.name] = task
            self.logger.info(f"Added task '{task.name}' ({task.task_type.value})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add task '{task.name}': {e}")
            return False
    
    def remove_task(self, task_name: str) -> bool:
        """
        Remove a task from the scheduler.
        
        Args:
            task_name: Name of task to remove
            
        Returns:
            True if task removed successfully, False otherwise
        """
        if task_name not in self.tasks:
            self.logger.warning(f"Task '{task_name}' not found")
            return False
        
        try:
            # Cancel running execution if any
            for execution_id, future in list(self.execution_futures.items()):
                if execution_id.startswith(f"{task_name}-"):
                    future.cancel()
                    del self.execution_futures[execution_id]
            
            del self.tasks[task_name]
            self.logger.info(f"Removed task '{task_name}'")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove task '{task_name}': {e}")
            return False
    
    def add_recurring_task(self, name: str, task_func: Callable, interval_hours: int,
                          description: Optional[str] = None, start_immediately: bool = False,
                          **kwargs) -> Optional[ScheduledTask]:
        """
        Add a recurring task that runs at regular intervals.
        
        Args:
            name: Unique task name
            task_func: Function to execute
            interval_hours: Interval between executions in hours
            description: Optional task description
            start_immediately: Whether to run the task immediately
            **kwargs: Additional task configuration options
            
        Returns:
            ScheduledTask instance if added successfully, None otherwise
        """
        task = ScheduledTask(
            name=name,
            task_type=TaskType.RECURRING,
            task_func=task_func,
            description=description,
            interval_seconds=interval_hours * 3600,
            **kwargs
        )
        
        if start_immediately:
            task.next_run_time = datetime.now()
        
        if self.add_task(task):
            return task
        return None
    
    def add_cron_task(self, name: str, task_func: Callable, cron_expression: str,
                     description: Optional[str] = None, **kwargs) -> Optional[ScheduledTask]:
        """
        Add a cron-style scheduled task.
        
        Args:
            name: Unique task name
            task_func: Function to execute
            cron_expression: Cron expression (e.g., "0 2 * * *" for daily at 2 AM)
            description: Optional task description
            **kwargs: Additional task configuration options
            
        Returns:
            ScheduledTask instance if added successfully, None otherwise
        """
        task = ScheduledTask(
            name=name,
            task_type=TaskType.CRON,
            task_func=task_func,
            description=description,
            cron_expression=cron_expression,
            **kwargs
        )
        
        if self.add_task(task):
            return task
        return None
    
    def add_delayed_task(self, name: str, task_func: Callable, delay_seconds: int,
                        description: Optional[str] = None, **kwargs) -> Optional[ScheduledTask]:
        """
        Add a one-time delayed task.
        
        Args:
            name: Unique task name
            task_func: Function to execute
            delay_seconds: Delay before execution in seconds
            description: Optional task description
            **kwargs: Additional task configuration options
            
        Returns:
            ScheduledTask instance if added successfully, None otherwise
        """
        task = ScheduledTask(
            name=name,
            task_type=TaskType.DELAYED,
            task_func=task_func,
            description=description,
            delay_seconds=delay_seconds,
            **kwargs
        )
        
        if self.add_task(task):
            return task
        return None
    
    def get_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a task.
        
        Args:
            task_name: Name of task
            
        Returns:
            Dictionary with task status information, None if task not found
        """
        if task_name not in self.tasks:
            return None
        
        task = self.tasks[task_name]
        
        # Check if task is currently running
        is_running = any(
            execution_id.startswith(f"{task_name}-") and not future.done()
            for execution_id, future in self.execution_futures.items()
        )
        
        return {
            "name": task.name,
            "type": task.task_type.value,
            "enabled": task.enabled,
            "description": task.description,
            "next_run_time": task.next_run_time.isoformat() if task.next_run_time else None,
            "last_run_time": task.last_run_time.isoformat() if task.last_run_time else None,
            "last_execution_status": task.last_execution_status.value if task.last_execution_status else None,
            "consecutive_failures": task.consecutive_failures,
            "total_executions": task.total_executions,
            "is_running": is_running
        }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get comprehensive scheduler status.
        
        Returns:
            Dictionary with scheduler status information
        """
        running_tasks = [
            execution_id.split('-')[0] for execution_id in self.execution_futures
            if not self.execution_futures[execution_id].done()
        ]
        
        return {
            "state": self.state.value,
            "total_tasks": len(self.tasks),
            "enabled_tasks": len([t for t in self.tasks.values() if t.enabled]),
            "running_tasks": len(set(running_tasks)),
            "running_task_names": list(set(running_tasks)),
            "total_executions": len(self.executions),
            "config": self.config.dict()
        }
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that runs in background thread."""
        self.logger.info("Scheduler loop started")
        
        while not self.shutdown_event.is_set():
            try:
                self._process_scheduled_tasks()
                self._cleanup_completed_executions()
                
                # Wait for next iteration or shutdown signal
                self.shutdown_event.wait(timeout=self.config.scheduler_loop_interval)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                
                # Brief pause before continuing to avoid tight error loops
                self.shutdown_event.wait(timeout=5)
        
        self.logger.info("Scheduler loop ended")
    
    def _process_scheduled_tasks(self) -> None:
        """Process all scheduled tasks and execute those that are due."""
        for task_name, task in list(self.tasks.items()):
            try:
                if task.should_run_now():
                    # Check task dependencies
                    if self._check_task_dependencies(task):
                        self._execute_task(task)
                    else:
                        self.logger.info(f"Task '{task_name}' skipped due to dependency failure")
                        
            except Exception as e:
                self.logger.error(f"Error processing task '{task_name}': {e}")
    
    def _check_task_dependencies(self, task: ScheduledTask) -> bool:
        """
        Check if task dependencies are satisfied.
        
        Args:
            task: Task to check dependencies for
            
        Returns:
            True if dependencies are satisfied, False otherwise
        """
        if not task.depends_on:
            return True  # No dependencies
        
        for dep_task_name in task.depends_on:
            if dep_task_name not in self.tasks:
                self.logger.warning(f"Dependency task '{dep_task_name}' not found for task '{task.name}'")
                if not task.run_after_failure:
                    return False
                continue
            
            dep_task = self.tasks[dep_task_name]
            
            # Check if dependency task has run recently and successfully
            if (dep_task.last_execution_status == TaskStatus.FAILED and 
                not task.run_after_failure):
                return False
        
        return True
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """
        Execute a task in the thread pool.
        
        Args:
            task: Task to execute
        """
        execution_id = f"{task.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        execution = TaskExecution(
            task_name=task.name,
            execution_id=execution_id,
            start_time=datetime.now()
        )
        
        self.executions.append(execution)
        
        # Submit task to thread pool
        future = self.thread_pool.submit(
            self._run_task_with_timeout,
            task,
            execution
        )
        
        self.execution_futures[execution_id] = future
        
        self.logger.info(f"Started execution of task '{task.name}' (ID: {execution_id})")
    
    def _run_task_with_timeout(self, task: ScheduledTask, execution: TaskExecution) -> None:
        """
        Run a task with timeout and error handling.
        
        Args:
            task: Task to execute
            execution: Execution tracking object
        """
        try:
            execution.status = TaskStatus.RUNNING
            
            # Execute the task function
            result = task.task_func()
            
            execution.mark_completed(result)
            task.update_after_execution(TaskStatus.COMPLETED)
            
            self.logger.info(f"Task '{task.name}' completed successfully")
            
            # Send success notification if configured
            if (self.config.enable_task_notifications and 
                not self.config.notification_on_failure_only and 
                self.notification_service):
                self.notification_service.send_success_notification(
                    f"Task '{task.name}' completed successfully"
                )
            
        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            
            execution.mark_failed(error_msg, error_traceback)
            task.update_after_execution(TaskStatus.FAILED)
            
            self.logger.error(f"Task '{task.name}' failed: {error_msg}")
            self.logger.debug(f"Task '{task.name}' traceback: {error_traceback}")
            
            # Send failure notification
            if self.config.enable_task_notifications and self.notification_service:
                self.notification_service.send_error_notification(
                    f"Task '{task.name}' failed: {error_msg}",
                    details={
                        "task_name": task.name,
                        "execution_id": execution.execution_id,
                        "error": error_msg,
                        "consecutive_failures": task.consecutive_failures
                    }
                )
            
            # Schedule retry if configured
            if (self.config.retry_failed_tasks and 
                task.max_retries > 0 and 
                task.consecutive_failures <= task.max_retries):
                
                retry_time = datetime.now() + timedelta(seconds=task.retry_delay_seconds)
                task.next_run_time = retry_time
                
                self.logger.info(
                    f"Scheduled retry for task '{task.name}' at {retry_time} "
                    f"(attempt {task.consecutive_failures + 1}/{task.max_retries + 1})"
                )
        
        finally:
            # Clean up execution future
            if execution.execution_id in self.execution_futures:
                del self.execution_futures[execution.execution_id]
    
    def _cleanup_completed_executions(self) -> None:
        """Clean up old execution records to prevent memory growth."""
        if len(self.executions) > self.config.max_task_history:
            # Keep only the most recent executions
            self.executions = self.executions[-self.config.max_task_history:]
            self.logger.debug(f"Cleaned up old task executions, kept {self.config.max_task_history}")
        
        # Remove completed one-time tasks if configured
        if self.config.cleanup_completed_tasks:
            completed_onetime_tasks = []
            
            for task_name, task in list(self.tasks.items()):
                if (task.task_type in [TaskType.DELAYED, TaskType.IMMEDIATE] and 
                    task.last_execution_status == TaskStatus.COMPLETED):
                    completed_onetime_tasks.append(task_name)
            
            for task_name in completed_onetime_tasks:
                del self.tasks[task_name]
                self.logger.debug(f"Removed completed one-time task: {task_name}")