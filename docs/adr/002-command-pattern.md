# ADR-002: Command Pattern for Operations

## Status
Accepted

## Context

The original PlexCacheUltra system performed file operations directly within service methods, leading to several problems:

1. **No operation history**: Once an operation completed, there was no record of what was done
2. **No undo capability**: Mistaken operations could not be reversed
3. **Difficult error recovery**: Failed operations left the system in inconsistent states
4. **No operation scheduling**: All operations were immediate, no queuing or batch processing
5. **Poor audit trails**: Limited visibility into what operations were performed when
6. **Inconsistent error handling**: Each operation handled errors differently
7. **No retry mechanisms**: Failed operations could not be automatically retried
8. **Difficult testing**: Complex operations were hard to test in isolation

The system needed a way to encapsulate operations as objects that could be executed, queued, logged, and potentially reversed.

## Decision

We decided to implement the Command Pattern with comprehensive features:

### Core Command Pattern Implementation
- **ICommand interface**: Standard interface for all operations
- **BaseCommand class**: Common functionality for all commands
- **UndoableCommand class**: Support for reversible operations
- **Command metadata**: Rich metadata for tracking and monitoring

### Command Queue System
- **Priority-based queue**: Commands executed based on priority levels
- **Concurrent execution**: Support for parallel command execution
- **Queue management**: Pause, resume, and clear operations
- **Size limits**: Configurable queue size limits to prevent memory issues

### Command History and Monitoring
- **Persistent history**: Optional file-based command history storage
- **Command monitoring**: Performance metrics and execution tracking
- **Comprehensive logging**: Structured logging of all command operations
- **Error tracking**: Detailed error information and context

### Integration with DI Container
- **Service resolution**: Commands resolve dependencies through DI container
- **Factory pattern**: Command factories for creating configured commands
- **Service registration**: Commands and related services registered in container

## Consequences

### Positive Consequences

1. **Operation Auditability**
   - Complete history of all operations performed
   - Detailed metadata including timing, user context, and results
   - Compliance and troubleshooting capabilities

2. **Undo/Redo Capabilities**
   - Reversible operations through undo commands
   - Safety net for accidental operations
   - Ability to rollback problematic changes

3. **Queue Management**
   - Operations can be queued for later execution
   - Priority-based execution order
   - Batch processing capabilities for efficiency

4. **Better Error Handling**
   - Consistent error handling across all operations
   - Detailed error context and recovery information
   - Retry mechanisms for transient failures

5. **Enhanced Testing**
   - Operations can be tested in isolation
   - Mock commands for testing complex workflows
   - Deterministic operation execution

6. **Performance Monitoring**
   - Detailed performance metrics for each operation type
   - Identification of bottlenecks and optimization opportunities
   - Resource usage tracking

### Negative Consequences

1. **Increased Complexity**
   - Additional abstraction layer for simple operations
   - More classes and interfaces to maintain
   - Learning curve for developers

2. **Memory Overhead**
   - Command objects consume memory
   - History storage requires additional disk space
   - Queue management adds memory pressure

3. **Performance Impact**
   - Small overhead for command object creation
   - Serialization cost for persistent history
   - Queue management processing time

4. **Development Overhead**
   - New operations require command implementation
   - Additional testing complexity
   - More boilerplate code for simple operations

### Migration Considerations

1. **Gradual Implementation**
   - Existing operations can be wrapped in commands
   - Legacy operations can coexist with command-based operations
   - Migration can happen incrementally

2. **Backward Compatibility**
   - Existing API endpoints continue to work
   - Internal implementation changes don't affect external interfaces
   - Configuration changes are optional

## Alternatives Considered

### 1. Simple Operation Logging
- **Pros**: Easier to implement, minimal overhead
- **Cons**: No undo capability, limited queuing support
- **Why rejected**: Doesn't address queuing and undo requirements

### 2. Database Transaction Pattern
- **Pros**: Built-in rollback capabilities, ACID compliance
- **Cons**: Requires database, complex for file operations
- **Why rejected**: File operations don't map well to database transactions

### 3. Event Sourcing Pattern
- **Pros**: Complete audit trail, natural undo support
- **Cons**: Complex implementation, significant overhead
- **Why rejected**: Too complex for current requirements

### 4. Decorator Pattern for Operations
- **Pros**: Non-invasive, can wrap existing operations
- **Cons**: Limited queuing support, no built-in undo
- **Why rejected**: Doesn't provide the full range of required features

## Implementation Details

The command pattern implementation includes:

### Command Interface Hierarchy
```python
class ICommand(Protocol):
    def execute(self, context: CommandContext) -> CommandResult
    def validate(self, context: CommandContext) -> bool
    def can_undo(self) -> bool

class UndoableCommand(BaseCommand):
    def undo(self, context: CommandContext) -> CommandResult
```

### Command Types
- **File Operations**: Move, copy, delete file commands
- **Cache Operations**: Cache and restore operations
- **Batch Operations**: Multiple operations executed as a unit
- **Test Operations**: Dry-run operations for validation

### Queue Management
```python
class CommandQueue:
    def enqueue_command(self, command: ICommand) -> Optional[str]
    def dequeue_command(self) -> Optional[ICommand]
    def get_queue_status(self) -> Dict[str, Any]
    def clear_queue(self, filter_type: Optional[str] = None) -> int
```

### Command Service Integration
```python
class CommandService:
    def execute_command(self, command: ICommand, queue: bool = False)
    def execute_commands_batch(self, commands: List[ICommand])
    def undo_last_command(self) -> Optional[CommandResult]
    def get_command_history(self) -> List[Dict[str, Any]]
```

## Validation Criteria

Success of this decision is measured by:

1. **Operation Reliability**: Reduced failed operations and improved error recovery
2. **Audit Compliance**: Complete operation history with searchable records
3. **User Safety**: Undo capability prevents data loss from mistakes
4. **Performance**: Queue management improves system responsiveness
5. **Development Velocity**: Easier testing and debugging of operations

## Implementation Phases

The command pattern was implemented in phases:

1. **Phase 1**: Core command interfaces and base implementations
2. **Phase 2**: Command queue and execution management
3. **Phase 3**: Command history and monitoring
4. **Phase 4**: Integration with existing operations
5. **Phase 5**: Undo capabilities and error recovery

## Usage Examples

### Basic Command Execution
```python
# Create and execute a move command
move_command = MoveFileCommand(
    source_path="/array/movie.mkv",
    destination_path="/cache/movie.mkv",
    operation_type="move_to_cache"
)

result = command_service.execute_command(move_command)
if result.success:
    print(f"File moved successfully: {result.message}")
```

### Queued Execution
```python
# Queue multiple operations
commands = [
    MoveFileCommand(src1, dest1),
    MoveFileCommand(src2, dest2),
    CopyFileCommand(src3, dest3)
]

for command in commands:
    command_service.execute_command(command, queue=True)
```

### Undo Operations
```python
# Undo the last operation
undo_result = command_service.undo_last_command()
if undo_result and undo_result.success:
    print("Last operation undone successfully")
```

## Future Considerations

1. **Advanced Scheduling**: Integration with cron-like scheduling
2. **Command Templates**: Pre-configured command templates for common operations
3. **Remote Commands**: Commands that can be executed on remote systems
4. **Command Composition**: Complex operations composed of simpler commands
5. **Performance Optimization**: Optimize command execution for high-throughput scenarios

This ADR establishes a robust foundation for operation management that improves system reliability, auditability, and user safety while providing a clear path for future enhancements.