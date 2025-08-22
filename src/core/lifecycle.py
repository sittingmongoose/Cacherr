"""
Service Lifecycle Management for PlexCacheUltra.

This module provides comprehensive lifecycle management for services including
initialization, startup, shutdown, health monitoring, and graceful disposal.
It implements patterns for managing service dependencies, startup ordering,
and coordinated shutdown sequences.

The lifecycle management system handles:
- Service initialization and startup ordering
- Health monitoring and status tracking
- Graceful shutdown with dependency consideration
- Resource cleanup and disposal
- Service recovery and restart capabilities
- Event notifications for lifecycle changes

Example:
    Basic lifecycle usage:
    
    ```python
    lifecycle_manager = ServiceLifecycleManager()
    
    # Register services with lifecycle
    lifecycle_manager.register_service(media_service, dependencies=[config_service])
    lifecycle_manager.register_service(cache_service, dependencies=[media_service, file_service])
    
    # Start all services in dependency order
    await lifecycle_manager.start_all()
    
    # Monitor and manage services
    health_status = lifecycle_manager.get_health_status()
    
    # Graceful shutdown
    await lifecycle_manager.shutdown_all()
    ```
"""

import asyncio
import threading
import time
import weakref
from abc import ABC, abstractmethod
from typing import (
    List, Dict, Optional, Set, Any, Callable, Awaitable, Union,
    Protocol, runtime_checkable
)
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """Represents the current state of a service in its lifecycle."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    DISPOSED = "disposed"


class HealthStatus(Enum):
    """Represents the health status of a service."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceLifecycleEvent(BaseModel):
    """
    Represents a service lifecycle event.
    
    Attributes:
        service_id: Unique identifier for the service
        service_type: Type of the service
        event_type: Type of lifecycle event
        previous_state: Previous service state (optional)
        new_state: New service state
        timestamp: When the event occurred
        error: Error information if event represents a failure
        metadata: Additional event metadata
    """
    service_id: str
    service_type: str
    event_type: str
    previous_state: Optional[ServiceState] = None
    new_state: ServiceState
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class HealthCheck(BaseModel):
    """
    Represents a health check result.
    
    Attributes:
        service_id: Unique identifier for the service
        status: Health status result
        timestamp: When the health check was performed
        response_time_ms: Response time in milliseconds
        error_message: Error message if health check failed
        details: Additional health check details
    """
    service_id: str
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


