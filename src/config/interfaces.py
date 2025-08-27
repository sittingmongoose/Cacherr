"""
Configuration interfaces for PlexCacheUltra.

This module defines the configuration interfaces that establish clear contracts
for configuration management, environment detection, and path operations.
These interfaces support dependency injection and enable flexible configuration
sources including environment variables, files, and remote configuration systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseModel, Field


class PathConfigurationModel(BaseModel):
    """Pydantic model for path configuration with validation."""
    plex_source: str = Field(..., description="Source path for Plex media files")
    cache_destination: str = Field(..., description="Destination path for cached files") 
    config_directory: Optional[str] = Field(None, description="Configuration directory path")
    log_directory: Optional[str] = Field(None, description="Log directory path")
    data_directory: Optional[str] = Field(None, description="Data directory path")
    temp_directory: Optional[str] = Field(None, description="Temporary directory path")


class PlexConfiguration(BaseModel):
    """Pydantic model for Plex server configuration."""
    url: str = Field(..., description="Plex server URL")
    token: str = Field(..., description="Plex authentication token")
    library_names: List[str] = Field(default_factory=list, description="Library names to monitor")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class MediaConfiguration(BaseModel):
    """Pydantic model for media handling configuration."""
    supported_formats: List[str] = Field(default_factory=lambda: ['.mkv', '.mp4', '.avi', '.mov'], 
                                       description="Supported media file formats")
    max_file_size_gb: Optional[float] = Field(None, description="Maximum file size in GB")
    min_file_size_mb: Optional[float] = Field(None, description="Minimum file size in MB")
    exclude_patterns: List[str] = Field(default_factory=list, description="File patterns to exclude")


class PerformanceConfiguration(BaseModel):
    """Pydantic model for performance configuration."""
    max_concurrent_operations: int = Field(default=5, description="Maximum concurrent file operations")
    chunk_size_mb: int = Field(default=64, description="File operation chunk size in MB")
    enable_progress_reporting: bool = Field(default=True, description="Enable operation progress reporting")
    memory_limit_mb: Optional[int] = Field(None, description="Memory usage limit in MB")


class NotificationConfiguration(BaseModel):
    """Pydantic model for notification configuration."""
    enabled: bool = Field(default=True, description="Enable notifications")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    webhook_headers: Dict[str, str] = Field(default_factory=dict, description="Additional headers for webhook requests")
    notification_levels: List[str] = Field(default_factory=lambda: ['error', 'warning', 'info'], 
                                         description="Enabled notification levels")
    rate_limit_minutes: int = Field(default=5, description="Rate limit for notifications in minutes")


class TestModeConfiguration(BaseModel):
    """Pydantic model for test mode configuration."""
    enabled: bool = Field(default=False, description="Enable test mode")
    dry_run: bool = Field(default=True, description="Perform dry run operations")
    max_test_files: int = Field(default=10, description="Maximum files to process in test mode")
    test_data_path: Optional[str] = Field(None, description="Path to test data")


class RealTimeWatchConfiguration(BaseModel):
    """Pydantic model for real-time watch configuration."""
    enabled: bool = Field(default=False, description="Enable real-time Plex watching")
    check_interval: int = Field(default=30, description="Check interval in seconds")
    auto_cache_on_watch: bool = Field(default=True, description="Automatically cache media when watching starts")
    cache_on_complete: bool = Field(default=True, description="Cache media when watching completes")
    respect_existing_rules: bool = Field(default=True, description="Respect existing caching rules")
    max_concurrent_watches: int = Field(default=5, description="Maximum concurrent watches to process")
    remove_from_cache_after_hours: int = Field(default=24, description="Hours before removing media from cache (0 = never)")
    respect_other_users_watchlists: bool = Field(default=True, description="Respect other users' watchlists")
    exclude_inactive_users_days: int = Field(default=30, description="Days of inactivity before excluding users (0 = no exclusion)")


class TraktConfiguration(BaseModel):
    """Pydantic model for Trakt.tv configuration."""
    enabled: bool = Field(default=False, description="Enable Trakt.tv integration")
    client_id: Optional[str] = Field(None, description="Trakt.tv API client ID")
    client_secret: Optional[str] = Field(None, description="Trakt.tv API client secret")
    trending_movies_count: int = Field(default=10, description="Number of trending movies to fetch")
    check_interval: int = Field(default=3600, description="Check interval in seconds")


class WebConfiguration(BaseModel):
    """Pydantic model for web server configuration."""
    host: str = Field(default="0.0.0.0", description="Web server host")
    port: int = Field(default=5445, description="Web server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    enable_scheduler: bool = Field(default=True, description="Enable task scheduler")


class ConfigProvider(ABC):
    """
    Interface for configuration value providers.
    
    Provides methods for retrieving typed configuration values from various sources
    including environment variables, configuration files, and remote configuration
    systems. Supports hierarchical configuration with section-based organization.
    """
    
    @abstractmethod
    def get_string(self, key: str, default: Optional[str] = None, section: Optional[str] = None) -> str:
        """
        Get a string configuration value.
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            section: Configuration section (optional)
            
        Returns:
            Configuration value as string
            
        Raises:
            KeyError: If key not found and no default provided
            ValueError: If value cannot be converted to string
        """
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: Optional[int] = None, section: Optional[str] = None) -> int:
        """
        Get an integer configuration value.
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            section: Configuration section (optional)
            
        Returns:
            Configuration value as integer
            
        Raises:
            KeyError: If key not found and no default provided
            ValueError: If value cannot be converted to integer
        """
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: Optional[bool] = None, section: Optional[str] = None) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            section: Configuration section (optional)
            
        Returns:
            Configuration value as boolean
            
        Raises:
            KeyError: If key not found and no default provided
            ValueError: If value cannot be converted to boolean
        """
        pass
    
    @abstractmethod
    def get_float(self, key: str, default: Optional[float] = None, section: Optional[str] = None) -> float:
        """
        Get a float configuration value.
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            section: Configuration section (optional)
            
        Returns:
            Configuration value as float
            
        Raises:
            KeyError: If key not found and no default provided
            ValueError: If value cannot be converted to float
        """
        pass
    
    @abstractmethod
    def get_list(self, key: str, default: Optional[List[str]] = None, section: Optional[str] = None, 
                 separator: str = ",") -> List[str]:
        """
        Get a list configuration value.
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            section: Configuration section (optional)
            separator: Character to split string values on
            
        Returns:
            Configuration value as list of strings
            
        Raises:
            KeyError: If key not found and no default provided
        """
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any, section: Optional[str] = None) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key name
            value: Configuration value
            section: Configuration section (optional)
            
        Raises:
            ValueError: If value type is not supported
            PermissionError: If configuration is read-only
        """
        pass
    
    @abstractmethod
    def reload(self) -> bool:
        """
        Reload configuration from source.
        
        Returns:
            True if reload was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_all_keys(self, section: Optional[str] = None) -> List[str]:
        """
        Get all configuration keys.
        
        Args:
            section: Configuration section (optional)
            
        Returns:
            List of configuration keys
        """
        pass


