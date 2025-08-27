"""
Flask application factory for PlexCacheUltra.

This module implements the Flask application factory pattern, providing a clean
way to create and configure Flask applications with dependency injection support.
The factory pattern enables better testing, configuration management, and 
deployment flexibility.

Key Features:
- Application factory pattern for flexible configuration
- Dependency injection container integration
- Modular route registration with blueprints
- Comprehensive error handling and logging
- Production-ready configuration management
- Health check and monitoring endpoints
- CORS support for API endpoints
- Request/response middleware integration

Example:
    Basic usage:
    
    ```python
    from src.web.app import create_app
    from src.core.container import DIContainer
    
    container = DIContainer()
    # Configure container with services...
    
    app = create_app(container)
    app.run(host='0.0.0.0', port=5445)
    ```
    
    Testing usage:
    
    ```python
    app = create_app(container, testing=True)
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200
    ```
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from flask import Flask, request, g, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field

from ..core.container import DIContainer, IServiceProvider
from ..core.interfaces import CacheService, MediaService, FileService, NotificationService
from ..config.settings import Config


class FlaskAppConfig(BaseModel):
    """Configuration model for Flask application factory."""
    
    testing: bool = Field(default=False, description="Enable testing mode")
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=5445, description="Port to bind to")
    enable_cors: bool = Field(default=True, description="Enable CORS support")
    cors_origins: list = Field(default_factory=lambda: ["*"], description="CORS allowed origins")
    max_content_length: int = Field(default=16 * 1024 * 1024, description="Max request content length")
    secret_key: Optional[str] = Field(default=None, description="Flask secret key")
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        extra = "forbid"


class WebApplicationFactory:
    """
    Factory class for creating configured Flask applications.
    
    This factory encapsulates the application creation logic, making it easier
    to test and configure applications for different environments.
    """
    
    def __init__(self, container: DIContainer):
        """
        Initialize the web application factory.
        
        Args:
            container: Dependency injection container with configured services
            
        Raises:
            ValueError: If container is None or improperly configured
        """
        if not container:
            raise ValueError("DIContainer is required")
            
        self.container = container
        self.logger = logging.getLogger(__name__)
    
    def create_app(self, config: Optional[FlaskAppConfig] = None) -> Flask:
        """
        Create and configure a Flask application.
        
        Args:
            config: Flask application configuration (uses defaults if None)
            
        Returns:
            Configured Flask application instance
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If application creation fails
        """
        if config is None:
            config = FlaskAppConfig()
        
        try:
            app = Flask(__name__)
            
            # Configure Flask application
            self._configure_app(app, config)
            
            # Setup dependency injection
            self._setup_dependency_injection(app)
            
            # Setup CORS if enabled
            if config.enable_cors:
                self._setup_cors(app, config.cors_origins)
            
            # Register middleware
            self._register_middleware(app)
            
            # Register routes
            self._register_routes(app)
            
            # Setup error handlers
            self._setup_error_handlers(app)
            
            # Setup logging
            self._setup_logging(app, config.log_level)
            
            self.logger.info("Flask application created successfully")
            return app
            
        except Exception as e:
            self.logger.error(f"Failed to create Flask application: {e}")
            raise RuntimeError(f"Application creation failed: {e}") from e
    
    def _configure_app(self, app: Flask, config: FlaskAppConfig) -> None:
        """Configure Flask application settings."""
        app.config.update({
            'TESTING': config.testing,
            'DEBUG': config.debug,
            'MAX_CONTENT_LENGTH': config.max_content_length,
            'SECRET_KEY': config.secret_key or 'dev-key-change-in-production',
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': True
        })
        
        self.logger.debug("Flask application configuration completed")
    
    def _setup_dependency_injection(self, app: Flask) -> None:
        """Setup dependency injection for Flask application."""
        @app.before_request
        def inject_services():
            """Inject services into Flask's global context."""
            g.container = self.container
            
            # Pre-resolve commonly used services for performance
            try:
                g.cache_service = self.container.try_resolve(CacheService)
                g.media_service = self.container.try_resolve(MediaService)
                g.file_service = self.container.try_resolve(FileService)
                g.notification_service = self.container.try_resolve(NotificationService)
                # Try to resolve CachedFilesService if available
                try:
                    from ..core.cached_files_service import CachedFilesService
                    g.cached_files_service = self.container.try_resolve(CachedFilesService)
                except ImportError:
                    g.cached_files_service = None
            except Exception as e:
                self.logger.warning(f"Failed to pre-resolve services: {e}")
        
        self.logger.debug("Dependency injection setup completed")
    
    def _setup_cors(self, app: Flask, origins: list) -> None:
        """Setup CORS configuration."""
        CORS(app, origins=origins, supports_credentials=True)
        self.logger.debug(f"CORS configured for origins: {origins}")
    
    def _register_middleware(self, app: Flask) -> None:
        """Register middleware components."""
        @app.before_request
        def log_request_info():
            """Log incoming request information."""
            if not app.config.get('TESTING', False):
                self.logger.debug(
                    f"Request: {request.method} {request.url} "
                    f"from {request.remote_addr}"
                )
        
        @app.after_request
        def log_response_info(response):
            """Log outgoing response information."""
            if not app.config.get('TESTING', False):
                self.logger.debug(
                    f"Response: {response.status_code} "
                    f"for {request.method} {request.url}"
                )
            return response
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to responses."""
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
        
        self.logger.debug("Middleware registration completed")
    
    def _register_routes(self, app: Flask) -> None:
        """Register route blueprints."""
        try:
            # Import and register blueprints
            from .routes.dashboard import dashboard_bp
            from .routes.api import api_bp
            from .routes.health import health_bp
            
            app.register_blueprint(dashboard_bp)
            app.register_blueprint(api_bp, url_prefix='/api')
            app.register_blueprint(health_bp)
            
            self.logger.debug("Route blueprints registered successfully")
            
        except ImportError as e:
            self.logger.error(f"Failed to import route blueprints: {e}")
            raise RuntimeError(f"Route registration failed: {e}") from e
    
    def _setup_error_handlers(self, app: Flask) -> None:
        """Setup global error handlers."""
        @app.errorhandler(404)
        def handle_not_found(error):
            """Handle 404 Not Found errors."""
            return jsonify({
                'error': 'Resource not found',
                'status_code': 404,
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @app.errorhandler(500)
        def handle_internal_error(error):
            """Handle 500 Internal Server Error."""
            self.logger.error(f"Internal server error: {error}")
            return jsonify({
                'error': 'Internal server error',
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }), 500
        
        @app.errorhandler(400)
        def handle_bad_request(error):
            """Handle 400 Bad Request errors."""
            return jsonify({
                'error': 'Bad request',
                'status_code': 400,
                'timestamp': datetime.now().isoformat()
            }), 400
        
        @app.errorhandler(Exception)
        def handle_unexpected_error(error):
            """Handle unexpected errors."""
            self.logger.error(f"Unexpected error: {error}", exc_info=True)
            
            # Don't expose internal error details in production
            if app.config.get('DEBUG', False):
                error_detail = str(error)
            else:
                error_detail = "An unexpected error occurred"
            
            return jsonify({
                'error': error_detail,
                'status_code': 500,
                'timestamp': datetime.now().isoformat()
            }), 500
        
        self.logger.debug("Error handlers setup completed")
    
    def _setup_logging(self, app: Flask, log_level: str) -> None:
        """Setup application logging."""
        # Configure Flask's logger
        flask_logger = logging.getLogger('flask')
        flask_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Configure werkzeug logger to be less verbose
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.WARNING)
        
        self.logger.debug(f"Logging configured with level: {log_level}")


def create_app(container: DIContainer, 
               config: Optional[FlaskAppConfig] = None) -> Flask:
    """
    Factory function for creating Flask applications.
    
    This is the main entry point for creating Flask applications with
    dependency injection support.
    
    Args:
        container: Configured dependency injection container
        config: Flask application configuration
        
    Returns:
        Configured Flask application
        
    Raises:
        ValueError: If container is invalid
        RuntimeError: If application creation fails
    """
    factory = WebApplicationFactory(container)
    return factory.create_app(config)


def create_test_app(container: DIContainer) -> Flask:
    """
    Factory function for creating Flask test applications.
    
    Args:
        container: Configured dependency injection container
        
    Returns:
        Flask application configured for testing
    """
    config = FlaskAppConfig(
        testing=True,
        debug=True,
        log_level='DEBUG'
    )
    
    return create_app(container, config)