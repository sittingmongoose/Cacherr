"""
Command factory for creating PlexCacheUltra commands.

This module provides factory classes for creating command instances
with proper dependency injection and configuration. Factories abstract
command creation complexity and ensure consistent command setup.

Classes:
- CommandFactory: Generic command factory base class
- CacheCommandFactory: Specialized factory for cache operation commands
"""

import logging
from typing import List, Dict, Optional, Any, Type, Union
from pathlib import Path

from .interfaces import ICommand, CommandPriority, CommandContext
from .cache_commands import (
    MoveToCache, MoveToArray, CopyToCache, DeleteFromCache,
    TestCacheOperation, AnalyzeCacheImpact, CleanupCache, ValidateCache
)
from ..container import IServiceProvider

logger = logging.getLogger(__name__)


class CommandFactory:
    """
    Generic factory for creating command instances.
    
    Provides a consistent interface for command creation with
    dependency injection and configuration management.
    
    Attributes:
        service_provider: Service provider for dependency resolution
        default_priority: Default priority for created commands
        default_timeout: Default timeout for created commands
    """
    
    def __init__(self, service_provider: Optional[IServiceProvider] = None,
                 default_priority: CommandPriority = CommandPriority.NORMAL,
                 default_timeout: Optional[int] = None):
        """
        Initialize command factory.
        
        Args:
            service_provider: Service provider for dependency injection
            default_priority: Default priority for commands
            default_timeout: Default timeout in seconds for commands
        """
        self.service_provider = service_provider
        self.default_priority = default_priority
        self.default_timeout = default_timeout
        
        logger.debug("CommandFactory initialized")
    
    def create_command(self, command_type: str, **kwargs) -> ICommand:
        """
        Create a command instance by type.
        
        Args:
            command_type: Type identifier for the command
            **kwargs: Command-specific parameters
            
        Returns:
            Created command instance
            
        Raises:
            ValueError: If command type is not supported
            TypeError: If required parameters are missing
        """
        # Set default values if not provided
        if 'priority' not in kwargs and self.default_priority:
            kwargs['priority'] = self.default_priority
            
        if 'timeout_seconds' not in kwargs and self.default_timeout:
            kwargs['timeout_seconds'] = self.default_timeout
        
        # Command type mapping would go here
        command_registry = self._get_command_registry()
        
        if command_type not in command_registry:
            available_types = list(command_registry.keys())
            raise ValueError(
                f"Unknown command type '{command_type}'. "
                f"Available types: {', '.join(available_types)}"
            )
        
        command_class = command_registry[command_type]
        
        try:
            # Create command instance
            command = command_class(**kwargs)
            
            logger.debug(f"Created command: {command_type} with ID {command.metadata.command_id}")
            return command
            
        except Exception as e:
            logger.error(f"Failed to create command '{command_type}': {str(e)}")
            raise TypeError(f"Failed to create command '{command_type}': {str(e)}") from e
    
    def _get_command_registry(self) -> Dict[str, Type[ICommand]]:
        """
        Get the command type registry.
        
        Subclasses should override this method to provide
        their specific command mappings.
        
        Returns:
            Dictionary mapping command type strings to command classes
        """
        return {}
    
    def validate_command_parameters(self, command_type: str, **kwargs) -> List[str]:
        """
        Validate parameters for command creation.
        
        Args:
            command_type: Type of command to validate
            **kwargs: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not command_type:
            errors.append("Command type is required")
        
        command_registry = self._get_command_registry()
        if command_type not in command_registry:
            errors.append(f"Unknown command type: {command_type}")
            return errors
        
        # Command-specific validation would go here
        # This is a basic implementation
        
        return errors
    
    def get_supported_command_types(self) -> List[str]:
        """
        Get list of supported command types.
        
        Returns:
            List of command type strings
        """
        return list(self._get_command_registry().keys())


class CacheCommandFactory(CommandFactory):
    """
    Specialized factory for cache operation commands.
    
    Provides convenient methods for creating cache-related commands
    with proper parameter validation and default configurations.
    """
    
    def __init__(self, service_provider: Optional[IServiceProvider] = None,
                 cache_directory: Optional[str] = None,
                 array_directory: Optional[str] = None,
                 default_priority: CommandPriority = CommandPriority.NORMAL,
                 default_max_concurrent: Optional[int] = None):
        """
        Initialize cache command factory.
        
        Args:
            service_provider: Service provider for dependency injection
            cache_directory: Default cache directory path
            array_directory: Default array directory path
            default_priority: Default priority for commands
            default_max_concurrent: Default max concurrent operations
        """
        super().__init__(service_provider, default_priority)
        self.cache_directory = cache_directory
        self.array_directory = array_directory
        self.default_max_concurrent = default_max_concurrent
        
        logger.debug("CacheCommandFactory initialized")
    
    def _get_command_registry(self) -> Dict[str, Type[ICommand]]:
        """Get cache command type registry."""
        return {
            "move_to_cache": MoveToCache,
            "move_to_array": MoveToArray,
            "copy_to_cache": CopyToCache,
            "delete_from_cache": DeleteFromCache,
            "test_cache_operation": TestCacheOperation,
            "analyze_cache_impact": AnalyzeCacheImpact,
            "cleanup_cache": CleanupCache,
            "validate_cache": ValidateCache,
        }
    
    def create_move_to_cache_command(
        self,
        files: List[str],
        source_directory: Optional[str] = None,
        cache_directory: Optional[str] = None,
        max_concurrent: Optional[int] = None,
        create_symlinks: bool = False,
        priority: Optional[CommandPriority] = None
    ) -> MoveToCache:
        """
        Create a move to cache command.
        
        Args:
            files: List of file paths to move
            source_directory: Source directory (defaults to array_directory)
            cache_directory: Cache directory (defaults to factory default)
            max_concurrent: Max concurrent operations (defaults to factory default)
            create_symlinks: Whether to create symlinks after move
            priority: Command priority (defaults to factory default)
            
        Returns:
            MoveToCache command instance
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Use factory defaults
        source_dir = source_directory or self.array_directory
        cache_dir = cache_directory or self.cache_directory
        max_conc = max_concurrent if max_concurrent is not None else self.default_max_concurrent
        cmd_priority = priority or self.default_priority
        
        # Validate required parameters
        if not source_dir:
            raise ValueError("Source directory is required")
        if not cache_dir:
            raise ValueError("Cache directory is required")
        if not files:
            raise ValueError("Files list cannot be empty")
        
        # Resolve paths
        source_path = str(Path(source_dir).resolve())
        cache_path = str(Path(cache_dir).resolve())
        
        return MoveToCache(
            files=files,
            source_directory=source_path,
            cache_directory=cache_path,
            max_concurrent=max_conc,
            create_symlinks=create_symlinks,
            priority=cmd_priority
        )
    
    def create_move_to_array_command(
        self,
        files: List[str],
        cache_directory: Optional[str] = None,
        array_directory: Optional[str] = None,
        max_concurrent: Optional[int] = None,
        priority: Optional[CommandPriority] = None
    ) -> MoveToArray:
        """
        Create a move to array command.
        
        Args:
            files: List of file paths to move from cache
            cache_directory: Cache directory (defaults to factory default)
            array_directory: Array directory (defaults to factory default)
            max_concurrent: Max concurrent operations (defaults to factory default)
            priority: Command priority (defaults to factory default)
            
        Returns:
            MoveToArray command instance
            
        Raises:
            ValueError: If required parameters are missing
        """
        cache_dir = cache_directory or self.cache_directory
        array_dir = array_directory or self.array_directory
        max_conc = max_concurrent if max_concurrent is not None else self.default_max_concurrent
        cmd_priority = priority or self.default_priority
        
        if not cache_dir:
            raise ValueError("Cache directory is required")
        if not array_dir:
            raise ValueError("Array directory is required")
        if not files:
            raise ValueError("Files list cannot be empty")
        
        cache_path = str(Path(cache_dir).resolve())
        array_path = str(Path(array_dir).resolve())
        
        return MoveToArray(
            files=files,
            cache_directory=cache_path,
            array_directory=array_path,
            max_concurrent=max_conc,
            priority=cmd_priority
        )
    
    def create_copy_to_cache_command(
        self,
        files: List[str],
        source_directory: Optional[str] = None,
        cache_directory: Optional[str] = None,
        max_concurrent: Optional[int] = None,
        priority: Optional[CommandPriority] = None
    ) -> CopyToCache:
        """
        Create a copy to cache command.
        
        Args:
            files: List of file paths to copy
            source_directory: Source directory (defaults to array_directory)
            cache_directory: Cache directory (defaults to factory default)
            max_concurrent: Max concurrent operations (defaults to factory default)
            priority: Command priority (defaults to factory default)
            
        Returns:
            CopyToCache command instance
        """
        source_dir = source_directory or self.array_directory
        cache_dir = cache_directory or self.cache_directory
        max_conc = max_concurrent if max_concurrent is not None else self.default_max_concurrent
        cmd_priority = priority or self.default_priority
        
        if not source_dir:
            raise ValueError("Source directory is required")
        if not cache_dir:
            raise ValueError("Cache directory is required")
        if not files:
            raise ValueError("Files list cannot be empty")
        
        source_path = str(Path(source_dir).resolve())
        cache_path = str(Path(cache_dir).resolve())
        
        return CopyToCache(
            files=files,
            source_directory=source_path,
            cache_directory=cache_path,
            max_concurrent=max_conc,
            priority=cmd_priority
        )
    
    def create_delete_from_cache_command(
        self,
        files: List[str],
        max_concurrent: Optional[int] = None,
        priority: Optional[CommandPriority] = None
    ) -> DeleteFromCache:
        """
        Create a delete from cache command.
        
        Args:
            files: List of cache file paths to delete
            max_concurrent: Max concurrent delete operations
            priority: Command priority (defaults to factory default)
            
        Returns:
            DeleteFromCache command instance
        """
        max_conc = max_concurrent if max_concurrent is not None else self.default_max_concurrent
        cmd_priority = priority or self.default_priority
        
        if not files:
            raise ValueError("Files list cannot be empty")
        
        return DeleteFromCache(
            files=files,
            max_concurrent=max_conc,
            priority=cmd_priority
        )
    
    def create_test_cache_operation_command(
        self,
        files: List[str],
        operation_type: str = "cache",
        priority: Optional[CommandPriority] = None
    ) -> TestCacheOperation:
        """
        Create a test cache operation command.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation to test ("cache", "array", "delete")
            priority: Command priority (defaults to factory default)
            
        Returns:
            TestCacheOperation command instance
        """
        cmd_priority = priority or CommandPriority.LOW
        
        if not files:
            raise ValueError("Files list cannot be empty")
        
        return TestCacheOperation(
            files=files,
            operation_type=operation_type,
            priority=cmd_priority
        )
    
    def create_analyze_cache_impact_command(
        self,
        files: List[str],
        operation_type: str = "cache",
        priority: Optional[CommandPriority] = None
    ) -> AnalyzeCacheImpact:
        """
        Create an analyze cache impact command.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation to analyze
            priority: Command priority (defaults to factory default)
            
        Returns:
            AnalyzeCacheImpact command instance
        """
        cmd_priority = priority or CommandPriority.LOW
        
        if not files:
            raise ValueError("Files list cannot be empty")
        
        return AnalyzeCacheImpact(
            files=files,
            operation_type=operation_type,
            priority=cmd_priority
        )
    
    def create_cleanup_cache_command(
        self,
        max_age_hours: Optional[int] = None,
        remove_watched: bool = True,
        priority: Optional[CommandPriority] = None
    ) -> CleanupCache:
        """
        Create a cleanup cache command.
        
        Args:
            max_age_hours: Maximum age for cache files (None for default)
            remove_watched: Whether to remove watched content
            priority: Command priority (defaults to factory default)
            
        Returns:
            CleanupCache command instance
        """
        cmd_priority = priority or CommandPriority.LOW
        
        return CleanupCache(
            max_age_hours=max_age_hours,
            remove_watched=remove_watched,
            priority=cmd_priority
        )
    
    def create_validate_cache_command(
        self,
        deep_scan: bool = False,
        priority: Optional[CommandPriority] = None
    ) -> ValidateCache:
        """
        Create a validate cache command.
        
        Args:
            deep_scan: Whether to perform deep file integrity checks
            priority: Command priority (defaults to factory default)
            
        Returns:
            ValidateCache command instance
        """
        cmd_priority = priority or CommandPriority.LOW
        
        return ValidateCache(
            deep_scan=deep_scan,
            priority=cmd_priority
        )
    
    def create_commands_from_config(self, config: Dict[str, Any]) -> List[ICommand]:
        """
        Create multiple commands from configuration.
        
        Args:
            config: Configuration dictionary with command specifications
            
        Returns:
            List of created command instances
            
        Example config:
            {
                "commands": [
                    {
                        "type": "move_to_cache",
                        "files": ["/path/to/file1", "/path/to/file2"],
                        "priority": "high"
                    },
                    {
                        "type": "cleanup_cache",
                        "max_age_hours": 168,
                        "priority": "low"
                    }
                ]
            }
        """
        commands = []
        
        command_specs = config.get("commands", [])
        
        for spec in command_specs:
            try:
                command_type = spec.get("type")
                if not command_type:
                    logger.warning("Command specification missing 'type' field, skipping")
                    continue
                
                # Convert priority string to enum if needed
                priority_str = spec.get("priority", "normal")
                priority = self._parse_priority(priority_str)
                spec["priority"] = priority
                
                # Remove type from spec since it's not a constructor parameter
                spec_copy = spec.copy()
                del spec_copy["type"]
                
                # Create command using the factory method
                command = self.create_command(command_type, **spec_copy)
                commands.append(command)
                
                logger.debug(f"Created command from config: {command_type}")
                
            except Exception as e:
                logger.error(f"Failed to create command from config: {str(e)}")
                # Continue with other commands instead of failing completely
                continue
        
        logger.info(f"Created {len(commands)} commands from configuration")
        return commands
    
    def _parse_priority(self, priority_str: str) -> CommandPriority:
        """Parse priority string to CommandPriority enum."""
        priority_map = {
            "low": CommandPriority.LOW,
            "normal": CommandPriority.NORMAL,
            "high": CommandPriority.HIGH,
            "critical": CommandPriority.CRITICAL,
        }
        
        return priority_map.get(priority_str.lower(), CommandPriority.NORMAL)
    
    def validate_command_parameters(self, command_type: str, **kwargs) -> List[str]:
        """
        Validate parameters for cache command creation.
        
        Args:
            command_type: Type of command to validate
            **kwargs: Parameters to validate
            
        Returns:
            List of validation error messages
        """
        errors = super().validate_command_parameters(command_type, **kwargs)
        
        # Add cache-specific validation
        if command_type in ["move_to_cache", "copy_to_cache"]:
            if not kwargs.get("files"):
                errors.append("Files parameter is required")
            
            if not kwargs.get("source_directory") and not self.array_directory:
                errors.append("Source directory is required")
            
            if not kwargs.get("cache_directory") and not self.cache_directory:
                errors.append("Cache directory is required")
        
        elif command_type == "move_to_array":
            if not kwargs.get("files"):
                errors.append("Files parameter is required")
            
            if not kwargs.get("cache_directory") and not self.cache_directory:
                errors.append("Cache directory is required")
            
            if not kwargs.get("array_directory") and not self.array_directory:
                errors.append("Array directory is required")
        
        elif command_type == "delete_from_cache":
            if not kwargs.get("files"):
                errors.append("Files parameter is required")
        
        elif command_type in ["test_cache_operation", "analyze_cache_impact"]:
            if not kwargs.get("files"):
                errors.append("Files parameter is required")
            
            operation_type = kwargs.get("operation_type", "cache")
            if operation_type not in ["cache", "array", "delete"]:
                errors.append("Operation type must be 'cache', 'array', or 'delete'")
        
        return errors