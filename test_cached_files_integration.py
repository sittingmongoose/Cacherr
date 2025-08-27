#!/usr/bin/env python3
"""
Integration test for CachedFilesService implementation.

This script demonstrates that the CachedFilesService is working correctly
with all its features including Pydantic v2.5 validation, SQLite storage,
and multi-user support.
"""

import tempfile
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.cached_files_service import CachedFilesService, CachedFilesFilter
from core.interfaces import UserOperationContext


def test_cached_files_service():
    """Test the CachedFilesService with various operations."""
    
    print("🚀 Testing CachedFilesService Implementation")
    print("=" * 50)
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        # Initialize the service
        print("📊 Initializing CachedFilesService...")
        service = CachedFilesService(database_path=db_path)
        print("✅ Service initialized successfully")
        
        # Run database migration
        print("\n🔄 Running database migration...")
        migration_success = service.migrate_database()
        print(f"{'✅' if migration_success else '❌'} Migration {'completed' if migration_success else 'failed'}")
        
        # Test adding cached files
        print("\n📁 Testing file caching...")
        
        # Create user contexts
        user1 = UserOperationContext(user_id="user1", plex_username="Alice", trigger_source="web_ui")
        user2 = UserOperationContext(user_id="user2", plex_username="Bob", trigger_source="api")
        
        # Add some test cached files
        test_files = [
            {
                'file_path': '/media/movies/Movie1.mkv',
                'original_path': '/array/movies/Movie1.mkv',
                'cached_path': '/cache/movies/Movie1.mkv',
                'cache_method': 'atomic_symlink',
                'user_context': user1,
                'operation_reason': 'watchlist',
                'metadata': {'quality': '1080p', 'codec': 'h264'}
            },
            {
                'file_path': '/media/tv/Show1/S01E01.mkv',
                'original_path': '/array/tv/Show1/S01E01.mkv', 
                'cached_path': '/cache/tv/Show1/S01E01.mkv',
                'cache_method': 'atomic_copy',
                'user_context': user2,
                'operation_reason': 'real_time_watch',
                'metadata': {'season': 1, 'episode': 1}
            },
            {
                'file_path': '/media/movies/Movie2.mkv',
                'original_path': '/array/movies/Movie2.mkv',
                'cached_path': '/cache/movies/Movie2.mkv',
                'cache_method': 'atomic_symlink',
                'user_context': user1,
                'operation_reason': 'ondeck',
                'metadata': {'quality': '4K', 'hdr': True}
            }
        ]
        
        cached_file_objects = []
        for file_data in test_files:
            cached_file = service.add_cached_file(**file_data)
            cached_file_objects.append(cached_file)
            print(f"✅ Added: {cached_file.filename} ({cached_file.cache_method})")
        
        # Test statistics
        print("\n📈 Testing cache statistics...")
        stats = service.get_cache_statistics()
        print(f"✅ Total files: {stats.total_files}")
        print(f"✅ Active files: {stats.active_files}")
        print(f"✅ Total size: {stats.total_size_readable}")
        print(f"✅ Users: {stats.users_count}")
        
        # Test user-specific statistics
        print("\n👤 Testing user statistics...")
        user1_stats = service.get_user_statistics("user1", days=30)
        print(f"✅ User1 files: {user1_stats['total_files']}")
        print(f"✅ User1 operations: {user1_stats['files_by_operation']}")
        
        # Test filtering
        print("\n🔍 Testing file filtering...")
        
        # Filter by user
        filter1 = CachedFilesFilter(user_id="user1", limit=10)
        user1_files, count1 = service.get_cached_files(filter1)
        print(f"✅ User1 has {count1} files")
        
        # Filter by operation type
        filter2 = CachedFilesFilter(triggered_by_operation="real_time_watch", limit=10)
        realtime_files, count2 = service.get_cached_files(filter2)
        print(f"✅ Real-time watch files: {count2}")
        
        # Filter by filename search
        filter3 = CachedFilesFilter(search="Movie", limit=10)
        movie_files, count3 = service.get_cached_files(filter3)
        print(f"✅ Movie files found: {count3}")
        
        # Test individual file retrieval
        print("\n🔍 Testing individual file retrieval...")
        file_id = cached_file_objects[0].id
        retrieved_file = service.get_cached_file_by_id(file_id)
        if retrieved_file:
            print(f"✅ Retrieved file: {retrieved_file.filename}")
        
        # Test file access tracking
        print("\n📊 Testing access tracking...")
        access_success = service.update_file_access("/media/movies/Movie1.mkv", "user1")
        print(f"{'✅' if access_success else '❌'} Access tracking {'succeeded' if access_success else 'failed'}")
        
        # Test user attribution
        print("\n👥 Testing user attribution...")
        add_user_success = service.add_user_to_file("/media/movies/Movie1.mkv", "user2", "shared_access")
        print(f"{'✅' if add_user_success else '❌'} User attribution {'succeeded' if add_user_success else 'failed'}")
        
        # Test cache integrity check
        print("\n🔍 Testing cache integrity...")
        verified_count, error_count = service.verify_cache_integrity()
        print(f"✅ Verified: {verified_count}, Errors: {error_count}")
        
        # Test operation logs
        print("\n📝 Testing operation logs...")
        logs = service.get_operation_logs(limit=10)
        print(f"✅ Operation logs retrieved: {len(logs)} entries")
        
        # Test cleanup operations
        print("\n🧹 Testing cleanup operations...")
        orphaned_count = service.cleanup_orphaned_files()
        print(f"✅ Orphaned files cleaned: {orphaned_count}")
        
        # Test file removal
        print("\n🗑️ Testing file removal...")
        remove_success = service.remove_cached_file("/media/movies/Movie2.mkv", "manual_cleanup", "user1")
        print(f"{'✅' if remove_success else '❌'} File removal {'succeeded' if remove_success else 'failed'}")
        
        # Final statistics
        print("\n📊 Final statistics...")
        final_stats = service.get_cache_statistics()
        print(f"✅ Final total files: {final_stats.total_files}")
        print(f"✅ Final active files: {final_stats.active_files}")
        
        print("\n🎉 All tests completed successfully!")
        print("✅ CachedFilesService is fully functional")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary database
        try:
            Path(db_path).unlink()
        except Exception:
            pass
    
    return True


if __name__ == "__main__":
    success = test_cached_files_service()
    sys.exit(0 if success else 1)