class EnvironmentConfig(ABC):
    """
    Interface for environment detection and platform-specific configuration.
    
    Provides methods for detecting the runtime environment (Docker, bare metal, etc.)
    and retrieving environment-specific configuration defaults, resource limits,
    and platform capabilities.
    """
    
    @abstractmethod
    def detect_environment(self) -> str:
        """
        Detect the current runtime environment.
        
        Returns:
            Environment type string ('docker', 'kubernetes', 'bare_metal', 'test')
        """
        pass
    
    @abstractmethod
    def is_docker_environment(self) -> bool:
        """
        Check if running in Docker container.
        
        Returns:
            True if running in Docker, False otherwise
        """
        pass
    
    @abstractmethod
    def is_kubernetes_environment(self) -> bool:
        """
        Check if running in Kubernetes cluster.
        
        Returns:
            True if running in Kubernetes, False otherwise
        """
        pass
    
    @abstractmethod
    def get_default_paths(self) -> PathConfigurationModel:
        """
        Get default paths for the current environment.
        
        Returns:
            PathConfigurationModel with environment-appropriate defaults
        """
        pass
    
    @abstractmethod
    def validate_environment_requirements(self) -> Dict[str, bool]:
        """
        Validate environment requirements.
        
        Returns:
            Dictionary of requirement name -> validation result
        """
        pass
    
    @abstractmethod
    def get_resource_limits(self) -> Dict[str, Any]:
        """
        Get platform-specific resource limits.
        
        Returns:
            Dictionary containing memory, CPU, and other resource limits
        """
        pass
    
    @abstractmethod
    def get_environment_variables(self) -> Dict[str, str]:
        """
        Get environment variables relevant to configuration.
        
        Returns:
            Dictionary of environment variable name -> value
        """
        pass


class PathConfiguration(ABC):
    """
    Interface for path validation and filesystem operations.
    
    Provides methods for validating paths, normalizing filesystem paths across
    platforms, detecting network shares, and querying filesystem information
    like available space and permissions.
    """
    
    @abstractmethod
    def validate_path(self, path: Union[str, Path], check_exists: bool = True, 
                     check_writable: bool = False) -> bool:
        """
        Validate a filesystem path.
        
        Args:
            path: Path to validate
            check_exists: Whether to check if path exists
            check_writable: Whether to check if path is writable
            
        Returns:
            True if path is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """
        Normalize a filesystem path.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized Path object
        """
        pass
    
    @abstractmethod
    def is_network_path(self, path: Union[str, Path]) -> bool:
        """
        Check if path is a network share.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a network share, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_space(self, path: Union[str, Path]) -> int:
        """
        Get available disk space at path.
        
        Args:
            path: Path to check
            
        Returns:
            Available space in bytes
            
        Raises:
            OSError: If path is not accessible
        """
        pass
    
    @abstractmethod
    def ensure_directory_exists(self, path: Union[str, Path]) -> bool:
        """
        Ensure directory exists, creating if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created successfully
        """
        pass
    
    @abstractmethod
    def get_path_permissions(self, path: Union[str, Path]) -> Dict[str, bool]:
        """
        Get path permissions information.
        
        Args:
            path: Path to check
            
        Returns:
            Dictionary with 'readable', 'writable', 'executable' keys
        """
        pass
    
    @abstractmethod
    def get_default_paths(self) -> PathConfigurationModel:
        """
        Get default path configuration for the current environment.
        
        Returns:
            PathConfigurationModel with default paths
        """
        pass
    
    @abstractmethod
    def resolve_relative_path(self, path: Union[str, Path], base_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Resolve relative path to absolute path.
        
        Args:
            path: Path to resolve
            base_path: Base path for relative resolution (defaults to current working directory)
            
        Returns:
            Absolute Path object
        """
        pass


__all__ = [
    # Configuration models
    'PathConfigurationModel',
    'PlexConfiguration', 
    'MediaConfiguration',
    'PerformanceConfiguration',
    'NotificationConfiguration',
    'TestModeConfiguration',
    
    # Configuration interfaces
    'ConfigProvider',
    'EnvironmentConfig',
    'PathConfiguration'
]