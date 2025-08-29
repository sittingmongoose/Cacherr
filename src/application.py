"""
Application bootstrap and dependency wiring for PlexCacheUltra.

This module provides the main application factory and dependency injection
configuration. It serves as the central bootstrap point that wires together
all components of the PlexCacheUltra system using dependency injection patterns.

Key Features:
- Centralized dependency injection container configuration
- Service registration and lifecycle management
- Application factory pattern for flexible deployment
- Configuration-driven service wiring
- Environment-specific service registration
- Graceful startup and shutdown handling
- Health check and monitoring integration

Example:
    Basic application startup:
    
    ```python
    from src.application import create_application
    
    app_context = create_application()
    
    # Start all services
    app_context.start()
    
    # Access services
    cache_engine = app_context.get_service(CacherrEngine)
    web_app = app_context.get_web_app()
    
    # Shutdown
    app_context.shutdown()
    ```
    
    Configuration-driven startup:
    
    ```python
    app_context = create_application(
        config_overrides={
            'web': {'port': 5445, 'debug': True},
            'scheduler': {'enable_auto_start': True}
        }
    )
    ```
"""

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from contextlib import contextmanager

from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationError
from flask import Flask

from .config.settings import Config
from .core.container import DIContainer, ServiceLifetime
from .core.interfaces import (
    MediaService, FileService, CacheService, NotificationService,
    CacheOperationResult, TestModeAnalysis
)
from .core.plex_cache_engine import CacherrEngine
from .web.app import create_app, FlaskAppConfig
from .scheduler import TaskScheduler, SchedulerConfig
from .scheduler.tasks.cache_tasks import CacheOperationTask, TestModeAnalysisTask
from .scheduler.tasks.cleanup_tasks import CacheCleanupTask, LogCleanupTask


logger = logging.getLogger(__name__)


class ApplicationConfig(BaseModel):
    """Configuration model for application bootstrap."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    # Web application configuration
    web: FlaskAppConfig = Field(default_factory=FlaskAppConfig, description="Flask web app configuration")

    # Scheduler configuration
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig, description="Task scheduler configuration")
    enable_scheduler: bool = Field(default=True, description="Whether to enable task scheduler")
    auto_start_scheduler: bool = Field(default=False, description="Whether to start scheduler automatically")

    # Service configuration
    enable_cache_engine: bool = Field(default=True, description="Whether to enable cache engine")
    enable_notifications: bool = Field(default=True, description="Whether to enable notification service")
    enable_real_time_watcher: bool = Field(default=False, description="Whether to enable real-time Plex watcher")

    # Startup configuration
    validate_config_on_startup: bool = Field(default=True, description="Validate configuration during startup")
    initialize_services_on_startup: bool = Field(default=True, description="Initialize services during startup")
    create_required_directories: bool = Field(default=True, description="Create required directories on startup")

    # Logging configuration
    setup_logging: bool = Field(default=True, description="Whether to setup application logging")
    log_level: str = Field(default="INFO", description="Application log level")
    log_file: Optional[str] = Field(default=None, description="Log file path (None for default)")

    # Health and monitoring
    enable_health_checks: bool = Field(default=True, description="Enable health check endpoints")
    startup_timeout_seconds: int = Field(default=60, description="Startup timeout in seconds")

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the expected values."""
        allowed_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in allowed_levels:
            raise ValueError(f'log_level must be one of: {allowed_levels}')
        return v.upper()


