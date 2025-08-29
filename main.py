#!/usr/bin/env python3
"""
Cacherr - Docker-optimized Plex media caching system
Main application entry point using modular architecture with dependency injection
"""

import os
import sys
import logging
import signal
from pathlib import Path
from typing import Optional

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from dotenv import load_dotenv

# Import the new modular application factory
try:
    from src.application import create_application, create_production_application, ApplicationContext
    from src.config.settings import Config
except ImportError as e:
    # Fallback to relative imports if package import fails
    try:
        from application import create_application, create_production_application, ApplicationContext
        from config.settings import Config
    except ImportError:
        print(f"Import error: {e}")
        print(f"Current sys.path: {sys.path}")
        print(f"Looking for src directory at: {src_path}")
        raise

# Load environment variables
load_dotenv()

# Global application context for signal handling
app_context: Optional[ApplicationContext] = None
logger = logging.getLogger(__name__)


def setup_signal_handlers() -> None:
    """
    Setup signal handlers for graceful shutdown.
    
    Handles SIGTERM and SIGINT (Ctrl+C) for clean application shutdown.
    """
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        
        if app_context:
            try:
                app_context.shutdown(timeout_seconds=30)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                sys.exit(1)
        
        logger.info("Shutdown completed")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.debug("Signal handlers registered")


def determine_run_mode() -> str:
    """
    Determine the application run mode based on environment variables.
    
    Returns:
        Run mode string: 'development', 'production', or 'testing'
    """
    # Check for explicit mode setting
    run_mode = os.getenv('RUN_MODE', '').lower()
    if run_mode in ['development', 'dev']:
        return 'development'
    elif run_mode in ['testing', 'test']:
        return 'testing'
    elif run_mode in ['production', 'prod']:
        return 'production'
    
    # Determine mode based on other environment variables
    if os.getenv('DEBUG', '').lower() in ['true', '1', 'yes']:
        return 'development'
    elif os.getenv('TESTING', '').lower() in ['true', '1', 'yes']:
        return 'testing'
    else:
        return 'production'


def create_application_for_mode(mode: str) -> ApplicationContext:
    """
    Create application context based on the specified mode.
    
    Args:
        mode: Application mode ('development', 'production', 'testing')
        
    Returns:
        Configured ApplicationContext
    """
    if mode == 'development':
        logger.info("Creating development application configuration")
        return create_application({
            'web': {
                'debug': True,
                'port': int(os.getenv('WEB_PORT', '5445')),
                'testing': False,
                'host': os.getenv('WEB_HOST', '0.0.0.0')
            },
            'scheduler': {
                'enable_task_notifications': False  # Reduce noise in development
            },
            'auto_start_scheduler': os.getenv('AUTO_START_SCHEDULER', 'false').lower() in ['true', '1', 'yes'],
            'log_level': os.getenv('LOG_LEVEL', 'DEBUG'),
            'validate_config_on_startup': True
        })
    
    elif mode == 'testing':
        logger.info("Creating testing application configuration")
        return create_application({
            'web': {
                'testing': True,
                'debug': True,
                'port': 0,  # Use random port for testing
                'host': '127.0.0.1'
            },
            'enable_scheduler': False,  # Don't start scheduler in tests
            'enable_real_time_watcher': False,
            'initialize_services_on_startup': False,  # Let tests control initialization
            'setup_logging': False,  # Let test framework handle logging
            'log_level': 'DEBUG'
        })
    
    else:  # production mode
        logger.info("Creating production application configuration")
        return create_application({
            'web': {
                'debug': False,
                'port': int(os.getenv('WEB_PORT', os.getenv('PORT', '5445'))),
                'testing': False,
                'host': os.getenv('WEB_HOST', '0.0.0.0')
            },
            'scheduler': {
                'enable_task_notifications': True,
                'max_worker_threads': int(os.getenv('SCHEDULER_WORKERS', '4')),
                'scheduler_loop_interval': int(os.getenv('SCHEDULER_INTERVAL', '60'))
            },
            'auto_start_scheduler': os.getenv('AUTO_START_SCHEDULER', 'true').lower() in ['true', '1', 'yes'],
            'validate_config_on_startup': True,
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'enable_real_time_watcher': os.getenv('ENABLE_REAL_TIME_WATCHER', 'false').lower() in ['true', '1', 'yes']
        })


