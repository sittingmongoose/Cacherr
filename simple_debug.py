#!/usr/bin/env python3
"""
Simple diagnostic script to check file permissions and paths.
"""

import os
import sys
from pathlib import Path

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_float = float(size_bytes)
    while size_float >= 1024 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1
    
    return f"{size_float:.1f}{size_names[i]}"

def check_path(path: str):
    """Check if a path exists and is accessible."""
    print(f"\nChecking path: {path}")
    
    try:
        path_obj = Path(path)
        exists = path_obj.exists()
        print(f"  Exists: {exists}")
        
        if exists:
            try:
                stat_info = path_obj.stat()
                print(f"  Permissions: {oct(stat_info.st_mode)[-3:]}")
                print(f"  Owner: {stat_info.st_uid}")
                print(f"  Group: {stat_info.st_gid}")
                
                if path_obj.is_file():
                    print(f"  Size: {format_file_size(stat_info.st_size)}")
                elif path_obj.is_dir():
                    try:
                        files = list(path_obj.iterdir())
                        print(f"  Directory contents: {len(files)} items")
                        # Show first few files
                        for i, item in enumerate(files[:3]):
                            if item.is_file():
                                try:
                                    size = item.stat().st_size
                                    print(f"    {item.name}: {format_file_size(size)}")
                                except PermissionError:
                                    print(f"    {item.name}: Permission denied")
                            else:
                                print(f"    {item.name}: [directory]")
                    except PermissionError:
                        print("  Cannot read directory contents: Permission denied")
                        
            except PermissionError:
                print("  Permission denied")
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print("  Path does not exist")
            
    except Exception as e:
        print(f"  Error: {e}")

def create_test_files():
    """Create test files to verify file size functionality."""
    test_dir = Path("/tmp/cacherr_test")
    print(f"\nCreating test files in {test_dir}...")
    
    try:
        test_dir.mkdir(exist_ok=True)
        
        # Create test files
        test_files = [
            ("test1.mkv", 1024 * 1024),  # 1MB
            ("test2.mp4", 5 * 1024 * 1024),  # 5MB
        ]
        
        created_files = []
        for filename, size in test_files:
            file_path = test_dir / filename
            with open(file_path, 'wb') as f:
                f.write(b'0' * size)
            created_files.append(str(file_path))
            print(f"  Created: {filename} ({format_file_size(size)})")
        
        return created_files
        
    except Exception as e:
        print(f"  Error creating test files: {e}")
        return []

def test_file_size_retrieval(files):
    """Test file size retrieval like the analyze_files_for_test_mode function."""
    print(f"\nTesting file size retrieval for {len(files)} files...")
    
    total_size = 0
    successful_files = 0
    
    for file_path in files:
        try:
            path_obj = Path(file_path)
            if path_obj.exists():
                stat_info = path_obj.stat()
                file_size = stat_info.st_size
                total_size += file_size
                successful_files += 1
                print(f"  ✅ {path_obj.name}: {format_file_size(file_size)}")
            else:
                print(f"  ❌ {file_path}: File does not exist")
        except (OSError, PermissionError) as e:
            print(f"  ❌ {file_path}: {e}")
    
    print(f"\nResults:")
    print(f"  Files processed: {successful_files}/{len(files)}")
    print(f"  Total size: {format_file_size(total_size)}")
    
    return successful_files > 0

def main():
    """Main diagnostic function."""
    print("=== Cacherr File Size Diagnostic ===")
    
    # Check common paths that might be configured
    paths_to_check = [
        "/mediasource",
        "/plexsource", 
        "/cache",
        "/config",
        "/media",
        "/mnt/user",
        "/mnt/user0",
    ]
    
    print("\n1. Checking configured paths...")
    for path in paths_to_check:
        check_path(path)
    
    # Create and test with local files
    print("\n2. Testing file size functionality...")
    test_files = create_test_files()
    
    if test_files:
        success = test_file_size_retrieval(test_files)
        
        if success:
            print("\n✅ File size retrieval is working correctly")
        else:
            print("\n❌ File size retrieval is not working")
        
        # Cleanup
        try:
            import shutil
            shutil.rmtree("/tmp/cacherr_test")
            print("\nCleaned up test files")
        except Exception as e:
            print(f"\nCould not clean up test files: {e}")
    else:
        print("\n❌ Could not create test files")
    
    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    main()