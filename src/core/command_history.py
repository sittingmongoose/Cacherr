"""
Command history implementation for PlexCacheUltra.

This module provides comprehensive command history tracking with undo/redo
capabilities, audit trails, and history persistence. It supports both
in-memory and persistent storage for command history.

Classes:
- CommandHistoryEntry: Single history entry with full command context
- CommandHistory: In-memory command history with undo/redo support
- PersistentCommandHistory: File-based persistent command history
- CommandHistoryManager: High-level history management coordinator
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Callable
from uuid import UUID
from dataclasses import dataclass, asdict

from pydantic import BaseModel

from .commands.interfaces import (
    ICommand, IUndoableCommand, ICommandHistory, CommandResult, 
    CommandContext, CommandStatus, UndoNotSupportedError
)

logger = logging.getLogger(__name__)


class CommandHistoryEntry(BaseModel):
    """
    Complete history entry for a command execution.
    
    Stores all information needed to track, replay, or undo
    command executions with full context preservation.
    
    Attributes:
        command_id: Unique identifier for the command
        command_type: Type of command that was executed
        execution_time: When the command was executed
        execution_result: Result of the command execution
        undo_information: Data needed for undo operations
        context_snapshot: Snapshot of execution context
        user_id: User who executed the command
        session_id: Session identifier for grouping related commands
        tags: Tags for categorizing and filtering commands
        parent_command_id: ID of parent command for nested operations
        retry_count: Number of times command was retried
        status: Current status of the command
    """
    
    command_id: UUID
    command_type: str
    execution_time: datetime
    execution_result: Dict[str, Any]  # CommandResult as dict
    undo_information: Optional[Dict[str, Any]] = None
    context_snapshot: Dict[str, Any] = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = []
    parent_command_id: Optional[UUID] = None
    retry_count: int = 0
    status: str = CommandStatus.COMPLETED.value
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class CommandHistory(ICommandHistory):
    """
    In-memory command history with undo/redo capabilities.
    
    Maintains a chronological history of executed commands with
    support for undo/redo operations, filtering, and search.
    
    Attributes:
        max_history_size: Maximum number of history entries to keep
        auto_cleanup: Whether to automatically clean up old entries
        cleanup_interval_hours: Hours between automatic cleanup
    """
    
    def __init__(self, max_history_size: int = 1000,
                 auto_cleanup: bool = True,
                 cleanup_interval_hours: int = 24):
        """
        Initialize command history.
        
        Args:
            max_history_size: Maximum number of history entries
            auto_cleanup: Whether to auto-clean old entries
            cleanup_interval_hours: Hours between cleanup runs
        """
        self.max_history_size = max_history_size
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval_hours = cleanup_interval_hours
        
        # History storage
        self._history: List[CommandHistoryEntry] = []
        self._history_by_id: Dict[UUID, CommandHistoryEntry] = {}
        
        # Undo/redo tracking
        self._undo_stack: List[CommandHistoryEntry] = []
        self._redo_stack: List[CommandHistoryEntry] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cleanup tracking
        self._last_cleanup: Optional[datetime] = None
        
        # Event callbacks
        self._command_executed_callbacks: List[Callable[[CommandHistoryEntry], None]] = []
        self._command_undone_callbacks: List[Callable[[CommandHistoryEntry], None]] = []
        
        logger.info(f"CommandHistory initialized with max size {max_history_size}")
    
    def add_command(self, command: ICommand, result: CommandResult) -> None:
        """
        Add a command and its result to history.
        
        Args:
            command: The executed command
            result: The execution result
        """
        with self._lock:
            # Create history entry
            entry = CommandHistoryEntry(
                command_id=command.metadata.command_id,
                command_type=command.metadata.command_type,
                execution_time=result.timestamp,
                execution_result=result.dict(),
                context_snapshot=self._create_context_snapshot(command),
                user_id=None,  # Could be extracted from context
                session_id=None,  # Could be extracted from context
                tags=command.metadata.tags.copy(),
                parent_command_id=command.metadata.parent_command_id,
                retry_count=command.metadata.retry_count,
                status=CommandStatus.COMPLETED.value if result.success else CommandStatus.FAILED.value
            )
            
            # Store undo information for undoable commands
            if isinstance(command, IUndoableCommand) and command.can_undo:
                entry.undo_information = command.undo_information
            
            # Add to history
            self._history.append(entry)
            self._history_by_id[entry.command_id] = entry
            
            # Add to undo stack if command succeeded and is undoable
            if result.success and isinstance(command, IUndoableCommand) and command.can_undo:
                self._undo_stack.append(entry)
                # Clear redo stack when new command is executed
                self._redo_stack.clear()
            
            # Trigger callbacks
            for callback in self._command_executed_callbacks:
                try:
                    callback(entry)
                except Exception as e:
                    logger.error(f"Command executed callback failed: {str(e)}")
            
            # Maintain size limit
            if len(self._history) > self.max_history_size:
                removed_entry = self._history.pop(0)
                self._history_by_id.pop(removed_entry.command_id, None)
                # Remove from undo stack if present
                if removed_entry in self._undo_stack:
                    self._undo_stack.remove(removed_entry)
            
            # Auto cleanup if needed
            if self.auto_cleanup and self._should_cleanup():
                self._cleanup_old_entries()
            
            logger.debug(f"Added command to history: {command.metadata.command_type} "
                        f"(ID: {command.metadata.command_id})")
    
    def get_history(self, limit: Optional[int] = None, 
                   offset: int = 0,
                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get command execution history.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            filters: Optional filters to apply
            
        Returns:
            List of history entries as dictionaries
        """
        with self._lock:
            # Apply filters
            filtered_history = self._apply_filters(self._history, filters or {})
            
            # Sort by execution time (most recent first)
            filtered_history.sort(key=lambda e: e.execution_time, reverse=True)
            
            # Apply offset and limit
            end_index = None if limit is None else offset + limit
            selected_entries = filtered_history[offset:end_index]
            
            return [entry.dict() for entry in selected_entries]
    
    def can_undo(self) -> bool:
        """Check if there are commands that can be undone."""
        with self._lock:
            return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if there are commands that can be redone."""
        with self._lock:
            return len(self._redo_stack) > 0
    
    def undo_last_command(self, context: Optional[CommandContext] = None) -> Optional[CommandResult]:
        """
        Undo the last executed command.
        
        Args:
            context: Optional execution context for undo
            
        Returns:
            CommandResult if undo was performed, None if nothing to undo
        """
        with self._lock:
            if not self._undo_stack:
                logger.debug("No commands available for undo")
                return None
            
            # Get the last undoable command
            entry = self._undo_stack.pop()
            
            # This is a conceptual implementation - in reality, we'd need
            # access to the original command object to call its undo method
            logger.warning("Undo operation requires original command object - "
                          "this is a history tracking limitation")
            
            # Move to redo stack
            self._redo_stack.append(entry)
            
            # Update entry status
            entry.status = CommandStatus.UNDONE.value
            
            # Trigger callbacks
            for callback in self._command_undone_callbacks:
                try:
                    callback(entry)
                except Exception as e:
                    logger.error(f"Command undone callback failed: {str(e)}")
            
            # Return a placeholder result
            return CommandResult(
                success=False,
                message="Undo operation requires command object reference",
                warnings=["History tracking cannot directly execute undo operations"],
                data={
                    "command_id": str(entry.command_id),
                    "command_type": entry.command_type,
                    "original_execution_time": entry.execution_time.isoformat()
                }
            )
    
    def redo_next_command(self, context: Optional[CommandContext] = None) -> Optional[CommandResult]:
        """
        Redo the next command in history.
        
        Args:
            context: Optional execution context for redo
            
        Returns:
            CommandResult if redo was performed, None if nothing to redo
        """
        with self._lock:
            if not self._redo_stack:
                logger.debug("No commands available for redo")
                return None
            
            # Get the next command to redo
            entry = self._redo_stack.pop()
            
            # Similar limitation as undo - we'd need the original command
            logger.warning("Redo operation requires original command object")
            
            # Move back to undo stack
            self._undo_stack.append(entry)
            
            # Update entry status
            entry.status = CommandStatus.COMPLETED.value
            
            return CommandResult(
                success=False,
                message="Redo operation requires command object reference",
                warnings=["History tracking cannot directly execute redo operations"],
                data={
                    "command_id": str(entry.command_id),
                    "command_type": entry.command_type,
                    "original_execution_time": entry.execution_time.isoformat()
                }
            )
    
    def clear_history(self, before_timestamp: Optional[datetime] = None) -> int:
        """
        Clear command history.
        
        Args:
            before_timestamp: Only clear entries before this timestamp
            
        Returns:
            Number of entries cleared
        """
        with self._lock:
            if before_timestamp is None:
                # Clear everything
                cleared_count = len(self._history)
                self._history.clear()
                self._history_by_id.clear()
                self._undo_stack.clear()
                self._redo_stack.clear()
            else:
                # Clear entries before timestamp
                cleared_entries = [e for e in self._history if e.execution_time < before_timestamp]
                cleared_count = len(cleared_entries)
                
                # Remove from main history
                self._history = [e for e in self._history if e.execution_time >= before_timestamp]
                
                # Remove from ID mapping
                for entry in cleared_entries:
                    self._history_by_id.pop(entry.command_id, None)
                
                # Remove from undo/redo stacks
                self._undo_stack = [e for e in self._undo_stack if e.execution_time >= before_timestamp]
                self._redo_stack = [e for e in self._redo_stack if e.execution_time >= before_timestamp]
            
            logger.info(f"Cleared {cleared_count} entries from command history")
            return cleared_count
    
    def get_command_by_id(self, command_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific command from history by ID.
        
        Args:
            command_id: Command identifier
            
        Returns:
            Command history entry or None if not found
        """
        with self._lock:
            entry = self._history_by_id.get(command_id)
            return entry.dict() if entry else None
    
    def get_undo_stack_info(self) -> List[Dict[str, Any]]:
        """
        Get information about commands available for undo.
        
        Returns:
            List of undoable command entries
        """
        with self._lock:
            return [
                {
                    "command_id": str(entry.command_id),
                    "command_type": entry.command_type,
                    "execution_time": entry.execution_time.isoformat(),
                    "can_undo": entry.undo_information is not None
                }
                for entry in reversed(self._undo_stack)  # Most recent first
            ]
    
    def get_redo_stack_info(self) -> List[Dict[str, Any]]:
        """
        Get information about commands available for redo.
        
        Returns:
            List of redoable command entries
        """
        with self._lock:
            return [
                {
                    "command_id": str(entry.command_id),
                    "command_type": entry.command_type,
                    "execution_time": entry.execution_time.isoformat()
                }
                for entry in reversed(self._redo_stack)  # Most recent first
            ]
    
    def add_command_executed_callback(self, callback: Callable[[CommandHistoryEntry], None]) -> None:
        """Add callback for when commands are added to history."""
        self._command_executed_callbacks.append(callback)
    
    def add_command_undone_callback(self, callback: Callable[[CommandHistoryEntry], None]) -> None:
        """Add callback for when commands are undone."""
        self._command_undone_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get history statistics.
        
        Returns:
            Dictionary with history statistics
        """
        with self._lock:
            total_commands = len(self._history)
            successful_commands = sum(1 for e in self._history 
                                     if e.status == CommandStatus.COMPLETED.value)
            failed_commands = sum(1 for e in self._history 
                                 if e.status == CommandStatus.FAILED.value)
            
            # Command type distribution
            command_types = {}
            for entry in self._history:
                command_types[entry.command_type] = command_types.get(entry.command_type, 0) + 1
            
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_commands = sum(1 for e in self._history if e.execution_time > recent_cutoff)
            
            return {
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "failed_commands": failed_commands,
                "success_rate": successful_commands / total_commands if total_commands > 0 else 0,
                "undoable_commands": len(self._undo_stack),
                "redoable_commands": len(self._redo_stack),
                "command_types": command_types,
                "recent_commands_24h": recent_commands,
                "oldest_entry": self._history[0].execution_time.isoformat() if self._history else None,
                "newest_entry": self._history[-1].execution_time.isoformat() if self._history else None
            }
    
    def _create_context_snapshot(self, command: ICommand) -> Dict[str, Any]:
        """Create a snapshot of command execution context."""
        return {
            "command_metadata": {
                "command_id": str(command.metadata.command_id),
                "command_type": command.metadata.command_type,
                "created_at": command.metadata.created_at.isoformat(),
                "priority": command.metadata.priority.value,
                "tags": command.metadata.tags,
                "retry_count": command.metadata.retry_count,
                "max_retries": command.metadata.max_retries
            },
            "affected_resources": command.get_affected_resources(),
            "estimated_execution_time": command.estimate_execution_time()
        }
    
    def _apply_filters(self, entries: List[CommandHistoryEntry], 
                      filters: Dict[str, Any]) -> List[CommandHistoryEntry]:
        """Apply filters to history entries."""
        filtered = entries
        
        # Filter by command type
        if "command_type" in filters:
            command_type = filters["command_type"]
            filtered = [e for e in filtered if e.command_type == command_type]
        
        # Filter by success/failure
        if "success" in filters:
            success = filters["success"]
            if success:
                filtered = [e for e in filtered if e.status == CommandStatus.COMPLETED.value]
            else:
                filtered = [e for e in filtered if e.status != CommandStatus.COMPLETED.value]
        
        # Filter by date range
        if "start_date" in filters:
            start_date = filters["start_date"]
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            filtered = [e for e in filtered if e.execution_time >= start_date]
        
        if "end_date" in filters:
            end_date = filters["end_date"]
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            filtered = [e for e in filtered if e.execution_time <= end_date]
        
        # Filter by tags
        if "tags" in filters:
            required_tags = set(filters["tags"])
            filtered = [e for e in filtered if required_tags.issubset(set(e.tags))]
        
        # Filter by user
        if "user_id" in filters:
            user_id = filters["user_id"]
            filtered = [e for e in filtered if e.user_id == user_id]
        
        return filtered
    
    def _should_cleanup(self) -> bool:
        """Check if automatic cleanup should be performed."""
        if not self._last_cleanup:
            return True
        
        time_since_cleanup = datetime.utcnow() - self._last_cleanup
        return time_since_cleanup.total_seconds() > (self.cleanup_interval_hours * 3600)
    
    def _cleanup_old_entries(self) -> None:
        """Perform automatic cleanup of old entries."""
        # Keep entries from the last 7 days by default
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        cleared_count = self.clear_history(cutoff_date)
        
        self._last_cleanup = datetime.utcnow()
        
        if cleared_count > 0:
            logger.info(f"Auto-cleanup removed {cleared_count} old history entries")


class PersistentCommandHistory(CommandHistory):
    """
    File-based persistent command history.
    
    Extends the in-memory history with file persistence capabilities,
    allowing history to survive application restarts.
    
    Attributes:
        history_file: Path to the history file
        auto_save: Whether to automatically save changes
        save_interval: Interval between automatic saves (in seconds)
    """
    
    def __init__(self, history_file: Union[str, Path],
                 max_history_size: int = 10000,
                 auto_save: bool = True,
                 save_interval: int = 300):  # 5 minutes
        """
        Initialize persistent command history.
        
        Args:
            history_file: Path to history file
            max_history_size: Maximum number of history entries
            auto_save: Whether to auto-save changes
            save_interval: Seconds between auto-saves
        """
        super().__init__(max_history_size, auto_cleanup=True)
        
        self.history_file = Path(history_file)
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        # Ensure directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        self._load_history()
        
        # Auto-save tracking
        self._last_save: Optional[datetime] = None
        self._changes_since_save = 0
        
        logger.info(f"PersistentCommandHistory initialized with file: {self.history_file}")
    
    def add_command(self, command: ICommand, result: CommandResult) -> None:
        """Add command to history and save if needed."""
        super().add_command(command, result)
        
        self._changes_since_save += 1
        
        if self.auto_save and self._should_save():
            self.save_history()
    
    def save_history(self) -> bool:
        """
        Save history to file.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with self._lock:
                # Convert entries to serializable format
                history_data = {
                    "version": "1.0",
                    "saved_at": datetime.utcnow().isoformat(),
                    "total_entries": len(self._history),
                    "entries": [entry.dict() for entry in self._history]
                }
                
                # Write to temporary file first
                temp_file = self.history_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(history_data, f, indent=2, default=str)
                
                # Atomic replace
                temp_file.replace(self.history_file)
                
                self._last_save = datetime.utcnow()
                self._changes_since_save = 0
                
                logger.debug(f"Saved {len(self._history)} history entries to {self.history_file}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save command history: {str(e)}")
            return False
    
    def load_history(self) -> bool:
        """
        Load history from file.
        
        Returns:
            True if load was successful, False otherwise
        """
        return self._load_history()
    
    def _load_history(self) -> bool:
        """Internal method to load history from file."""
        if not self.history_file.exists():
            logger.debug(f"History file does not exist: {self.history_file}")
            return False
        
        try:
            with open(self.history_file, 'r') as f:
                history_data = json.load(f)
            
            # Validate file format
            if "entries" not in history_data:
                logger.warning("Invalid history file format")
                return False
            
            # Clear current history
            with self._lock:
                self._history.clear()
                self._history_by_id.clear()
                self._undo_stack.clear()
                self._redo_stack.clear()
                
                # Load entries
                for entry_data in history_data["entries"]:
                    try:
                        # Convert string UUIDs back to UUID objects
                        if isinstance(entry_data["command_id"], str):
                            entry_data["command_id"] = UUID(entry_data["command_id"])
                        if entry_data.get("parent_command_id") and isinstance(entry_data["parent_command_id"], str):
                            entry_data["parent_command_id"] = UUID(entry_data["parent_command_id"])
                        
                        # Convert ISO timestamp back to datetime
                        if isinstance(entry_data["execution_time"], str):
                            entry_data["execution_time"] = datetime.fromisoformat(entry_data["execution_time"])
                        
                        entry = CommandHistoryEntry(**entry_data)
                        self._history.append(entry)
                        self._history_by_id[entry.command_id] = entry
                        
                        # Rebuild undo stack for undoable commands
                        if (entry.status == CommandStatus.COMPLETED.value and 
                            entry.undo_information is not None):
                            self._undo_stack.append(entry)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load history entry: {str(e)}")
                        continue
            
            loaded_count = len(self._history)
            logger.info(f"Loaded {loaded_count} history entries from {self.history_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load command history: {str(e)}")
            return False
    
    def _should_save(self) -> bool:
        """Check if history should be saved."""
        if self._changes_since_save == 0:
            return False
        
        if not self._last_save:
            return True
        
        time_since_save = (datetime.utcnow() - self._last_save).total_seconds()
        return time_since_save >= self.save_interval


