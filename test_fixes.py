#!/usr/bin/env python3
"""
Test script to verify the fixes made for database initialization and error handling.
"""
import tempfile
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_database_initialization():
    """Test CachedFilesService database initialization with fallback paths."""
    print("=== Testing Database Initialization ===")
    
    try:
        from src.core.cached_files_service import CachedFilesService
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test 1: Bad path should fail
            bad_path = '/nonexistent/path/db.sqlite'
            try:
                service1 = CachedFilesService(bad_path)
                print("✗ ERROR: Should have failed with bad path")
                return False
            except Exception as e:
                print(f"✓ Expected failure with bad path: {type(e).__name__}")
            
            # Test 2: Good path should succeed
            good_path = f'{temp_dir}/test.db'
            try:
                service2 = CachedFilesService(good_path)
                print("✓ SUCCESS: Database created at good path")
                
                # Test basic operations
                stats = service2.get_cache_statistics()
                print(f"✓ Cache statistics retrieved: {stats.total_files} files")
                
            except Exception as e:
                print(f"✗ Unexpected error with good path: {e}")
                return False
        
        print("✓ Database initialization test passed")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import CachedFilesService: {e}")
        return False

def test_application_import():
    """Test that the application can be imported successfully."""
    print("=== Testing Application Import ===")
    
    try:
        from src.application import create_application, ApplicationContext, ApplicationConfig
        from src.config.settings import Config
        print("✓ Application modules imported successfully")
        
        # Test that we can create a Config instance
        config = Config()
        print("✓ Config instance created successfully")
        
        # Test that we can create ApplicationConfig
        app_config = ApplicationConfig()
        print("✓ ApplicationConfig instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Application import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pydantic_models():
    """Test that Pydantic models are working correctly."""
    print("=== Testing Pydantic Models ===")
    
    try:
        from src.config.pydantic_models import MediaConfig, LoggingConfig, PlexConfig
        
        # Test MediaConfig
        media_config = MediaConfig(days_to_monitor=50, number_episodes=10)
        print(f"✓ MediaConfig created: copy_to_cache={media_config.copy_to_cache}")
        
        # Test LoggingConfig
        log_config = LoggingConfig(level="DEBUG", max_files=10)
        print(f"✓ LoggingConfig created: level={log_config.level}")
        
        # Test PlexConfig
        plex_config = PlexConfig(url="http://localhost:32400", token="test-token")
        print(f"✓ PlexConfig created: url={plex_config.url}")
        
        return True
        
    except Exception as e:
        print(f"✗ Pydantic models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Starting PlexCacheUltra fixes verification...")
    print()
    
    tests = [
        test_application_import,
        test_pydantic_models,
        test_database_initialization,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("=== Test Summary ===")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The fixes appear to be working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)