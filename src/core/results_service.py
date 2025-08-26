"""
Results service implementation for PlexCacheUltra.

Provides comprehensive operation tracking, real-time updates, and historical
data management. Integrates with the existing DI container and WebSocket system.
"""

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from .interfaces import (
    ResultsService, OperationResult, BatchOperation, 
    UserOperationContext
)

try:
    from ..config.settings import Config
except ImportError:
    from config.settings import Config


class SQLiteResultsService(ResultsService):
    """
    SQLite-based implementation of ResultsService.
    
    Features:
    - Thread-safe database operations
    - Real-time WebSocket notifications
    - Automatic cleanup of old data
    - Comprehensive indexing for performance
    - Multi-user support
    """
    
    def __init__(self, config: Config, websocket_manager=None):
        self.config = config
        self.websocket_manager = websocket_manager
        self.logger = logging.getLogger(__name__)
        self._db_lock = threading.RLock()
        
        # Database setup
        self.db_path = Path("/config/data/results.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self.logger.info("Results service initialized with SQLite backend")
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                # Enable foreign keys and WAL mode for better performance
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA temp_store = MEMORY")
                conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
                
                # Create batch_operations table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS batch_operations (
                        id TEXT PRIMARY KEY,
                        operation_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        test_mode BOOLEAN NOT NULL DEFAULT 0,
                        triggered_by TEXT NOT NULL,
                        triggered_by_user TEXT,
                        reason TEXT NOT NULL,
                        started_at TIMESTAMP NOT NULL,
                        completed_at TIMESTAMP,
                        total_files INTEGER NOT NULL DEFAULT 0,
                        files_processed INTEGER NOT NULL DEFAULT 0,
                        files_successful INTEGER NOT NULL DEFAULT 0,
                        files_failed INTEGER NOT NULL DEFAULT 0,
                        total_size_bytes INTEGER NOT NULL DEFAULT 0,
                        bytes_processed INTEGER NOT NULL DEFAULT 0,
                        error_message TEXT,
                        metadata TEXT,  -- JSON blob
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create operation_results table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS operation_results (
                        id TEXT PRIMARY KEY,
                        operation_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        destination_path TEXT,
                        operation_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        triggered_by_user TEXT,
                        file_size_bytes INTEGER NOT NULL DEFAULT 0,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        parent_operation_id TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (parent_operation_id) REFERENCES batch_operations (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_batch_status ON batch_operations(status)",
                    "CREATE INDEX IF NOT EXISTS idx_batch_started_at ON batch_operations(started_at)",
                    "CREATE INDEX IF NOT EXISTS idx_batch_user ON batch_operations(triggered_by_user)",
                    "CREATE INDEX IF NOT EXISTS idx_batch_type ON batch_operations(operation_type)",
                    "CREATE INDEX IF NOT EXISTS idx_results_batch ON operation_results(parent_operation_id)",
                    "CREATE INDEX IF NOT EXISTS idx_results_status ON operation_results(status)",
                    "CREATE INDEX IF NOT EXISTS idx_results_started_at ON operation_results(started_at)",
                    "CREATE INDEX IF NOT EXISTS idx_results_file_path ON operation_results(file_path)"
                ]
                
                for index_sql in indexes:
                    conn.execute(index_sql)
                
                conn.commit()
                
            finally:
                conn.close()
    
    def create_batch_operation(self, operation_type: str, test_mode: bool = False,
                             triggered_by: str = "manual", user_context: Optional[UserOperationContext] = None,
                             reason: str = "user_request", metadata: Optional[Dict[str, Any]] = None) -> BatchOperation:
        """Create a new batch operation."""
        batch_id = str(uuid.uuid4())
        started_at = datetime.now()
        
        batch_op = BatchOperation(
            id=batch_id,
            operation_type=operation_type,
            status="pending",
            test_mode=test_mode,
            triggered_by=triggered_by,
            triggered_by_user=user_context.plex_username if user_context else None,
            reason=reason,
            started_at=started_at,
            total_files=0,
            files_processed=0,
            files_successful=0,
            files_failed=0,
            total_size_bytes=0,
            bytes_processed=0,
            metadata=metadata
        )
        
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                conn.execute('''
                    INSERT INTO batch_operations 
                    (id, operation_type, status, test_mode, triggered_by, triggered_by_user, 
                     reason, started_at, total_files, files_processed, files_successful, 
                     files_failed, total_size_bytes, bytes_processed, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch_op.id, batch_op.operation_type, batch_op.status,
                    batch_op.test_mode, batch_op.triggered_by, batch_op.triggered_by_user,
                    batch_op.reason, batch_op.started_at, batch_op.total_files,
                    batch_op.files_processed, batch_op.files_successful, batch_op.files_failed,
                    batch_op.total_size_bytes, batch_op.bytes_processed,
                    json.dumps(batch_op.metadata) if batch_op.metadata else None
                ))
                conn.commit()
            finally:
                conn.close()
        
        # Notify WebSocket clients
        self._notify_operation_update(batch_op)
        
        self.logger.info(f"Created batch operation {batch_id}: {operation_type} ({'test' if test_mode else 'live'})")
        return batch_op
    
    def add_file_operation(self, batch_id: str, file_path: str, operation_type: str,
                          reason: str, source_path: str, destination_path: Optional[str] = None,
                          file_size_bytes: int = 0, user_id: Optional[str] = None) -> OperationResult:
        """Add a file operation to a batch."""
        operation_id = str(uuid.uuid4())
        filename = Path(file_path).name
        
        file_op = OperationResult(
            id=operation_id,
            operation_id=operation_id,
            file_path=file_path,
            filename=filename,
            source_path=source_path,
            destination_path=destination_path,
            operation_type=operation_type,
            status="pending",
            reason=reason,
            triggered_by_user=user_id,
            file_size_bytes=file_size_bytes,
            parent_operation_id=batch_id
        )
        
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                conn.execute('''
                    INSERT INTO operation_results 
                    (id, operation_id, file_path, filename, source_path, destination_path,
                     operation_type, status, reason, triggered_by_user, file_size_bytes, parent_operation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_op.id, file_op.operation_id, file_op.file_path, file_op.filename,
                    file_op.source_path, file_op.destination_path, file_op.operation_type,
                    file_op.status, file_op.reason, file_op.triggered_by_user,
                    file_op.file_size_bytes, file_op.parent_operation_id
                ))
                
                # Update batch total_files and total_size_bytes
                conn.execute('''
                    UPDATE batch_operations 
                    SET total_files = total_files + 1, total_size_bytes = total_size_bytes + ?
                    WHERE id = ?
                ''', (file_size_bytes, batch_id))
                
                conn.commit()
            finally:
                conn.close()
        
        return file_op
    
    def update_operation_status(self, operation_id: str, status: str,
                               error_message: Optional[str] = None, 
                               completed_at: Optional[datetime] = None) -> bool:
        """Update the status of an operation."""
        if completed_at is None and status in ['completed', 'failed']:
            completed_at = datetime.now()
        
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                conn.execute('''
                    UPDATE operation_results 
                    SET status = ?, error_message = ?, completed_at = ?,
                        started_at = CASE WHEN started_at IS NULL AND ? = 'processing' THEN ? ELSE started_at END
                    WHERE id = ?
                ''', (status, error_message, completed_at, status, datetime.now(), operation_id))
                
                rows_affected = conn.rowcount
                conn.commit()
                
                # Notify WebSocket clients about individual file operation update
                if self.websocket_manager:
                    self.websocket_manager.broadcast({
                        'type': 'operation_file_update',
                        'data': {
                            'operation_id': operation_id,
                            'status': status,
                            'error_message': error_message,
                            'completed_at': completed_at.isoformat() if completed_at else None
                        }
                    })
                
                return rows_affected > 0
                
            finally:
                conn.close()
    
    def update_batch_progress(self, batch_id: str, files_processed: int,
                            files_successful: int, files_failed: int,
                            bytes_processed: int) -> bool:
        """Update batch operation progress."""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                # Get current batch info
                cursor = conn.execute('''
                    SELECT status, total_files, total_size_bytes FROM batch_operations WHERE id = ?
                ''', (batch_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                current_status, total_files, total_size_bytes = result
                
                # Determine new status
                new_status = current_status
                completed_at = None
                
                if files_processed >= total_files and current_status == 'running':
                    if files_failed > 0:
                        new_status = 'completed_with_errors'
                    else:
                        new_status = 'completed'
                    completed_at = datetime.now()
                elif current_status == 'pending' and files_processed > 0:
                    new_status = 'running'
                
                # Update batch progress
                conn.execute('''
                    UPDATE batch_operations 
                    SET files_processed = ?, files_successful = ?, files_failed = ?,
                        bytes_processed = ?, status = ?, completed_at = ?
                    WHERE id = ?
                ''', (files_processed, files_successful, files_failed, 
                     bytes_processed, new_status, completed_at, batch_id))
                
                conn.commit()
                
                # Get updated batch for notification
                updated_batch = self._get_batch_by_id(batch_id)
                if updated_batch:
                    self._notify_operation_update(updated_batch)
                
                return True
                
            finally:
                conn.close()
    
    def get_active_operations(self, user_id: Optional[str] = None) -> List[BatchOperation]:
        """Get currently active operations."""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                sql = '''
                    SELECT * FROM batch_operations 
                    WHERE status IN ('pending', 'running')
                '''
                params = []
                
                if user_id:
                    sql += ' AND triggered_by_user = ?'
                    params.append(user_id)
                
                sql += ' ORDER BY started_at DESC'
                
                cursor = conn.execute(sql, params)
                return [self._row_to_batch_operation(row) for row in cursor.fetchall()]
                
            finally:
                conn.close()
    
    def get_operation_history(self, limit: int = 50, offset: int = 0,
                            user_id: Optional[str] = None,
                            operation_type: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Tuple[List[BatchOperation], int]:
        """Get operation history with pagination and filtering."""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if user_id:
                    where_conditions.append('triggered_by_user = ?')
                    params.append(user_id)
                
                if operation_type:
                    where_conditions.append('operation_type = ?')
                    params.append(operation_type)
                
                if start_date:
                    where_conditions.append('started_at >= ?')
                    params.append(start_date)
                
                if end_date:
                    where_conditions.append('started_at <= ?')
                    params.append(end_date)
                
                where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
                
                # Get total count
                count_sql = f"SELECT COUNT(*) FROM batch_operations {where_clause}"
                cursor = conn.execute(count_sql, params)
                total_count = cursor.fetchone()[0]
                
                # Get paginated results
                data_sql = f'''
                    SELECT * FROM batch_operations {where_clause}
                    ORDER BY started_at DESC LIMIT ? OFFSET ?
                '''
                cursor = conn.execute(data_sql, params + [limit, offset])
                operations = [self._row_to_batch_operation(row) for row in cursor.fetchall()]
                
                return operations, total_count
                
            finally:
                conn.close()
    
    def get_operation_details(self, operation_id: str) -> Tuple[BatchOperation, List[OperationResult]]:
        """Get detailed information about a specific operation."""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                # Get batch operation
                cursor = conn.execute('SELECT * FROM batch_operations WHERE id = ?', (operation_id,))
                batch_row = cursor.fetchone()
                
                if not batch_row:
                    raise ValueError(f"Batch operation {operation_id} not found")
                
                batch_op = self._row_to_batch_operation(batch_row)
                
                # Get file operations
                cursor = conn.execute('''
                    SELECT * FROM operation_results 
                    WHERE parent_operation_id = ? 
                    ORDER BY started_at DESC, created_at DESC
                ''', (operation_id,))
                
                file_ops = [self._row_to_operation_result(row) for row in cursor.fetchall()]
                
                return batch_op, file_ops
                
            finally:
                conn.close()
    
    def get_user_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        start_date = datetime.now() - timedelta(days=days)
        
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                stats = {}
                
                # Get batch operation stats
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_operations,
                        SUM(files_successful) as total_files_successful,
                        SUM(files_failed) as total_files_failed,
                        SUM(bytes_processed) as total_bytes_processed,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_operations,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_operations
                    FROM batch_operations 
                    WHERE triggered_by_user = ? AND started_at >= ?
                ''', (user_id, start_date))
                
                batch_stats = cursor.fetchone()
                stats.update({
                    'total_operations': batch_stats[0] or 0,
                    'total_files_successful': batch_stats[1] or 0,
                    'total_files_failed': batch_stats[2] or 0,
                    'total_bytes_processed': batch_stats[3] or 0,
                    'successful_operations': batch_stats[4] or 0,
                    'failed_operations': batch_stats[5] or 0,
                    'period_days': days,
                    'start_date': start_date.isoformat(),
                    'user_id': user_id
                })
                
                return stats
                
            finally:
                conn.close()
    
    def cleanup_old_results(self, days_to_keep: int = 90) -> int:
        """Clean up old operation results."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                # Count operations to be deleted
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM batch_operations WHERE started_at < ?
                ''', (cutoff_date,))
                count_to_delete = cursor.fetchone()[0]
                
                # Delete old operations (cascades to operation_results)
                conn.execute('DELETE FROM batch_operations WHERE started_at < ?', (cutoff_date,))
                
                conn.commit()
                
                self.logger.info(f"Cleaned up {count_to_delete} old operations (older than {days_to_keep} days)")
                return count_to_delete
                
            finally:
                conn.close()
    
    def _get_batch_by_id(self, batch_id: str) -> Optional[BatchOperation]:
        """Get batch operation by ID."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            cursor = conn.execute('SELECT * FROM batch_operations WHERE id = ?', (batch_id,))
            row = cursor.fetchone()
            return self._row_to_batch_operation(row) if row else None
        finally:
            conn.close()
    
    def _row_to_batch_operation(self, row) -> BatchOperation:
        """Convert database row to BatchOperation."""
        metadata = json.loads(row[16]) if row[16] else None
        
        return BatchOperation(
            id=row[0],
            operation_type=row[1],
            status=row[2],
            test_mode=bool(row[3]),
            triggered_by=row[4],
            triggered_by_user=row[5],
            reason=row[6],
            started_at=datetime.fromisoformat(row[7]) if row[7] else None,
            completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
            total_files=row[9],
            files_processed=row[10],
            files_successful=row[11],
            files_failed=row[12],
            total_size_bytes=row[13],
            bytes_processed=row[14],
            error_message=row[15],
            metadata=metadata
        )
    
    def _row_to_operation_result(self, row) -> OperationResult:
        """Convert database row to OperationResult."""
        return OperationResult(
            id=row[0],
            operation_id=row[1],
            file_path=row[2],
            filename=row[3],
            source_path=row[4],
            destination_path=row[5],
            operation_type=row[6],
            status=row[7],
            reason=row[8],
            triggered_by_user=row[9],
            file_size_bytes=row[10],
            started_at=datetime.fromisoformat(row[11]) if row[11] else None,
            completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
            error_message=row[13],
            parent_operation_id=row[14]
        )
    
    def _notify_operation_update(self, batch_op: BatchOperation) -> None:
        """Send WebSocket notification for operation update."""
        if self.websocket_manager:
            try:
                self.websocket_manager.broadcast({
                    'type': 'operation_progress',
                    'data': {
                        'operation_id': batch_op.id,
                        'operation_type': batch_op.operation_type,
                        'status': batch_op.status,
                        'test_mode': batch_op.test_mode,
                        'progress': (batch_op.files_processed / batch_op.total_files * 100) if batch_op.total_files > 0 else 0,
                        'files_processed': batch_op.files_processed,
                        'files_successful': batch_op.files_successful,
                        'files_failed': batch_op.files_failed,
                        'total_files': batch_op.total_files,
                        'bytes_processed': batch_op.bytes_processed,
                        'total_bytes': batch_op.total_size_bytes,
                        'started_at': batch_op.started_at.isoformat() if batch_op.started_at else None,
                        'completed_at': batch_op.completed_at.isoformat() if batch_op.completed_at else None,
                        'triggered_by': batch_op.triggered_by,
                        'triggered_by_user': batch_op.triggered_by_user,
                        'reason': batch_op.reason,
                        'error_message': batch_op.error_message
                    }
                })
            except Exception as e:
                self.logger.warning(f"Failed to send WebSocket notification: {e}")