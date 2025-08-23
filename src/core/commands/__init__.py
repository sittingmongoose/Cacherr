"""
Command Pattern Implementation for PlexCacheUltra.

This module implements the Command Pattern for operation management, providing:
- Command interfaces and base classes
- Cache operation commands
- Command execution tracking
- Undo/redo capabilities
- Command queuing and management

The command pattern encapsulates operations as objects, allowing for:
- Operation queuing and batching
- Undo/redo functionality
- Operation logging and auditing
- Retry mechanisms
- Progress tracking

Example:
    ```python
    from src.core.commands import CacheCommand, MoveToCache
    
    # Create command
    command = MoveToCache(files=["/path/to/file"], cache_path="/cache")
    
    # Execute command
    result = command.execute()
    
    # Undo if needed
    if result.success:
        undo_result = command.undo()
    ```
"""

from .interfaces import (
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
)

from .base_commands import (
    BaseCommand,
    BaseUndoableCommand,
    CompositeCacheCommand,
)

from .cache_commands import (
    MoveToCache,
    MoveToArray, 
    CopyToCache,
    DeleteFromCache,
    TestCacheOperation,
    AnalyzeCacheImpact,
    CleanupCache,
    ValidateCache,
)

from .command_factory import (
    CommandFactory,
    CacheCommandFactory,
)

__all__ = [
    # Interfaces
    "ICommand",
    "IUndoableCommand", 
    "ICommandExecutor",
    "ICommandHistory",
    "ICommandQueue",
    "CommandResult",
    "CommandStatus",
    "CommandMetadata",
    "CommandContext",
    "CommandPriority",
    
    # Base classes
    "BaseCommand",
    "BaseUndoableCommand", 
    "CompositeCacheCommand",
    
    # Cache commands
    "MoveToCache",
    "MoveToArray",
    "CopyToCache", 
    "DeleteFromCache",
    "TestCacheOperation",
    "AnalyzeCacheImpact",
    "CleanupCache",
    "ValidateCache",
    
    # Factory
    "CommandFactory",
    "CacheCommandFactory",
]