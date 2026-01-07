"""
Instance Lock for Cacherr.

Prevents multiple instances from running simultaneously using file-based locking.
"""

import os
import sys
import logging
import signal
import atexit
from pathlib import Path
from typing import Optional

# Platform-specific locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False


logger = logging.getLogger(__name__)


class InstanceLock:
    """
    File-based instance lock to prevent multiple Cacherr instances.
    
    Uses fcntl on Unix/Linux and msvcrt on Windows.
    Automatically releases on process exit.
    """
    
    def __init__(self, lock_file: str = "/config/cacherr.lock"):
        self.lock_file = Path(lock_file)
        self._file_handle: Optional[object] = None
        self._locked = False
    
    def acquire(self, exit_on_failure: bool = True) -> bool:
        """
        Attempt to acquire the instance lock.
        
        Args:
            exit_on_failure: If True, exit process if lock cannot be acquired
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            # Ensure directory exists
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Open lock file
            self._file_handle = open(self.lock_file, 'w')
            
            # Try to acquire lock
            if HAS_FCNTL:
                try:
                    fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._locked = True
                except (IOError, OSError):
                    self._locked = False
            elif HAS_MSVCRT:
                try:
                    msvcrt.locking(self._file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                    self._locked = True
                except (IOError, OSError):
                    self._locked = False
            else:
                # Fallback: use PID file
                self._locked = self._pid_lock()
            
            if self._locked:
                # Write PID to lock file
                self._file_handle.write(str(os.getpid()))
                self._file_handle.flush()
                
                # Register cleanup handlers
                atexit.register(self.release)
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
                
                logger.info(f"Instance lock acquired: {self.lock_file}")
                return True
            else:
                # Another instance is running
                logger.error("Another instance of Cacherr is already running")
                
                # Try to read PID of existing instance
                try:
                    with open(self.lock_file, 'r') as f:
                        existing_pid = f.read().strip()
                        if existing_pid:
                            logger.error(f"Existing instance PID: {existing_pid}")
                except:
                    pass
                
                if exit_on_failure:
                    sys.exit(1)
                return False
                
        except Exception as e:
            logger.error(f"Failed to acquire instance lock: {e}")
            if exit_on_failure:
                sys.exit(1)
            return False
    
    def release(self) -> None:
        """Release the instance lock."""
        if not self._locked:
            return
        
        try:
            if self._file_handle:
                if HAS_FCNTL:
                    fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
                elif HAS_MSVCRT:
                    try:
                        msvcrt.locking(self._file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
                
                self._file_handle.close()
                self._file_handle = None
            
            # Remove lock file
            if self.lock_file.exists():
                self.lock_file.unlink()
            
            self._locked = False
            logger.info("Instance lock released")
            
        except Exception as e:
            logger.warning(f"Error releasing instance lock: {e}")
    
    def force_release(self) -> bool:
        """
        Force release a stale lock.
        
        Use with caution - only when sure no other instance is running.
        """
        try:
            if self.lock_file.exists():
                # Check if process is still running
                try:
                    with open(self.lock_file, 'r') as f:
                        pid_str = f.read().strip()
                        if pid_str:
                            pid = int(pid_str)
                            # Check if process exists
                            try:
                                os.kill(pid, 0)
                                logger.warning(f"Process {pid} is still running, cannot force release")
                                return False
                            except OSError:
                                # Process not running, safe to remove
                                pass
                except:
                    pass
                
                self.lock_file.unlink()
                logger.info("Stale lock file removed")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to force release lock: {e}")
            return False
    
    def _pid_lock(self) -> bool:
        """Fallback PID-based locking when fcntl/msvcrt unavailable."""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    pid_str = f.read().strip()
                    if pid_str:
                        pid = int(pid_str)
                        try:
                            os.kill(pid, 0)
                            # Process exists, lock is held
                            return False
                        except OSError:
                            # Process doesn't exist, stale lock
                            logger.info("Removing stale lock file")
                            self.lock_file.unlink()
            except:
                pass
        
        return True
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, cleaning up...")
        self.release()
        sys.exit(0)
    
    @property
    def is_locked(self) -> bool:
        """Check if this instance holds the lock."""
        return self._locked
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


def acquire_instance_lock(lock_file: str = "/config/cacherr.lock",
                          exit_on_failure: bool = True) -> InstanceLock:
    """
    Convenience function to acquire instance lock.
    
    Args:
        lock_file: Path to lock file
        exit_on_failure: Exit process if lock cannot be acquired
        
    Returns:
        InstanceLock object
    """
    lock = InstanceLock(lock_file)
    lock.acquire(exit_on_failure=exit_on_failure)
    return lock
