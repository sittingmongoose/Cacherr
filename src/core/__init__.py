# Core functionality package for Cacherr

# Import main classes for easier access
from .plex_cache_engine import CacherrEngine
from .plex_operations import PlexOperations
from .plex_watcher import PlexWatcher
from .trakt_watcher import TraktWatcher
from .file_operations import FileOperations
from .notifications import NotificationManager

# Import interfaces for dependency injection and type safety
from .interfaces import (
    MediaService,
    FileService,
    NotificationService,
    CacheService,
    MediaFileInfo,
    CacheOperationResult,
    TestModeAnalysis,
    NotificationEvent
)

from .repositories import (
    CacheRepository,
    ConfigRepository,
    MetricsRepository,
    CacheEntry,
    WatchedItem,
    UserActivity,
    MetricsData,
    ConfigurationItem
)

# Import dependency injection components
from .container import (
    DIContainer,
    ServiceLifetime,
    ServiceRegistration,
    ServiceResolutionContext,
    IServiceProvider,
    ScopedServiceProvider,
    ContainerError,
    ServiceNotRegisteredException,
    CircularDependencyException,
    ServiceCreationException,
    MaxResolutionDepthExceededException,
    inject
)

from .factories import (
    IServiceFactory,
    BaseServiceFactory,
    MediaServiceFactory,
    FileServiceFactory,
    NotificationServiceFactory,
    CacheServiceFactory,
    ServiceFactoryRegistry,
    FactoryConfiguration,
    ServiceCreationError,
    ConfigurationValidationError,
    factory_registry,
    register_default_factories
)

from .lifecycle import (
    ServiceLifecycleManager,
    ServiceState,
    HealthStatus,
    ServiceLifecycleEvent,
    HealthCheck,
    ILifecycleAware,
    IHealthCheckable,
    ServiceDescriptor,
    LifecycleError,
    ServiceStartupError,
    ServiceShutdownError,
    DependencyError,
    get_global_lifecycle_manager,
    set_global_lifecycle_manager
)

from .service_configuration import (
    ServiceConfiguration,
    ServiceRegistrationInfo,
    EnvironmentServiceConfiguration,
    ServiceImplementationStrategy,
    ServiceConfigurationBuilder,
    IServiceConfigurationProvider,
    FileServiceConfigurationProvider,
    EnvironmentServiceConfigurationProvider,
    ConfigurationError,
    ServiceResolutionError
)

from .service_locator import (
    ServiceLocator,
    ScopedServiceLocator,
    IServiceLocator,
    ServiceLocationEvent,
    ServiceLocatorError,
    ServiceNotLocatedException,
    ServiceLocatorNotInitializedException,
    get_service,
    try_get_service,
    has_service,
    service_scope,
    locate_service,
    temporary_service_registration
)

# Import command system components
from .commands import (
    ICommand,
    IUndoableCommand,
    ICommandExecutor,
    ICommandHistory,
    ICommandQueue,
    CommandResult,
    CommandStatus,
    CommandMetadata,
    CommandContext,
    CommandPriority,
    BaseCommand,
    BaseUndoableCommand,
    CompositeCacheCommand,
    MoveToCache,
    MoveToArray,
    CopyToCache,
    DeleteFromCache,
    TestCacheOperation,
    AnalyzeCacheImpact,
    CleanupCache,
    ValidateCache,
    CommandFactory,
    CacheCommandFactory
)

from .command_queue import (
    CommandQueue,
    CommandExecutionManager,
    CommandQueueEntry,
    CommandQueueStatus
)

from .command_history import (
    CommandHistory,
    PersistentCommandHistory,
    CommandHistoryManager,
    CommandHistoryEntry
)

from .command_monitor import (
    CommandMonitor,
    CommandLogger,
    CommandMetrics
)

from .command_service import (
    CommandService,
    CommandSystemConfiguration,
    CommandServiceRegistry,
    setup_command_system
)

from .operation_integration import (
    CacheOperationHandler,
    LegacyOperationBridge,
    OperationCommandAdapter,
    create_operation_handler,
    create_legacy_bridge
)