@runtime_checkable
class ILifecycleAware(Protocol):
    """
    Protocol for services that are aware of their lifecycle.
    
    Services implementing this protocol can participate in
    coordinated startup and shutdown sequences.
    """
    
    async def initialize(self) -> bool:
        """
        Initialize the service.
        
        Returns:
            True if initialization successful, False otherwise
        """
        ...
    
    async def start(self) -> bool:
        """
        Start the service.
        
        Returns:
            True if startup successful, False otherwise
        """
        ...
    
    async def stop(self) -> bool:
        """
        Stop the service gracefully.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        ...
    
    async def dispose(self) -> None:
        """Dispose the service and clean up resources."""
        ...


@runtime_checkable
class IHealthCheckable(Protocol):
    """
    Protocol for services that support health checking.
    
    Services implementing this protocol can report their health status
    for monitoring and management purposes.
    """
    
    async def check_health(self) -> HealthCheck:
        """
        Perform a health check on the service.
        
        Returns:
            HealthCheck result
        """
        ...


class LifecycleError(Exception):
    """Base exception for lifecycle management errors."""
    pass


class ServiceStartupError(LifecycleError):
    """Raised when service startup fails."""
    
    def __init__(self, service_id: str, reason: str, inner_exception: Exception = None):
        self.service_id = service_id
        self.reason = reason
        self.inner_exception = inner_exception
        
        message = f"Service '{service_id}' startup failed: {reason}"
        if inner_exception:
            message += f" (Inner exception: {str(inner_exception)})"
        
        super().__init__(message)


class ServiceShutdownError(LifecycleError):
    """Raised when service shutdown fails."""
    
    def __init__(self, service_id: str, reason: str, inner_exception: Exception = None):
        self.service_id = service_id
        self.reason = reason
        self.inner_exception = inner_exception
        
        message = f"Service '{service_id}' shutdown failed: {reason}"
        if inner_exception:
            message += f" (Inner exception: {str(inner_exception)})"
        
        super().__init__(message)


class DependencyError(LifecycleError):
    """Raised when service dependency issues occur."""
    
    def __init__(self, service_id: str, dependency_issues: List[str]):
        self.service_id = service_id
        self.dependency_issues = dependency_issues
        
        message = f"Service '{service_id}' has dependency issues: {', '.join(dependency_issues)}"
        super().__init__(message)


@dataclass
class ServiceDescriptor:
    """
    Describes a service and its lifecycle requirements.
    
    Attributes:
        service_id: Unique identifier for the service
        service_instance: The actual service instance
        service_type: Type information for the service
        dependencies: List of service IDs this service depends on
        dependents: List of service IDs that depend on this service
        startup_timeout: Maximum time allowed for service startup
        shutdown_timeout: Maximum time allowed for service shutdown
        health_check_interval: Interval between health checks
        restart_on_failure: Whether to restart service on failure
        max_restart_attempts: Maximum number of restart attempts
        metadata: Additional service metadata
    """
    service_id: str
    service_instance: Any
    service_type: type
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    startup_timeout: float = 30.0
    shutdown_timeout: float = 10.0
    health_check_interval: float = 60.0
    restart_on_failure: bool = False
    max_restart_attempts: int = 3
    restart_attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state
    current_state: ServiceState = ServiceState.UNINITIALIZED
    last_state_change: datetime = field(default_factory=datetime.utcnow)
    last_health_check: Optional[HealthCheck] = None
    startup_time: Optional[datetime] = None
    shutdown_time: Optional[datetime] = None


class ServiceLifecycleManager:
    """
    Manages the lifecycle of services including startup, shutdown, and health monitoring.
    
    This manager coordinates service initialization, startup ordering based on dependencies,
    health monitoring, and graceful shutdown with proper cleanup. It provides a centralized
    way to manage service lifecycles in complex applications.
    
    Features:
    - Dependency-based startup ordering
    - Parallel startup of independent services
    - Health monitoring with configurable intervals
    - Graceful shutdown with timeout handling
    - Service recovery and restart capabilities
    - Event notifications for lifecycle changes
    - Thread-safe operations
    
    Thread Safety:
        All operations are thread-safe and can be called from multiple threads.
    """
    
    def __init__(self, default_startup_timeout: float = 30.0,
                 default_shutdown_timeout: float = 10.0,
                 health_check_enabled: bool = True,
                 health_check_interval: float = 60.0):
        """
        Initialize the service lifecycle manager.
        
        Args:
            default_startup_timeout: Default timeout for service startup
            default_shutdown_timeout: Default timeout for service shutdown
            health_check_enabled: Whether to enable health checking
            health_check_interval: Default interval between health checks
        """
        self._services: Dict[str, ServiceDescriptor] = {}
        self._service_states: Dict[str, ServiceState] = {}
        self._lock = threading.RLock()
        self._event_listeners: List[Callable[[ServiceLifecycleEvent], None]] = []
        
        # Configuration
        self.default_startup_timeout = default_startup_timeout
        self.default_shutdown_timeout = default_shutdown_timeout
        self.health_check_enabled = health_check_enabled
        self.health_check_interval = health_check_interval
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_running = False
        self._shutdown_requested = False
        
        logger.info(
            "ServiceLifecycleManager initialized with startup_timeout=%.1fs, "
            "shutdown_timeout=%.1fs, health_check_enabled=%s",
            default_startup_timeout, default_shutdown_timeout, health_check_enabled
        )
    
    def register_service(self, service_instance: Any, service_id: Optional[str] = None,
                        dependencies: Optional[List[str]] = None,
                        startup_timeout: Optional[float] = None,
                        shutdown_timeout: Optional[float] = None,
                        health_check_interval: Optional[float] = None,
                        restart_on_failure: bool = False,
                        max_restart_attempts: int = 3,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a service for lifecycle management.
        
        Args:
            service_instance: The service instance to manage
            service_id: Unique identifier (auto-generated if not provided)
            dependencies: List of service IDs this service depends on
            startup_timeout: Custom startup timeout for this service
            shutdown_timeout: Custom shutdown timeout for this service
            health_check_interval: Custom health check interval for this service
            restart_on_failure: Whether to restart this service on failure
            max_restart_attempts: Maximum number of restart attempts
            metadata: Additional metadata for the service
            
        Returns:
            The service ID assigned to the service
            
        Raises:
            ValueError: If service_id is already registered
        """
        if service_id is None:
            service_id = f"{type(service_instance).__name__}_{id(service_instance)}"
        
        with self._lock:
            if service_id in self._services:
                raise ValueError(f"Service with ID '{service_id}' is already registered")
            
            descriptor = ServiceDescriptor(
                service_id=service_id,
                service_instance=service_instance,
                service_type=type(service_instance),
                dependencies=dependencies or [],
                startup_timeout=startup_timeout or self.default_startup_timeout,
                shutdown_timeout=shutdown_timeout or self.default_shutdown_timeout,
                health_check_interval=health_check_interval or self.health_check_interval,
                restart_on_failure=restart_on_failure,
                max_restart_attempts=max_restart_attempts,
                metadata=metadata or {}
            )
            
            self._services[service_id] = descriptor
            self._service_states[service_id] = ServiceState.UNINITIALIZED
            
            # Update dependents for dependencies
            for dependency_id in descriptor.dependencies:
                if dependency_id in self._services:
                    if service_id not in self._services[dependency_id].dependents:
                        self._services[dependency_id].dependents.append(service_id)
        
        logger.info(
            "Registered service '%s' of type %s with %d dependencies",
            service_id, type(service_instance).__name__, len(dependencies or [])
        )
        
        self._emit_event(ServiceLifecycleEvent(
            service_id=service_id,
            service_type=type(service_instance).__name__,
            event_type="service_registered",
            new_state=ServiceState.UNINITIALIZED,
            metadata={"dependencies": dependencies or []}
        ))
        
        return service_id
    
    def unregister_service(self, service_id: str) -> bool:
        """
        Unregister a service from lifecycle management.
        
        Args:
            service_id: ID of the service to unregister
            
        Returns:
            True if service was unregistered, False if not found
        """
        with self._lock:
            if service_id not in self._services:
                return False
            
            descriptor = self._services[service_id]
            
            # Remove from dependents of dependencies
            for dependency_id in descriptor.dependencies:
                if dependency_id in self._services:
                    if service_id in self._services[dependency_id].dependents:
                        self._services[dependency_id].dependents.remove(service_id)
            
            # Remove from services
            del self._services[service_id]
            del self._service_states[service_id]
        
        logger.info("Unregistered service '%s'", service_id)
        return True
    
    async def start_all(self, parallel: bool = True) -> Dict[str, bool]:
        """
        Start all registered services in dependency order.
        
        Args:
            parallel: Whether to start independent services in parallel
            
        Returns:
            Dictionary mapping service IDs to their startup success status
            
        Raises:
            DependencyError: If circular dependencies are detected
        """
        with self._lock:
            startup_order = self._calculate_startup_order()
        
        results = {}
        
        if parallel:
            # Start services in groups based on dependency levels
            dependency_levels = self._group_by_dependency_level(startup_order)
            
            for level, service_ids in dependency_levels.items():
                logger.info("Starting dependency level %d: %s", level, service_ids)
                
                # Start all services in this level in parallel
                tasks = []
                for service_id in service_ids:
                    task = asyncio.create_task(self._start_service(service_id))
                    tasks.append((service_id, task))
                
                # Wait for all services in this level to start
                for service_id, task in tasks:
                    try:
                        success = await task
                        results[service_id] = success
                        if not success:
                            logger.error("Service '%s' failed to start", service_id)
                    except Exception as e:
                        logger.error("Exception starting service '%s': %s", service_id, str(e))
                        results[service_id] = False
        else:
            # Start services sequentially
            for service_id in startup_order:
                try:
                    success = await self._start_service(service_id)
                    results[service_id] = success
                    if not success:
                        logger.error("Service '%s' failed to start", service_id)
                        break  # Stop on first failure in sequential mode
                except Exception as e:
                    logger.error("Exception starting service '%s': %s", service_id, str(e))
                    results[service_id] = False
                    break
        
        # Start health monitoring if enabled
        if self.health_check_enabled and not self._health_check_running:
            await self._start_health_monitoring()
        
        successful_starts = sum(1 for success in results.values() if success)
        logger.info(
            "Service startup completed: %d/%d services started successfully",
            successful_starts, len(results)
        )
        
        return results
    
    async def shutdown_all(self, timeout: Optional[float] = None) -> Dict[str, bool]:
        """
        Shutdown all services in reverse dependency order.
        
        Args:
            timeout: Maximum time to wait for all services to shutdown
            
        Returns:
            Dictionary mapping service IDs to their shutdown success status
        """
        self._shutdown_requested = True
        
        # Stop health monitoring
        if self._health_check_running:
            await self._stop_health_monitoring()
        
        with self._lock:
            shutdown_order = self._calculate_shutdown_order()
        
        results = {}
        overall_timeout = timeout or (self.default_shutdown_timeout * len(shutdown_order))
        start_time = time.time()
        
        for service_id in shutdown_order:
            remaining_time = overall_timeout - (time.time() - start_time)
            if remaining_time <= 0:
                logger.warning("Overall shutdown timeout reached, forcing remaining shutdowns")
                break
            
            try:
                success = await self._stop_service(service_id, timeout=min(
                    remaining_time,
                    self._services[service_id].shutdown_timeout
                ))
                results[service_id] = success
                if not success:
                    logger.warning("Service '%s' failed to shutdown gracefully", service_id)
            except Exception as e:
                logger.error("Exception shutting down service '%s': %s", service_id, str(e))
                results[service_id] = False
        
        successful_shutdowns = sum(1 for success in results.values() if success)
        logger.info(
            "Service shutdown completed: %d/%d services shutdown successfully",
            successful_shutdowns, len(results)
        )
        
        return results
    
    async def restart_service(self, service_id: str) -> bool:
        """
        Restart a specific service.
        
        Args:
            service_id: ID of the service to restart
            
        Returns:
            True if restart successful, False otherwise
        """
        if service_id not in self._services:
            logger.error("Cannot restart unknown service '%s'", service_id)
            return False
        
        logger.info("Restarting service '%s'", service_id)
        
        # Stop the service
        stop_success = await self._stop_service(service_id)
        if not stop_success:
            logger.warning("Service '%s' did not stop gracefully during restart", service_id)
        
        # Start the service
        start_success = await self._start_service(service_id)
        
        if start_success:
            logger.info("Service '%s' restarted successfully", service_id)
        else:
            logger.error("Service '%s' failed to restart", service_id)
        
        return start_success
    
    def get_service_state(self, service_id: str) -> Optional[ServiceState]:
        """
        Get the current state of a service.
        
        Args:
            service_id: ID of the service
            
        Returns:
            Current service state, or None if service not found
        """
        return self._service_states.get(service_id)
    
    def get_all_service_states(self) -> Dict[str, ServiceState]:
        """
        Get the current states of all services.
        
        Returns:
            Dictionary mapping service IDs to their current states
        """
        with self._lock:
            return self._service_states.copy()
    
    def get_health_status(self) -> Dict[str, HealthCheck]:
        """
        Get the latest health status for all services.
        
        Returns:
            Dictionary mapping service IDs to their latest health checks
        """
        health_status = {}
        
        with self._lock:
            for service_id, descriptor in self._services.items():
                if descriptor.last_health_check:
                    health_status[service_id] = descriptor.last_health_check
                else:
                    health_status[service_id] = HealthCheck(
                        service_id=service_id,
                        status=HealthStatus.UNKNOWN,
                        response_time_ms=0.0
                    )
        
        return health_status
    
    def add_event_listener(self, listener: Callable[[ServiceLifecycleEvent], None]) -> None:
        """
        Add an event listener for lifecycle events.
        
        Args:
            listener: Function to call when lifecycle events occur
        """
        self._event_listeners.append(listener)
        logger.debug("Added lifecycle event listener: %s", listener.__name__)
    
    def remove_event_listener(self, listener: Callable[[ServiceLifecycleEvent], None]) -> bool:
        """
        Remove an event listener.
        
        Args:
            listener: Event listener to remove
            
        Returns:
            True if listener was removed, False if not found
        """
        try:
            self._event_listeners.remove(listener)
            logger.debug("Removed lifecycle event listener: %s", listener.__name__)
            return True
        except ValueError:
            return False
    
    async def _start_service(self, service_id: str) -> bool:
        """Start a single service."""
        if service_id not in self._services:
            logger.error("Cannot start unknown service '%s'", service_id)
            return False
        
        descriptor = self._services[service_id]
        service_instance = descriptor.service_instance
        
        # Check if already running
        current_state = self._service_states[service_id]
        if current_state == ServiceState.RUNNING:
            logger.debug("Service '%s' is already running", service_id)
            return True
        
        # Check dependencies
        for dependency_id in descriptor.dependencies:
            dependency_state = self._service_states.get(dependency_id)
            if dependency_state != ServiceState.RUNNING:
                logger.error(
                    "Cannot start service '%s': dependency '%s' is not running (state: %s)",
                    service_id, dependency_id, dependency_state
                )
                return False
        
        try:
            # Update state to starting
            self._update_service_state(service_id, ServiceState.STARTING)
            
            start_time = time.time()
            
            # Initialize if implements ILifecycleAware
            if isinstance(service_instance, ILifecycleAware):
                self._update_service_state(service_id, ServiceState.INITIALIZING)
                
                init_success = await asyncio.wait_for(
                    service_instance.initialize(),
                    timeout=descriptor.startup_timeout / 2
                )
                
                if not init_success:
                    raise ServiceStartupError(service_id, "Service initialization returned False")
                
                self._update_service_state(service_id, ServiceState.INITIALIZED)
                
                # Start the service
                start_success = await asyncio.wait_for(
                    service_instance.start(),
                    timeout=descriptor.startup_timeout / 2
                )
                
                if not start_success:
                    raise ServiceStartupError(service_id, "Service start returned False")
            
            # Update state to running
            self._update_service_state(service_id, ServiceState.RUNNING)
            descriptor.startup_time = datetime.utcnow()
            
            startup_duration = time.time() - start_time
            logger.info(
                "Service '%s' started successfully in %.2f seconds",
                service_id, startup_duration
            )
            
            self._emit_event(ServiceLifecycleEvent(
                service_id=service_id,
                service_type=descriptor.service_type.__name__,
                event_type="service_started",
                previous_state=ServiceState.STARTING,
                new_state=ServiceState.RUNNING,
                metadata={"startup_duration": startup_duration}
            ))
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("Service '%s' startup timed out after %.1f seconds", 
                        service_id, descriptor.startup_timeout)
            self._update_service_state(service_id, ServiceState.FAILED)
            return False
        except Exception as e:
            logger.error("Service '%s' startup failed: %s", service_id, str(e))
            self._update_service_state(service_id, ServiceState.FAILED)
            
            self._emit_event(ServiceLifecycleEvent(
                service_id=service_id,
                service_type=descriptor.service_type.__name__,
                event_type="service_startup_failed",
                previous_state=ServiceState.STARTING,
                new_state=ServiceState.FAILED,
                error=str(e)
            ))
            
            return False
    
    async def _stop_service(self, service_id: str, timeout: Optional[float] = None) -> bool:
        """Stop a single service."""
        if service_id not in self._services:
            logger.error("Cannot stop unknown service '%s'", service_id)
            return False
        
        descriptor = self._services[service_id]
        service_instance = descriptor.service_instance
        shutdown_timeout = timeout or descriptor.shutdown_timeout
        
        # Check if already stopped
        current_state = self._service_states[service_id]
        if current_state in (ServiceState.STOPPED, ServiceState.DISPOSED):
            logger.debug("Service '%s' is already stopped", service_id)
            return True
        
        try:
            # Update state to stopping
            self._update_service_state(service_id, ServiceState.STOPPING)
            
            start_time = time.time()
            
            # Stop the service if implements ILifecycleAware
            if isinstance(service_instance, ILifecycleAware):
                stop_success = await asyncio.wait_for(
                    service_instance.stop(),
                    timeout=shutdown_timeout
                )
                
                if not stop_success:
                    logger.warning("Service '%s' stop returned False", service_id)
            
            # Update state to stopped
            self._update_service_state(service_id, ServiceState.STOPPED)
            descriptor.shutdown_time = datetime.utcnow()
            
            shutdown_duration = time.time() - start_time
            logger.info(
                "Service '%s' stopped successfully in %.2f seconds",
                service_id, shutdown_duration
            )
            
            self._emit_event(ServiceLifecycleEvent(
                service_id=service_id,
                service_type=descriptor.service_type.__name__,
                event_type="service_stopped",
                previous_state=ServiceState.STOPPING,
                new_state=ServiceState.STOPPED,
                metadata={"shutdown_duration": shutdown_duration}
            ))
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("Service '%s' shutdown timed out after %.1f seconds", 
                        service_id, shutdown_timeout)
            self._update_service_state(service_id, ServiceState.FAILED)
            return False
        except Exception as e:
            logger.error("Service '%s' shutdown failed: %s", service_id, str(e))
            self._update_service_state(service_id, ServiceState.FAILED)
            
            self._emit_event(ServiceLifecycleEvent(
                service_id=service_id,
                service_type=descriptor.service_type.__name__,
                event_type="service_shutdown_failed",
                previous_state=ServiceState.STOPPING,
                new_state=ServiceState.FAILED,
                error=str(e)
            ))
            
            return False
    
    def _calculate_startup_order(self) -> List[str]:
        """Calculate the order in which services should be started based on dependencies."""
        # Topological sort to determine startup order
        in_degree = {}
        graph = {}
        
        # Initialize
        for service_id in self._services:
            in_degree[service_id] = 0
            graph[service_id] = []
        
        # Build dependency graph
        for service_id, descriptor in self._services.items():
            for dependency_id in descriptor.dependencies:
                if dependency_id not in self._services:
                    raise DependencyError(service_id, [f"Unknown dependency: {dependency_id}"])
                
                graph[dependency_id].append(service_id)
                in_degree[service_id] += 1
        
        # Topological sort
        queue = [service_id for service_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            service_id = queue.pop(0)
            result.append(service_id)
            
            for dependent_id in graph[service_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        # Check for circular dependencies
        if len(result) != len(self._services):
            remaining = [sid for sid in self._services if sid not in result]
            raise DependencyError("circular_dependency", [f"Circular dependency detected involving: {remaining}"])
        
        return result
    
    def _calculate_shutdown_order(self) -> List[str]:
        """Calculate the order in which services should be shut down (reverse of startup order)."""
        startup_order = self._calculate_startup_order()
        return list(reversed(startup_order))
    
    def _group_by_dependency_level(self, startup_order: List[str]) -> Dict[int, List[str]]:
        """Group services by their dependency level for parallel startup."""
        levels = {}
        service_levels = {}
        
        # Calculate dependency level for each service
        for service_id in startup_order:
            descriptor = self._services[service_id]
            
            if not descriptor.dependencies:
                # No dependencies, level 0
                service_levels[service_id] = 0
            else:
                # Level is max of dependency levels + 1
                max_dep_level = max(
                    service_levels.get(dep_id, 0) for dep_id in descriptor.dependencies
                )
                service_levels[service_id] = max_dep_level + 1
        
        # Group by level
        for service_id, level in service_levels.items():
            if level not in levels:
                levels[level] = []
            levels[level].append(service_id)
        
        return levels
    
    def _update_service_state(self, service_id: str, new_state: ServiceState) -> None:
        """Update the state of a service and track the change."""
        with self._lock:
            if service_id not in self._services:
                return
            
            old_state = self._service_states.get(service_id)
            self._service_states[service_id] = new_state
            self._services[service_id].current_state = new_state
            self._services[service_id].last_state_change = datetime.utcnow()
        
        logger.debug("Service '%s' state changed: %s -> %s", service_id, old_state, new_state)
    
    def _emit_event(self, event: ServiceLifecycleEvent) -> None:
        """Emit a lifecycle event to all listeners."""
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error("Lifecycle event listener failed: %s", str(e))
    
    async def _start_health_monitoring(self) -> None:
        """Start the health monitoring background task."""
        if self._health_check_running:
            return
        
        self._health_check_running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health monitoring started")
    
    async def _stop_health_monitoring(self) -> None:
        """Stop the health monitoring background task."""
        if not self._health_check_running:
            return
        
        self._health_check_running = False
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
        
        logger.info("Health monitoring stopped")
    
    async def _health_check_loop(self) -> None:
        """Background loop for performing health checks."""
        while self._health_check_running and not self._shutdown_requested:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check loop error: %s", str(e))
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all running services."""
        tasks = []
        
        with self._lock:
            for service_id, descriptor in self._services.items():
                if (self._service_states[service_id] == ServiceState.RUNNING and
                    isinstance(descriptor.service_instance, IHealthCheckable)):
                    
                    task = asyncio.create_task(self._check_service_health(service_id))
                    tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service_id: str) -> None:
        """Perform health check on a specific service."""
        descriptor = self._services[service_id]
        service_instance = descriptor.service_instance
        
        try:
            start_time = time.time()
            health_check = await asyncio.wait_for(
                service_instance.check_health(),
                timeout=10.0  # Health check timeout
            )
            response_time = (time.time() - start_time) * 1000
            
            # Update response time if not set by service
            if health_check.response_time_ms == 0:
                health_check.response_time_ms = response_time
            
            with self._lock:
                descriptor.last_health_check = health_check
            
            # Handle unhealthy services
            if health_check.status == HealthStatus.UNHEALTHY and descriptor.restart_on_failure:
                if descriptor.restart_attempts < descriptor.max_restart_attempts:
                    logger.warning(
                        "Service '%s' is unhealthy, attempting restart (attempt %d/%d)",
                        service_id, descriptor.restart_attempts + 1, descriptor.max_restart_attempts
                    )
                    descriptor.restart_attempts += 1
                    
                    # Schedule restart (don't await to avoid blocking health checks)
                    asyncio.create_task(self.restart_service(service_id))
                else:
                    logger.error(
                        "Service '%s' has exceeded maximum restart attempts (%d)",
                        service_id, descriptor.max_restart_attempts
                    )
            
        except asyncio.TimeoutError:
            health_check = HealthCheck(
                service_id=service_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=10000,  # Timeout duration
                error_message="Health check timed out"
            )
            
            with self._lock:
                descriptor.last_health_check = health_check
                
        except Exception as e:
            health_check = HealthCheck(
                service_id=service_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=str(e)
            )
            
            with self._lock:
                descriptor.last_health_check = health_check
            
            logger.error("Health check failed for service '%s': %s", service_id, str(e))


# Global lifecycle manager instance for convenience
_global_lifecycle_manager: Optional[ServiceLifecycleManager] = None


def get_global_lifecycle_manager() -> ServiceLifecycleManager:
    """Get the global lifecycle manager instance, creating it if necessary."""
    global _global_lifecycle_manager
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = ServiceLifecycleManager()
    return _global_lifecycle_manager


def set_global_lifecycle_manager(manager: ServiceLifecycleManager) -> None:
    """Set the global lifecycle manager instance."""
    global _global_lifecycle_manager
    _global_lifecycle_manager = manager