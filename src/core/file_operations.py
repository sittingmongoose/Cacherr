"""
Atomic File Operations for Cacherr.

Provides zero-interruption file caching operations that are invisible to Plex.
Uses atomic symlink replacement so Plex seamlessly switches between storage tiers.

The key operation sequence:
1. Copy file to SSD cache (original remains accessible during copy)
2. Create temp symlink pointing to cached copy
3. Atomically replace original with symlink (os.replace is POSIX atomic)
4. Plex seamlessly continues reading from fast storage
"""

import os
import shutil
import logging
import threading
import uuid
import time
from pathlib import Path
from typing import Optional, List, Set, Tuple, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum


logger = logging.getLogger(__name__)


# Extension used to mark array files that have been cached
PLEXCACHED_EXTENSION = ".plexcached"


class OperationType(str, Enum):
    """Types of file operations."""
    CACHE = "cache"  # Move to cache
    RESTORE = "restore"  # Move back to array
    COPY = "copy"  # Copy only (no symlink)


@dataclass
class OperationResult:
    """Result of a file operation."""
    success: bool
    source_path: str
    dest_path: str
    operation: OperationType
    bytes_transferred: int = 0
    duration_seconds: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'source_path': self.source_path,
            'dest_path': self.dest_path,
            'operation': self.operation.value,
            'bytes_transferred': self.bytes_transferred,
            'duration_seconds': round(self.duration_seconds, 2),
            'error': self.error,
        }


