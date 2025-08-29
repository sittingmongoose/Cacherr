"""
Example usage of the Cacherr Command Pattern system.

This module demonstrates how to use the command system for cache operations,
including setting up the dependency injection container, creating commands,
and using the various features like queuing, monitoring, and undo functionality.

This serves as both documentation and a working example of the command system.
"""

import logging
from pathlib import Path
from typing import List

# Import the command system components
from .command_service import setup_command_system, CommandSystemConfiguration
from .commands import CommandPriority
from .container import DIContainer
from .operation_integration import create_operation_handler, create_legacy_bridge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_example_command_system() -> tuple:
    """
    Set up the command system for demonstration.
    
    Returns:
        Tuple of (container, command_service, operation_handler)
    """
    # Create DI container
    container = DIContainer()
    
    # Note: In a real application, you would register your actual services:
    # - FileService implementation
    # - CacheService implementation  
    # - NotificationService implementation
    # - MetricsRepository implementation
    
    # Set up the command system with configuration
    command_service = setup_command_system(
        container=container,
        cache_directory="/cache",  # Would come from actual config
        array_directory="/array",  # Would come from actual config
        config_overrides={
            "max_concurrent_commands": 2,
            "history_enabled": True,
            "monitoring_enabled": True,
            "history_file": "data/demo_command_history.json"
        }
    )
    
    # Create operation handler for high-level operations
    operation_handler = create_operation_handler(command_service)
    
    return container, command_service, operation_handler


