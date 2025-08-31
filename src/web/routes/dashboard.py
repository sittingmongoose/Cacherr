"""
Dashboard routes for Cacherr web interface.

This module provides routes for the modern React-based web interface.
The root route redirects to the React application.

Example:
    ```
    GET /
    Returns: Redirect to React application
    ```
"""

import logging
import os
from pathlib import Path
from typing import Optional

from flask import Blueprint, current_app, send_from_directory, send_file, redirect, url_for
from pydantic import BaseModel, Field


# Blueprint for dashboard routes
dashboard_bp = Blueprint('dashboard', __name__)

logger = logging.getLogger(__name__)


class DashboardConfig(BaseModel):
    """Configuration for dashboard rendering."""
    
    title: str = Field(default="Cacherr Dashboard", description="Dashboard page title")
    refresh_interval: int = Field(default=5000, description="Auto-refresh interval in milliseconds")
    show_debug_info: bool = Field(default=False, description="Show debug information")
    theme: str = Field(default="default", description="Dashboard theme")
    
    class Config:
        extra = "forbid"


def serve_react_app(path=None):
    """
    Helper function to serve the React application.
    
    This function handles serving the built React application for the modern UI.
    It handles client-side routing by serving index.html for all paths
    that don't correspond to static assets.
    
    Args:
        path: Optional path for client-side routing
        
    Returns:
        React application HTML or static assets
    """
    try:
        # Define the frontend build directory using absolute path
        # In Docker, the working directory is /app, so frontend is at /app/frontend/dist
        # In development, it might be relative to the project root
        app_root = Path('/app')
        if not app_root.exists():
            # Fallback to current working directory for development
            app_root = Path.cwd()
        
        # Check multiple possible locations for the frontend
        possible_paths = [
            app_root / 'frontend' / 'dist',  # Docker path
            Path.cwd() / 'frontend' / 'dist',  # Current working directory
            Path('/mnt/user/Cursor/Cacherr/frontend/dist'),  # Absolute path for current setup
        ]
        
        frontend_dist = None
        for possible_path in possible_paths:
            if possible_path.exists():
                frontend_dist = possible_path
                break
        
        if not frontend_dist or not frontend_dist.exists():
            logger.error(f"Frontend build directory not found. Checked paths: {possible_paths}")
            return """
            <html>
            <head><title>Frontend Not Built</title></head>
            <body>
                <h1>Frontend Not Available</h1>
                <p>The React frontend has not been built yet.</p>
                <p>Please build the frontend using: npm run build</p>
                <p>Expected location: /app/frontend/dist</p>
            </body>
            </html>
            """, 404
        
        # If no path or path doesn't exist as a file, serve index.html
        if not path:
            return send_file(frontend_dist / 'index.html')
        
        # Check if the path corresponds to a static file
        static_file = frontend_dist / path
        if static_file.exists() and static_file.is_file():
            return send_from_directory(frontend_dist, path)
        
        # For client-side routing, serve index.html
        return send_file(frontend_dist / 'index.html')
        
    except Exception as e:
        logger.error(f"Failed to serve React app: {e}")
        return f"""
        <html>
        <head><title>Frontend Error</title></head>
        <body>
            <h1>Frontend Error</h1>
            <p>Failed to load React frontend: {e}</p>
            <p>Please check the application logs for more details.</p>
        </body>
        </html>
        """, 500


@dashboard_bp.route('/')
def index():
    """
    Main dashboard page route.
    
    Serves the React application directly at the root path.
    
    Returns:
        React application HTML
    """
    try:
        # Serve React application directly at root
        return serve_react_app()
        
    except Exception as e:
        logger.error(f"Failed to serve React app: {e}")
        return f"""
        <html>
        <head><title>Application Error</title></head>
        <body>
        <h1>Application Error</h1>
        <p>Failed to load application: {e}</p>
        <p>Please check the application logs for more details.</p>
        </body>
        </html>
        """, 500


@dashboard_bp.route('/dashboard/config')
def dashboard_config():
    """
    Dashboard configuration endpoint.
    
    Returns configuration information that can be used by external
    dashboard implementations or for debugging purposes.
    
    Returns:
        JSON response with dashboard configuration
    """
    try:
        config = DashboardConfig(
            show_debug_info=current_app.config.get('DEBUG', False),
            refresh_interval=5000
        )
        
        return {
            "config": config.model_dump(),
            "flask_config": {
                "debug": current_app.config.get('DEBUG', False),
                "testing": current_app.config.get('TESTING', False)
            },
            "endpoints": {
                "status": "/api/status",
                "health": "/health",
                "logs": "/api/logs",
                "run": "/api/run",
                "scheduler_start": "/api/scheduler/start",
                "scheduler_stop": "/api/scheduler/stop"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard config: {e}")
        return {"error": str(e)}, 500


@dashboard_bp.route('/app')
@dashboard_bp.route('/app/<path:path>')
def react_app(path=None):
    """
    Serve the React application at /app path (for backward compatibility).
    
    This route serves the built React application for the modern UI.
    It handles client-side routing by serving index.html for all paths
    that don't correspond to static assets.
    
    Args:
        path: Optional path for client-side routing
        
    Returns:
        React application HTML or static assets
    """
    return serve_react_app(path)


@dashboard_bp.route('/assets/<path:filename>')
def react_assets(filename):
    """
    Serve React application static assets.
    
    Args:
        filename: Asset filename
        
    Returns:
        Static asset file
    """
    try:
        # Use the same path resolution logic as react_app
        app_root = Path('/app')
        if not app_root.exists():
            app_root = Path.cwd()
        
        # Check multiple possible locations for the frontend
        possible_paths = [
            app_root / 'frontend' / 'dist',  # Docker path
            Path.cwd() / 'frontend' / 'dist',  # Current working directory
            Path('/mnt/user/Cursor/Cacherr/frontend/dist'),  # Absolute path for current setup
        ]
        
        frontend_dist = None
        for path in possible_paths:
            if path.exists():
                frontend_dist = path
                break
        
        if not frontend_dist:
            return "Frontend not found", 404
            
        assets_dir = frontend_dist / 'assets'
        
        if not assets_dir.exists():
            return "Asset not found", 404
            
        return send_from_directory(assets_dir, filename)
        
    except Exception as e:
        logger.error(f"Failed to serve asset {filename}: {e}")
        return "Asset error", 500


@dashboard_bp.route('/<path:path>')
def catch_all(path):
    """
    Catch-all route for client-side routing.
    
    This route handles all other paths and serves the React application
    to enable client-side routing. It should be placed after all other
    specific routes.
    
    Args:
        path: The requested path
        
    Returns:
        React application HTML for client-side routing
    """
    # Skip API routes and other backend routes
    if path.startswith(('api/', 'health', 'dashboard/config')):
        return "Not found", 404
    
    # Serve React app for all other paths (client-side routing)
    return serve_react_app(path)