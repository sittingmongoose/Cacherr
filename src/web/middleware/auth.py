"""
Authentication middleware for PlexCacheUltra web application.

This module provides authentication and authorization middleware for the
Flask web application. Currently implements basic security headers and
request validation, with extensible design for future authentication
mechanisms.

Features:
- Security headers injection
- Request rate limiting (placeholder)
- IP-based access control (placeholder)
- API key validation (placeholder)
- Session management (placeholder)

Example:
    ```python
    from src.web.middleware.auth import setup_auth_middleware
    
    app = Flask(__name__)
    setup_auth_middleware(app)
    ```
"""

import logging
from typing import Optional, List, Dict, Any
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, request, g, jsonify, current_app
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class AuthConfig(BaseModel):
    """Configuration for authentication middleware."""
    
    enable_rate_limiting: bool = Field(default=False, description="Enable request rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Max requests per minute per IP")
    allowed_ips: Optional[List[str]] = Field(default=None, description="Allowed IP addresses (None = all)")
    blocked_ips: Optional[List[str]] = Field(default=None, description="Blocked IP addresses")
    require_api_key: bool = Field(default=False, description="Require API key for API endpoints")
    api_key_header: str = Field(default="X-API-Key", description="Header name for API key")
    enable_security_headers: bool = Field(default=True, description="Enable security headers")
    
    class Config:
        extra = "forbid"


class RateLimiter:
    """
    Simple in-memory rate limiter for request throttling.
    
    This is a basic implementation suitable for single-instance deployments.
    For production use with multiple instances, consider using Redis or
    similar distributed storage.
    """
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, List[datetime]] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a client is allowed to make a request.
        
        Args:
            client_id: Client identifier (usually IP address)
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > minute_ago
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.max_requests:
            self.logger.warning(f"Rate limit exceeded for client {client_id}")
            return False
        
        # Record this request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get number of remaining requests for a client."""
        if client_id not in self.requests:
            return self.max_requests
        
        minute_ago = datetime.now() - timedelta(minutes=1)
        recent_requests = [
            req_time for req_time in self.requests[client_id] 
            if req_time > minute_ago
        ]
        
        return max(0, self.max_requests - len(recent_requests))


