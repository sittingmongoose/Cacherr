"""
Command service integration for PlexCacheUltra dependency injection system.

This module provides the integration layer between the command pattern
implementation and the dependency injection container. It includes
service registration, command service providers, and high-level
orchestration of the command system.

Classes:
- CommandSystemConfiguration: Configuration for command system
- CommandService: Main service for command orchestration
- CommandServiceRegistry: Service registration for DI container
"""

import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from pydantic import BaseModel, Field

from .container import DIContainer, ServiceLifetime
from .command_queue import CommandQueue, CommandExecutionManager
from .command_history import CommandHistory, PersistentCommandHistory, CommandHistoryManager
from .command_monitor import CommandMonitor, CommandLogger
from .commands.command_factory import CacheCommandFactory
from .commands.interfaces import (
    ICommand, ICommandQueue, ICommandExecutor, ICommandHistory, 
    CommandContext, CommandResult, CommandPriority
)
from .interfaces import FileService, CacheService, NotificationService
from .repositories import MetricsRepository

logger = logging.getLogger(__name__)


class CommandSystemConfiguration(BaseModel):
    """
    Configuration for the command system.
    
    Centralizes all command system settings for easy management
    and validation.
    
    Attributes:
        max_concurrent_commands: Maximum concurrent command executions
        command_queue_size: Maximum size of command queue (0 = unlimited)
        default_command_timeout: Default timeout for commands in seconds
        history_enabled: Whether to enable command history tracking
        history_persistent: Whether to persist history to disk
        history_file: Path to history file (if persistent)
        max_history_size: Maximum number of history entries to keep
        monitoring_enabled: Whether to enable command monitoring
        performance_tracking: Whether to track detailed performance metrics
        cache_directory: Default cache directory for commands
        array_directory: Default array directory for commands
        auto_cleanup_history: Whether to automatically cleanup old history
        cleanup_interval_hours: Hours between automatic cleanup
        alert_thresholds: Thresholds for monitoring alerts
    """
    
    max_concurrent_commands: int = Field(default=4, ge=1, le=20)
    command_queue_size: int = Field(default=100, ge=0)
    default_command_timeout: Optional[int] = Field(default=3600, ge=60)  # 1 hour
    
    history_enabled: bool = True
    history_persistent: bool = True
    history_file: Optional[str] = Field(default="data/command_history.json")
    max_history_size: int = Field(default=10000, ge=100)
    
    monitoring_enabled: bool = True
    performance_tracking: bool = True
    
    cache_directory: Optional[str] = None
    array_directory: Optional[str] = None
    
    auto_cleanup_history: bool = True
    cleanup_interval_hours: int = Field(default=24, ge=1)
    
    alert_thresholds: Dict[str, Any] = Field(default_factory=lambda: {
        "max_execution_time": 3600,  # 1 hour
        "max_queue_size": 100,
        "error_rate_threshold": 0.1,  # 10%
        "memory_threshold": 8 * 1024 * 1024 * 1024  # 8GB
    })


