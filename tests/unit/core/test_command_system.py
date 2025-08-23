"""
Unit tests for the command pattern implementation.

This module provides comprehensive tests for the command system including
command interfaces, queue management, history tracking, and monitoring.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import time

from src.core.commands.interfaces import (
    ICommand, ICommandQueue, ICommandExecutor, ICommandHistory,
    CommandContext, CommandResult, CommandPriority, CommandMetadata, 
    CommandStatus, UndoableCommand
)
from src.core.commands.base_commands import BaseCommand
from src.core.commands.cache_commands import (
    MoveFileCommand, CopyFileCommand, TestModeAnalysisCommand,
    BatchCacheOperationCommand
)
from src.core.command_queue import CommandQueue, CommandExecutionManager
from src.core.command_history import CommandHistory, PersistentCommandHistory
from src.core.command_monitor import CommandMonitor
from src.core.command_service import CommandService, CommandSystemConfiguration
from src.core.container import DIContainer


# Test command implementations
class TestCommand(BaseCommand):
    """Simple test command implementation."""
    
    def __init__(self, value: str = "test", should_fail: bool = False):
        super().__init__(
            command_type="test_command",
            description=f"Test command with value: {value}"
        )
        self.value = value
        self.should_fail = should_fail
        self.executed = False
    
    def execute(self, context: CommandContext) -> CommandResult:
        if self.should_fail:
            raise RuntimeError("Test command failed")
        
        self.executed = True
        return CommandResult(
            success=True,
            message=f"Test command executed with value: {self.value}",
            data={"executed_value": self.value}
        )
    
    def can_undo(self) -> bool:
        return True
    
    def undo(self, context: CommandContext) -> CommandResult:
        self.executed = False
        return CommandResult(
            success=True,
            message=f"Test command undone for value: {self.value}",
            data={"undone_value": self.value}
        )


class UndoableTestCommand(UndoableCommand):
    """Undoable test command implementation."""
    
    def __init__(self, value: str = "undoable"):
        super().__init__(
            command_type="undoable_test",
            description=f"Undoable test command: {value}"
        )
        self.value = value
        self.execution_state = None
    
    def execute(self, context: CommandContext) -> CommandResult:
        self.execution_state = f"executed_{self.value}_{int(time.time())}"
        return CommandResult(
            success=True,
            message=f"Undoable command executed: {self.value}",
            data={"state": self.execution_state}
        )
    
    def undo(self, context: CommandContext) -> CommandResult:
        previous_state = self.execution_state
        self.execution_state = None
        return CommandResult(
            success=True,
            message=f"Undoable command undone: {self.value}",
            data={"previous_state": previous_state}
        )


class TestCommandMetadata:
    """Test cases for CommandMetadata."""
    
    def test_metadata_creation(self):
        """Test CommandMetadata creation with default values."""
        metadata = CommandMetadata(
            command_type="test_command",
            description="Test command description"
        )
        
        assert metadata.command_type == "test_command"
        assert metadata.description == "Test command description"
        assert metadata.priority == CommandPriority.NORMAL
        assert metadata.status == CommandStatus.PENDING
        assert metadata.timeout_seconds is None
        assert isinstance(metadata.command_id, uuid.UUID)
        assert isinstance(metadata.created_at, datetime)
    
    def test_metadata_with_custom_values(self):
        """Test CommandMetadata with custom values."""
        command_id = uuid.uuid4()
        created_at = datetime.now()
        
        metadata = CommandMetadata(
            command_type="custom_command",
            description="Custom description",
            priority=CommandPriority.HIGH,
            timeout_seconds=300,
            command_id=command_id,
            created_at=created_at
        )
        
        assert metadata.command_type == "custom_command"
        assert metadata.priority == CommandPriority.HIGH
        assert metadata.timeout_seconds == 300
        assert metadata.command_id == command_id
        assert metadata.created_at == created_at


class TestCommandContext:
    """Test cases for CommandContext."""
    
    def test_context_creation(self, clean_container: DIContainer):
        """Test CommandContext creation."""
        context = CommandContext(
            services=clean_container,
            dry_run=True,
            user_context={"user": "test_user"}
        )
        
        assert context.services is clean_container
        assert context.dry_run is True
        assert context.user_context["user"] == "test_user"
        assert isinstance(context.execution_id, uuid.UUID)
        assert isinstance(context.created_at, datetime)
    
    def test_context_defaults(self):
        """Test CommandContext with default values."""
        context = CommandContext()
        
        assert context.services is None
        assert context.dry_run is False
        assert context.user_context == {}
        assert context.execution_metadata == {}


class TestCommandResult:
    """Test cases for CommandResult."""
    
    def test_result_success(self):
        """Test successful CommandResult."""
        result = CommandResult(
            success=True,
            message="Operation completed successfully",
            data={"processed_files": 5}
        )
        
        assert result.success is True
        assert result.message == "Operation completed successfully"
        assert result.data["processed_files"] == 5
        assert result.errors == []
        assert isinstance(result.execution_time, datetime)
        assert result.duration_ms is None
    
    def test_result_failure(self):
        """Test failed CommandResult."""
        result = CommandResult(
            success=False,
            message="Operation failed",
            errors=["File not found", "Permission denied"]
        )
        
        assert result.success is False
        assert result.message == "Operation failed"
        assert len(result.errors) == 2
        assert "File not found" in result.errors


class TestBaseCommand:
    """Test cases for BaseCommand."""
    
    def test_command_creation(self):
        """Test BaseCommand creation."""
        command = TestCommand("test_value")
        
        assert command.metadata.command_type == "test_command"
        assert "test_value" in command.metadata.description
        assert command.metadata.priority == CommandPriority.NORMAL
        assert command.value == "test_value"
    
    def test_command_execution(self):
        """Test command execution."""
        command = TestCommand("execute_test")
        context = CommandContext(dry_run=False)
        
        result = command.execute(context)
        
        assert result.success is True
        assert "execute_test" in result.message
        assert command.executed is True
        assert result.data["executed_value"] == "execute_test"
    
    def test_command_failure(self):
        """Test command execution failure."""
        command = TestCommand("fail_test", should_fail=True)
        context = CommandContext()
        
        with pytest.raises(RuntimeError):
            command.execute(context)
    
    def test_command_undo(self):
        """Test command undo functionality."""
        command = TestCommand("undo_test")
        context = CommandContext()
        
        # Execute first
        execute_result = command.execute(context)
        assert execute_result.success
        assert command.executed
        
        # Then undo
        undo_result = command.undo(context)
        assert undo_result.success
        assert not command.executed
    
    def test_command_validation(self):
        """Test command validation."""
        command = TestCommand("validation_test")
        context = CommandContext()
        
        # Should be valid by default
        assert command.validate(context) is True
    
    def test_command_equality(self):
        """Test command equality comparison."""
        command1 = TestCommand("same_value")
        command2 = TestCommand("same_value")
        command3 = TestCommand("different_value")
        
        # Commands are equal if they have the same ID
        assert command1 == command1
        assert command1 != command2  # Different instances have different IDs
        assert command1 != command3


class TestUndoableCommand:
    """Test cases for UndoableCommand."""
    
    def test_undoable_command_creation(self):
        """Test UndoableCommand creation."""
        command = UndoableTestCommand("undoable_test")
        
        assert command.can_undo() is True
        assert command.value == "undoable_test"
        assert command.execution_state is None
    
    def test_undoable_command_execution_and_undo(self):
        """Test undoable command execution and undo."""
        command = UndoableTestCommand("test_value")
        context = CommandContext()
        
        # Execute
        execute_result = command.execute(context)
        assert execute_result.success
        assert command.execution_state is not None
        
        # Undo
        undo_result = command.undo(context)
        assert undo_result.success
        assert command.execution_state is None


class TestCommandQueue:
    """Test cases for CommandQueue."""
    
    def test_queue_creation(self):
        """Test CommandQueue creation."""
        queue = CommandQueue(max_size=10)
        
        assert queue.max_size == 10
        assert queue.size == 0
        assert queue.is_empty
        assert not queue.is_full
    
    def test_enqueue_command(self):
        """Test enqueuing commands."""
        queue = CommandQueue(max_size=5)
        command = TestCommand("queue_test")
        
        queue_id = queue.enqueue_command(command)
        
        assert queue_id is not None
        assert queue.size == 1
        assert not queue.is_empty
    
    def test_enqueue_with_priority(self):
        """Test enqueuing commands with priority."""
        queue = CommandQueue()
        
        low_command = TestCommand("low")
        low_command.metadata.priority = CommandPriority.LOW
        
        high_command = TestCommand("high")
        high_command.metadata.priority = CommandPriority.HIGH
        
        normal_command = TestCommand("normal")
        normal_command.metadata.priority = CommandPriority.NORMAL
        
        # Enqueue in order: low, high, normal
        queue.enqueue_command(low_command)
        queue.enqueue_command(high_command)
        queue.enqueue_command(normal_command)
        
        # Should dequeue in priority order: high, normal, low
        assert queue.dequeue_command().value == "high"
        assert queue.dequeue_command().value == "normal"
        assert queue.dequeue_command().value == "low"
    
    def test_dequeue_empty_queue(self):
        """Test dequeuing from empty queue."""
        queue = CommandQueue()
        
        result = queue.dequeue_command()
        assert result is None
    
    def test_queue_full(self):
        """Test queue full condition."""
        queue = CommandQueue(max_size=2)
        
        queue.enqueue_command(TestCommand("1"))
        queue.enqueue_command(TestCommand("2"))
        
        assert queue.is_full
        
        # Third command should not be enqueued
        result = queue.enqueue_command(TestCommand("3"))
        assert result is None
        assert queue.size == 2
    
    def test_queue_status(self):
        """Test queue status information."""
        queue = CommandQueue(max_size=5)
        queue.enqueue_command(TestCommand("test"))
        
        status = queue.get_queue_status()
        
        assert status["size"] == 1
        assert status["max_size"] == 5
        assert status["is_empty"] is False
        assert status["is_full"] is False
        assert "commands" in status
    
    def test_clear_queue(self):
        """Test clearing queue."""
        queue = CommandQueue()
        queue.enqueue_command(TestCommand("1"))
        queue.enqueue_command(TestCommand("2"))
        
        cleared_count = queue.clear_queue()
        
        assert cleared_count == 2
        assert queue.is_empty
        assert queue.size == 0


class TestCommandExecutionManager:
    """Test cases for CommandExecutionManager."""
    
    def test_executor_creation(self, clean_container: DIContainer):
        """Test CommandExecutionManager creation."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            max_concurrent_commands=2,
            service_provider=clean_container
        )
        
        assert executor.command_queue is queue
        assert executor.max_concurrent_commands == 2
        assert executor.service_provider is clean_container
    
    def test_execute_command(self, clean_container: DIContainer):
        """Test direct command execution."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        
        command = TestCommand("execute_test")
        context = CommandContext(services=clean_container)
        
        result = executor.execute_command(command, context)
        
        assert result.success
        assert "execute_test" in result.message
        assert command.executed
    
    def test_execute_command_failure(self, clean_container: DIContainer):
        """Test command execution failure handling."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        
        command = TestCommand("fail_test", should_fail=True)
        context = CommandContext(services=clean_container)
        
        result = executor.execute_command(command, context)
        
        assert not result.success
        assert "failed" in result.message.lower()
        assert len(result.errors) > 0
    
    def test_execution_statistics(self, clean_container: DIContainer):
        """Test execution statistics tracking."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        
        # Execute some commands
        context = CommandContext(services=clean_container)
        executor.execute_command(TestCommand("success1"), context)
        executor.execute_command(TestCommand("success2"), context)
        executor.execute_command(TestCommand("fail", should_fail=True), context)
        
        stats = executor.get_execution_statistics()
        
        assert stats["total_executions"] == 3
        assert stats["successful_executions"] == 2
        assert stats["failed_executions"] == 1


class TestCommandHistory:
    """Test cases for CommandHistory."""
    
    def test_history_creation(self):
        """Test CommandHistory creation."""
        history = CommandHistory(max_history_size=100)
        
        assert history.max_history_size == 100
        assert len(history.get_history()) == 0
    
    def test_add_command(self):
        """Test adding command to history."""
        history = CommandHistory()
        command = TestCommand("history_test")
        result = CommandResult(success=True, message="Test result")
        
        history.add_command(command, result)
        
        entries = history.get_history()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry["command_type"] == "test_command"
        assert entry["success"] is True
        assert "history_test" in entry["description"]
    
    def test_history_limit(self):
        """Test history size limit."""
        history = CommandHistory(max_history_size=2)
        
        # Add more commands than the limit
        for i in range(5):
            command = TestCommand(f"test_{i}")
            result = CommandResult(success=True, message=f"Result {i}")
            history.add_command(command, result)
        
        entries = history.get_history()
        assert len(entries) == 2
        
        # Should keep the most recent entries
        assert entries[0]["description"].endswith("test_4")
        assert entries[1]["description"].endswith("test_3")
    
    def test_get_history_with_limit(self):
        """Test getting history with limit."""
        history = CommandHistory()
        
        # Add multiple commands
        for i in range(5):
            command = TestCommand(f"test_{i}")
            result = CommandResult(success=True, message=f"Result {i}")
            history.add_command(command, result)
        
        # Get limited history
        entries = history.get_history(limit=3)
        assert len(entries) == 3
    
    def test_get_history_with_filters(self):
        """Test getting history with filters."""
        history = CommandHistory()
        
        # Add successful and failed commands
        success_command = TestCommand("success")
        success_result = CommandResult(success=True, message="Success")
        history.add_command(success_command, success_result)
        
        fail_command = TestCommand("fail")
        fail_result = CommandResult(success=False, message="Fail")
        history.add_command(fail_command, fail_result)
        
        # Filter for successful commands only
        successful_entries = history.get_history(filters={"success": True})
        assert len(successful_entries) == 1
        assert successful_entries[0]["success"] is True
    
    @pytest.mark.slow
    def test_persistent_history(self, temp_dir: Path):
        """Test persistent command history."""
        history_file = temp_dir / "test_history.json"
        history = PersistentCommandHistory(
            history_file=str(history_file),
            max_history_size=10,
            auto_save=True
        )
        
        # Add command
        command = TestCommand("persistent_test")
        result = CommandResult(success=True, message="Persistent result")
        history.add_command(command, result)
        
        # Create new instance and verify data persisted
        history2 = PersistentCommandHistory(
            history_file=str(history_file),
            max_history_size=10
        )
        
        entries = history2.get_history()
        assert len(entries) == 1
        assert entries[0]["description"].endswith("persistent_test")


class TestCommandService:
    """Test cases for CommandService."""
    
    def test_service_creation(self, clean_container: DIContainer):
        """Test CommandService creation."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        history = CommandHistory()
        
        service = CommandService(
            command_queue=queue,
            command_executor=executor,
            command_history=history,
            service_provider=clean_container
        )
        
        assert service.command_queue is queue
        assert service.command_executor is executor
        assert service.command_history is history
        assert service.service_provider is clean_container
    
    def test_execute_command_immediate(self, clean_container: DIContainer):
        """Test immediate command execution through service."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        history = CommandHistory()
        
        service = CommandService(
            command_queue=queue,
            command_executor=executor,
            command_history=history,
            service_provider=clean_container
        )
        
        command = TestCommand("service_test")
        context = CommandContext(services=clean_container)
        
        result = service.execute_command(command, context, queue=False)
        
        assert result.success
        assert "service_test" in result.message
        
        # Command should be in history
        history_entries = service.get_command_history()
        assert len(history_entries) == 1
    
    def test_execute_command_queued(self, clean_container: DIContainer):
        """Test queued command execution through service."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        
        service = CommandService(
            command_queue=queue,
            command_executor=executor,
            service_provider=clean_container
        )
        
        command = TestCommand("queue_test")
        
        result = service.execute_command(command, queue=True)
        
        assert result.success
        assert "queued" in result.message.lower()
        assert result.data["queued"] is True
        assert "queue_id" in result.data
    
    def test_execute_commands_batch(self, clean_container: DIContainer):
        """Test batch command execution."""
        queue = CommandQueue()
        executor = CommandExecutionManager(
            command_queue=queue,
            service_provider=clean_container
        )
        
        service = CommandService(
            command_queue=queue,
            command_executor=executor,
            service_provider=clean_container
        )
        
        commands = [
            TestCommand("batch1"),
            TestCommand("batch2"), 
            TestCommand("batch_fail", should_fail=True)
        ]
        
        results = service.execute_commands_batch(commands)
        
        assert len(results) == 3
        assert results[0].success
        assert results[1].success
        assert not results[2].success  # Failed command


class TestCommandSystemConfiguration:
    """Test cases for CommandSystemConfiguration."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = CommandSystemConfiguration()
        
        assert config.max_concurrent_commands == 4
        assert config.command_queue_size == 100
        assert config.default_command_timeout == 3600
        assert config.history_enabled is True
        assert config.monitoring_enabled is True
        assert config.performance_tracking is True
    
    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = CommandSystemConfiguration(
            max_concurrent_commands=8,
            command_queue_size=50,
            history_enabled=False,
            monitoring_enabled=False
        )
        
        assert config.max_concurrent_commands == 8
        assert config.command_queue_size == 50
        assert config.history_enabled is False
        assert config.monitoring_enabled is False
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test invalid max_concurrent_commands
        with pytest.raises(Exception):  # Pydantic validation error
            CommandSystemConfiguration(max_concurrent_commands=0)
        
        with pytest.raises(Exception):
            CommandSystemConfiguration(max_concurrent_commands=25)