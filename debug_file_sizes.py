#!/usr/bin/env python3
"""
Debug script to identify file size retrieval issues in test mode.

This script helps diagnose why file sizes are not showing in test runs
by checking file permissions, path accessibility, and testing the
analyze_files_for_test_mode function.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, '/workspace/src')

try:
    from config.settings import Config
    from core.file_operations import FileOperations
    from core.interfaces import TestModeAnalysis
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the workspace root")
    sys.exit(1)

def setup_logging():
    """Setup logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_directory_permissions(path: str, logger: logging.Logger) -> Dict[str, Any]:
    """Check directory permissions and accessibility."""
    result = {
        'path': path,
        'exists': False,
        'readable': False,
        'writable': False,
        'permissions': None,
        'owner': None,
        'group': None,
        'error': None
    }
    
    try:
        path_obj = Path(path)
        result['exists'] = path_obj.exists()
        
        if result['exists']:
            stat_info = path_obj.stat()
            result['permissions'] = oct(stat_info.st_mode)[-3:]
            result['owner'] = stat_info.st_uid
            result['group'] = stat_info.st_gid
            
            # Check readability
            try:
                list(path_obj.iterdir())
                result['readable'] = True
            except PermissionError:
                result['readable'] = False
                result['error'] = "Permission denied - cannot read directory"
            
            # Check writability
            try:
                test_file = path_obj / '.test_write'
                test_file.touch()
                test_file.unlink()
                result['writable'] = True
            except PermissionError:
                result['writable'] = False
                if not result['error']:
                    result['error'] = "Permission denied - cannot write to directory"
        else:
            result['error'] = "Directory does not exist"
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def check_file_permissions(file_path: str, logger: logging.Logger) -> Dict[str, Any]:
    """Check individual file permissions and size retrieval."""
    result = {
        'path': file_path,
        'exists': False,
        'readable': False,
        'size_bytes': 0,
        'size_readable': '0B',
        'permissions': None,
        'owner': None,
        'group': None,
        'error': None
    }
    
    try:
        path_obj = Path(file_path)
        result['exists'] = path_obj.exists()
        
        if result['exists']:
            stat_info = path_obj.stat()
            result['permissions'] = oct(stat_info.st_mode)[-3:]
            result['owner'] = stat_info.st_uid
            result['group'] = stat_info.st_gid
            
            # Try to get file size
            try:
                result['size_bytes'] = stat_info.st_size
                result['size_readable'] = format_file_size(result['size_bytes'])
                result['readable'] = True
            except (OSError, PermissionError) as e:
                result['error'] = f"Cannot read file size: {e}"
        else:
            result['error'] = "File does not exist"
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

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

def test_analyze_files_for_test_mode(file_operations: FileOperations, test_files: List[str], logger: logging.Logger):
    """Test the analyze_files_for_test_mode function."""
    logger.info("Testing analyze_files_for_test_mode function...")
    
    try:
        analysis = file_operations.analyze_files_for_test_mode(test_files, "cache")
        
        logger.info(f"Analysis results:")
        logger.info(f"  Files processed: {analysis.file_count}")
        logger.info(f"  Total size: {analysis.total_size_readable}")
        logger.info(f"  Operation type: {analysis.operation_type}")
        
        if analysis.file_details:
            logger.info("  File details:")
            for detail in analysis.file_details[:5]:  # Show first 5
                logger.info(f"    {detail.filename}: {detail.size_readable}")
        else:
            logger.warning("  No file details available - this indicates permission issues")
            
        return analysis
        
    except Exception as e:
        logger.error(f"Error in analyze_files_for_test_mode: {e}")
        return None

def create_test_files(test_dir: str, logger: logging.Logger) -> List[str]:
    """Create test files for testing."""
    test_files = []
    
    try:
        test_path = Path(test_dir)
        test_path.mkdir(exist_ok=True)
        
        # Create some test files with different sizes
        test_files_data = [
            ("test1.mkv", 1024 * 1024),  # 1MB
            ("test2.mp4", 5 * 1024 * 1024),  # 5MB
            ("test3.avi", 10 * 1024 * 1024),  # 10MB
        ]
        
        for filename, size in test_files_data:
            file_path = test_path / filename
            with open(file_path, 'wb') as f:
                f.write(b'0' * size)
            test_files.append(str(file_path))
            logger.info(f"Created test file: {file_path} ({format_file_size(size)})")
            
    except Exception as e:
        logger.error(f"Error creating test files: {e}")
    
    return test_files

def main():
    """Main diagnostic function."""
    logger = setup_logging()
    logger.info("Starting file size diagnostic...")
    
    # Load configuration
    try:
        config = Config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Check configured paths
    paths_to_check = [
        config.paths.plex_source,
        config.paths.real_source,
        config.paths.cache_destination,
    ]
    
    if config.paths.additional_sources:
        paths_to_check.extend(config.paths.additional_sources)
    
    logger.info("Checking configured paths...")
    for path in paths_to_check:
        if path:
            result = check_directory_permissions(path, logger)
            logger.info(f"Path: {path}")
            logger.info(f"  Exists: {result['exists']}")
            logger.info(f"  Readable: {result['readable']}")
            logger.info(f"  Writable: {result['writable']}")
            logger.info(f"  Permissions: {result['permissions']}")
            if result['error']:
                logger.warning(f"  Error: {result['error']}")
    
    # Create test files in a writable location
    test_dir = "/tmp/cacherr_test"
    logger.info(f"Creating test files in {test_dir}...")
    test_files = create_test_files(test_dir, logger)
    
    if not test_files:
        logger.error("No test files created, cannot proceed with testing")
        return 1
    
    # Test file operations
    try:
        file_operations = FileOperations(config)
        logger.info("FileOperations initialized successfully")
        
        # Test analyze_files_for_test_mode
        analysis = test_analyze_files_for_test_mode(file_operations, test_files, logger)
        
        if analysis and analysis.file_count > 0:
            logger.info("✅ File size analysis is working correctly")
        else:
            logger.error("❌ File size analysis is not working - no files processed")
            
    except Exception as e:
        logger.error(f"Error testing file operations: {e}")
        return 1
    
    # Check individual test files
    logger.info("Checking individual test files...")
    for test_file in test_files:
        result = check_file_permissions(test_file, logger)
        logger.info(f"File: {test_file}")
        logger.info(f"  Exists: {result['exists']}")
        logger.info(f"  Readable: {result['readable']}")
        logger.info(f"  Size: {result['size_readable']}")
        logger.info(f"  Permissions: {result['permissions']}")
        if result['error']:
            logger.warning(f"  Error: {result['error']}")
    
    # Cleanup test files
    try:
        import shutil
        shutil.rmtree(test_dir)
        logger.info(f"Cleaned up test directory: {test_dir}")
    except Exception as e:
        logger.warning(f"Could not clean up test directory: {e}")
    
    logger.info("Diagnostic complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())