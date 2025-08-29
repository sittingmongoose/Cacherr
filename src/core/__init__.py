"""
Core module for PlexCacheUltra WebSocket functionality.

This module provides the core WebSocket management capabilities
with proper Socket.IO v4 event handler signatures.
"""

from .websocket_manager import WebSocketManager

__all__ = ['WebSocketManager']