__all__ = [
    # Core implementations
    'CacherrEngine',
    'PlexOperations', 
    'PlexWatcher',
    'TraktWatcher',
    'FileOperations',
    'NotificationManager',
    
    # Service interfaces
    'MediaService',
    'FileService',
    'NotificationService',
    'CacheService',
    
    # Repository interfaces
    'CacheRepository',
    'ConfigRepository',
    'MetricsRepository',
    
    # Data models
    'MediaFileInfo',
    'CacheOperationResult',
    'TestModeAnalysis',
    'NotificationEvent',
    'CacheEntry',
    'WatchedItem',
    'UserActivity',
    'MetricsData',
    'ConfigurationItem',
    
    # Dependency Injection Container
    'DIContainer',
    'ServiceLifetime',
    'ServiceRegistration',
    'ServiceResolutionContext',
    'IServiceProvider',
    'ScopedServiceProvider',
    'ContainerError',
    'ServiceNotRegisteredException',
    'CircularDependencyException',
    'ServiceCreationException',
    'MaxResolutionDepthExceededException',
    'inject',
    
    # Service Factories
    'IServiceFactory',
    'BaseServiceFactory',
    'MediaServiceFactory',
    'FileServiceFactory',
    'NotificationServiceFactory',
    'CacheServiceFactory',
    'ServiceFactoryRegistry',
    'FactoryConfiguration',
    'ServiceCreationError',
    'ConfigurationValidationError',
    'factory_registry',
    'register_default_factories',
    
    # Service Lifecycle Management
    'ServiceLifecycleManager',
    'ServiceState',
    'HealthStatus',
    'ServiceLifecycleEvent',
    'HealthCheck',
    'ILifecycleAware',
    'IHealthCheckable',
    'ServiceDescriptor',
    'LifecycleError',
    'ServiceStartupError',
    'ServiceShutdownError',
    'DependencyError',
    'get_global_lifecycle_manager',
    'set_global_lifecycle_manager',
    
    # Service Configuration
    'ServiceConfiguration',
    'ServiceRegistrationInfo',
    'EnvironmentServiceConfiguration',
    'ServiceImplementationStrategy',
    'ServiceConfigurationBuilder',
    'IServiceConfigurationProvider',
    'FileServiceConfigurationProvider',
    'EnvironmentServiceConfigurationProvider',
    'ConfigurationError',
    'ServiceResolutionError',
    
    # Service Locator
    'ServiceLocator',
    'ScopedServiceLocator',
    'IServiceLocator',
    'ServiceLocationEvent',
    'ServiceLocatorError',
    'ServiceNotLocatedException',
    'ServiceLocatorNotInitializedException',
    'get_service',
    'try_get_service',
    'has_service',
    'service_scope',
    'locate_service',
    'temporary_service_registration',
    
    # Command System - Core Interfaces
    'ICommand',
    'IUndoableCommand',
    'ICommandExecutor',
    'ICommandHistory',
    'ICommandQueue',
    'CommandResult',
    'CommandStatus',
    'CommandMetadata',
    'CommandContext',
    'CommandPriority',
    
    # Command System - Base Classes
    'BaseCommand',
    'BaseUndoableCommand',
    'CompositeCacheCommand',
    
    # Command System - Cache Commands
    'MoveToCache',
    'MoveToArray',
    'CopyToCache',
    'DeleteFromCache',
    'TestCacheOperation',
    'AnalyzeCacheImpact',
    'CleanupCache',
    'ValidateCache',
    
    # Command System - Factories
    'CommandFactory',
    'CacheCommandFactory',
    
    # Command System - Queue Management
    'CommandQueue',
    'CommandExecutionManager',
    'CommandQueueEntry',
    'CommandQueueStatus',
    
    # Command System - History Management
    'CommandHistory',
    'PersistentCommandHistory',
    'CommandHistoryManager',
    'CommandHistoryEntry',
    
    # Command System - Monitoring
    'CommandMonitor',
    'CommandLogger',
    'CommandMetrics',
    
    # Command System - Service Integration
    'CommandService',
    'CommandSystemConfiguration',
    'CommandServiceRegistry',
    'setup_command_system',
    
    # Command System - Operation Integration
    'CacheOperationHandler',
    'LegacyOperationBridge',
    'OperationCommandAdapter',
    'create_operation_handler',
    'create_legacy_bridge'
]