def demonstrate_basic_command_usage():
    """Demonstrate basic command creation and execution."""
    logger.info("=== Basic Command Usage Demo ===")
    
    try:
        # Set up the system
        container, command_service, operation_handler = setup_example_command_system()
        
        # Example files to work with
        example_files = [
            "/array/Movies/Example Movie (2024)/Example Movie (2024).mkv",
            "/array/TV Shows/Example Series/Season 01/S01E01 - Pilot.mkv",
            "/array/TV Shows/Example Series/Season 01/S01E02 - Episode 2.mkv"
        ]
        
        # 1. Create and execute a test cache operation command
        logger.info("1. Testing cache operation analysis...")
        test_result = operation_handler.test_cache_operation(
            files=example_files,
            operation_type="cache"
        )
        logger.info(f"Test result: {test_result.success} - {test_result.message}")
        
        # 2. Create a move to cache command with high priority
        logger.info("2. Creating move to cache command...")
        move_result = operation_handler.move_files_to_cache(
            files=example_files,
            source_directory="/array",
            cache_directory="/cache",
            create_symlinks=True,
            dry_run=True,  # Dry run for demo
            priority=CommandPriority.HIGH
        )
        logger.info(f"Move result: {move_result.success} - {move_result.message}")
        
        # 3. Demonstrate batch operations
        logger.info("3. Demonstrating batch operations...")
        batch_operations = [
            {
                "type": "test_cache_operation",
                "files": example_files[:2],
                "operation_type": "cache",
                "priority": "normal"
            },
            {
                "type": "analyze_cache_impact", 
                "files": example_files[2:],
                "operation_type": "cache",
                "priority": "low"
            }
        ]
        
        batch_results = operation_handler.batch_cache_operations(
            operations=batch_operations,
            dry_run=True
        )
        
        successful_batch = sum(1 for r in batch_results if r.success)
        logger.info(f"Batch operations: {successful_batch}/{len(batch_results)} successful")
        
        # 4. Check queue status and execution statistics
        logger.info("4. Checking system status...")
        queue_status = command_service.get_queue_status()
        exec_stats = command_service.get_execution_statistics()
        
        logger.info(f"Queue size: {queue_status.get('pending_commands', 0)}")
        logger.info(f"Total commands executed: {exec_stats.get('total_executed', 0)}")
        
        # 5. Get command history
        logger.info("5. Checking command history...")
        history = command_service.get_command_history(limit=5)
        logger.info(f"Recent history entries: {len(history)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        return False


def demonstrate_advanced_features():
    """Demonstrate advanced command system features."""
    logger.info("=== Advanced Features Demo ===")
    
    try:
        # Set up the system
        container, command_service, operation_handler = setup_example_command_system()
        
        example_files = ["/array/test_file.mkv"]
        
        # 1. Demonstrate command factory usage
        logger.info("1. Using command factory directly...")
        factory = container.resolve('CacheCommandFactory')  # String resolution for demo
        
        # Note: This would fail in demo since factory needs actual service registrations
        # In real usage with proper services registered:
        # command = factory.create_move_to_cache_command(
        #     files=example_files,
        #     priority=CommandPriority.CRITICAL
        # )
        # result = command_service.execute_command(command)
        
        # 2. Demonstrate queue management
        logger.info("2. Queue management features...")
        command_service.pause_queue()
        logger.info("Queue paused")
        
        command_service.resume_queue()
        logger.info("Queue resumed")
        
        # 3. Demonstrate performance insights
        logger.info("3. Getting performance insights...")
        insights = command_service.get_performance_insights()
        logger.info(f"Performance insights available: {len(insights)}")
        
        # 4. Legacy compatibility bridge
        logger.info("4. Using legacy compatibility bridge...")
        legacy_bridge = create_legacy_bridge(command_service)
        
        # This demonstrates backward compatibility with old interfaces
        # legacy_result = legacy_bridge.execute_cache_operation(
        #     files=example_files,
        #     operation_type="cache",
        #     dry_run=True
        # )
        
        return True
        
    except Exception as e:
        logger.error(f"Advanced demo failed: {str(e)}", exc_info=True)
        return False


def demonstrate_configuration_options():
    """Demonstrate different configuration options for the command system."""
    logger.info("=== Configuration Options Demo ===")
    
    try:
        # 1. Minimal configuration
        logger.info("1. Minimal configuration setup...")
        minimal_config = CommandSystemConfiguration(
            max_concurrent_commands=1,
            history_enabled=False,
            monitoring_enabled=False
        )
        
        container1 = DIContainer()
        # In real usage: register actual services here
        
        # 2. High-performance configuration
        logger.info("2. High-performance configuration...")
        performance_config = CommandSystemConfiguration(
            max_concurrent_commands=8,
            command_queue_size=200,
            default_command_timeout=7200,  # 2 hours
            history_enabled=True,
            history_persistent=True,
            monitoring_enabled=True,
            performance_tracking=True
        )
        
        # 3. Development configuration with debugging
        logger.info("3. Development configuration...")
        dev_config = CommandSystemConfiguration(
            max_concurrent_commands=2,
            history_enabled=True,
            history_persistent=False,  # In-memory for dev
            monitoring_enabled=True,
            auto_cleanup_history=False,  # Keep all history for debugging
            alert_thresholds={
                "max_execution_time": 300,  # 5 minutes (shorter for dev)
                "error_rate_threshold": 0.05  # 5% (stricter for dev)
            }
        )
        
        logger.info("Configuration examples demonstrated")
        return True
        
    except Exception as e:
        logger.error(f"Configuration demo failed: {str(e)}", exc_info=True)
        return False


def run_complete_demo():
    """Run the complete command system demonstration."""
    logger.info("Starting Cacherr Command System Demo")
    logger.info("=" * 50)
    
    success_count = 0
    
    # Run all demonstration sections
    demos = [
        ("Basic Command Usage", demonstrate_basic_command_usage),
        ("Advanced Features", demonstrate_advanced_features),
        ("Configuration Options", demonstrate_configuration_options)
    ]
    
    for name, demo_func in demos:
        logger.info(f"\n--- {name} ---")
        try:
            if demo_func():
                logger.info(f"✓ {name} completed successfully")
                success_count += 1
            else:
                logger.warning(f"✗ {name} had issues")
        except Exception as e:
            logger.error(f"✗ {name} failed with exception: {str(e)}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Demo Summary: {success_count}/{len(demos)} sections successful")
    
    if success_count == len(demos):
        logger.info("🎉 All demonstrations completed successfully!")
    else:
        logger.info("⚠️  Some demonstrations had issues (expected in demo environment)")
    
    logger.info("\nNote: Some features require actual service implementations")
    logger.info("This demo shows the command system structure and interfaces")


if __name__ == "__main__":
    # Run the demo when executed directly
    run_complete_demo()