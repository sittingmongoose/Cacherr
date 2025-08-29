"""
Flask application with Socket.IO integration for Cacherr.

This module sets up the web server with proper Socket.IO v4 configuration
and integrates the WebSocket manager for handling client connections.
"""

import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from core.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'plexcacheultra-secret-key')

# Enable CORS for all routes
CORS(app)

# Configure Socket.IO with proper settings for v4
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading'  # Use threading for better compatibility
)

# Initialize WebSocket manager
websocket_manager = WebSocketManager(socketio, logger)

@app.route('/')
def index():
    """Serve the WebSocket test page."""
    return app.send_static_file('test.html')

@app.route('/api')
def api_info():
    """Serve basic API information."""
    return jsonify({
        'name': 'Cacherr WebSocket API',
        'version': '1.0.0',
        'status': 'operational',
        'websocket_clients': websocket_manager.get_connected_clients_count()
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'websocket_clients': websocket_manager.get_connected_clients_count(),
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    })

@app.route('/stats')
def connection_stats():
    """Get WebSocket connection statistics."""
    stats = websocket_manager.get_connection_stats()
    return jsonify(stats)

@app.route('/broadcast', methods=['POST'])
def broadcast_message():
    """Broadcast a message to all connected WebSocket clients."""
    data = request.get_json()

    if not data or 'event' not in data:
        return jsonify({'error': 'Missing event field'}), 400

    event = data['event']
    message_data = data.get('data', {})

    websocket_manager.broadcast_message(event, message_data)

    return jsonify({
        'status': 'broadcast_sent',
        'event': event,
        'clients_notified': websocket_manager.get_connected_clients_count()
    })

@socketio.on_error_default
def default_error_handler(e):
    """Handle Socket.IO errors."""
    logger.error(f'Socket.IO error: {e}')
    emit('error', {'message': 'An error occurred', 'details': str(e)})

def create_app():
    """Factory function to create and configure the Flask app."""
    return app, socketio, websocket_manager

if __name__ == '__main__':
    # For development/testing
    logger.info("Starting Cacherr WebSocket server...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5445)),
        debug=os.environ.get('DEBUG', 'false').lower() == 'true'
    )