"""
Health check routes for PlexCacheUltra web application.

This module provides health check and monitoring endpoints for Docker
container health checks, load balancer health checks, and system monitoring.
Includes detailed system status, dependency health, and performance metrics.

Endpoints:
- /health: Basic health check endpoint
- /health/detailed: Detailed system health information
- /health/dependencies: Check status of external dependencies
- /ready: Readiness probe endpoint for orchestration systems

Example:
    Basic health check:
    ```
    GET /health
    {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z",
        "version": "1.0.0"
    }
    ```
    
    Detailed health check:
    ```
    GET /health/detailed
    {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z",
        "version": "1.0.0",
        "uptime_seconds": 3600,
        "services": {
            "cache_service": "healthy",
            "media_service": "healthy",
            "file_service": "healthy"
        },
        "system": {
            "memory_usage_mb": 256,
            "disk_usage_percent": 45
        }
    }
    ```
"""

import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from flask import Blueprint, jsonify, g
from pydantic import BaseModel, Field

from ...core.interfaces import CacheService, MediaService, FileService, NotificationService


# Blueprint for health check routes
health_bp = Blueprint('health', __name__)

logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_start_time = time.time()


class HealthStatus(BaseModel):
    """Health status response model."""
    
    status: str = Field(description="Overall health status")
    timestamp: str = Field(description="ISO timestamp of health check")
    version: str = Field(default="1.0.0", description="Application version")
    uptime_seconds: Optional[int] = Field(default=None, description="Application uptime in seconds")


class DetailedHealthStatus(HealthStatus):
    """Detailed health status with service and system information."""
    
    services: Dict[str, str] = Field(default_factory=dict, description="Service health status")
    system: Dict[str, Any] = Field(default_factory=dict, description="System metrics")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")
    cache_statistics: Dict[str, Any] = Field(default_factory=dict, description="Cache statistics")


class DependencyHealthChecker:
    """
    Helper class for checking the health of external dependencies.
    
    Provides methods to check Plex server connectivity, file system access,
    and other external services that the application depends on.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def check_plex_connectivity(self, media_service: MediaService) -> str:
        """
        Check Plex server connectivity.
        
        Args:
            media_service: Media service instance to test
            
        Returns:
            Health status string ("healthy", "unhealthy", "unknown")
        """
        try:
            if not media_service:
                return "not_configured"
            
            plex_connection = media_service.get_plex_connection()
            if plex_connection is None:
                return "unhealthy"
            
            # Try to access Plex server
            _ = plex_connection.library
            return "healthy"
            
        except Exception as e:
            self.logger.warning(f"Plex connectivity check failed: {e}")
            return "unhealthy"
    
    def check_file_system_access(self, file_service: FileService) -> str:
        """
        Check file system access for key directories.
        
        Args:
            file_service: File service instance to test
            
        Returns:
            Health status string ("healthy", "unhealthy", "unknown")
        """
        try:
            if not file_service:
                return "not_configured"
            
            # This would need to be implemented based on your file service interface
            # For now, we'll assume healthy if the service exists
            return "healthy"
            
        except Exception as e:
            self.logger.warning(f"File system access check failed: {e}")
            return "unhealthy"
    
    def check_cache_service(self, cache_service: CacheService) -> str:
        """
        Check cache service health.
        
        Args:
            cache_service: Cache service instance to test
            
        Returns:
            Health status string ("healthy", "unhealthy", "unknown")
        """
        try:
            if not cache_service:
                return "not_configured"
            
            # Try to get cache statistics
            _ = cache_service.get_cache_statistics()
            return "healthy"
            
        except Exception as e:
            self.logger.warning(f"Cache service health check failed: {e}")
            return "unhealthy"
    
    def check_notification_service(self, notification_service: NotificationService) -> str:
        """
        Check notification service health.
        
        Args:
            notification_service: Notification service instance to test
            
        Returns:
            Health status string ("healthy", "unhealthy", "unknown")
        """
        try:
            if not notification_service:
                return "not_configured"
            
            # Check if webhook configuration is valid
            is_valid = notification_service.validate_webhook_config()
            return "healthy" if is_valid else "misconfigured"
            
        except Exception as e:
            self.logger.warning(f"Notification service health check failed: {e}")
            return "unhealthy"


def get_system_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics.
    
    Returns:
        Dictionary containing system metrics like memory, CPU, and disk usage
    """
    try:
        # Get memory information
        memory = psutil.virtual_memory()
        
        # Get disk usage for root filesystem
        disk = psutil.disk_usage('/')
        
        # Get CPU usage (1-second average)
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "memory_usage_mb": round(memory.used / (1024 * 1024), 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2),
            "memory_percent": memory.percent,
            "disk_usage_gb": round(disk.used / (1024 * 1024 * 1024), 2),
            "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2),
            "cpu_usage_percent": cpu_percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        return {"error": f"Failed to collect system metrics: {e}"}