class CommandService:
    """
    Main command service for orchestrating command operations.
    
    Provides a high-level interface for command execution, management,
    and monitoring. Integrates all command system components through
    dependency injection.
    
    This service acts as the primary entry point for command operations
    and coordinates between the queue, executor, history, and monitoring
    systems.
    """
    
    def __init__(self, 
                 command_queue: ICommandQueue,
                 command_executor: ICommandExecutor,
                 command_history: Optional[ICommandHistory] = None,
                 command_monitor: Optional[CommandMonitor] = None,
                 command_factory: Optional[CacheCommandFactory] = None,
                 service_provider: Optional[DIContainer] = None):
        """
        Initialize command service.
        
        Args:
            command_queue: Command queue for managing execution order
            command_executor: Command executor for running commands
            command_history: Optional command history for tracking
            command_monitor: Optional monitoring system
            command_factory: Optional factory for creating commands
            service_provider: Service provider for dependency resolution
        """
        self.command_queue = command_queue
        self.command_executor = command_executor
        self.command_history = command_history
        self.command_monitor = command_monitor
        self.command_factory = command_factory
        self.service_provider = service_provider
        
        # Initialize command logger
        self.logger = CommandLogger(structured_logging=True)
        
        logger.info("CommandService initialized")
    
    def execute_command(self, command: ICommand, 
                       context: Optional[CommandContext] = None,
                       queue: bool = False) -> CommandResult:
        """
        Execute a command either immediately or through the queue.
        
        Args:
            command: Command to execute
            context: Optional execution context
            queue: Whether to queue the command for later execution
            
        Returns:
            CommandResult with execution details
        """
        # Create execution context if not provided
        if not context:
            context = CommandContext(
                services=self.service_provider,
                dry_run=False
            )
        
        # Start monitoring if available
        metrics = None
        if self.command_monitor:
            metrics = self.command_monitor.start_command_monitoring(command, context)
        
        # Log command start
        self.logger.log_command_start(command, context)
        
        try:
            if queue:
                # Queue for later execution
                queue_id = self.command_queue.enqueue_command(command)
                
                return CommandResult(
                    success=True,
                    message=f"Command queued for execution (Queue ID: {queue_id})",
                    data={
                        "queued": True,
                        "queue_id": str(queue_id),
                        "command_id": str(command.metadata.command_id)
                    }
                )
            else:
                # Execute immediately
                result = self.command_executor.execute_command(command, context)
                
                # Add to history if available
                if self.command_history:
                    self.command_history.add_command(command, result)
                
                # Complete monitoring if available
                if self.command_monitor and metrics:
                    self.command_monitor.complete_command_monitoring(command, result)
                
                # Log completion
                self.logger.log_command_completion(command, result, metrics)
                
                return result
                
        except Exception as e:
            # Log error
            self.logger.log_command_error(command, e)
            
            # Complete monitoring with error if available
            if self.command_monitor and metrics:
                error_result = CommandResult(
                    success=False,
                    message=f"Command execution failed: {str(e)}",
                    errors=[str(e)]
                )
                self.command_monitor.complete_command_monitoring(command, error_result)
            
            raise
    
    def execute_commands_batch(self, commands: List[ICommand],
                              context: Optional[CommandContext] = None,
                              parallel: bool = False) -> List[CommandResult]:
        """
        Execute multiple commands in batch.
        
        Args:
            commands: List of commands to execute
            context: Optional execution context
            parallel: Whether to execute in parallel
            
        Returns:
            List of CommandResult objects
        """
        if not commands:
            return []
        
        logger.info(f"Executing batch of {len(commands)} commands")
        
        results = []
        for command in commands:
            try:
                result = self.execute_command(command, context, queue=False)
                results.append(result)
            except Exception as e:
                error_result = CommandResult(
                    success=False,
                    message=f"Batch command failed: {str(e)}",
                    errors=[str(e)],
                    metadata={
                        "command_id": str(command.metadata.command_id),
                        "command_type": command.metadata.command_type
                    }
                )
                results.append(error_result)
        
        return results
    
    def create_cache_command(self, command_type: str, **kwargs) -> ICommand:
        """
        Create a cache command using the command factory.
        
        Args:
            command_type: Type of command to create
            **kwargs: Command parameters
            
        Returns:
            Created command instance
            
        Raises:
            ValueError: If command factory is not available or command type is invalid
        """
        if not self.command_factory:
            raise ValueError("Command factory is not available")
        
        return self.command_factory.create_command(command_type, **kwargs)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current command queue status."""
        return self.command_queue.get_queue_status()
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get command execution statistics."""
        stats = self.command_executor.get_execution_statistics()
        
        if self.command_monitor:
            monitoring_stats = self.command_monitor.get_monitoring_statistics()
            stats.update(monitoring_stats)
        
        return stats
    
    def get_command_history(self, limit: Optional[int] = None,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get command execution history.
        
        Args:
            limit: Maximum number of entries to return
            filters: Optional filters to apply
            
        Returns:
            List of history entries
        """
        if not self.command_history:
            return []
        
        return self.command_history.get_history(limit=limit, filters=filters)
    
    def undo_last_command(self, context: Optional[CommandContext] = None) -> Optional[CommandResult]:
        """
        Undo the last executed command.
        
        Args:
            context: Optional execution context
            
        Returns:
            CommandResult if undo was performed, None if nothing to undo
        """
        if not self.command_history:
            logger.warning("Cannot undo: command history is not available")
            return None
        
        return self.command_history.undo_last_command(context)
    
    def clear_queue(self, command_type_filter: Optional[str] = None) -> int:
        """
        Clear the command queue.
        
        Args:
            command_type_filter: Only clear commands of this type
            
        Returns:
            Number of commands cleared
        """
        return self.command_queue.clear_queue(command_type_filter)
    
    def pause_queue(self) -> None:
        """Pause command queue processing."""
        self.command_queue.pause_queue()
    
    def resume_queue(self) -> None:
        """Resume command queue processing."""
        self.command_queue.resume_queue()
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """
        Get performance insights and recommendations.
        
        Returns:
            Dictionary with performance analysis
        """
        if not self.command_monitor:
            return {"error": "Monitoring is not enabled"}
        
        return self.command_monitor.get_performance_insights()


class CommandServiceRegistry:
    """
    Service registration for the command system in the DI container.
    
    Handles registration of all command system components with the
    dependency injection container, including proper lifecycle
    management and service resolution.
    """
    
    @staticmethod
    def register_command_services(container: DIContainer,
                                 config: CommandSystemConfiguration) -> None:
        """
        Register all command system services in the DI container.
        
        Args:
            container: DI container to register services in
            config: Command system configuration
        """
        logger.info("Registering command system services...")
        
        # Register configuration
        container.register_instance(CommandSystemConfiguration, config)
        
        # Register command queue
        container.register_singleton(
            ICommandQueue,
            CommandQueue
        ).register_factory(
            CommandQueue,
            lambda provider: CommandQueue(
                max_size=config.command_queue_size,
                default_priority=CommandPriority.NORMAL
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register command executor
        container.register_factory(
            ICommandExecutor,
            lambda provider: CommandExecutionManager(
                command_queue=provider.resolve(CommandQueue),
                max_concurrent_commands=config.max_concurrent_commands,
                default_timeout=config.default_command_timeout,
                service_provider=provider
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register command history if enabled
        if config.history_enabled:
            if config.history_persistent and config.history_file:
                container.register_factory(
                    ICommandHistory,
                    lambda provider: PersistentCommandHistory(
                        history_file=config.history_file,
                        max_history_size=config.max_history_size,
                        auto_save=True
                    ),
                    ServiceLifetime.SINGLETON
                )
            else:
                container.register_factory(
                    ICommandHistory,
                    lambda provider: CommandHistory(
                        max_history_size=config.max_history_size,
                        auto_cleanup=config.auto_cleanup_history,
                        cleanup_interval_hours=config.cleanup_interval_hours
                    ),
                    ServiceLifetime.SINGLETON
                )
            
            # Register history manager
            container.register_factory(
                CommandHistoryManager,
                lambda provider: CommandHistoryManager(
                    history_backend=provider.resolve(ICommandHistory)
                ),
                ServiceLifetime.SINGLETON
            )
        
        # Register command monitor if enabled
        if config.monitoring_enabled:
            container.register_factory(
                CommandMonitor,
                lambda provider: CommandMonitor(
                    metrics_repository=provider.try_resolve(MetricsRepository),
                    notification_service=provider.try_resolve(NotificationService),
                    enable_performance_tracking=config.performance_tracking
                ),
                ServiceLifetime.SINGLETON
            )
        
        # Register command logger
        container.register_factory(
            CommandLogger,
            lambda provider: CommandLogger(
                structured_logging=True,
                log_level=logging.INFO
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register command factory
        container.register_factory(
            CacheCommandFactory,
            lambda provider: CacheCommandFactory(
                service_provider=provider,
                cache_directory=config.cache_directory,
                array_directory=config.array_directory,
                default_priority=CommandPriority.NORMAL
            ),
            ServiceLifetime.SINGLETON
        )
        
        # Register main command service
        container.register_factory(
            CommandService,
            lambda provider: CommandService(
                command_queue=provider.resolve(ICommandQueue),
                command_executor=provider.resolve(ICommandExecutor),
                command_history=provider.try_resolve(ICommandHistory),
                command_monitor=provider.try_resolve(CommandMonitor),
                command_factory=provider.resolve(CacheCommandFactory),
                service_provider=provider
            ),
            ServiceLifetime.SINGLETON
        )
        
        logger.info("Command system services registered successfully")
    
    @staticmethod
    def create_command_service_from_config(config_dict: Dict[str, Any]) -> CommandService:
        """
        Create a complete command service from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Configured CommandService instance
        """
        # Parse configuration
        config = CommandSystemConfiguration(**config_dict)
        
        # Create DI container
        container = DIContainer()
        
        # Register command services
        CommandServiceRegistry.register_command_services(container, config)
        
        # Resolve and return command service
        return container.resolve(CommandService)
    
    @staticmethod
    def register_with_existing_container(container: DIContainer,
                                       cache_directory: Optional[str] = None,
                                       array_directory: Optional[str] = None,
                                       enable_monitoring: bool = True,
                                       enable_history: bool = True) -> None:
        """
        Register command services with an existing DI container.
        
        Args:
            container: Existing DI container
            cache_directory: Cache directory path
            array_directory: Array directory path
            enable_monitoring: Whether to enable monitoring
            enable_history: Whether to enable history tracking
        """
        config = CommandSystemConfiguration(
            cache_directory=cache_directory,
            array_directory=array_directory,
            monitoring_enabled=enable_monitoring,
            history_enabled=enable_history
        )
        
        CommandServiceRegistry.register_command_services(container, config)


# Convenience function for easy integration
def setup_command_system(container: DIContainer,
                        cache_directory: Optional[str] = None,
                        array_directory: Optional[str] = None,
                        config_overrides: Optional[Dict[str, Any]] = None) -> CommandService:
    """
    Convenience function to set up the complete command system.
    
    Args:
        container: DI container to use
        cache_directory: Default cache directory
        array_directory: Default array directory
        config_overrides: Optional configuration overrides
        
    Returns:
        Configured CommandService instance
    """
    # Create base configuration
    config_data = {
        "cache_directory": cache_directory,
        "array_directory": array_directory
    }
    
    # Apply overrides
    if config_overrides:
        config_data.update(config_overrides)
    
    # Parse configuration
    config = CommandSystemConfiguration(**config_data)
    
    # Register services
    CommandServiceRegistry.register_command_services(container, config)
    
    # Return configured service
    return container.resolve(CommandService)