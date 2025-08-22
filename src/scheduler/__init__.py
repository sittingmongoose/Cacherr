"""
Scheduler module for PlexCacheUltra background task management.

This module provides comprehensive task scheduling functionality for automated
cache operations, cleanup tasks, and maintenance routines. Built with dependency
injection support and proper error handling.

Key Components:
- TaskScheduler: Main scheduler service with cron-like functionality
- Task definitions for cache operations and cleanup
- Background thread management with graceful shutdown
- Task result tracking and error handling
- Integration with notification system

Example:
    ```python
    from src.scheduler import TaskScheduler
    from src.core.container import DIContainer
    
    container = DIContainer()
    scheduler = TaskScheduler(container)
    
    # Start scheduler
    scheduler.start()
    
    # Schedule tasks
    scheduler.schedule_cache_operation(interval_hours=6)
    scheduler.schedule_cleanup_task(interval_hours=24)
    
    # Stop scheduler
    scheduler.stop()
    ```
"""

from .task_scheduler import TaskScheduler, SchedulerConfig
from .tasks.cache_tasks import CacheOperationTask, TestModeAnalysisTask
from .tasks.cleanup_tasks import CacheCleanupTask, LogCleanupTask

__all__ = [
    'TaskScheduler',
    'SchedulerConfig',
    'CacheOperationTask',
    'TestModeAnalysisTask', 
    'CacheCleanupTask',
    'LogCleanupTask'
]