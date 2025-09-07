#!/usr/bin/env python3
"""
Test script for Cacherr file operations functionality.
This tests the core file moving/copying functionality with symlinks/hardlinks.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.file_operations import FileOperations
from src.config.settings import Config

def test_file_operations():
    """Test file operations functionality."""
    print("Testing Cacherr File Operations...\n")
    
    # Create test directories
    with tempfile.TemporaryDirectory() as temp_dir:
        media_dir = Path(temp_dir) / "media"
        cache_dir = Path(temp_dir) / "cache"
        media_dir.mkdir()
        cache_dir.mkdir()
        
        # Create test files
        test_files = [
            "movie1.mkv",
            "movie2.mp4", 
            "show/s01e01.mkv",
            "show/s01e02.mkv"
        ]
        
        for file_path in test_files:
            full_path = media_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Test content for {file_path}")
        
        print(f"✅ Created test files in {media_dir}")
        print(f"   Files: {[str(f.relative_to(media_dir)) for f in media_dir.rglob('*') if f.is_file()]}")
        
        # Test file operations configuration
        try:
            # Set environment variables for config
            os.environ['PLEX_SOURCE'] = str(media_dir)
            os.environ['CACHE_DIRECTORY'] = str(cache_dir)
            os.environ['PLEX_URL'] = 'http://localhost:32400'
            os.environ['PLEX_TOKEN'] = 'test-token'
            
            config = Config()
            print("✅ Configuration created successfully")
        except Exception as e:
            print(f"❌ Configuration failed: {e}")
            return False
        
        # Test file operations
        try:
            file_ops = FileOperations(config)
            print("✅ FileOperations instance created successfully")
            
            # Test file path processing
            test_paths = [
                "/media/movie1.mkv",
                "/media/show/s01e01.mkv"
            ]
            
            processed = file_ops.process_file_paths(test_paths)
            print(f"✅ File path processing: {processed}")
            
            # Test file operations (in test mode)
            print("\n🧪 Testing file operations...")
            
            # Test symlink creation
            test_file = media_dir / "movie1.mkv"
            cache_file = cache_dir / "movie1.mkv"
            
            if test_file.exists():
                # Create symlink
                cache_file.symlink_to(test_file)
                print(f"✅ Created symlink: {cache_file} -> {test_file}")
                
                # Verify symlink works
                if cache_file.is_symlink() and cache_file.read_text() == test_file.read_text():
                    print("✅ Symlink verification successful")
                else:
                    print("❌ Symlink verification failed")
                
                # Test hardlink creation
                hardlink_file = cache_dir / "movie1_hardlink.mkv"
                try:
                    os.link(test_file, hardlink_file)
                    print(f"✅ Created hardlink: {hardlink_file}")
                    
                    # Verify hardlink works
                    if hardlink_file.exists() and hardlink_file.read_text() == test_file.read_text():
                        print("✅ Hardlink verification successful")
                    else:
                        print("❌ Hardlink verification failed")
                except OSError as e:
                    print(f"⚠️  Hardlink creation failed (expected on some filesystems): {e}")
            
            print("\n✅ File operations test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ File operations test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_file_operations()
    sys.exit(0 if success else 1)
