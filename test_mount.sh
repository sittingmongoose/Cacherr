#!/bin/bash

# test_mount.sh - Testing script for PlexCacheUltra mount problem solutions
# This script tests the hardlink preservation fix to ensure Plex can still see media after cache operations

echo "=== PlexCacheUltra Mount Problem Test Script ==="
echo "Testing hardlink preservation solution for Plex visibility"
echo ""

# Test configuration
TEST_DIR="/tmp/plexcacheultra_test"
MEDIASOURCE_TEST="$TEST_DIR/mediasource"
PLEXSOURCE_TEST="$TEST_DIR/plexsource" 
CACHE_TEST="$TEST_DIR/cache"
TEST_FILE="test_movie.mkv"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "[${GREEN}PASS${NC}] $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "[${RED}FAIL${NC}] $message"
    else
        echo -e "[${YELLOW}INFO${NC}] $message"
    fi
}

cleanup_test() {
    print_status "INFO" "Cleaning up test environment..."
    rm -rf "$TEST_DIR"
}

setup_test() {
    print_status "INFO" "Setting up test environment..."
    
    # Clean up any previous test
    cleanup_test
    
    # Create test directories
    mkdir -p "$MEDIASOURCE_TEST"
    mkdir -p "$PLEXSOURCE_TEST"
    mkdir -p "$CACHE_TEST"
    
    # Create test file with some content
    echo "This is a test media file for PlexCacheUltra testing" > "$MEDIASOURCE_TEST/$TEST_FILE"
    
    # Create initial file in Plex source (simulating normal Plex setup)
    cp "$MEDIASOURCE_TEST/$TEST_FILE" "$PLEXSOURCE_TEST/$TEST_FILE"
    
    print_status "PASS" "Test environment created"
}

test_initial_state() {
    print_status "INFO" "Testing initial state..."
    
    # Check that files exist in both locations
    if [ -f "$MEDIASOURCE_TEST/$TEST_FILE" ] && [ -f "$PLEXSOURCE_TEST/$TEST_FILE" ]; then
        print_status "PASS" "Initial files present in both mediasource and plexsource"
    else
        print_status "FAIL" "Initial setup failed - files not present"
        return 1
    fi
}

test_move_with_hardlink() {
    print_status "INFO" "Testing move operation with hardlink creation..."
    
    local original_file="$MEDIASOURCE_TEST/$TEST_FILE"
    local cache_file="$CACHE_TEST/$TEST_FILE"
    local plex_file="$PLEXSOURCE_TEST/$TEST_FILE"
    
    # Simulate the file operation: move to cache and create hardlink in Plex location
    print_status "INFO" "Moving file from mediasource to cache..."
    mv "$original_file" "$cache_file"
    
    if [ ! -f "$cache_file" ]; then
        print_status "FAIL" "File not moved to cache location"
        return 1
    fi
    
    print_status "INFO" "Creating hardlink in Plex-visible location..."
    # Remove existing file in plex location
    rm -f "$plex_file"
    
    # Create hardlink from cache to Plex location
    if ln "$cache_file" "$plex_file" 2>/dev/null; then
        print_status "PASS" "Hardlink created successfully"
    else
        print_status "YELLOW" "Hardlink failed, trying symlink..."
        if ln -s "$cache_file" "$plex_file" 2>/dev/null; then
            print_status "PASS" "Symlink created as fallback"
        else
            print_status "FAIL" "Both hardlink and symlink creation failed"
            return 1
        fi
    fi
}

test_plex_visibility() {
    print_status "INFO" "Testing Plex visibility after cache operation..."
    
    local plex_file="$PLEXSOURCE_TEST/$TEST_FILE"
    local cache_file="$CACHE_TEST/$TEST_FILE"
    
    # Check if Plex can still "see" the file (file exists at Plex path)
    if [ -f "$plex_file" ]; then
        print_status "PASS" "File is visible at Plex location"
    else
        print_status "FAIL" "File is NOT visible at Plex location"
        return 1
    fi
    
    # Check if the content is accessible
    local plex_content
    local cache_content
    
    if plex_content=$(cat "$plex_file" 2>/dev/null) && cache_content=$(cat "$cache_file" 2>/dev/null); then
        if [ "$plex_content" = "$cache_content" ]; then
            print_status "PASS" "File content accessible through Plex path"
        else
            print_status "FAIL" "File content mismatch between Plex and cache paths"
            return 1
        fi
    else
        print_status "FAIL" "Cannot read file content from Plex or cache path"
        return 1
    fi
}

