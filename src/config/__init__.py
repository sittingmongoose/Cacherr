# Configuration package for PlexCacheUltra

# Legacy configuration interface
from .settings import Config

# New configuration system (recommended)
try:
    from .settings_new import (
        get_application_config,
        get_config_manager,
        ConfigurationManager,
        LegacyConfigAdapter,
        is_config_production_ready,
        get_current_environment,
        is_docker_environment,
        is_development_environment,
        is_test_environment
    )
    from .factory import (
        ConfigurationFactory,
        ApplicationConfiguration,
        EnvironmentType,
        EnvironmentDetector
    )
    from .validators import (
        ConfigurationValidator,
        ValidationResult,
        ValidationSeverity
    )
    from .providers import (
        ChainedConfigProvider,
        EnvironmentConfigProvider,
        FileConfigProvider,
        InMemoryConfigProvider,
        ConfigProviderFactory
    )
    from .migrations import (
        ConfigurationMigrator,
        MigrationHistory,
        MigrationResult
    )
    from .service_registration import (
        register_configuration_services,
        register_test_configuration_services,
        register_development_configuration_services
    )
    
    # Mark new system as available
    NEW_CONFIG_SYSTEM_AVAILABLE = True
except ImportError as e:
    # Fallback if new system is not available
    NEW_CONFIG_SYSTEM_AVAILABLE = False
    import warnings
    warnings.warn(f"New configuration system not available: {e}", ImportWarning)

# Import configuration interfaces for dependency injection and type safety
from .interfaces import (
    ConfigProvider,
    EnvironmentConfig,
    PathConfiguration,
    PlexConfiguration,
    PathConfigurationModel,
    MediaConfiguration,
    PerformanceConfiguration,
    NotificationConfiguration,
    TestModeConfiguration
)


# Convenience functions for easy migration to new system
def get_config(use_new_system: bool = True):
    """
    Get configuration instance with optional new system usage.
    
    This function provides a smooth migration path from the legacy
    Config class to the new configuration system.
    
    Args:
        use_new_system: Whether to use new configuration system (if available)
        
    Returns:
        Configuration instance (legacy Config or new LegacyConfigAdapter)
    """
    if use_new_system and NEW_CONFIG_SYSTEM_AVAILABLE:
        return LegacyConfigAdapter()
    else:
        return Config(use_new_system=False)


def get_modern_config():
    """
    Get modern application configuration.
    
    This function returns the new ApplicationConfiguration object
    with full validation, environment detection, and modern features.
    
    Returns:
        ApplicationConfiguration instance
        
    Raises:
        ImportError: If new configuration system is not available
    """
    if not NEW_CONFIG_SYSTEM_AVAILABLE:
        raise ImportError(
            "New configuration system is not available. "
            "Please ensure all dependencies are installed."
        )
    
    return get_application_config()


def setup_configuration_for_environment(environment: str = 'auto'):
    """
    Set up configuration optimized for specific environment.
    
    Args:
        environment: Environment type ('auto', 'docker', 'development', 'test', 'production')
        
    Returns:
        Configuration instance appropriate for the environment
    """
    if not NEW_CONFIG_SYSTEM_AVAILABLE:
        return Config()
    
    if environment == 'auto':
        return get_application_config()
    
    env_map = {
        'docker': EnvironmentType.DOCKER,
        'development': EnvironmentType.DEVELOPMENT,
        'test': EnvironmentType.TEST,
        'production': EnvironmentType.BARE_METAL
    }
    
    if environment not in env_map:
        raise ValueError(f"Unknown environment: {environment}. Valid options: {list(env_map.keys()) + ['auto']}")
    
    manager = get_config_manager(force_reload=True, force_environment=env_map[environment])
    return manager.get_configuration()

__all__ = [
    # Legacy configuration (maintained for backward compatibility)
    'Config',
    
    # Configuration interfaces
    'ConfigProvider',
    'EnvironmentConfig', 
    'PathConfiguration',
    
    # Configuration models
    'PlexConfiguration',
    'PathConfigurationModel',
    'MediaConfiguration',
    'PerformanceConfiguration',
    'NotificationConfiguration',
    'TestModeConfiguration',
    
    # Convenience functions (always available)
    'get_config',
    'NEW_CONFIG_SYSTEM_AVAILABLE'
]

# Add new system exports if available
if NEW_CONFIG_SYSTEM_AVAILABLE:
    __all__.extend([
        # New configuration system (recommended)
        'get_application_config',
        'get_config_manager',
        'ConfigurationManager',
        'LegacyConfigAdapter',
        'is_config_production_ready',
        
        # Environment detection
        'get_current_environment',
        'is_docker_environment',
        'is_development_environment',
        'is_test_environment',
        
        # Core components
        'ConfigurationFactory',
        'ApplicationConfiguration',
        'EnvironmentType',
        'EnvironmentDetector',
        
        # Validation
        'ConfigurationValidator',
        'ValidationResult',
        'ValidationSeverity',
        
        # Providers
        'ChainedConfigProvider',
        'EnvironmentConfigProvider',
        'FileConfigProvider',
        'InMemoryConfigProvider',
        'ConfigProviderFactory',
        
        # Migration
        'ConfigurationMigrator',
        'MigrationHistory',
        'MigrationResult',
        
        # Service registration
        'register_configuration_services',
        'register_test_configuration_services',
        'register_development_configuration_services',
        
        # Additional convenience functions
        'get_modern_config',
        'setup_configuration_for_environment'
    ])
