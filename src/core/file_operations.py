import os
import shutil
import logging
from pathlib import Path
from typing import List, Set, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ..config.settings import Config
except ImportError:
    # Fallback for testing
    from config.settings import Config

class FileOperations:
    """Handles file operations for PlexCacheUltra"""
    
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
    
    def analyze_files_for_test_mode(self, files: List[str], operation_type: str = "cache") -> Dict:
        """Analyze files for test mode, showing what would be moved without actually moving"""
        if not files:
            return {
                'files': [],
                'total_size': 0,
                'total_size_readable': '0B',
                'file_details': [],
                'operation_type': operation_type
            }
        
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
                file_size = file_path.stat().st_size
                file_size_readable = self.get_file_size_readable(file_size)
                
                # Determine destination path
                if operation_type == "cache":
                    dest_path = self._get_cache_path(file_path_str)
                else:  # array
                    dest_path = self._get_array_path(file_path_str)
                
                file_detail = {
                    'source': file_path_str,
                    'destination': dest_path,
                    'size_bytes': file_size,
                    'size_readable': file_size_readable,
                    'filename': file_path.name,
                    'directory': str(file_path.parent)
                }
                
                file_details.append(file_detail)
                total_size += file_size
                
            except (OSError, PermissionError) as e:
                self.logger.warning(f"Cannot analyze file {file_path_str}: {e}")
        
        return {
            'files': files,
            'total_size': total_size,
            'total_size_readable': self.get_file_size_readable(total_size),
            'file_details': file_details,
            'operation_type': operation_type,
            'file_count': len(file_details)
        }
    
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
                   max_concurrent: int = None, dry_run: bool = False, copy_mode: bool = False, 
                   create_symlinks: bool = False, move_with_symlinks: bool = False) -> Tuple[int, int]:
        """Move or copy files from source to destination with concurrent operations"""
        if not files:
            return 0, 0
        
        # Auto-detect concurrency based on source type if not specified
        if max_concurrent is None:
            max_concurrent = self._get_optimal_concurrency(source_dir)
        
        if move_with_symlinks:
            operation = "move+symlink"
        elif create_symlinks:
            operation = "symlink"
        elif copy_mode:
            operation = "copy"
        else:
            operation = "move"
        
        if dry_run:
            self.logger.info(f"DRY RUN: Would {operation} {len(files)} files from {source_dir} to {dest_dir} (concurrency: {max_concurrent})")
            return 0, 0
        
        self.logger.info(f"{operation.capitalize()}ing {len(files)} files from {source_dir} to {dest_dir} (concurrency: {max_concurrent})")
        
        moved_count = 0
        total_size = 0
        failed_files = []
        
        # Create move operations
        move_operations = []
        for file_path_str in files:
            if not file_path_str:
                continue

            src_path = Path(file_path_str)
            if not src_path.exists():
                continue
            
            # Calculate destination path
            try:
                rel_path = src_path.relative_to(source_dir)
            except ValueError:
                self.logger.warning(f"File {src_path} is not in source directory {source_dir}, skipping move.")
                continue

            dest_path = Path(dest_dir) / rel_path
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            move_operations.append((str(src_path), str(dest_path)))
        
        if not move_operations:
            return 0, 0
        
        # Execute operations with thread pool
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all operations
            if move_with_symlinks:
                future_to_move = {
                    executor.submit(self._move_with_symlink, src, dest): (src, dest)
                    for src, dest in move_operations
                }
            elif copy_mode:
                future_to_move = {
                    executor.submit(self._copy_single_file, src, dest): (src, dest)
                    for src, dest in move_operations
                }
            else:
                future_to_move = {
                    executor.submit(self._move_single_file, src, dest): (src, dest)
                    for src, dest in move_operations
                }
            
            for future in as_completed(future_to_move):
                src, dest = future_to_move[future]
                try:
                    success, file_size = future.result()
                    if success:
                        moved_count += 1
                        total_size += file_size
                        self.logger.debug(f"Successfully moved: {src} -> {dest}")
                    else:
                        failed_files.append(src)
                        self.logger.warning(f"Failed to move: {src}")
                except Exception as e:
                    failed_files.append(src)
                    self.logger.error(f"Exception moving {src}: {e}")
        
        if failed_files:
            self.logger.warning(f"Failed to {operation} {len(failed_files)} files")
        
        self.logger.info(f"Successfully {operation}d {moved_count} files ({self.get_file_size_readable(total_size)})")
        return moved_count, total_size
    
    def _move_single_file(self, src_str: str, dest_str: str) -> Tuple[bool, int]:
        """Move a single file and return success status and file size"""
        src = Path(src_str)
        dest = Path(dest_str)
        try:
            if not src.exists():
                return False, 0
            
            file_size = src.stat().st_size
            
            # Move the file
            shutil.move(str(src), str(dest))
            
            # Preserve permissions if on Linux
            if os.name == 'posix':
                try:
                    # Set reasonable permissions
                    dest.chmod(0o644)
                except OSError:
                    pass  # Ignore permission errors
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error moving {src_str} to {dest_str}: {e}")
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
            
            # Set reasonable permissions if on Linux
            if os.name == 'posix':
                try:
                    dest.chmod(0o644)
                except OSError:
                    pass  # Ignore permission errors
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error moving with symlink {src_str} to {dest_str}: {e}")
            return False, 0
    
    def _copy_single_file(self, src_str: str, dest_str: str) -> Tuple[bool, int]:
        """Copy a single file and return success status and file size"""
        src = Path(src_str)
        dest = Path(dest_str)
        try:
            if not src.exists():
                return False, 0
            
            file_size = src.stat().st_size
            
            # Copy the file
            shutil.copy2(str(src), str(dest))  # copy2 preserves metadata
            
            # Set reasonable permissions if on Linux
            if os.name == 'posix':
                try:
                    dest.chmod(0o644)
                except OSError:
                    pass  # Ignore permission errors
            
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Error copying {src_str} to {dest_str}: {e}")
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