class CommandHistoryManager:
    """
    High-level command history management coordinator.
    
    Provides a unified interface for command history operations,
    supporting both in-memory and persistent storage with
    additional features like history export/import and analytics.
    """
    
    def __init__(self, history_backend: CommandHistory):
        """
        Initialize command history manager.
        
        Args:
            history_backend: History implementation to use
        """
        self.history = history_backend
        self._analytics_enabled = True
        
        logger.info("CommandHistoryManager initialized")
    
    def record_command_execution(self, command: ICommand, result: CommandResult) -> None:
        """
        Record a command execution in history.
        
        Args:
            command: The executed command
            result: The execution result
        """
        self.history.add_command(command, result)
        
        if self._analytics_enabled:
            self._update_analytics(command, result)
    
    def export_history(self, file_path: Union[str, Path], 
                      filters: Optional[Dict[str, Any]] = None,
                      format: str = "json") -> bool:
        """
        Export command history to a file.
        
        Args:
            file_path: Path for the export file
            filters: Optional filters to apply
            format: Export format ("json" or "csv")
            
        Returns:
            True if export was successful
        """
        try:
            history_entries = self.history.get_history(filters=filters)
            
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                with open(export_path, 'w') as f:
                    json.dump({
                        "exported_at": datetime.utcnow().isoformat(),
                        "total_entries": len(history_entries),
                        "entries": history_entries
                    }, f, indent=2, default=str)
            
            elif format.lower() == "csv":
                import csv
                with open(export_path, 'w', newline='') as f:
                    if history_entries:
                        writer = csv.DictWriter(f, fieldnames=history_entries[0].keys())
                        writer.writeheader()
                        writer.writerows(history_entries)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Exported {len(history_entries)} history entries to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export history: {str(e)}")
            return False
    
    def get_command_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about command execution patterns.
        
        Returns:
            Dictionary with analytics data
        """
        stats = self.history.get_statistics()
        
        # Add additional analytics
        analytics = stats.copy()
        analytics.update({
            "undo_stack_depth": len(self.history.get_undo_stack_info()),
            "redo_stack_depth": len(self.history.get_redo_stack_info()),
            "history_backend_type": type(self.history).__name__
        })
        
        return analytics
    
    def cleanup_history(self, retention_days: int = 30) -> int:
        """
        Clean up old history entries.
        
        Args:
            retention_days: Number of days to retain
            
        Returns:
            Number of entries cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return self.history.clear_history(cutoff_date)
    
    def _update_analytics(self, command: ICommand, result: CommandResult) -> None:
        """Update internal analytics tracking."""
        # Analytics implementation would go here
        # This could include metrics like:
        # - Command execution frequency
        # - Performance trends
        # - Error patterns
        # - User behavior analysis
        pass