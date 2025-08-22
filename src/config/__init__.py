# Configuration package for Cacherr

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

__all__ = [
    # Core configuration
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
    'TestModeConfiguration'
]