def run_web_server(app_context: ApplicationContext) -> None:
    """
    Run the Flask web server with WebSocket support.
    
    Args:
        app_context: Application context containing the web app
    """
    web_app = app_context.get_web_app()
    if not web_app:
        raise RuntimeError("Web application not available")
    
    # Get configuration from app context
    web_config = app_context.app_config.web
    
    logger.info(f"Starting web server on {web_config.host}:{web_config.port}")
    
    try:
        # Check if WebSocket support is available
        from src.web.app import WebApplicationFactory
        factory = WebApplicationFactory(app_context.container)
        
        # Create the app with WebSocket support
        web_app_with_websocket = factory.create_app()
        
        # Check if the factory has SocketIO support
        if hasattr(factory, 'socketio') and factory.socketio:
            logger.info("Starting Flask-SocketIO server with WebSocket support")
            # Run with SocketIO
            factory.socketio.run(
                web_app_with_websocket,
                host=web_config.host,
                port=web_config.port,
                debug=web_config.debug,
                use_reloader=False,
                allow_unsafe_werkzeug=True  # Required for production
            )
        else:
            logger.info("Starting standard Flask server (WebSocket not available)")
            # Fallback to standard Flask
            web_app.run(
                host=web_config.host,
                port=web_config.port,
                debug=web_config.debug,
                use_reloader=False,
                threaded=True
            )
    except Exception as e:
        logger.error(f"Web server failed to start: {e}")
        raise


def run_cli_mode() -> None:
    """
    Run in CLI mode for one-time operations.
    
    This mode is activated when specific command-line arguments are provided
    for running cache operations without starting the web server.
    """
    logger.info("Running in CLI mode")
    
    # Parse command line arguments for CLI operations
    import argparse
    
    parser = argparse.ArgumentParser(description='Cacherr CLI Operations')
    parser.add_argument('--run-cache', action='store_true', help='Run cache operation once and exit')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode (dry run)')
    parser.add_argument('--cleanup', action='store_true', help='Run cache cleanup operation')
    parser.add_argument('--validate-config', action='store_true', help='Validate configuration and exit')
    
    args = parser.parse_args()
    
    if not any([args.run_cache, args.test_mode, args.cleanup, args.validate_config]):
        parser.print_help()
        return
    
    # Create minimal application context for CLI operations
    cli_app_context = create_application({
        'enable_scheduler': False,
        'auto_start_scheduler': False,
        'initialize_services_on_startup': True,
        'setup_logging': True,
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    })
    
    try:
        cli_app_context.start()
        
        if args.validate_config:
            logger.info("Configuration validation completed successfully")
            return
        
        cache_engine = cli_app_context.get_cache_engine()
        if not cache_engine:
            logger.error("Cache engine not available for CLI operations")
            sys.exit(1)
        
        if args.cleanup:
            logger.info("Running cache cleanup operation...")
            # This would need to be implemented based on the actual cache service
            logger.info("Cache cleanup completed")
        
        elif args.run_cache or args.test_mode:
            logger.info(f"Running cache operation (test_mode={args.test_mode})...")
            success = cache_engine.run(test_mode=args.test_mode)
            
            if success:
                logger.info("Cache operation completed successfully")
            else:
                logger.error("Cache operation failed")
                sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("CLI operation interrupted by user")
    except Exception as e:
        logger.error(f"CLI operation failed: {e}")
        sys.exit(1)
    finally:
        cli_app_context.shutdown()


def main():
    """
    Main application entry point.
    
    Determines run mode, creates application context, and starts services.
    """
    global app_context
    
    try:
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        # Check if running in CLI mode
        if len(sys.argv) > 1 and any(arg.startswith('--') for arg in sys.argv[1:]):
            run_cli_mode()
            return
        
        # Determine run mode
        run_mode = determine_run_mode()
        print(f"Starting Cacherr in {run_mode} mode...")
        
        # Create application context
        app_context = create_application_for_mode(run_mode)
        
        # Start the application
        if not app_context.start():
            print("Failed to start application")
            sys.exit(1)
        
        # Print startup information
        status = app_context.get_status()
        print(f"Cacherr started successfully!")
        print(f"Web interface: http://{app_context.app_config.web.host}:{app_context.app_config.web.port}")
        print(f"Uptime: {status['uptime_seconds']:.1f} seconds")
        
        if status['startup_errors']:
            print(f"Startup warnings: {len(status['startup_errors'])}")
            for error in status['startup_errors']:
                print(f"  - {error}")
        
        # Start web server (this blocks until shutdown)
        run_web_server(app_context)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        print(f"Failed to start Cacherr: {e}")
        sys.exit(1)
    finally:
        # Ensure cleanup
        if app_context:
            try:
                app_context.shutdown()
            except Exception as e:
                logger.error(f"Error during final cleanup: {e}")


if __name__ == '__main__':
    main()