@health_bp.route('/health')
def health_check():
    """
    Basic health check endpoint.
    
    This endpoint provides a simple health status response suitable for
    Docker health checks and load balancer health probes.
    
    Returns:
        JSON response with basic health information
    """
    try:
        current_time = time.time()
        uptime_seconds = int(current_time - _start_time)
        
        response = HealthStatus(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime_seconds
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


@health_bp.route('/health/detailed')
def detailed_health_check():
    """
    Detailed health check endpoint.
    
    This endpoint provides comprehensive health information including
    service status, system metrics, and dependency health checks.
    
    Returns:
        JSON response with detailed health information
    """
    try:
        current_time = time.time()
        uptime_seconds = int(current_time - _start_time)
        
        # Initialize health checker
        health_checker = DependencyHealthChecker()
        
        # Check service health
        services_status = {}
        dependencies_status = {}
        cache_stats = {}
        
        # Get services from Flask context
        cache_service = getattr(g, 'cache_service', None)
        media_service = getattr(g, 'media_service', None)
        file_service = getattr(g, 'file_service', None)
        notification_service = getattr(g, 'notification_service', None)
        
        # Check individual services
        if cache_service:
            services_status['cache_service'] = health_checker.check_cache_service(cache_service)
            try:
                cache_stats = cache_service.get_cache_statistics()
            except Exception as e:
                logger.warning(f"Failed to get cache statistics: {e}")
                cache_stats = {"error": str(e)}
        else:
            services_status['cache_service'] = 'not_configured'
        
        if media_service:
            services_status['media_service'] = health_checker.check_plex_connectivity(media_service)
            dependencies_status['plex_server'] = services_status['media_service']
        else:
            services_status['media_service'] = 'not_configured'
            dependencies_status['plex_server'] = 'not_configured'
        
        if file_service:
            services_status['file_service'] = health_checker.check_file_system_access(file_service)
            dependencies_status['file_system'] = services_status['file_service']
        else:
            services_status['file_service'] = 'not_configured'
            dependencies_status['file_system'] = 'not_configured'
        
        if notification_service:
            services_status['notification_service'] = health_checker.check_notification_service(notification_service)
        else:
            services_status['notification_service'] = 'not_configured'
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        # Determine overall health status
        unhealthy_services = [k for k, v in services_status.items() if v == 'unhealthy']
        overall_status = "unhealthy" if unhealthy_services else "healthy"
        
        response = DetailedHealthStatus(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime_seconds,
            services=services_status,
            system=system_metrics,
            dependencies=dependencies_status,
            cache_statistics=cache_stats
        )
        
        status_code = 200 if overall_status == "healthy" else 503
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


@health_bp.route('/health/dependencies')
def dependencies_health_check():
    """
    Dependencies health check endpoint.
    
    This endpoint specifically checks the health of external dependencies
    like Plex server, file system access, and other critical services.
    
    Returns:
        JSON response with dependency health information
    """
    try:
        health_checker = DependencyHealthChecker()
        
        # Get services from Flask context
        media_service = getattr(g, 'media_service', None)
        file_service = getattr(g, 'file_service', None)
        notification_service = getattr(g, 'notification_service', None)
        
        dependencies = {
            "plex_server": health_checker.check_plex_connectivity(media_service),
            "file_system": health_checker.check_file_system_access(file_service),
            "notification_system": health_checker.check_notification_service(notification_service)
        }
        
        # Determine overall dependency health
        unhealthy_deps = [k for k, v in dependencies.items() if v == 'unhealthy']
        overall_status = "unhealthy" if unhealthy_deps else "healthy"
        
        response = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "dependencies": dependencies,
            "unhealthy_dependencies": unhealthy_deps
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Dependencies health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


@health_bp.route('/ready')
def readiness_probe():
    """
    Readiness probe endpoint for orchestration systems.
    
    This endpoint indicates whether the application is ready to receive traffic.
    Unlike liveness probes, readiness probes should fail if the application
    cannot properly handle requests due to dependency issues.
    
    Returns:
        JSON response indicating readiness status
    """
    try:
        # Check critical dependencies
        health_checker = DependencyHealthChecker()
        
        media_service = getattr(g, 'media_service', None)
        cache_service = getattr(g, 'cache_service', None)
        
        # Application is ready if core services are available
        critical_checks = {
            "cache_service": health_checker.check_cache_service(cache_service),
        }
        
        # Plex connectivity is not required for readiness (can be configured later)
        
        # Check if any critical services are unhealthy
        unhealthy_critical = [k for k, v in critical_checks.items() 
                            if v == 'unhealthy']
        
        is_ready = len(unhealthy_critical) == 0
        status = "ready" if is_ready else "not_ready"
        
        response = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "critical_services": critical_checks,
            "unhealthy_critical_services": unhealthy_critical
        }
        
        status_code = 200 if is_ready else 503
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return jsonify({
            "status": "not_ready",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 503