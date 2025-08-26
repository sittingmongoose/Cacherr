# Configuration package for PlexCacheUltra

# Legacy configuration interface
from .settings import Config

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


# Convenience function for configuration access
def get_config():
    """Get configuration instance."""
    return Config()

__all__ = [
    # Configuration
    'Config',
    'get_config',
    
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
    'TestModeConfiguration'
]