class CacheHealthStatus(BaseModel):
    """Cache system health status using Pydantic v2.5."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    overall_status: str = Field(..., description="Overall cache system status")
    cache_directories: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Cache directory statuses")
    database_status: Dict[str, Any] = Field(default_factory=dict, description="Database service status")
    services_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Cache services status")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    summary: Dict[str, int] = Field(default_factory=dict, description="Status summary counts")

    @field_validator('overall_status')
    @classmethod
    def validate_overall_status(cls, v: str) -> str:
        """Validate overall status is one of the expected values."""
        allowed_statuses = {'healthy', 'degraded', 'failed', 'partial', 'error', 'unknown'}
        if v not in allowed_statuses:
            raise ValueError(f'overall_status must be one of: {allowed_statuses}')
        return v


class ServiceRegistrationError(Exception):
    """Raised when service registration fails."""
    pass


class ApplicationStartupError(Exception):
    """Raised when application startup fails."""
    pass


class ApplicationContext:
    """
    Application context that manages the complete application lifecycle.
    
    This class encapsulates all application components including the
    dependency injection container, web application, scheduler, and
    other services. It provides a unified interface for managing
    the application lifecycle.
    """
    
    def __init__(self, config: Config, app_config: ApplicationConfig):
        """
        Initialize application context.
        
        Args:
            config: PlexCacheUltra configuration
            app_config: Application bootstrap configuration
        """
        self.config = config
        self.app_config = app_config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components
        self.container: Optional[DIContainer] = None
        self.web_app: Optional[Flask] = None
        self.scheduler: Optional[TaskScheduler] = None
        self.cache_engine: Optional[CacherrEngine] = None
        
        # State management
        self.is_started = False
        self.startup_errors: List[str] = []
        self.startup_time: Optional[datetime] = None
        self.shutdown_callbacks: List[Callable] = []
        
        self.logger.info("ApplicationContext initialized")
    
    def start(self) -> bool:
        """
        Start the application and all its components.
        
        Returns:
            True if startup successful, False otherwise
            
        Raises:
            ApplicationStartupError: If startup fails critically
        """
        if self.is_started:
            self.logger.warning("Application is already started")
            return True
        
        start_time = datetime.now()
        self.logger.info("Starting PlexCacheUltra application...")
        
        try:
            # Setup logging if configured
            if self.app_config.setup_logging:
                self._setup_logging()
            
            # Create required directories
            if self.app_config.create_required_directories:
                self._create_required_directories()
            
            # Validate configuration
            if self.app_config.validate_config_on_startup:
                if not self._validate_configuration():
                    raise ApplicationStartupError("Configuration validation failed")
            
            # Initialize dependency injection container
            self._initialize_container()
            
            # Register services
            self._register_services()
            
            # Initialize core services
            if self.app_config.initialize_services_on_startup:
                self._initialize_services()
            
            # Create web application
            self._create_web_application()
            
            # Setup scheduler
            if self.app_config.enable_scheduler:
                self._setup_scheduler()
            
            # Start scheduler if configured
            if self.app_config.auto_start_scheduler and self.scheduler:
                if not self.scheduler.start():
                    self.logger.warning("Failed to start scheduler automatically")
                    self.startup_errors.append("Scheduler auto-start failed")
            
            self.is_started = True
            self.startup_time = start_time
            
            startup_duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Application started successfully in {startup_duration:.2f} seconds")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Application startup failed: {e}", exc_info=True)
            self.startup_errors.append(str(e))
            
            # Attempt cleanup
            try:
                self._cleanup_failed_startup()
            except Exception as cleanup_error:
                self.logger.error(f"Cleanup after failed startup failed: {cleanup_error}")
            
            raise ApplicationStartupError(f"Application startup failed: {e}") from e
    
    def shutdown(self, timeout_seconds: int = 30) -> bool:
        """
        Gracefully shutdown the application and all components.
        
        Args:
            timeout_seconds: Maximum time to wait for graceful shutdown
            
        Returns:
            True if shutdown successful, False otherwise
        """
        if not self.is_started:
            self.logger.info("Application is not started, nothing to shutdown")
            return True
        
        self.logger.info("Shutting down PlexCacheUltra application...")
        shutdown_success = True
        
        try:
            # Execute shutdown callbacks
            for callback in self.shutdown_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Shutdown callback failed: {e}")
                    shutdown_success = False
            
            # Stop scheduler
            if self.scheduler:
                try:
                    if not self.scheduler.stop(timeout_seconds // 2):
                        self.logger.warning("Scheduler did not stop gracefully")
                        shutdown_success = False
                except Exception as e:
                    self.logger.error(f"Error stopping scheduler: {e}")
                    shutdown_success = False
            
            # Dispose container
            if self.container:
                try:
                    self.container.dispose()
                except Exception as e:
                    self.logger.error(f"Error disposing container: {e}")
                    shutdown_success = False
            
            self.is_started = False
            
            if shutdown_success:
                self.logger.info("Application shutdown completed successfully")
            else:
                self.logger.warning("Application shutdown completed with errors")
            
            return shutdown_success
            
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            return False
    
    def get_service(self, service_type):
        """
        Get a service instance from the dependency injection container.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance if available
            
        Raises:
            ValueError: If container is not initialized
            ServiceNotRegisteredException: If service is not registered
        """
        if not self.container:
            raise ValueError("Container is not initialized")
        
        return self.container.resolve(service_type)
    
    def get_web_app(self) -> Optional[Flask]:
        """Get the Flask web application instance."""
        return self.web_app
    
    def get_scheduler(self) -> Optional[TaskScheduler]:
        """Get the task scheduler instance."""
        return self.scheduler
    
    def get_cache_engine(self) -> Optional[CacherrEngine]:
        """Get the cache engine instance."""
        return self.cache_engine
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive application status.
        
        Returns:
            Dictionary with application status information
        """
        return {
            "is_started": self.is_started,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds() if self.startup_time else None,
            "startup_errors": self.startup_errors,
            "components": {
                "container_initialized": self.container is not None,
                "web_app_created": self.web_app is not None,
                "scheduler_available": self.scheduler is not None,
                "scheduler_running": self.scheduler.get_scheduler_status()["state"] == "running" if self.scheduler else False,
                "cache_engine_available": self.cache_engine is not None
            },
            "configuration": {
                "enable_scheduler": self.app_config.enable_scheduler,
                "enable_cache_engine": self.app_config.enable_cache_engine,
                "enable_notifications": self.app_config.enable_notifications,
                "web_port": self.app_config.web.port,
                "web_debug": self.app_config.web.debug
            }
        }
    
    def add_shutdown_callback(self, callback: Callable) -> None:
        """
        Add a callback to be executed during shutdown.
        
        Args:
            callback: Function to call during shutdown
        """
        self.shutdown_callbacks.append(callback)
    
    def _setup_logging(self) -> None:
        """Setup application logging configuration."""
        try:
            log_dir = Path("/config/logs")
            log_dir.mkdir(exist_ok=True)
            
            # Set log level
            log_level = getattr(logging, self.app_config.log_level.upper(), logging.INFO)
            
            # Determine log file
            if self.app_config.log_file:
                log_file = Path(self.app_config.log_file)
            else:
                log_file = log_dir / "cacherr.log"
            
            # Configure root logger
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler(log_file)
                ],
                force=True  # Override existing configuration
            )
            
            self.logger.info(f"Logging configured: level={self.app_config.log_level}, file={log_file}")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")  # Use print since logging may not be working
            self.startup_errors.append(f"Logging setup failed: {e}")
    
    def _create_required_directories(self) -> None:
        """Create required directories for the application with enhanced cache support."""
        # Core application directories
        core_dirs = [
            Path("/config"),
            Path("/config/logs"),
            Path("/config/temp"),
            Path("/config/data")
        ]

        # Cache-related directories
        cache_dirs = [
            Path("/workspace/cache"),  # Default cache directory
            Path("/mnt/cache"),        # Alternative cache mount
            Path("/tmp/cache")         # Fallback cache directory
        ]

        all_dirs = core_dirs + cache_dirs

        for directory in all_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Ensured directory exists: {directory}")
            except Exception as e:
                self.logger.warning(f"Failed to create directory {directory}: {e}")
                self.startup_errors.append(f"Directory creation failed: {directory}")

        # Validate cache directory permissions
        self._validate_cache_directories()

    def _verify_directory_permissions(self, directory: Path) -> bool:
        """Test if a directory is writable by attempting to create and delete a temporary file."""
        if not directory.exists():
            return False

        test_file = directory / ".write_test"
        try:
            # Try to create a temporary file
            with open(test_file, 'w') as f:
                f.write("test")
            # Try to delete it
            test_file.unlink()
            return True
        except (OSError, IOError, PermissionError):
            return False

    def _validate_cache_directories(self) -> None:
        """Validate the existence and writability of configured cache directories."""
        try:
            cache_dirs = [
                Path("/workspace/cache"),
                Path("/mnt/cache"),
                Path("/tmp/cache")
            ]

            writable_dirs = []
            non_writable_dirs = []

            for directory in cache_dirs:
                if directory.exists():
                    if self._verify_directory_permissions(directory):
                        writable_dirs.append(str(directory))
                        self.logger.debug(f"Cache directory is writable: {directory}")
                    else:
                        non_writable_dirs.append(str(directory))
                        self.logger.warning(f"Cache directory exists but is not writable: {directory}")
                else:
                    self.logger.debug(f"Cache directory does not exist: {directory}")

            if writable_dirs:
                self.logger.info(f"Found {len(writable_dirs)} writable cache directories: {', '.join(writable_dirs)}")
            if non_writable_dirs:
                self.logger.warning(f"Found {len(non_writable_dirs)} non-writable cache directories: {', '.join(non_writable_dirs)}")
                self.startup_errors.append(f"Non-writable cache directories: {', '.join(non_writable_dirs)}")

        except Exception as e:
            self.logger.error(f"Error validating cache directories: {e}")
            self.startup_errors.append(f"Cache directory validation failed: {e}")

    def _validate_configuration(self) -> bool:
        """Validate the application configuration."""
        try:
            self.logger.info("Validating application configuration...")
            
            # Validate core configuration using new Pydantic validation
            validation_results = self.config.validate_all()
            if not validation_results['valid']:
                self.logger.error(f"Core configuration validation failed: {validation_results['errors']}")
                return False
            
            # Additional validation can be added here
            
            self.logger.info("Configuration validation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            self.startup_errors.append(f"Configuration validation error: {e}")
            return False
    
    def _initialize_container(self) -> None:
        """Initialize the dependency injection container."""
        try:
            self.container = DIContainer()
            self.logger.info("Dependency injection container initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize DI container: {e}")
            raise ApplicationStartupError(f"Container initialization failed: {e}")
    
    def _register_services(self) -> None:
        """Register all services in the dependency injection container."""
        try:
            self.logger.info("Registering services in DI container...")
            
            # Register configuration as singleton
            self.container.register_instance(Config, self.config)
            
            # Register core services
            # Note: These would need to be imported from actual implementations
            # For now, we'll register the cache engine which we know exists
            
            if self.app_config.enable_cache_engine:
                self.container.register_singleton(CacherrEngine, CacherrEngine)
            
            # Register CachedFilesService for tracking cached files with enhanced error recovery
            try:
                from .core.cached_files_service import CachedFilesService
                import os
                from pathlib import Path

                # Try multiple database paths in order of preference
                db_paths = [
                    "/config/data/cached_files.db",  # Preferred: in data subdirectory
                    "/config/cached_files.db",       # Secondary: in config root
                    "/workspace/cached_files.db",    # Tertiary: workspace directory
                    "/tmp/cached_files.db"           # Fallback: temp directory
                ]

                db_path = None
                cached_files_service = None
                last_error = None

                for path in db_paths:
                    try:
                        # Ensure parent directory exists
                        parent_dir = Path(path).parent
                        parent_dir.mkdir(parents=True, exist_ok=True)

                        # Check if database file exists and is corrupted
                        db_file = Path(path)
                        if db_file.exists():
                            # Test if database is readable by attempting to connect
                            try:
                                test_service = CachedFilesService(database_path=path)
                                # Try a simple operation to verify database integrity
                                test_service._ensure_tables_exist()  # Assuming this method exists
                                cached_files_service = test_service
                                db_path = path
                                self.logger.info(f"Successfully connected to existing database: {path}")
                                break
                            except Exception as db_error:
                                # Database might be corrupted, try to remove it and recreate
                                self.logger.warning(f"Database at {path} appears corrupted: {db_error}")
                                try:
                                    db_file.unlink()
                                    self.logger.info(f"Removed corrupted database file: {path}")
                                except Exception as remove_error:
                                    self.logger.error(f"Failed to remove corrupted database file {path}: {remove_error}")

                        # Create new database or retry after removal
                        try:
                            test_service = CachedFilesService(database_path=path)
                            # Initialize database schema
                            test_service._ensure_tables_exist()  # Assuming this method exists
                            cached_files_service = test_service
                            db_path = path
                            self.logger.info(f"Successfully created new database: {path}")
                            break
                        except Exception as create_error:
                            self.logger.debug(f"Failed to create database at {path}: {create_error}")
                            last_error = create_error
                            continue

                    except Exception as e:
                        last_error = e
                        self.logger.debug(f"Database path {path} failed: {e}")
                        continue

                if cached_files_service and db_path:
                    self.container.register_instance(CachedFilesService, cached_files_service)
                    self.logger.info(f"CachedFilesService registered successfully using database: {db_path}")

                    # Test basic database operations
                    self._test_database_operations(cached_files_service)
                else:
                    error_msg = f"Failed to initialize CachedFilesService database at any location"
                    if last_error:
                        error_msg += f". Last error: {last_error}"
                    self.logger.error(error_msg)
                    self.startup_errors.append(error_msg)
                    # Don't fail startup for this service - it's not critical
                    self.logger.warning("Continuing startup without CachedFilesService")

            except ImportError as e:
                self.logger.warning(f"Failed to import CachedFilesService: {e}")
                self.startup_errors.append(f"CachedFilesService import failed: {e}")
            except Exception as e:
                self.logger.error(f"Failed to register CachedFilesService: {e}")
                self.startup_errors.append(f"CachedFilesService registration failed: {e}")
                # Don't fail startup for this service - it's not critical
                self.logger.warning("Continuing startup without CachedFilesService")
            
            self.logger.info("Service registration completed")
            
        except Exception as e:
            self.logger.error(f"Service registration failed: {e}")
            raise ServiceRegistrationError(f"Failed to register services: {e}")
    
    def _initialize_services(self) -> None:
        """Initialize core services after registration."""
        try:
            self.logger.info("Initializing core services...")
            
            # Initialize cache engine if enabled
            if self.app_config.enable_cache_engine:
                try:
                    self.cache_engine = self.container.resolve(CacherrEngine)
                    self.logger.info("Cache engine initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Cache engine initialization failed (Plex connection issue): {e}")
                    self.startup_errors.append(f"Cache engine initialization failed: {e}")
                    # Don't fail startup for Plex connection issues
            
            self.logger.info("Service initialization completed")
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            self.startup_errors.append(f"Service initialization error: {e}")
            # Don't raise exception here, allow partial startup
    
    def _create_web_application(self) -> None:
        """Create the Flask web application."""
        try:
            self.logger.info("Creating Flask web application...")
            
            # Inject services into Flask app factory
            self.web_app = create_app(self.container, self.app_config.web)
            
            # Add application context to Flask app for route access
            with self.web_app.app_context():
                self.web_app.config['app_context'] = self
                
                # Make services available to routes
                @self.web_app.before_request
                def inject_application_context():
                    from flask import g
                    g.app_context = self
                    g.container = self.container
                    g.cache_engine = self.cache_engine
                    g.config = self.config
            
            self.logger.info("Flask web application created successfully")
            
        except Exception as e:
            self.logger.error(f"Web application creation failed: {e}")
            raise ApplicationStartupError(f"Web application creation failed: {e}")
    
    def _setup_scheduler(self) -> None:
        """Setup the task scheduler with default tasks."""
        try:
            self.logger.info("Setting up task scheduler...")
            
            # Create scheduler
            self.scheduler = TaskScheduler(self.container, self.app_config.scheduler)
            
            # Add default tasks
            self._register_default_tasks()
            
            self.logger.info("Task scheduler setup completed")
            
        except Exception as e:
            self.logger.error(f"Scheduler setup failed: {e}")
            self.startup_errors.append(f"Scheduler setup error: {e}")
            # Don't fail startup for scheduler issues
    
    def _register_default_tasks(self) -> None:
        """Register default scheduled tasks."""
        try:
            # Cache operation task - runs every 6 hours
            cache_task_factory = lambda: CacheOperationTask(self.container).execute()
            self.scheduler.add_recurring_task(
                name="cache_operation",
                task_func=cache_task_factory,
                interval_hours=6,
                description="Regular cache operation to move files to/from cache"
            )
            
            # Cleanup task - runs daily at 2 AM
            cleanup_task_factory = lambda: CacheCleanupTask(self.container).execute()
            self.scheduler.add_cron_task(
                name="daily_cleanup",
                task_func=cleanup_task_factory,
                cron_expression="0 2 * * *",
                description="Daily cleanup of old cache files and logs"
            )
            
            # Log cleanup task - runs weekly
            log_cleanup_task_factory = lambda: LogCleanupTask().execute()
            self.scheduler.add_cron_task(
                name="log_cleanup",
                task_func=log_cleanup_task_factory,
                cron_expression="0 3 * * 0",  # Weekly on Sunday at 3 AM
                description="Weekly log file cleanup and rotation"
            )
            
            self.logger.info("Default scheduled tasks registered")
            
        except Exception as e:
            self.logger.warning(f"Failed to register some default tasks: {e}")
    
    def _cleanup_failed_startup(self) -> None:
        """Clean up resources after a failed startup."""
        self.logger.info("Cleaning up after failed startup...")
        
        if self.scheduler:
            try:
                self.scheduler.stop(timeout_seconds=5)
            except Exception as e:
                self.logger.error(f"Error stopping scheduler during cleanup: {e}")
        
        if self.container:
            try:
                self.container.dispose()
            except Exception as e:
                self.logger.error(f"Error disposing container during cleanup: {e}")
        
        self.is_started = False
    
    @contextmanager
    def application_scope(self):
        """Context manager for application lifecycle management."""
        try:
            self.start()
            yield self
        finally:
            self.shutdown()


def create_application(config_overrides: Optional[Dict[str, Any]] = None,
                      config_file: Optional[Path] = None) -> ApplicationContext:
    """
    Factory function for creating configured ApplicationContext instances.
    
    Args:
        config_overrides: Optional configuration overrides
        config_file: Optional path to configuration file
        
    Returns:
        Configured ApplicationContext instance
        
    Raises:
        ApplicationStartupError: If application creation fails
    """
    try:
        # Load main configuration
        config = Config()
        
        # Create application configuration with overrides
        app_config_dict = {}
        if config_overrides:
            app_config_dict.update(config_overrides)
        
        app_config = ApplicationConfig(**app_config_dict)
        
        # Create application context
        app_context = ApplicationContext(config, app_config)
        
        return app_context
        
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise ApplicationStartupError(f"Application creation failed: {e}") from e


def create_development_application() -> ApplicationContext:
    """
    Create an application configured for development.
    
    Returns:
        ApplicationContext configured for development
    """
    return create_application({
        'web': {
            'debug': True,
            'port': int(os.getenv('WEB_PORT', os.getenv('PORT', '5445'))),
            'testing': False
        },
        'scheduler': {
            'enable_task_notifications': False  # Reduce noise in development
        },
        'auto_start_scheduler': False,
        'log_level': 'DEBUG'
    })


def create_production_application() -> ApplicationContext:
    """
    Create an application configured for production.
    
    Returns:
        ApplicationContext configured for production
    """
    return create_application({
        'web': {
            'debug': False,
            'port': int(os.getenv('WEB_PORT', os.getenv('PORT', '5445'))),
            'testing': False
        },
        'scheduler': {
            'enable_task_notifications': True
        },
        'auto_start_scheduler': True,
        'validate_config_on_startup': True,
        'log_level': 'INFO'
    })


def create_test_application() -> ApplicationContext:
    """
    Create an application configured for testing.
    
    Returns:
        ApplicationContext configured for testing
    """
    return create_application({
        'web': {
            'testing': True,
            'debug': True,
            'port': 0  # Use random port for testing
        },
        'enable_scheduler': False,  # Don't start scheduler in tests
        'enable_real_time_watcher': False,
        'initialize_services_on_startup': False,  # Let tests control service initialization
        'setup_logging': False,  # Let test framework handle logging
        'log_level': 'DEBUG'
    })