def format_bytes(size: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def get_media_identity(filepath: str) -> str:
    """Extract core media identity from filename, ignoring quality/codec info.
    
    Examples:
        "Wreck-It Ralph (2012) [WEBDL-1080p].mkv" -> "Wreck-It Ralph (2012)"
        "Show - S01E02 - Title [HDTV-1080p].mkv" -> "Show - S01E02 - Title"
    """
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    
    # Remove .plexcached extension if present
    if name.endswith('.plexcached'):
        name = name[:-len('.plexcached')]
        name = os.path.splitext(name)[0]
    
    # Remove quality/codec info in brackets
    if '[' in name:
        name = name[:name.index('[')].strip()
    
    # Clean up trailing dashes
    name = name.rstrip(' -').rstrip('-').strip()
    return name


class AtomicFileOperations:
    """
    Atomic file operations for invisible-to-Plex caching.
    
    Provides:
    - copy_to_cache: Copy file to cache, create atomic symlink
    - restore_to_array: Reverse the operation, restore original
    - Concurrent operations with configurable parallelism
    - Progress tracking and error handling
    """
    
    def __init__(self,
                 cache_path: str,
                 array_path: str,
                 max_concurrent_cache: int = 3,
                 max_concurrent_array: int = 1,
                 dry_run: bool = False):
        """
        Initialize file operations.
        
        Args:
            cache_path: Base path for cache storage
            array_path: Base path for array storage
            max_concurrent_cache: Concurrent cache operations
            max_concurrent_array: Concurrent array operations
            dry_run: Simulate without moving files
        """
        self.cache_path = Path(cache_path)
        self.array_path = Path(array_path)
        self.max_concurrent_cache = max_concurrent_cache
        self.max_concurrent_array = max_concurrent_array
        self.dry_run = dry_run
        
        self._lock = threading.RLock()
        self._active_operations: Dict[str, Future] = {}
        
        # Track symlink mappings for restoration
        self._symlink_registry: Dict[str, Dict[str, str]] = {}
        # Format: {original_path: {cached_path, backup_path}}
    
    def copy_to_cache_atomic(self, 
                             source_path: str,
                             preserve_structure: bool = True) -> OperationResult:
        """
        Copy file to cache and atomically replace original with symlink.
        
        This is the key operation for invisible-to-Plex caching:
        1. Copy file to cache (original stays accessible)
        2. Create temp symlink in same directory
        3. Atomically replace original with symlink
        4. Keep backup of original for restoration
        
        Args:
            source_path: Path to file on array
            preserve_structure: Maintain directory structure in cache
            
        Returns:
            OperationResult with success status and details
        """
        source = Path(source_path)
        start_time = time.time()
        
        try:
            # Validate source
            if not source.exists():
                return OperationResult(
                    success=False,
                    source_path=source_path,
                    dest_path="",
                    operation=OperationType.CACHE,
                    error=f"Source file not found: {source_path}"
                )
            
            # Check if already a symlink (already cached)
            if source.is_symlink():
                target = os.path.realpath(source_path)
                if self._is_in_cache(target):
                    logger.debug(f"Already cached (symlink): {source.name}")
                    return OperationResult(
                        success=True,
                        source_path=source_path,
                        dest_path=target,
                        operation=OperationType.CACHE,
                        error="Already cached"
                    )
            
            # Calculate cache destination
            cache_dest = self._get_cache_destination(source_path, preserve_structure)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would cache: {source.name} -> {cache_dest}")
                return OperationResult(
                    success=True,
                    source_path=source_path,
                    dest_path=str(cache_dest),
                    operation=OperationType.CACHE,
                    bytes_transferred=source.stat().st_size,
                )
            
            # Create cache directory
            cache_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Copy to cache (if not already there)
            if not cache_dest.exists():
                logger.info(f"Copying to cache: {source.name}")
                shutil.copy2(source_path, cache_dest)
            
            file_size = cache_dest.stat().st_size
            
            # Step 2: Atomic symlink replacement
            success = self._atomic_symlink_replace(source_path, str(cache_dest))
            
            duration = time.time() - start_time
            
            if success:
                logger.info(
                    f"✓ Cached: {source.name} ({format_bytes(file_size)}) "
                    f"in {duration:.1f}s"
                )
                return OperationResult(
                    success=True,
                    source_path=source_path,
                    dest_path=str(cache_dest),
                    operation=OperationType.CACHE,
                    bytes_transferred=file_size,
                    duration_seconds=duration,
                )
            else:
                # Cleanup on failure
                if cache_dest.exists():
                    try:
                        cache_dest.unlink()
                    except:
                        pass
                return OperationResult(
                    success=False,
                    source_path=source_path,
                    dest_path=str(cache_dest),
                    operation=OperationType.CACHE,
                    error="Symlink replacement failed",
                )
                
        except Exception as e:
            logger.error(f"Cache operation failed for {source.name}: {e}")
            return OperationResult(
                success=False,
                source_path=source_path,
                dest_path="",
                operation=OperationType.CACHE,
                error=str(e),
            )
    
    def restore_to_array(self,
                         symlink_path: str,
                         remove_cache_copy: bool = True) -> OperationResult:
        """
        Restore a cached file back to array storage.
        
        Reverses the cache operation:
        1. Verify symlink and backup exist
        2. Atomically replace symlink with original file
        3. Optionally remove cache copy
        
        Args:
            symlink_path: Path to symlink (original location)
            remove_cache_copy: Delete cached copy after restore
            
        Returns:
            OperationResult with success status
        """
        symlink = Path(symlink_path)
        start_time = time.time()
        
        try:
            # Check if it's actually a symlink
            if not symlink.is_symlink():
                if symlink.exists():
                    logger.debug(f"Not a symlink, already on array: {symlink.name}")
                    return OperationResult(
                        success=True,
                        source_path=symlink_path,
                        dest_path=symlink_path,
                        operation=OperationType.RESTORE,
                        error="Already on array"
                    )
                return OperationResult(
                    success=False,
                    source_path=symlink_path,
                    dest_path="",
                    operation=OperationType.RESTORE,
                    error="File not found"
                )
            
            # Get cached file path
            cache_path = os.path.realpath(symlink_path)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would restore: {symlink.name}")
                return OperationResult(
                    success=True,
                    source_path=symlink_path,
                    dest_path=symlink_path,
                    operation=OperationType.RESTORE,
                )
            
            # Look for backup file
            backup_path = self._find_backup(symlink_path)
            
            if backup_path and Path(backup_path).exists():
                # Restore from backup (atomic rename)
                file_size = Path(backup_path).stat().st_size
                
                # Remove symlink
                symlink.unlink()
                
                # Restore original
                os.rename(backup_path, symlink_path)
                
                logger.info(f"✓ Restored from backup: {symlink.name}")
            else:
                # No backup - copy from cache back to array
                if not Path(cache_path).exists():
                    return OperationResult(
                        success=False,
                        source_path=symlink_path,
                        dest_path="",
                        operation=OperationType.RESTORE,
                        error="Neither backup nor cache copy exists"
                    )
                
                file_size = Path(cache_path).stat().st_size
                
                # Remove symlink
                symlink.unlink()
                
                # Copy from cache
                shutil.copy2(cache_path, symlink_path)
                
                logger.info(f"✓ Restored from cache: {symlink.name}")
            
            # Remove cache copy if requested
            if remove_cache_copy and Path(cache_path).exists():
                try:
                    Path(cache_path).unlink()
                    logger.debug(f"Removed cache copy: {cache_path}")
                except Exception as e:
                    logger.warning(f"Could not remove cache copy: {e}")
            
            # Clear from registry
            self._symlink_registry.pop(symlink_path, None)
            
            duration = time.time() - start_time
            
            return OperationResult(
                success=True,
                source_path=symlink_path,
                dest_path=symlink_path,
                operation=OperationType.RESTORE,
                bytes_transferred=file_size,
                duration_seconds=duration,
            )
            
        except Exception as e:
            logger.error(f"Restore failed for {symlink.name}: {e}")
            return OperationResult(
                success=False,
                source_path=symlink_path,
                dest_path="",
                operation=OperationType.RESTORE,
                error=str(e),
            )
    
    def batch_cache(self,
                    file_paths: List[str],
                    callback: Optional[callable] = None) -> List[OperationResult]:
        """
        Cache multiple files with concurrent execution.
        
        Args:
            file_paths: List of files to cache
            callback: Optional callback(result) after each file
            
        Returns:
            List of OperationResult for each file
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_cache) as executor:
            futures = {
                executor.submit(self.copy_to_cache_atomic, path): path
                for path in file_paths
            }
            
            for future in futures:
                path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    if callback:
                        callback(result)
                except Exception as e:
                    result = OperationResult(
                        success=False,
                        source_path=path,
                        dest_path="",
                        operation=OperationType.CACHE,
                        error=str(e)
                    )
                    results.append(result)
                    if callback:
                        callback(result)
        
        return results
    
    def batch_restore(self,
                      file_paths: List[str],
                      remove_cache_copies: bool = True,
                      callback: Optional[callable] = None) -> List[OperationResult]:
        """
        Restore multiple files with concurrent execution.
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_array) as executor:
            futures = {
                executor.submit(self.restore_to_array, path, remove_cache_copies): path
                for path in file_paths
            }
            
            for future in futures:
                path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    if callback:
                        callback(result)
                except Exception as e:
                    result = OperationResult(
                        success=False,
                        source_path=path,
                        dest_path="",
                        operation=OperationType.RESTORE,
                        error=str(e)
                    )
                    results.append(result)
                    if callback:
                        callback(result)
        
        return results
    
    def _atomic_symlink_replace(self, original_path: str, cache_path: str) -> bool:
        """
        Atomically replace original file with symlink to cache.
        
        This ensures Plex never sees an interruption:
        1. Create backup of original (atomic rename)
        2. Create temp symlink
        3. Atomically replace original with symlink
        """
        original = Path(original_path)
        temp_link = original.parent / f".{original.name}.cacherr.{uuid.uuid4().hex[:8]}"
        backup_path = original.parent / f".{original.name}{PLEXCACHED_EXTENSION}"
        
        try:
            # Handle existing backup
            actual_backup = backup_path
            counter = 0
            while actual_backup.exists():
                counter += 1
                actual_backup = original.parent / f".{original.name}.{counter}{PLEXCACHED_EXTENSION}"
            
            # Step 1: Rename original to backup (atomic)
            original.rename(actual_backup)
            
            try:
                # Step 2: Create symlink
                os.symlink(cache_path, temp_link)
                
                # Step 3: Atomically move symlink to original location
                os.replace(temp_link, original_path)
                
                # Register for restoration
                with self._lock:
                    self._symlink_registry[original_path] = {
                        'cached_path': cache_path,
                        'backup_path': str(actual_backup),
                    }
                
                logger.debug(f"Created atomic symlink: {original.name} -> {cache_path}")
                return True
                
            except Exception as e:
                # Restore original on failure
                logger.error(f"Symlink failed, restoring: {e}")
                try:
                    if temp_link.exists() or temp_link.is_symlink():
                        temp_link.unlink()
                except:
                    pass
                try:
                    actual_backup.rename(original_path)
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Atomic replace failed: {e}")
            try:
                if temp_link.exists() or temp_link.is_symlink():
                    temp_link.unlink()
            except:
                pass
            return False
    
    def _get_cache_destination(self, source_path: str, preserve_structure: bool) -> Path:
        """Calculate cache destination maintaining directory structure."""
        source = Path(source_path)
        
        if preserve_structure:
            # Try to get relative path from array
            try:
                relative = source.relative_to(self.array_path)
                return self.cache_path / relative
            except ValueError:
                pass
            
            # Try common media roots
            for root in ['/media', '/mnt/user', '/data', '/mnt']:
                try:
                    relative = source.relative_to(root)
                    return self.cache_path / relative
                except ValueError:
                    continue
        
        # Fall back to just filename
        return self.cache_path / source.name
    
    def _is_in_cache(self, path: str) -> bool:
        """Check if a path is within the cache directory."""
        try:
            Path(path).relative_to(self.cache_path)
            return True
        except ValueError:
            return False
    
    def _find_backup(self, original_path: str) -> Optional[str]:
        """Find backup file for an original path."""
        # Check registry first
        with self._lock:
            if original_path in self._symlink_registry:
                return self._symlink_registry[original_path].get('backup_path')
        
        # Search for backup file
        original = Path(original_path)
        backup = original.parent / f".{original.name}{PLEXCACHED_EXTENSION}"
        if backup.exists():
            return str(backup)
        
        # Check numbered backups
        for i in range(1, 10):
            numbered = original.parent / f".{original.name}.{i}{PLEXCACHED_EXTENSION}"
            if numbered.exists():
                return str(numbered)
        
        return None
    
    def get_cached_files(self) -> List[str]:
        """Get list of all symlinks pointing to cache."""
        cached = []
        
        # Check registry
        with self._lock:
            cached.extend(self._symlink_registry.keys())
        
        return cached
    
    def cleanup_orphaned_backups(self, directory: str) -> int:
        """Remove .plexcached backups that are no longer needed."""
        removed = 0
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(PLEXCACHED_EXTENSION):
                    backup_path = os.path.join(root, filename)
                    
                    # Reconstruct original filename
                    original_name = filename.replace(PLEXCACHED_EXTENSION, '')
                    if original_name.startswith('.'):
                        original_name = original_name[1:]
                    
                    original_path = os.path.join(root, original_name)
                    
                    # If original exists and is not a symlink, backup is orphaned
                    if os.path.exists(original_path) and not os.path.islink(original_path):
                        if not self.dry_run:
                            try:
                                os.unlink(backup_path)
                                removed += 1
                                logger.debug(f"Removed orphaned backup: {backup_path}")
                            except Exception as e:
                                logger.warning(f"Could not remove backup {backup_path}: {e}")
                        else:
                            logger.info(f"[DRY RUN] Would remove: {backup_path}")
                            removed += 1
        
        return removed


class SubtitleFinder:
    """Finds associated subtitle files for media files."""
    
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt', '.pgs', '.sup'}
    
    @classmethod
    def find_subtitles(cls, media_path: str) -> List[str]:
        """Find subtitle files for a media file."""
        media = Path(media_path)
        subtitles = []
        
        if not media.parent.exists():
            return subtitles
        
        media_stem = media.stem
        
        for entry in media.parent.iterdir():
            if entry.is_file():
                # Check if it's a subtitle file starting with media name
                if entry.stem.startswith(media_stem):
                    if entry.suffix.lower() in cls.SUBTITLE_EXTENSIONS:
                        subtitles.append(str(entry))
        
        return subtitles
    
    @classmethod
    def get_media_with_subtitles(cls, 
                                  media_paths: List[str],
                                  skip_paths: Optional[Set[str]] = None) -> List[str]:
        """Get media paths plus their subtitle files."""
        if skip_paths is None:
            skip_paths = set()
        
        all_paths = []
        
        for media_path in media_paths:
            if media_path not in skip_paths:
                all_paths.append(media_path)
            
            for subtitle in cls.find_subtitles(media_path):
                if subtitle not in skip_paths:
                    all_paths.append(subtitle)
        
        return all_paths
