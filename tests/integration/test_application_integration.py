"""
Integration tests for application context and service bootstrapping.

This module tests the complete application lifecycle including
dependency injection, service registration, and component integration.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from src.application import (
    ApplicationContext, ApplicationConfig, create_application,
    create_test_application, create_development_application
)
from src.config.settings import Config
from src.core.container import DIContainer
from src.core.interfaces import MediaService, FileService, CacheService
from src.core.plex_cache_engine import CacherrEngine


@pytest.mark.integration
class TestApplicationBootstrap:
    """Test application bootstrap and service wiring."""
    
    def test_create_test_application(self):
        """Test creating application with test configuration."""
        app_context = create_test_application()
        
        assert app_context is not None
        assert isinstance(app_context, ApplicationContext)
        assert app_context.app_config.web['testing'] is True
        assert app_context.app_config.enable_scheduler is False
        assert not app_context.is_started
    
    def test_create_development_application(self):
        """Test creating application with development configuration."""
        app_context = create_development_application()
        
        assert app_context is not None
        assert app_context.app_config.web['debug'] is True
        assert app_context.app_config.log_level == 'DEBUG'
        assert app_context.app_config.auto_start_scheduler is False
    
    def test_application_startup_success(self, mock_config: Config):
        """Test successful application startup."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            enable_scheduler=False,
            initialize_services_on_startup=False,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        # Mock successful validation
        with patch.object(mock_config, 'validate', return_value=True):
            success = app_context.start()
        
        assert success is True
        assert app_context.is_started
        assert app_context.container is not None
        assert app_context.web_app is not None
        assert app_context.startup_time is not None
        
        # Cleanup
        app_context.shutdown()
    
    def test_application_startup_with_config_validation_failure(self, mock_config: Config):
        """Test application startup with configuration validation failure."""
        app_config = ApplicationConfig(
            validate_config_on_startup=True,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        # Mock validation failure
        with patch.object(mock_config, 'validate', return_value=False):
            with pytest.raises(Exception):  # ApplicationStartupError
                app_context.start()
        
        assert not app_context.is_started
        assert len(app_context.startup_errors) > 0
    
    def test_application_startup_partial_failure(self, mock_config: Config):
        """Test application startup with partial service initialization failure."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            enable_cache_engine=True,
            initialize_services_on_startup=True,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        # Mock config validation success but service initialization failure
        with patch.object(mock_config, 'validate', return_value=True), \
             patch('src.application.CacherrEngine') as mock_engine:
            
            # Make cache engine initialization fail
            mock_engine.side_effect = RuntimeError("Plex connection failed")
            
            # Should still start successfully (partial failure allowed)
            success = app_context.start()
            
            assert success is True
            assert app_context.is_started
            assert len(app_context.startup_errors) > 0
            assert "Cache engine initialization failed" in str(app_context.startup_errors)
        
        app_context.shutdown()
    
    def test_application_shutdown(self, mock_config: Config):
        """Test graceful application shutdown."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            enable_scheduler=False,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        assert app_context.is_started
        
        # Add shutdown callback to test callback execution
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        app_context.add_shutdown_callback(test_callback)
        
        # Shutdown
        success = app_context.shutdown()
        
        assert success is True
        assert not app_context.is_started
        assert callback_called
    
    def test_application_context_manager(self, mock_config: Config):
        """Test application context as context manager."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            enable_scheduler=False,
            setup_logging=False
        )
        
        with patch.object(mock_config, 'validate', return_value=True):
            with ApplicationContext(mock_config, app_config).application_scope() as app_context:
                assert app_context.is_started
                assert app_context.container is not None
        
        # Should be shutdown after context exit
        assert not app_context.is_started
    
    def test_get_application_status(self, mock_config: Config):
        """Test getting application status information."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            enable_scheduler=False,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        try:
            status = app_context.get_status()
            
            assert status['is_started'] is True
            assert status['startup_time'] is not None
            assert status['uptime_seconds'] is not None
            assert 'components' in status
            assert status['components']['container_initialized'] is True
            assert status['components']['web_app_created'] is True
            assert 'configuration' in status
            
        finally:
            app_context.shutdown()


@pytest.mark.integration
class TestServiceIntegration:
    """Test service integration through DI container."""
    
    def test_container_service_registration(self, mock_config: Config):
        """Test that services are properly registered in container."""
        app_config = ApplicationConfig(
            enable_cache_engine=True,
            initialize_services_on_startup=False,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        try:
            container = app_context.container
            assert container is not None
            
            # Check that config is registered
            assert container.is_registered(Config)
            resolved_config = container.resolve(Config)
            assert resolved_config is mock_config
            
        finally:
            app_context.shutdown()
    
    def test_service_resolution(self, mock_config: Config):
        """Test resolving services from application context."""
        app_config = ApplicationConfig(
            initialize_services_on_startup=False,
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        try:
            # Should be able to get services from context
            config_service = app_context.get_service(Config)
            assert config_service is mock_config
            
        finally:
            app_context.shutdown()
    
    def test_service_resolution_before_startup(self, mock_config: Config):
        """Test service resolution before application startup fails appropriately."""
        app_config = ApplicationConfig(setup_logging=False)
        app_context = ApplicationContext(mock_config, app_config)
        
        # Should raise error when trying to get service before startup
        with pytest.raises(ValueError):
            app_context.get_service(Config)
    
    @pytest.mark.slow
    def test_web_app_integration(self, mock_config: Config):
        """Test web application integration."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        try:
            web_app = app_context.get_web_app()
            assert web_app is not None
            
            # Test that Flask app context has access to application context
            with web_app.app_context():
                assert web_app.config['app_context'] is app_context
                
            # Test that web app is properly configured
            assert web_app.config['TESTING'] is True
            assert web_app.config['DEBUG'] is True
            
        finally:
            app_context.shutdown()


@pytest.mark.integration
class TestApplicationConfigIntegration:
    """Test application configuration integration."""
    
    def test_config_overrides(self):
        """Test application creation with configuration overrides."""
        overrides = {
            'web': {
                'debug': False,
                'port': 9000
            },
            'enable_scheduler': True,
            'log_level': 'WARNING'
        }
        
        app_context = create_application(config_overrides=overrides)
        
        assert app_context.app_config.web['debug'] is False
        assert app_context.app_config.web['port'] == 9000
        assert app_context.app_config.enable_scheduler is True
        assert app_context.app_config.log_level == 'WARNING'
    
    def test_invalid_config_overrides(self):
        """Test application creation with invalid configuration."""
        invalid_overrides = {
            'web': {
                'port': 'not_a_number'  # Invalid port type
            }
        }
        
        # Should raise validation error during ApplicationConfig creation
        with pytest.raises(Exception):  # Pydantic validation error
            create_application(config_overrides=invalid_overrides)
    
    def test_environment_specific_configs(self):
        """Test different environment-specific configurations."""
        # Test development config
        dev_app = create_development_application()
        assert dev_app.app_config.web['debug'] is True
        assert dev_app.app_config.log_level == 'DEBUG'
        
        # Test application factories produce different configs
        test_app = create_test_application()
        assert test_app.app_config.web['testing'] is True
        assert test_app.app_config.enable_scheduler is False


@pytest.mark.integration
class TestApplicationErrorHandling:
    """Test application error handling and recovery."""
    
    def test_startup_error_recovery(self, mock_config: Config):
        """Test application behavior after startup errors."""
        app_config = ApplicationConfig(
            setup_logging=False,
            validate_config_on_startup=True
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        # First startup attempt fails
        with patch.object(mock_config, 'validate', return_value=False):
            try:
                app_context.start()
                assert False, "Should have raised exception"
            except Exception:
                pass  # Expected
        
        assert not app_context.is_started
        assert len(app_context.startup_errors) > 0
        
        # Second startup attempt succeeds
        with patch.object(mock_config, 'validate', return_value=True):
            # Clear previous errors
            app_context.startup_errors.clear()
            success = app_context.start()
        
        assert success is True
        assert app_context.is_started
        
        app_context.shutdown()
    
    def test_shutdown_error_handling(self, mock_config: Config):
        """Test shutdown error handling."""
        app_config = ApplicationConfig(
            web={'testing': True, 'debug': True, 'port': 0},
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        # Add callback that will raise an error
        def failing_callback():
            raise RuntimeError("Callback failed")
        
        app_context.add_shutdown_callback(failing_callback)
        
        # Shutdown should still succeed despite callback failure
        success = app_context.shutdown()
        
        # Should return False due to callback error
        assert success is False
        assert not app_context.is_started  # But should still be shutdown
    
    def test_multiple_startup_calls(self, mock_config: Config):
        """Test multiple startup calls are handled gracefully."""
        app_config = ApplicationConfig(
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            # First startup
            success1 = app_context.start()
            assert success1 is True
            assert app_context.is_started
            
            # Second startup should return True but not restart
            success2 = app_context.start()
            assert success2 is True
            assert app_context.is_started
        
        app_context.shutdown()
    
    def test_multiple_shutdown_calls(self, mock_config: Config):
        """Test multiple shutdown calls are handled gracefully."""
        app_config = ApplicationConfig(
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        # First shutdown
        success1 = app_context.shutdown()
        assert success1 is True
        assert not app_context.is_started
        
        # Second shutdown should return True without errors
        success2 = app_context.shutdown()
        assert success2 is True
        assert not app_context.is_started


@pytest.mark.integration
@pytest.mark.slow
class TestResourceManagement:
    """Test resource management during application lifecycle."""
    
    def test_container_disposal_on_shutdown(self, mock_config: Config):
        """Test that DI container is properly disposed during shutdown."""
        app_config = ApplicationConfig(
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        container = app_context.container
        assert container is not None
        assert not container._disposed
        
        app_context.shutdown()
        
        # Container should be disposed after shutdown
        assert container._disposed
    
    def test_temporary_directory_cleanup(self):
        """Test temporary directory cleanup during application lifecycle."""
        # This test would verify that temporary directories created
        # during application lifecycle are properly cleaned up
        
        app_context = create_test_application()
        
        with patch('src.application.Path') as mock_path:
            mock_temp_dir = Mock()
            mock_path.return_value = mock_temp_dir
            mock_temp_dir.mkdir.return_value = None
            
            with patch.object(app_context.config, 'validate', return_value=True):
                app_context.start()
            
            # Verify directories were created
            assert mock_temp_dir.mkdir.called
            
            app_context.shutdown()
    
    def test_memory_cleanup_after_shutdown(self, mock_config: Config):
        """Test that major objects are cleaned up after shutdown."""
        app_config = ApplicationConfig(
            setup_logging=False
        )
        
        app_context = ApplicationContext(mock_config, app_config)
        
        with patch.object(mock_config, 'validate', return_value=True):
            app_context.start()
        
        # Store references to verify cleanup
        container_ref = app_context.container
        web_app_ref = app_context.web_app
        
        app_context.shutdown()
        
        # Major components should be cleaned up
        assert container_ref._disposed
        # Web app reference might still exist but application is shutdown
        assert not app_context.is_started