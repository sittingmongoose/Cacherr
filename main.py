#!/usr/bin/env python3
"""
Cacherr - Intelligent Plex Media Caching for Unraid.

Main application entry point.
"""

import os
import sys
import logging
import argparse
import signal
import atexit
from pathlib import Path


def setup_logging(debug: bool = False, log_file: str = None):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=handlers
    )
    
    # Reduce noise from libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('plexapi').setLevel(logging.WARNING)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Cacherr - Plex Media Caching')
    parser.add_argument('--config', '-c', default='/config/cacherr.json',
                        help='Path to configuration file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate operations without moving files')
    parser.add_argument('--web-only', action='store_true',
                        help='Run only the web server (no cache operations)')
    parser.add_argument('--run-once', action='store_true',
                        help='Run one cache cycle and exit')
    parser.add_argument('--port', type=int, default=5445,
                        help='Web server port (default: 5445)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = os.environ.get('LOG_FILE', '/config/logs/cacherr.log')
    setup_logging(debug=args.debug, log_file=log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Cacherr starting...")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        from src.config.settings import CacherrSettings
        
        config_path = args.config if Path(args.config).exists() else None
        config = CacherrSettings.load(config_path)
        
        if args.debug:
            config.debug = True
        if args.dry_run:
            config.dry_run = True
        
        # Validate Plex settings
        if not config.plex.url or not config.plex.token:
            logger.error("PLEX_URL and PLEX_TOKEN are required")
            sys.exit(1)
        
        # Initialize components
        from src.core.plex_client import PlexClient
        from src.core.file_operations import AtomicFileOperations
        from src.core.cache_manager import CacheManager
        
        # Create Plex client
        plex = PlexClient(
            url=config.plex.url,
            token=config.plex.token,
            valid_sections=config.plex.valid_sections,
        )
        
        # Create file operations
        file_ops = AtomicFileOperations(
            cache_path=config.paths.cache_destination,
            array_path=config.paths.real_source or '/media',
            max_concurrent_cache=config.performance.max_concurrent_to_cache,
            max_concurrent_array=config.performance.max_concurrent_to_array,
            dry_run=config.dry_run,
        )
        
        # Create cache manager
        cache_manager = CacheManager(
            plex_client=plex,
            file_ops=file_ops,
            config=config,
            config_dir=config.paths.config_directory,
        )
        
        # Setup shutdown handler
        def shutdown():
            logger.info("Shutting down...")
            cache_manager.stop()
        
        atexit.register(shutdown)
        signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
        signal.signal(signal.SIGINT, lambda *args: sys.exit(0))
        
        # Start cache manager
        if not cache_manager.start():
            logger.error("Failed to start cache manager")
            sys.exit(1)
        
        if args.run_once:
            # Run single cache cycle
            logger.info("Running single cache cycle...")
            result = cache_manager.run_cache_cycle()
            logger.info(f"Cache cycle complete: {result}")
            return
        
        if args.web_only:
            # Just run web server
            from src.api.routes import create_app
            app = create_app(cache_manager)
            logger.info(f"Starting web server on port {args.port}")
            app.run(host='0.0.0.0', port=args.port, debug=args.debug)
        else:
            # Run web server with background cache operations
            from src.api.routes import create_app
            import threading
            import time
            
            app = create_app(cache_manager)
            
            # Background scheduler for periodic cache cycles
            def scheduler_loop():
                interval = 3600  # Default 1 hour
                while True:
                    time.sleep(interval)
                    try:
                        logger.info("Running scheduled cache cycle...")
                        cache_manager.run_cache_cycle()
                    except Exception as e:
                        logger.error(f"Scheduled cache cycle error: {e}")
            
            scheduler = threading.Thread(target=scheduler_loop, daemon=True)
            scheduler.start()
            
            logger.info(f"Starting web server on port {args.port}")
            app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
    
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