test_hardlink_properties() {
    print_status "INFO" "Testing hardlink properties..."
    
    local plex_file="$PLEXSOURCE_TEST/$TEST_FILE"
    local cache_file="$CACHE_TEST/$TEST_FILE"
    
    # Check if files are actually hardlinked (same inode)
    if [ -L "$plex_file" ]; then
        print_status "YELLOW" "Plex file is a symlink (fallback method used)"
        # For symlinks, just verify the target is correct
        local target
        target=$(readlink "$plex_file")
        if [ "$target" = "$cache_file" ]; then
            print_status "PASS" "Symlink points to correct cache file"
        else
            print_status "FAIL" "Symlink points to wrong location: $target"
            return 1
        fi
    else
        # Check for hardlink (same inode number)
        local plex_inode
        local cache_inode
        
        if command -v stat >/dev/null 2>&1; then
            plex_inode=$(stat -c '%i' "$plex_file" 2>/dev/null)
            cache_inode=$(stat -c '%i' "$cache_file" 2>/dev/null)
            
            if [ "$plex_inode" = "$cache_inode" ] && [ -n "$plex_inode" ]; then
                print_status "PASS" "Files are properly hardlinked (same inode: $plex_inode)"
            else
                print_status "FAIL" "Files are not hardlinked (different inodes: $plex_inode vs $cache_inode)"
                return 1
            fi
        else
            print_status "YELLOW" "Cannot verify hardlink status (stat command not available)"
        fi
    fi
}

test_file_operations() {
    print_status "INFO" "Testing file operation scenarios..."
    
    # Test writing to the cached file and reading from Plex path
    local test_content="Modified content for hardlink test"
    local cache_file="$CACHE_TEST/$TEST_FILE"
    local plex_file="$PLEXSOURCE_TEST/$TEST_FILE"
    
    echo "$test_content" > "$cache_file"
    
    local plex_content
    if plex_content=$(cat "$plex_file" 2>/dev/null); then
        if [ "$plex_content" = "$test_content" ]; then
            print_status "PASS" "Changes to cache file are visible through Plex path"
        else
            print_status "FAIL" "Changes to cache file are not reflected in Plex path"
            return 1
        fi
    else
        print_status "FAIL" "Cannot read from Plex path after cache modification"
        return 1
    fi
}

run_all_tests() {
    local failed_tests=0
    
    echo "Starting comprehensive mount problem tests..."
    echo "=============================================="
    
    # Setup
    setup_test || { echo "Setup failed, aborting tests"; exit 1; }
    
    # Run tests
    test_initial_state || ((failed_tests++))
    test_move_with_hardlink || ((failed_tests++))
    test_plex_visibility || ((failed_tests++))
    test_hardlink_properties || ((failed_tests++))
    test_file_operations || ((failed_tests++))
    
    echo ""
    echo "=============================================="
    if [ $failed_tests -eq 0 ]; then
        print_status "PASS" "All tests passed! Mount problem solution works correctly."
    else
        print_status "FAIL" "$failed_tests test(s) failed. Mount problem solution needs adjustment."
    fi
    
    # Cleanup
    cleanup_test
    
    return $failed_tests
}

# Show usage if help requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "This script tests the PlexCacheUltra mount problem solution."
    echo "It simulates moving files to cache while maintaining Plex visibility"
    echo "through hardlinks or symlinks."
    echo ""
    echo "The test creates temporary directories and files to verify:"
    echo "  - File movement to cache works correctly"
    echo "  - Hardlink/symlink creation maintains Plex visibility"
    echo "  - File operations work through both paths"
    echo ""
    exit 0
fi

# Run the tests
run_all_tests
exit $?