class AuthMiddleware:
    """
    Authentication and security middleware for Flask applications.
    
    Provides comprehensive request processing including rate limiting,
    IP filtering, API key validation, and security headers.
    """
    
    def __init__(self, app: Optional[Flask] = None, config: Optional[AuthConfig] = None):
        """
        Initialize authentication middleware.
        
        Args:
            app: Flask application instance (optional)
            config: Authentication configuration (uses defaults if None)
        """
        self.config = config or AuthConfig()
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_minute) if self.config.enable_rate_limiting else None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """
        Initialize middleware with Flask application.
        
        Args:
            app: Flask application instance
        """
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Store middleware instance in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['auth_middleware'] = self
        
        self.logger.info("Authentication middleware initialized")
    
    def before_request(self) -> Optional[tuple]:
        """
        Process incoming requests before route handling.
        
        Returns:
            Tuple of (response, status_code) if request should be rejected,
            None if request should continue processing
        """
        try:
            client_ip = self.get_client_ip()
            
            # Check IP-based access control
            if not self.is_ip_allowed(client_ip):
                self.logger.warning(f"Request blocked from IP: {client_ip}")
                return jsonify({
                    'error': 'Access denied',
                    'timestamp': datetime.now().isoformat()
                }), 403
            
            # Check rate limiting
            if self.rate_limiter and not self.rate_limiter.is_allowed(client_ip):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': 60,
                    'timestamp': datetime.now().isoformat()
                }), 429
            
            # Check API key for API endpoints
            if self.config.require_api_key and request.path.startswith('/api/'):
                if not self.validate_api_key():
                    return jsonify({
                        'error': 'Invalid or missing API key',
                        'timestamp': datetime.now().isoformat()
                    }), 401
            
            # Store client info in request context
            g.client_ip = client_ip
            g.auth_info = {
                'ip_allowed': True,
                'rate_limit_remaining': self.rate_limiter.get_remaining_requests(client_ip) if self.rate_limiter else None,
                'api_key_valid': True if not self.config.require_api_key else self.validate_api_key()
            }
            
        except Exception as e:
            self.logger.error(f"Error in before_request processing: {e}")
            return jsonify({
                'error': 'Authentication processing error',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        return None
    
    def after_request(self, response) -> Any:
        """
        Process outgoing responses after route handling.
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response object
        """
        try:
            # Add security headers
            if self.config.enable_security_headers:
                response = self.add_security_headers(response)
            
            # Add rate limiting headers
            if self.rate_limiter and hasattr(g, 'client_ip'):
                remaining = self.rate_limiter.get_remaining_requests(g.client_ip)
                response.headers['X-RateLimit-Limit'] = str(self.config.rate_limit_per_minute)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int((datetime.now() + timedelta(minutes=1)).timestamp()))
            
        except Exception as e:
            self.logger.error(f"Error in after_request processing: {e}")
        
        return response
    
    def get_client_ip(self) -> str:
        """
        Get the client IP address from the request.
        
        Handles various proxy headers to get the real client IP.
        
        Returns:
            Client IP address as string
        """
        # Check various headers that might contain the real IP
        ip_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Client-IP',
            'CF-Connecting-IP',  # Cloudflare
            'True-Client-IP'     # Cloudflare Enterprise
        ]
        
        for header in ip_headers:
            ip = request.headers.get(header)
            if ip:
                # X-Forwarded-For can contain multiple IPs, take the first one
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                return ip
        
        # Fallback to remote_addr
        return request.remote_addr or 'unknown'
    
    def is_ip_allowed(self, client_ip: str) -> bool:
        """
        Check if an IP address is allowed access.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if IP is allowed, False otherwise
        """
        # Check blocked IPs first
        if self.config.blocked_ips and client_ip in self.config.blocked_ips:
            return False
        
        # If allowed IPs are specified, check against the list
        if self.config.allowed_ips:
            return client_ip in self.config.allowed_ips
        
        # If no restrictions, allow all
        return True
    
    def validate_api_key(self) -> bool:
        """
        Validate API key from request headers.
        
        Returns:
            True if API key is valid, False otherwise
        """
        api_key = request.headers.get(self.config.api_key_header)
        
        if not api_key:
            return False
        
        # TODO: Implement actual API key validation logic
        # For now, we'll just check if it's not empty
        # In a real implementation, you would validate against a database
        # or configuration file
        return len(api_key.strip()) > 0
    
    def add_security_headers(self, response) -> Any:
        """
        Add security headers to the response.
        
        Args:
            response: Flask response object
            
        Returns:
            Response object with added security headers
        """
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


def require_auth(func):
    """
    Decorator to require authentication for specific routes.
    
    Args:
        func: Route function to protect
        
    Returns:
        Wrapped function with authentication requirement
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if authentication info is available
        if not hasattr(g, 'auth_info'):
            return jsonify({
                'error': 'Authentication required',
                'timestamp': datetime.now().isoformat()
            }), 401
        
        # Additional authentication checks can be added here
        
        return func(*args, **kwargs)
    
    return wrapper


def require_api_key(func):
    """
    Decorator to require API key for specific routes.
    
    Args:
        func: Route function to protect
        
    Returns:
        Wrapped function with API key requirement
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_middleware = current_app.extensions.get('auth_middleware')
        
        if not auth_middleware or not auth_middleware.validate_api_key():
            return jsonify({
                'error': 'Valid API key required',
                'timestamp': datetime.now().isoformat()
            }), 401
        
        return func(*args, **kwargs)
    
    return wrapper


def setup_auth_middleware(app: Flask, config: Optional[AuthConfig] = None) -> AuthMiddleware:
    """
    Setup authentication middleware for a Flask application.
    
    Args:
        app: Flask application instance
        config: Authentication configuration (optional)
        
    Returns:
        Configured AuthMiddleware instance
    """
    middleware = AuthMiddleware(app, config)
    return middleware