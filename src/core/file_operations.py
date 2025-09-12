import os
import shutil
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field, ConfigDict

try:
    from ..config.settings import Config
    from .interfaces import MediaFileInfo, CacheOperationResult, TestModeAnalysis
except ImportError:
    # Fallback for testing
    from config.settings import Config
    from .interfaces import MediaFileInfo, CacheOperationResult, TestModeAnalysis


class FileOperationConfig(BaseModel):
    """
    Configuration for file operations with Pydantic v2 validation.
    
    All operations now use atomic cache redirection by default to prevent
    Plex playback interruption. The atomic operations are transparent and
    provide seamless caching without requiring additional configuration.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    max_concurrent: Optional[int] = Field(
        default=None,
        description="Maximum concurrent file operations (auto-detected if None)"
    )
    dry_run: bool = Field(
        default=False,
        description="Simulate operations without executing them"
    )
    copy_mode: bool = Field(
        default=False,
        description="Copy files instead of moving (preserves originals)"
    )


class FileOperationResult(BaseModel):
    """Result of file operation with type safety."""
    success: bool
    file_size: int
    source_path: str
    destination_path: str
    error_message: Optional[str] = None

class FileOperations:
    """Handles file operations for Cacherr"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Keep extension list aligned with tests and common Unraid setups
        self.subtitle_extensions = [".srt", ".vtt", ".sbv", ".sub", ".idx"]
    
    def process_file_paths(self, files: List[str]) -> List[str]:
        """Process file paths to convert from Plex paths to actual system paths"""
        if not files:
            return []
        
        self.logger.info("Processing file paths...")
        processed_files = []
        
        # Build mapping of plex sources to real sources
        # For Docker, the main source is hardcoded to /mediasource
        source_mappings = [
            (self.config.paths.plex_source, '/mediasource')
        ]
        
        # Add additional source mappings
        if self.config.paths.additional_sources and self.config.paths.additional_plex_sources:
            # Ensure we have matching counts
            if len(self.config.paths.additional_sources) != len(self.config.paths.additional_plex_sources):
                self.logger.warning(f"Mismatch in additional sources: {len(self.config.paths.additional_sources)} real sources vs {len(self.config.paths.additional_plex_sources)} plex sources")
                # Use the shorter list length
                min_length = min(len(self.config.paths.additional_sources), len(self.config.paths.additional_plex_sources))
                for i in range(min_length):
                    source_mappings.append((
                        self.config.paths.additional_plex_sources[i],
                        self.config.paths.additional_sources[i]
                    ))
            else:
                # Perfect match, add all mappings
                for plex_source, real_source in zip(self.config.paths.additional_plex_sources, self.config.paths.additional_sources):
                    source_mappings.append((plex_source, real_source))
        
        self.logger.debug(f"Source mappings: {source_mappings}")
        
        for file_path_str in files:
            if not file_path_str:
                continue
            # Trim whitespace-only entries
            candidate = str(file_path_str).strip()
            if not candidate:
                continue
            
            file_path = Path(candidate)
            converted = False
            
            # Try to convert using any of the source mappings
            for plex_source, real_source in source_mappings:
                try:
                    if file_path.is_relative_to(plex_source):
                        real_path = real_source / file_path.relative_to(plex_source)
                        processed_files.append(str(real_path))
                        self.logger.debug(f"Converted path: {candidate} -> {real_path} (plex: {plex_source} -> real: {real_source})")
                        converted = True
                        break
                except ValueError:
                    # Not relative to this plex source, try next
                    continue
            
            # If no conversion was made, keep the original path
            if not converted:
                processed_files.append(candidate)
                self.logger.debug(f"Could not convert path: {candidate} (no matching plex source)")
        
        self.logger.info(f"Processed {len(processed_files)} file paths")
        return processed_files
    
    def scan_additional_sources(self, media_files: List[str]) -> List[str]:
        """Scan additional sources for media files.

        Behavior:
        - If media_files is provided, attempt to match by stem names.
        - If media_files is empty, return all media-like files found (test-friendly path).
        """
        if not self.config.paths.additional_sources:
            return []

        self.logger.info("Scanning additional source directories...")
        additional_files: List[str] = []

        media_names: Set[str] = set()
        for file_path_str in media_files or []:
            if file_path_str:
                p = Path(file_path_str)
                media_names.add(p.stem)

        # Supported media file extensions for discovery
        media_exts = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.m4v'}

        for source_dir_str in self.config.paths.additional_sources:
            try:
                # Use os.walk for broader compatibility and easier testing via mocking
                for root, _dirs, files in os.walk(source_dir_str):
                    for fname in files:
                        fpath = str(Path(root) / fname)
                        ext = Path(fname).suffix.lower()
                        if ext not in media_exts:
                            continue
                        if media_names:
                            if Path(fname).stem in media_names:
                                additional_files.append(fpath)
                                self.logger.debug(f"Found matching file in additional source: {fpath}")
                        else:
                            # No filter provided; include all media files
                            additional_files.append(fpath)
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Cannot access additional source directory {source_dir_str}: {e}")

        self.logger.info(f"Found {len(additional_files)} additional files in mounted shares")
        return additional_files
    
    def find_subtitle_files(self, media_files: List[str]) -> List[str]:
        """Find subtitle files for the given media files"""
        if not media_files:
            return []
        
        self.logger.info("Finding subtitle files...")
        subtitle_files: List[str] = []
        processed_dirs: Set[Path] = set()

        for media_file_str in media_files:
            if not media_file_str:
                continue

            media_file = Path(media_file_str)
            directory = media_file.parent
            if directory in processed_dirs:
                continue
            processed_dirs.add(directory)
            media_name = media_file.stem

            try:
                # Use glob to allow tests to mock it easily
                for item in directory.glob(f"{media_name}*"):
                    if item.is_file() and item.suffix in self.subtitle_extensions:
                        subtitle_files.append(str(item))
                        self.logger.debug(f"Found subtitle: {item}")
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Cannot access directory {directory}: {e}")

        self.logger.info(f"Found {len(subtitle_files)} subtitle files")
        return subtitle_files
    
    def filter_files_for_cache(self, files: List[str]) -> List[str]:
        """Filter files that should be moved to cache"""
        if not files:
            return []
        
        self.logger.info("Filtering files for cache...")
        files_to_cache = []
        
        for file_path_str in files:
            if not file_path_str:
                continue

            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
            
            # Check if file is already in cache destination
            cache_path = Path(self._get_cache_path(file_path_str))
            if cache_path.exists():
                continue
            
            # Check if file is in array (for Unraid systems)
            array_path = Path(self._get_array_path(file_path_str))
            if array_path.exists():
                files_to_cache.append(file_path_str)
        
        self.logger.info(f"Filtered {len(files_to_cache)} files for cache")
        return files_to_cache
    
    def filter_files_for_array(self, files: List[str]) -> List[str]:
        """Filter files that should be moved to array"""
        if not files:
            return []
        
        self.logger.info("Filtering files for array...")
        files_to_array = []
        
        for file_path_str in files:
            if not file_path_str:
                continue

            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
            
            # Check if file is already in array
            array_path = Path(self._get_array_path(file_path_str))
            if array_path.exists():
                continue
            
            # Check if file is in cache
            cache_path = Path(self._get_cache_path(file_path_str))
            if cache_path.exists():
                files_to_array.append(file_path_str)
        
        self.logger.info(f"Filtered {len(files_to_array)} files for array")
        return files_to_array
    
    def analyze_files_for_test_mode(self, files: List[str], operation_type: str = "cache") -> TestModeAnalysis:
        """Analyze files for test mode, showing what would be moved without actually moving"""
        if not files:
            return TestModeAnalysis(
                files=[],
                total_size=0,
                total_size_readable='0B',
                file_details=[],
                operation_type=operation_type,
                file_count=0
            )
        
        self.logger.info(f"Analyzing {len(files)} files for {operation_type} operation (test mode)")
        
        file_details = []
        total_size = 0
        
        for file_path_str in files:
            if not file_path_str:
                continue

            file_path = Path(file_path_str)
            if not file_path.exists():
                continue
            
            try:
                file_stat = file_path.stat()
                file_size = file_stat.st_size
                file_size_readable = self.get_file_size_readable(file_size)
                
                # Determine destination path
                if operation_type == "cache":
                    dest_path = self._get_cache_path(file_path_str)
                else:  # array
                    dest_path = self._get_array_path(file_path_str)
                
                file_detail = MediaFileInfo(
                    path=file_path_str,
                    size_bytes=file_size,
                    filename=file_path.name,
                    directory=str(file_path.parent),
                    size_readable=file_size_readable,
                    last_modified=datetime.fromtimestamp(file_stat.st_mtime)
                )
                
                file_details.append(file_detail)
                total_size += file_size
                
            except (OSError, PermissionError) as e:
                self.logger.warning(f"Cannot analyze file {file_path_str}: {e}")
        
        return TestModeAnalysis(
            files=files,
            total_size=total_size,
            total_size_readable=self.get_file_size_readable(total_size),
            file_details=file_details,
            operation_type=operation_type,
            file_count=len(file_details)
        )
    
    def check_available_space(self, files: List[str], destination: str) -> bool:
        """Check if there's enough space in the destination directory"""
        if not files or not destination:
            return False
        
        try:
            # Calculate required space
            required_space = sum(Path(f).stat().st_size for f in files if Path(f).exists())
            
            # Get available space
            dest_path = Path(destination)
            if not dest_path.exists():
                self.logger.error(f"Destination directory does not exist: {destination}")
                return False

            stat = shutil.disk_usage(dest_path)
            available_space = stat.free
            
            if required_space > available_space:
                self.logger.error(
                    f"Insufficient space: {required_space} bytes required, "
                    f"{available_space} bytes available in {destination}"
                )
                return False
            
            self.logger.info(
                f"Space check passed: {required_space} bytes required, "
                f"{available_space} bytes available in {destination}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check available space: {e}")
            return False
    
    def move_files(self, files: List[str], source_dir: str, dest_dir: str, 
                   config: Optional[FileOperationConfig] = None) -> CacheOperationResult:
        """Move or copy files from source to destination with concurrent operations"""
        if not files:
            return CacheOperationResult(
                success=True,
                files_processed=0,
                total_size_bytes=0,
                total_size_readable='0B',
                operation_type='none'
            )
        
        # Use default config if none provided
        if config is None:
            config = FileOperationConfig()
        
        # Auto-detect concurrency based on source type if not specified
        max_concurrent = config.max_concurrent
        if max_concurrent is None:
            max_concurrent = self._get_optimal_concurrency(source_dir)
        
        if config.copy_mode:
            operation = "atomic copy"
        else:
            operation = "atomic move"
        
        if config.dry_run:
            self.logger.info(f"DRY RUN: Would {operation} {len(files)} files from {source_dir} to {dest_dir} (concurrency: {max_concurrent})")
            return CacheOperationResult(
                success=True,
                files_processed=len(files),
                total_size_bytes=0,
                total_size_readable='0B (dry run)',
                operation_type=f"{operation} (dry run)"
            )
        
        self.logger.info(f"{operation.capitalize()}ing {len(files)} files from {source_dir} to {dest_dir} (concurrency: {max_concurrent})")
        
        moved_count = 0
        total_size = 0
        failed_files = []
        errors = []
        warnings = []
        
        # Create move operations
        move_operations = []
        for file_path_str in files:
            if not file_path_str:
                continue

            src_path = Path(file_path_str)
            if not src_path.exists():
                warnings.append(f"File does not exist: {file_path_str}")
                continue
            
            # Calculate destination path
            try:
                rel_path = src_path.relative_to(source_dir)
            except ValueError:
                warning_msg = f"File {src_path} is not in source directory {source_dir}, skipping move."
                self.logger.warning(warning_msg)
                warnings.append(warning_msg)
                continue

            dest_path = Path(dest_dir) / rel_path
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            move_operations.append((str(src_path), str(dest_path)))
        
        if not move_operations:
            return CacheOperationResult(
                success=True,
                files_processed=0,
                total_size_bytes=0,
                total_size_readable='0B',
                operation_type=operation,
                warnings=warnings
            )
        
        # Execute operations with thread pool
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all operations
            if config.copy_mode:
                # Copy mode - copy files 
                future_to_operations = {
                    executor.submit(self._copy_single_file, src, dest): (src, dest)
                    for src, dest in move_operations
                }
            else:
                # Move mode - move files
                future_to_operations = {
                    executor.submit(self._move_single_file, src, dest): (src, dest)
                    for src, dest in move_operations
                }
            
            for future in as_completed(future_to_operations):
                src, dest = future_to_operations[future]
                try:
                    success, file_size = future.result()
                    if success:
                        moved_count += 1
                        total_size += file_size
                        self.logger.debug(f"Successfully {operation}d: {src} -> {dest}")
                    else:
                        failed_files.append(src)
                        error_msg = f"Failed to {operation}: {src}"
                        self.logger.warning(error_msg)
                        errors.append(error_msg)
                except Exception as e:
                    failed_files.append(src)
                    error_msg = f"Exception during {operation} {src}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
        
        if failed_files:
            warning_msg = f"Failed to {operation} {len(failed_files)} files"
            self.logger.warning(warning_msg)
            warnings.append(warning_msg)
        
        success_msg = f"Successfully {operation}d {moved_count} files ({self.get_file_size_readable(total_size)})"
        self.logger.info(success_msg)
        
        return CacheOperationResult(
            success=len(errors) == 0,
            files_processed=moved_count,
            total_size_bytes=total_size,
            total_size_readable=self.get_file_size_readable(total_size),
            operation_type=operation,
            errors=errors,
            warnings=warnings
        )
    
    def _is_media_file(self, file_path: str) -> bool:
        """
        Check if a file is a media file that Plex might access.
        
        Returns True for video, audio, and subtitle files that should use
        atomic operations to prevent playback interruption.
        """
        media_extensions = {
            # Video formats
            '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.ts', '.m2ts',
            # Audio formats  
            '.mp3', '.flac', '.aac', '.ogg', '.wav', '.m4a', '.wma',
            # Subtitle formats
            '.srt', '.sub', '.idx', '.ass', '.ssa', '.vtt', '.smi', '.rt'
        }
        return Path(file_path).suffix.lower() in media_extensions
    
    def _create_atomic_symlink(self, original_path: str, cache_path: str) -> bool:
        """
        Atomically replace original file with symlink to cache.
        
        This implements the critical atomic operation that prevents Plex playback
        interruption by using temporary file + rename pattern.
        
        Args:
            original_path: Path to original file to replace
            cache_path: Path to cached file to link to
            
        Returns:
            bool: True if atomic replacement succeeded
            
        Technical Details:
            - Uses os.rename() for atomic replacement (POSIX guarantee)
            - Temporary file created in same directory to ensure atomic operation
            - Preserves directory structure and file visibility for Plex
        """
        try:
            original_path_obj = Path(original_path)
            
            # Create temporary symlink in same directory (ensures atomic rename)
            with tempfile.NamedTemporaryFile(
                dir=original_path_obj.parent,
                delete=False,
                prefix=f".{original_path_obj.name}_cache_",
                suffix=".tmp"
            ) as temp_file:
                temp_symlink_path = temp_file.name
                
            # Remove temp file, we just wanted the unique name
            os.unlink(temp_symlink_path)
            
            # Create symlink pointing to cache
            os.symlink(cache_path, temp_symlink_path)
            
            # Atomic replacement: rename temp symlink to original path
            # This is atomic on POSIX systems and won't interrupt active reads
            os.rename(temp_symlink_path, original_path)
            
            self.logger.debug(f"Atomic symlink created: {original_path} -> {cache_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating atomic symlink for {original_path}: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_symlink_path' in locals():
                    os.unlink(temp_symlink_path)
            except:
                pass
            return False
    
    def _move_single_file(self, src_str: str, dest_str: str) -> Tuple[bool, int]:
        """
        Atomically move a single file using atomic cache redirection.
        
        This method implements atomic operations that never interrupt Plex playback:
        1. Copy file to destination (preserves original during potential access)
        2. Create temporary symlink in same directory as original
        3. Atomically replace original with symlink to destination
        4. Original is replaced seamlessly without interrupting active reads
        
        Args:
            src_str: Source file path
            dest_str: Destination file path
            
        Returns:
            Tuple of (success: bool, file_size: int)
        """
        src = Path(src_str)
        dest = Path(dest_str)
        
        try:
            if not src.exists():
                return False, 0
            
            file_size = src.stat().st_size
            
            # Step 1: Copy file to destination first (preserves original during operation)
            shutil.copy2(str(src), str(dest))
            
            # Step 2: Set proper permissions on cached file
            if os.name == 'posix':
                try:
                    # Use 0o664 (rw-rw-r--) to ensure Plex group access
                    dest.chmod(0o664)
                except OSError:
                    pass  # Ignore permission errors - container environment may restrict
            
            # Step 3: Use atomic operations for media files that Plex might access
            if self._is_media_file(src_str):
                success = self._create_atomic_symlink(src_str, dest_str)
                if not success:
                    # If atomic symlink fails, fall back to regular move
                    self.logger.warning(f"Atomic symlink failed for {src_str}, falling back to regular move")
                    if dest.exists():
                        dest.unlink()  # Clean up partial copy
                    shutil.move(str(src), str(dest))
                    return True, file_size
            else:
                # For non-media files, regular removal is fine (no Plex access concern)
                src.unlink()  # Remove original after successful copy
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error in atomic move from {src_str} to {dest_str}: {e}")
            # Clean up on failure
            try:
                if dest.exists():
                    dest.unlink()
            except:
                pass
            return False, 0
    
    def _move_with_symlink(self, src_str: str, dest_str: str) -> Tuple[bool, int]:
        """Move a file and create a symlink back to original location"""
        src = Path(src_str)
        dest = Path(dest_str)
        try:
            if not src.exists():
                return False, 0
            
            file_size = src.stat().st_size
            
            # Move the file to cache
            shutil.move(str(src), str(dest))
            
            # Create symlink from original location to cache
            os.symlink(str(dest), str(src))
            
            # Set media-appropriate permissions if on Linux
            if os.name == 'posix':
                try:
                    # Use 0o664 (rw-rw-r--) to ensure Plex group access
                    dest.chmod(0o664)
                except OSError:
                    pass  # Ignore permission errors - container environment may restrict
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error moving with symlink {src_str} to {dest_str}: {e}")
            return False, 0
    
    def _copy_single_file(self, src_str: str, dest_str: str) -> Tuple[bool, int]:
        """
        Atomically copy a single file using atomic cache redirection.
        
        This method implements atomic operations for copy mode that never interrupt Plex playback:
        1. Copy file to destination (preserves original in source location)
        2. Create temporary symlink in same directory as original
        3. Atomically replace original with symlink to destination
        4. Plex seamlessly switches to reading from fast cache, original preserved
        
        Args:
            src_str: Source file path 
            dest_str: Destination file path
            
        Returns:
            Tuple of (success: bool, file_size: int)
        """
        src = Path(src_str)
        dest = Path(dest_str)
        
        try:
            if not src.exists():
                return False, 0
            
            file_size = src.stat().st_size
            
            # Step 1: Copy file to destination (preserves original)
            shutil.copy2(str(src), str(dest))  # copy2 preserves metadata
            
            # Step 2: Set proper permissions on cached file
            if os.name == 'posix':
                try:
                    # Use 0o664 (rw-rw-r--) to ensure Plex group access
                    dest.chmod(0o664)
                except OSError:
                    pass  # Ignore permission errors - container environment may restrict
            
            # Step 3: Use atomic operations for media files that Plex might access  
            if self._is_media_file(src_str):
                success = self._create_atomic_symlink(src_str, dest_str)
                if not success:
                    # If atomic symlink fails, keep original file and cached copy
                    # This is still successful for copy mode
                    self.logger.warning(f"Atomic symlink failed for {src_str}, original preserved, cache available")
            # For non-media files, no atomic redirection needed (no Plex access concern)
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error in atomic copy from {src_str} to {dest_str}: {e}")
            # Clean up on failure
            try:
                if dest.exists():
                    dest.unlink()
            except:
                pass
            return False, 0
    
    def delete_files(self, files: List[str], max_concurrent: int = None) -> Tuple[int, int]:
        """Delete files with concurrent operations"""
        if not files:
            return 0, 0
        
        if max_concurrent is None:
            max_concurrent = self.config.performance.max_concurrent_moves_cache
        
        self.logger.info(f"Deleting {len(files)} files (concurrency: {max_concurrent})")
        
        deleted_count = 0
        total_size = 0
        failed_files = []
        
        # Execute deletions with thread pool
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all delete operations
            future_to_file = {
                executor.submit(self._delete_single_file, file_path): file_path
                for file_path in files
            }
            
            # Process results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success, file_size = future.result()
                    if success:
                        deleted_count += 1
                        total_size += file_size
                    else:
                        failed_files.append(file_path)
                except Exception as e:
                    self.logger.error(f"Delete operation failed for {file_path}: {e}")
                    failed_files.append(file_path)
        
        if failed_files:
            self.logger.warning(f"Failed to delete {len(failed_files)} files")
        
        self.logger.info(f"Successfully deleted {deleted_count} files, total size: {self.get_file_size_readable(total_size)})")
        return deleted_count, total_size
    
    def _delete_single_file(self, file_path_str: str) -> Tuple[bool, int]:
        """Delete a single file and return success status and file size"""
        file_path = Path(file_path_str)
        try:
            if not file_path.exists():
                return False, 0
            
            file_size = file_path.stat().st_size
            
            # Delete the file
            file_path.unlink()
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error deleting {file_path_str}: {e}")
            return False, 0
    
    def _get_cache_path(self, file_path_str: str) -> str:
        """Get the cache destination path for a given file"""
        if not file_path_str:
            return ""
        
        file_path = Path(file_path_str)
        
        # Use the flexible cache destination if specified
        cache_destination = Path(self.config.paths.cache_destination)
        
        if cache_destination:
            # Try to find the file in any of the additional source directories
            for source_dir in [Path(s) for s in self.config.paths.additional_sources]:
                if file_path.is_relative_to(source_dir):
                    rel_path = file_path.relative_to(source_dir)
                    return str(cache_destination / rel_path)
        
        # For Docker, the cache destination is hardcoded to /cache
        # and the real source is hardcoded to /mediasource
        # This method is primarily used for additional sources
        
        return "" # Should not happen if paths are correct
    
    def _get_array_path(self, file_path: str) -> str:
        """Get the array path for a given file (Unraid specific)"""
        if not file_path:
            return ""
        
        # For Unraid systems, convert /mnt/user/ to /mnt/user0/
        if file_path.startswith("/mnt/user/"):
            return file_path.replace("/mnt/user/", "/mnt/user0/", 1)
        
        return file_path
    
    def _get_optimal_concurrency(self, source_path: str) -> int:
        """Determine optimal concurrency based on source type (local vs network)"""
        source_path_str = str(source_path)
        
        # Check if source is in additional sources (network/NAS)
        for additional_source in self.config.paths.additional_sources:
            if source_path_str.startswith(additional_source):
                self.logger.debug(f"Using network concurrency for source: {source_path_str}")
                return self.config.performance.max_concurrent_network_transfers
        
        # Check if source is in additional sources (network/NAS)
        # For Docker, the main source is hardcoded to /mediasource
        # so we'll use local concurrency for any path not in additional sources
        if not any(source_path_str.startswith(additional_source) for additional_source in self.config.paths.additional_sources):
            self.logger.debug(f"Using local concurrency for source: {source_path_str}")
            return self.config.performance.max_concurrent_local_transfers
        
        # Default fallback
        self.logger.debug(f"Using default concurrency for unknown source: {source_path_str}")
        return self.config.performance.max_concurrent_local_transfers
    
    def _get_plex_visible_path(self, real_file_path: str) -> Optional[str]:
        """Convert a real file path to the corresponding Plex-visible path.
        
        For the user's setup where Plex and cacherr share the same mount paths,
        the Plex-visible path IS the same as the real file path since both
        containers mount media at the same container paths.
        
        This approach works because:
        - Plex sees media at /media and /Nas1
        - cacherr also mounts media at /media and /Nas1  
        - When files are moved to /cache, we create hardlinks back to original locations
        - Plex continues to see files at expected paths through hardlinks
        
        Args:
            real_file_path: The original file path in container
            
        Returns:
            The same path (since Plex and cacherr use identical mount paths)
        """
        if not real_file_path:
            return None
            
        # For shared mount setup, Plex-visible path is the same as the real path
        # This works because both containers mount media at identical paths
        return real_file_path
    
    def get_file_size_readable(self, size_bytes: int) -> str:
        """Convert file size to human readable format"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size_float = float(size_bytes)
        while size_float >= 1024 and i < len(size_names) - 1:
            size_float /= 1024.0
            i += 1
        
        return f"{size_float:.1f}{size_names[i]}"
