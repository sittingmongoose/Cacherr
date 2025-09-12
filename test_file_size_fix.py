#!/usr/bin/env python3
"""
Test script to verify the file size fix works in development mode.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, '/workspace/src')

def test_file_operations():
    """Test the FileOperations class with the fix."""
    try:
        from config.settings import Config
        from core.file_operations import FileOperations
        from core.interfaces import TestModeAnalysis
        
        print("✅ Imports successful")
        
        # Load configuration
        config = Config()
        print("✅ Configuration loaded")
        
        # Initialize FileOperations
        file_ops = FileOperations(config)
        print(f"✅ FileOperations initialized (development mode: {file_ops.is_development_mode})")
        
        # Test with some mock file paths (that don't exist)
        test_files = [
            "/mediasource/Movies/Test Movie (2023)/Test Movie (2023).mkv",
            "/mediasource/TV Shows/Test Show/Season 01/Test Show S01E01.mkv",
            "/mediasource/Movies/Another Movie/Another Movie.mp4"
        ]
        
        print(f"\nTesting with {len(test_files)} mock files...")
        
        # Test analyze_files_for_test_mode
        analysis = file_ops.analyze_files_for_test_mode(test_files, "cache")
        
        print(f"\nResults:")
        print(f"  Files processed: {analysis.file_count}")
        print(f"  Total size: {analysis.total_size_readable}")
        print(f"  Operation type: {analysis.operation_type}")
        
        if analysis.file_details:
            print(f"\nFile details:")
            for i, detail in enumerate(analysis.file_details[:3]):  # Show first 3
                print(f"  {i+1}. {detail.filename}")
                print(f"     Path: {detail.path}")
                print(f"     Size: {detail.size_readable}")
                print(f"     Directory: {detail.directory}")
        else:
            print("  No file details available")
        
        # Check if the fix worked
        if analysis.file_count > 0:
            print(f"\n✅ SUCCESS: File analysis is working!")
            print(f"   - Found {analysis.file_count} files")
            print(f"   - Development mode handling is working")
            return True
        else:
            print(f"\n❌ FAILED: No files were processed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("=== Testing File Size Fix ===")
    
    success = test_file_operations()
    
    if success:
        print("\n🎉 The file size fix is working correctly!")
        print("   Test runs should now show files even in development mode.")
    else:
        print("\n💥 The file size fix needs more work.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())