#!/usr/bin/env python3
"""
Main entry point for PlexCacheUltra WebSocket Server.

This module starts the Flask-Socket.IO web server with proper
WebSocket event handling for real-time communication.
"""

import os
import sys
import logging
from app import create_app

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the WebSocket server."""

    # Configure logging
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/plexcache_websocket.log', mode='a')
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Initializing PlexCacheUltra WebSocket Server...")

    try:
        # Create the Flask app with Socket.IO
        app, socketio, websocket_manager = create_app()

        # Get server configuration from environment
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', '5000'))
        debug = os.environ.get('DEBUG', 'false').lower() == 'true'

        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info("WebSocket functionality initialized successfully")

        # Start the server
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug
        )

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()