"""
Command monitoring and metrics system for PlexCacheUltra.

This module provides comprehensive monitoring, logging, and metrics collection
for command execution. It integrates with the existing metrics repository
and notification systems to provide real-time insights into command
performance and system health.

Classes:
- CommandMetrics: Data model for command execution metrics
- CommandLogger: Specialized logging for command operations
- CommandMonitor: Real-time command execution monitoring
- MetricsCollector: Integration with metrics repository
- PerformanceTracker: Performance analysis and optimization insights
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel

from .commands.interfaces import (
    ICommand, CommandResult, CommandStatus, CommandPriority, CommandContext
)
from .repositories import MetricsRepository, MetricsData
from .interfaces import NotificationService

logger = logging.getLogger(__name__)


class CommandMetrics(BaseModel):
    """
    Comprehensive metrics for command execution.
    
    Attributes:
        command_id: Unique identifier for the command
        command_type: Type of command executed
        execution_start: When command execution started
        execution_end: When command execution finished
        execution_duration: Total execution time in seconds
        success: Whether command executed successfully
        files_processed: Number of files processed
        bytes_processed: Number of bytes processed
        memory_usage: Peak memory usage during execution
        cpu_usage: Average CPU usage during execution
        queue_wait_time: Time spent waiting in queue
        retry_count: Number of retry attempts
        errors: List of error messages
        warnings: List of warning messages
        user_id: User who initiated the command
        session_id: Session identifier
        priority: Command execution priority
        tags: Command tags for categorization
    """
    
    command_id: UUID
    command_type: str
    execution_start: datetime
    execution_end: Optional[datetime] = None
    execution_duration: Optional[float] = None
    success: Optional[bool] = None
    files_processed: int = 0
    bytes_processed: int = 0
    memory_usage: Optional[int] = None  # Peak memory in bytes
    cpu_usage: Optional[float] = None   # Average CPU percentage
    queue_wait_time: Optional[float] = None
    retry_count: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    priority: str = CommandPriority.NORMAL.name
    tags: List[str] = []
    
    def finalize_metrics(self, result: CommandResult) -> None:
        """
        Finalize metrics with command result data.
        
        Args:
            result: Command execution result
        """
        self.execution_end = datetime.utcnow()
        if self.execution_start:
            self.execution_duration = (self.execution_end - self.execution_start).total_seconds()
        
        self.success = result.success
        self.files_processed = len(result.files_affected)
        self.bytes_processed = result.bytes_processed
        self.errors = result.errors.copy()
        self.warnings = result.warnings.copy()
        
        if result.execution_time_seconds:
            self.execution_duration = result.execution_time_seconds


class CommandLogger:
    """
    Specialized logging system for command operations.
    
    Provides structured logging with context preservation,
    performance tracking, and integration with monitoring systems.
    """
    
    def __init__(self, base_logger: Optional[logging.Logger] = None,
                 log_level: int = logging.INFO,
                 structured_logging: bool = True):
        """
        Initialize command logger.
        
        Args:
            base_logger: Base logger to use (defaults to module logger)
            log_level: Minimum log level to capture
            structured_logging: Whether to use structured log format
        """
        self.logger = base_logger or logger
        self.log_level = log_level
        self.structured_logging = structured_logging
        
        # Thread-local storage for context
        self._local = threading.local()
        
        logger.debug("CommandLogger initialized")
    
    def log_command_start(self, command: ICommand, context: Optional[CommandContext] = None) -> None:
        """
        Log command execution start.
        
        Args:
            command: Command being executed
            context: Execution context
        """
        log_data = {
            "event": "command_start",
            "command_id": str(command.metadata.command_id),
            "command_type": command.metadata.command_type,
            "priority": command.metadata.priority.name,
            "tags": command.metadata.tags,
            "affected_resources": len(command.get_affected_resources()),
            "estimated_time": command.estimate_execution_time(),
            "dry_run": context.dry_run if context else False
        }
        
        if context:
            log_data.update({
                "user_id": context.user_id,
                "session_id": context.session_id
            })
        
        self._log_structured(logging.INFO, "Command execution started", log_data)
    
    def log_command_progress(self, command: ICommand, progress: float, message: Optional[str] = None) -> None:
        """
        Log command execution progress.
        
        Args:
            command: Command being executed
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
        """
        log_data = {
            "event": "command_progress",
            "command_id": str(command.metadata.command_id),
            "command_type": command.metadata.command_type,
            "progress": progress,
            "message": message
        }
        
        self._log_structured(logging.DEBUG, f"Command progress: {progress:.1%}", log_data)
    
    def log_command_completion(self, command: ICommand, result: CommandResult, 
                              metrics: Optional[CommandMetrics] = None) -> None:
        """
        Log command execution completion.
        
        Args:
            command: Executed command
            result: Execution result
            metrics: Optional execution metrics
        """
        log_data = {
            "event": "command_completion",
            "command_id": str(command.metadata.command_id),
            "command_type": command.metadata.command_type,
            "success": result.success,
            "execution_time": result.execution_time_seconds,
            "files_affected": len(result.files_affected),
            "bytes_processed": result.bytes_processed,
            "errors": len(result.errors),
            "warnings": len(result.warnings)
        }
        
        if metrics:
            log_data.update({
                "memory_usage": metrics.memory_usage,
                "cpu_usage": metrics.cpu_usage,
                "queue_wait_time": metrics.queue_wait_time
            })
        
        log_level = logging.INFO if result.success else logging.ERROR
        status = "completed successfully" if result.success else "failed"
        self._log_structured(log_level, f"Command {status}", log_data)
    
    def log_command_error(self, command: ICommand, error: Exception, context: Optional[str] = None) -> None:
        """
        Log command execution error.
        
        Args:
            command: Command that failed
            error: Exception that occurred
            context: Optional context information
        """
        log_data = {
            "event": "command_error",
            "command_id": str(command.metadata.command_id),
            "command_type": command.metadata.command_type,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        self._log_structured(logging.ERROR, f"Command error: {str(error)}", log_data, exc_info=True)
    
    def log_command_retry(self, command: ICommand, retry_count: int, reason: str) -> None:
        """
        Log command retry attempt.
        
        Args:
            command: Command being retried
            retry_count: Current retry attempt number
            reason: Reason for retry
        """
        log_data = {
            "event": "command_retry",
            "command_id": str(command.metadata.command_id),
            "command_type": command.metadata.command_type,
            "retry_count": retry_count,
            "max_retries": command.metadata.max_retries,
            "reason": reason
        }
        
        self._log_structured(logging.WARNING, f"Command retry attempt {retry_count}", log_data)
    
    def _log_structured(self, level: int, message: str, data: Dict[str, Any], 
                       exc_info: bool = False) -> None:
        """
        Log with structured data format.
        
        Args:
            level: Log level
            message: Log message
            data: Structured data
            exc_info: Whether to include exception info
        """
        if self.structured_logging:
            # Format as JSON-like structure for better parsing
            import json
            structured_msg = f"{message} | {json.dumps(data, default=str)}"
        else:
            # Human-readable format
            structured_msg = f"{message} [{data.get('command_type', 'unknown')}:{data.get('command_id', 'unknown')[:8]}]"
        
        self.logger.log(level, structured_msg, exc_info=exc_info)


class CommandMonitor:
    """
    Real-time command execution monitoring system.
    
    Tracks active commands, collects metrics, and provides
    real-time insights into system performance and health.
    """
    
    def __init__(self, metrics_repository: Optional[MetricsRepository] = None,
                 notification_service: Optional[NotificationService] = None,
                 enable_performance_tracking: bool = True):
        """
        Initialize command monitor.
        
        Args:
            metrics_repository: Repository for storing metrics data
            notification_service: Service for sending alerts
            enable_performance_tracking: Whether to track detailed performance
        """
        self.metrics_repository = metrics_repository
        self.notification_service = notification_service
        self.enable_performance_tracking = enable_performance_tracking
        
        # Active command tracking
        self._active_commands: Dict[UUID, CommandMetrics] = {}
        self._completed_commands: deque = deque(maxlen=1000)  # Keep recent history
        
        # Performance tracking
        self._performance_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._alert_thresholds = {
            "max_execution_time": 3600,  # 1 hour
            "max_queue_size": 100,
            "error_rate_threshold": 0.1,  # 10%
            "memory_threshold": 8 * 1024 * 1024 * 1024  # 8GB
        }
        
        # Statistics
        self._stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "average_execution_time": 0.0,
            "current_queue_size": 0
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Monitoring callbacks
        self._command_started_callbacks: List[Callable[[CommandMetrics], None]] = []
        self._command_completed_callbacks: List[Callable[[CommandMetrics], None]] = []
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        logger.info("CommandMonitor initialized")
    
    def start_command_monitoring(self, command: ICommand, 
                                context: Optional[CommandContext] = None) -> CommandMetrics:
        """
        Start monitoring a command execution.
        
        Args:
            command: Command to monitor
            context: Execution context
            
        Returns:
            CommandMetrics object for tracking
        """
        metrics = CommandMetrics(
            command_id=command.metadata.command_id,
            command_type=command.metadata.command_type,
            execution_start=datetime.utcnow(),
            priority=command.metadata.priority.name,
            tags=command.metadata.tags.copy(),
            retry_count=command.metadata.retry_count
        )
        
        if context:
            metrics.user_id = context.user_id
            metrics.session_id = context.session_id
        
        with self._lock:
            self._active_commands[command.metadata.command_id] = metrics
            self._stats["current_queue_size"] = len(self._active_commands)
        
        # Trigger callbacks
        for callback in self._command_started_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Command started callback failed: {str(e)}")
        
        # Start performance tracking if enabled
        if self.enable_performance_tracking:
            self._start_performance_tracking(metrics)
        
        logger.debug(f"Started monitoring command {command.metadata.command_type} "
                    f"(ID: {command.metadata.command_id})")
        
        return metrics
    
    def complete_command_monitoring(self, command: ICommand, result: CommandResult) -> CommandMetrics:
        """
        Complete monitoring for a command execution.
        
        Args:
            command: Completed command
            result: Execution result
            
        Returns:
            Final CommandMetrics with complete data
        """
        command_id = command.metadata.command_id
        
        with self._lock:
            metrics = self._active_commands.pop(command_id, None)
            if not metrics:
                # Create metrics if monitoring wasn't started
                metrics = CommandMetrics(
                    command_id=command_id,
                    command_type=command.metadata.command_type,
                    execution_start=datetime.utcnow() - timedelta(seconds=result.execution_time_seconds or 0),
                    priority=command.metadata.priority.name,
                    tags=command.metadata.tags.copy()
                )
            
            # Finalize metrics
            metrics.finalize_metrics(result)
            
            # Update statistics
            self._stats["total_commands"] += 1
            self._stats["current_queue_size"] = len(self._active_commands)
            
            if result.success:
                self._stats["successful_commands"] += 1
            else:
                self._stats["failed_commands"] += 1
            
            # Update average execution time
            if metrics.execution_duration:
                current_avg = self._stats["average_execution_time"]
                total_commands = self._stats["total_commands"]
                self._stats["average_execution_time"] = (
                    (current_avg * (total_commands - 1) + metrics.execution_duration) / total_commands
                )
            
            # Store in completed commands
            self._completed_commands.append(metrics)
        
        # Stop performance tracking
        if self.enable_performance_tracking:
            self._stop_performance_tracking(metrics)
        
        # Store metrics in repository
        if self.metrics_repository:
            self._store_metrics(metrics)
        
        # Check for alerts
        self._check_alerts(metrics)
        
        # Trigger callbacks
        for callback in self._command_completed_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Command completed callback failed: {str(e)}")
        
        logger.debug(f"Completed monitoring command {command.metadata.command_type} "
                    f"(ID: {command.metadata.command_id})")
        
        return metrics
    
    def get_active_commands(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active commands.
        
        Returns:
            List of active command information
        """
        with self._lock:
            return [
                {
                    "command_id": str(metrics.command_id),
                    "command_type": metrics.command_type,
                    "started_at": metrics.execution_start.isoformat(),
                    "duration_seconds": (datetime.utcnow() - metrics.execution_start).total_seconds(),
                    "priority": metrics.priority,
                    "user_id": metrics.user_id,
                    "session_id": metrics.session_id
                }
                for metrics in self._active_commands.values()
            ]
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring statistics.
        
        Returns:
            Dictionary with monitoring statistics
        """
        with self._lock:
            stats = self._stats.copy()
            
            # Calculate success rate
            if stats["total_commands"] > 0:
                stats["success_rate"] = stats["successful_commands"] / stats["total_commands"]
                stats["error_rate"] = stats["failed_commands"] / stats["total_commands"]
            else:
                stats["success_rate"] = 0.0
                stats["error_rate"] = 0.0
            
            # Add performance data
            if self._completed_commands:
                recent_commands = list(self._completed_commands)[-100:]  # Last 100 commands
                
                execution_times = [cmd.execution_duration for cmd in recent_commands 
                                  if cmd.execution_duration is not None]
                if execution_times:
                    stats["recent_avg_execution_time"] = sum(execution_times) / len(execution_times)
                    stats["recent_min_execution_time"] = min(execution_times)
                    stats["recent_max_execution_time"] = max(execution_times)
                
                # Command type distribution
                command_types = defaultdict(int)
                for cmd in recent_commands:
                    command_types[cmd.command_type] += 1
                stats["recent_command_types"] = dict(command_types)
            
            # Add system health indicators
            stats["health_status"] = self._calculate_health_status()
            
            return stats
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """
        Get performance insights and recommendations.
        
        Returns:
            Dictionary with performance analysis
        """
        insights = {
            "recommendations": [],
            "alerts": [],
            "trends": {},
            "bottlenecks": []
        }
        
        with self._lock:
            if not self._completed_commands:
                return insights
            
            recent_commands = list(self._completed_commands)[-100:]
            
            # Analyze execution times
            long_running = [cmd for cmd in recent_commands 
                           if cmd.execution_duration and cmd.execution_duration > 300]  # > 5 minutes
            if long_running:
                insights["recommendations"].append(
                    f"Found {len(long_running)} commands taking >5 minutes. "
                    "Consider optimization or parallel processing."
                )
            
            # Analyze error patterns
            failed_commands = [cmd for cmd in recent_commands if not cmd.success]
            if failed_commands:
                error_rate = len(failed_commands) / len(recent_commands)
                if error_rate > 0.1:  # > 10% error rate
                    insights["alerts"].append(
                        f"High error rate detected: {error_rate:.1%}. "
                        "Investigation recommended."
                    )
                
                # Common error types
                error_types = defaultdict(int)
                for cmd in failed_commands:
                    for error in cmd.errors:
                        error_types[error[:50]] += 1  # First 50 chars of error
                
                if error_types:
                    most_common = max(error_types.items(), key=lambda x: x[1])
                    insights["bottlenecks"].append(
                        f"Most common error: '{most_common[0]}' ({most_common[1]} occurrences)"
                    )
            
            # Memory usage analysis
            memory_samples = [cmd.memory_usage for cmd in recent_commands 
                             if cmd.memory_usage is not None]
            if memory_samples:
                avg_memory = sum(memory_samples) / len(memory_samples)
                max_memory = max(memory_samples)
                insights["trends"]["average_memory_usage_mb"] = avg_memory / (1024 * 1024)
                insights["trends"]["peak_memory_usage_mb"] = max_memory / (1024 * 1024)
                
                if max_memory > self._alert_thresholds["memory_threshold"]:
                    insights["alerts"].append("High memory usage detected. Memory optimization recommended.")
        
        return insights
    
    def add_command_started_callback(self, callback: Callable[[CommandMetrics], None]) -> None:
        """Add callback for when command monitoring starts."""
        self._command_started_callbacks.append(callback)
    
    def add_command_completed_callback(self, callback: Callable[[CommandMetrics], None]) -> None:
        """Add callback for when command monitoring completes."""
        self._command_completed_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for monitoring alerts."""
        self._alert_callbacks.append(callback)
    
    def _start_performance_tracking(self, metrics: CommandMetrics) -> None:
        """Start detailed performance tracking for a command."""
        # Performance tracking implementation would monitor:
        # - Memory usage
        # - CPU usage
        # - I/O operations
        # - Network activity
        # This is a placeholder for the actual implementation
        pass
    
    def _stop_performance_tracking(self, metrics: CommandMetrics) -> None:
        """Stop performance tracking and finalize metrics."""
        # Finalize performance data collection
        # This is a placeholder for the actual implementation
        pass
    
    def _store_metrics(self, metrics: CommandMetrics) -> None:
        """Store metrics in the metrics repository."""
        if not self.metrics_repository:
            return
        
        try:
            metrics_data = MetricsData(
                timestamp=metrics.execution_end or datetime.utcnow(),
                operation_type=metrics.command_type,
                files_processed=metrics.files_processed,
                bytes_processed=metrics.bytes_processed,
                duration_seconds=metrics.execution_duration or 0.0,
                success_rate=1.0 if metrics.success else 0.0,
                errors=metrics.errors
            )
            
            self.metrics_repository.record_metric(metrics_data)
            logger.debug(f"Stored metrics for command {metrics.command_id}")
            
        except Exception as e:
            logger.error(f"Failed to store command metrics: {str(e)}")
    
    def _check_alerts(self, metrics: CommandMetrics) -> None:
        """Check for alert conditions and trigger notifications."""
        alerts = []
        
        # Check execution time threshold
        if (metrics.execution_duration and 
            metrics.execution_duration > self._alert_thresholds["max_execution_time"]):
            alerts.append({
                "type": "long_execution",
                "message": f"Command {metrics.command_type} took {metrics.execution_duration:.1f} seconds",
                "severity": "warning"
            })
        
        # Check memory usage threshold
        if (metrics.memory_usage and 
            metrics.memory_usage > self._alert_thresholds["memory_threshold"]):
            alerts.append({
                "type": "high_memory",
                "message": f"Command {metrics.command_type} used {metrics.memory_usage / (1024**3):.1f} GB memory",
                "severity": "warning"
            })
        
        # Check error conditions
        if not metrics.success:
            alerts.append({
                "type": "command_failure",
                "message": f"Command {metrics.command_type} failed: {'; '.join(metrics.errors[:3])}",
                "severity": "error"
            })
        
        # Send alerts
        for alert in alerts:
            # Trigger alert callbacks
            for callback in self._alert_callbacks:
                try:
                    callback(alert["type"], {
                        "command_id": str(metrics.command_id),
                        "command_type": metrics.command_type,
                        "message": alert["message"],
                        "severity": alert["severity"],
                        "metrics": metrics.model_dump()
                    })
                except Exception as e:
                    logger.error(f"Alert callback failed: {str(e)}")
            
            # Send notification
            if self.notification_service and alert["severity"] == "error":
                self.notification_service.send_error_notification(
                    alert["message"],
                    {
                        "command_id": str(metrics.command_id),
                        "command_type": metrics.command_type,
                        "execution_time": metrics.execution_duration
                    }
                )
    
    def _calculate_health_status(self) -> str:
        """Calculate overall system health status."""
        if self._stats["total_commands"] == 0:
            return "unknown"
        
        error_rate = self._stats["failed_commands"] / self._stats["total_commands"]
        active_commands = len(self._active_commands)
        
        if error_rate > 0.2:  # > 20% error rate
            return "critical"
        elif error_rate > 0.1 or active_commands > 50:  # > 10% error rate or high load
            return "warning"
        elif error_rate < 0.05:  # < 5% error rate
            return "healthy"
        else:
            return "fair"