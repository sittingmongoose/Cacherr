"""
Metrics repository implementation for PlexCacheUltra.

This module provides the MetricsFileRepository class that implements the
MetricsRepository interface using file-based JSON persistence. It manages
performance metrics, user activity tracking, and system health monitoring
with efficient time-series data handling.

Key Features:
- File-based JSON persistence with atomic operations
- Time-series metrics data with efficient aggregation
- User activity and watched items tracking
- System health metrics collection
- Automatic data cleanup and retention management
- Thread-safe operations with proper locking
- Performance optimizations for large datasets
"""

from typing import List, Dict, Optional, Any, Type
from datetime import datetime, timedelta
from pathlib import Path
import logging
import statistics
import psutil
import shutil

from pydantic import BaseModel, Field

from ..core.repositories import MetricsRepository, MetricsData, UserActivity, WatchedItem
from .base_repository import BaseFileRepository
from .exceptions import (
    MetricsError,
    AggregationError,
    CleanupError,
    ValidationError,
    wrap_repository_error
)

logger = logging.getLogger(__name__)


class MetricsRepositoryData(BaseModel):
    """
    Root data model for metrics repository persistence.
    
    This model defines the structure of the metrics data file,
    containing all metrics, user activities, and system health data.
    """
    
    version: str = Field(default="1.0", description="Data format version")
    created_at: datetime = Field(default_factory=datetime.now, description="Repository creation time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last modification time")
    metrics: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Performance metrics time series"
    )
    user_activities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="User activity records"
    )
    watched_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Watched media items"
    )
    system_health: Dict[str, Any] = Field(
        default_factory=dict,
        description="System health metrics cache"
    )
    retention_settings: Dict[str, int] = Field(
        default_factory=lambda: {
            "metrics_retention_days": 90,
            "activity_retention_days": 365,
            "watched_items_retention_days": 365
        },
        description="Data retention policies"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsFileRepository(BaseFileRepository[MetricsData], MetricsRepository):
    """
    File-based implementation of MetricsRepository interface.
    
    This repository stores metrics data in a JSON file with time-series
    organization, efficient aggregation capabilities, and automatic
    data cleanup based on retention policies.
    
    Features:
    - JSON file-based persistence with atomic operations
    - Time-series metrics data with efficient querying
    - User activity and media consumption tracking
    - System health metrics collection and caching
    - Automatic data cleanup based on retention policies
    - Thread-safe operations with file locking
    - Performance optimizations for large datasets
    - Comprehensive error handling and logging
    
    Data Organization:
    - Metrics are stored in chronological order for efficient queries
    - User activities are indexed by username and timestamp
    - Watched items are organized by user and media type
    - System health data is cached with periodic refresh
    
    Usage:
        metrics_repo = MetricsFileRepository(
            data_file=Path("/path/to/metrics_data.json"),
            auto_backup=True
        )
        
        # Record metric
        metric = MetricsData(
            timestamp=datetime.now(),
            operation_type="cache_operation",
            files_processed=100,
            bytes_processed=1000000,
            duration_seconds=30.5,
            success_rate=0.95
        )
        metrics_repo.record_metric(metric)
        
        # Get aggregated metrics
        stats = metrics_repo.get_aggregated_metrics("cache_operation", 24)
    """
    
    def __init__(
        self,
        data_file: Path,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        backup_retention_days: int = 30,
        metrics_retention_days: int = 90,
        activity_retention_days: int = 365
    ):
        """
        Initialize metrics file repository.
        
        Args:
            data_file: Path to metrics data JSON file
            backup_dir: Directory for backup files
            auto_backup: Whether to automatically create backups
            backup_retention_days: Days to retain backup files
            metrics_retention_days: Days to retain metrics data
            activity_retention_days: Days to retain activity data
        """
        self.metrics_retention_days = metrics_retention_days
        self.activity_retention_days = activity_retention_days
        
        super().__init__(
            data_file=data_file,
            backup_dir=backup_dir,
            auto_backup=auto_backup,
            backup_retention_days=backup_retention_days,
            validate_on_load=False  # Large datasets may not need full validation on every load
        )
    
    def get_model_class(self) -> Type[MetricsData]:
        """Get the Pydantic model class for metrics data."""
        return MetricsData
    
    def get_default_data(self) -> Dict[str, Any]:
        """Get default data structure for new metrics files."""
        default_data = MetricsRepositoryData(
            retention_settings={
                "metrics_retention_days": self.metrics_retention_days,
                "activity_retention_days": self.activity_retention_days,
                "watched_items_retention_days": self.activity_retention_days
            }
        )
        return default_data.model_dump()
    
    def _metric_to_dict(self, metric: MetricsData) -> Dict[str, Any]:
        """Convert MetricsData to dictionary for storage."""
        return metric.model_dump()
    
    def _dict_to_metric(self, data: Dict[str, Any]) -> MetricsData:
        """Convert dictionary to MetricsData."""
        return MetricsData.model_validate(data)
    
    def _activity_to_dict(self, activity: UserActivity) -> Dict[str, Any]:
        """Convert UserActivity to dictionary for storage."""
        return activity.model_dump()
    
    def _dict_to_activity(self, data: Dict[str, Any]) -> UserActivity:
        """Convert dictionary to UserActivity."""
        return UserActivity.model_validate(data)
    
    def _watched_item_to_dict(self, item: WatchedItem) -> Dict[str, Any]:
        """Convert WatchedItem to dictionary for storage."""
        return item.model_dump()
    
    def _dict_to_watched_item(self, data: Dict[str, Any]) -> WatchedItem:
        """Convert dictionary to WatchedItem."""
        return WatchedItem.model_validate(data)
    
    def _cleanup_old_data(self, data: Dict[str, Any]) -> int:
        """
        Clean up old data based on retention settings.
        
        Args:
            data: Repository data dictionary
            
        Returns:
            int: Total number of records removed
        """
        removed_count = 0
        now = datetime.now()
        
        # Get retention settings
        retention = data.get("retention_settings", {})
        metrics_retention = retention.get("metrics_retention_days", self.metrics_retention_days)
        activity_retention = retention.get("activity_retention_days", self.activity_retention_days)
        watched_retention = retention.get("watched_items_retention_days", self.activity_retention_days)
        
        # Clean up metrics
        if metrics_retention > 0:
            cutoff_time = now - timedelta(days=metrics_retention)
            original_count = len(data.get("metrics", []))
            
            data["metrics"] = [
                metric for metric in data.get("metrics", [])
                if datetime.fromisoformat(metric["timestamp"]) >= cutoff_time
            ]
            
            removed_count += original_count - len(data["metrics"])
        
        # Clean up user activities
        if activity_retention > 0:
            cutoff_time = now - timedelta(days=activity_retention)
            original_count = len(data.get("user_activities", []))
            
            data["user_activities"] = [
                activity for activity in data.get("user_activities", [])
                if datetime.fromisoformat(activity["last_seen"]) >= cutoff_time
            ]
            
            removed_count += original_count - len(data["user_activities"])
        
        # Clean up watched items
        if watched_retention > 0:
            cutoff_time = now - timedelta(days=watched_retention)
            original_count = len(data.get("watched_items", []))
            
            data["watched_items"] = [
                item for item in data.get("watched_items", [])
                if datetime.fromisoformat(item["watched_at"]) >= cutoff_time
            ]
            
            removed_count += original_count - len(data["watched_items"])
        
        return removed_count
    
    def record_metric(self, metric: MetricsData) -> bool:
        """
        Record a performance metric.
        
        Args:
            metric: MetricsData to record
            
        Returns:
            bool: True if recording successful
            
        Raises:
            ValidationError: When metric data is invalid
            RepositoryError: When data access fails
        """
        try:
            # Validate metric
            metric = MetricsData.model_validate(metric.model_dump())
            
            data = self.load_data()
            
            # Add metric to list
            if "metrics" not in data:
                data["metrics"] = []
            
            data["metrics"].append(self._metric_to_dict(metric))
            
            # Sort metrics by timestamp to maintain chronological order
            data["metrics"].sort(key=lambda x: x["timestamp"])
            
            # Update metadata
            data["last_updated"] = datetime.now().isoformat()
            
            # Periodic cleanup (every 100 metrics)
            if len(data["metrics"]) % 100 == 0:
                removed_count = self._cleanup_old_data(data)
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old metrics records")
            
            # Save data
            self.save_data(data, "record_metric")
            
            logger.debug(f"Recorded metric: {metric.operation_type} at {metric.timestamp}")
            return True
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise wrap_repository_error(
                "metric recording",
                e,
                {"operation_type": metric.operation_type, "timestamp": str(metric.timestamp)}
            )
    
    def get_metrics(
        self,
        operation_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MetricsData]:
        """
        Retrieve metrics with optional filtering.
        
        Args:
            operation_type: Filter by operation type
            start_time: Filter metrics after this time
            end_time: Filter metrics before this time
            limit: Maximum number of metrics to return
            
        Returns:
            List[MetricsData]: List of matching metrics
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            metrics = data.get("metrics", [])
            
            # Convert to MetricsData objects with filtering
            result_metrics = []
            
            for metric_data in reversed(metrics):  # Newest first
                try:
                    metric = self._dict_to_metric(metric_data)
                    
                    # Apply filters
                    if operation_type and metric.operation_type != operation_type:
                        continue
                    
                    if start_time and metric.timestamp < start_time:
                        continue
                    
                    if end_time and metric.timestamp > end_time:
                        continue
                    
                    result_metrics.append(metric)
                    
                    # Apply limit
                    if len(result_metrics) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Skipping invalid metric data: {e}")
            
            return result_metrics
            
        except Exception as e:
            raise wrap_repository_error(
                "metrics retrieval",
                e,
                {
                    "operation_type": operation_type,
                    "start_time": str(start_time) if start_time else None,
                    "end_time": str(end_time) if end_time else None,
                    "limit": limit
                }
            )
    
    def get_aggregated_metrics(
        self,
        operation_type: Optional[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a time window.
        
        Args:
            operation_type: Filter by operation type
            time_window_hours: Time window for aggregation
            
        Returns:
            Dict[str, Any]: Aggregated metrics
            
        Raises:
            AggregationError: When data aggregation fails
        """
        try:
            # Get metrics for the time window
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            metrics = self.get_metrics(
                operation_type=operation_type,
                start_time=start_time,
                end_time=end_time,
                limit=10000  # Large limit to get all relevant metrics
            )
            
            if not metrics:
                return {
                    "total_operations": 0,
                    "total_files": 0,
                    "total_bytes": 0,
                    "average_duration": 0.0,
                    "success_rate": 0.0,
                    "error_summary": {},
                    "time_window_hours": time_window_hours,
                    "operation_type": operation_type,
                    "calculated_at": datetime.now().isoformat()
                }
            
            # Calculate aggregations
            total_operations = len(metrics)
            total_files = sum(m.files_processed for m in metrics)
            total_bytes = sum(m.bytes_processed for m in metrics)
            durations = [m.duration_seconds for m in metrics if m.duration_seconds > 0]
            success_rates = [m.success_rate for m in metrics if 0 <= m.success_rate <= 1]
            
            # Average duration
            average_duration = statistics.mean(durations) if durations else 0.0
            
            # Overall success rate
            overall_success_rate = statistics.mean(success_rates) if success_rates else 0.0
            
            # Error summary
            error_summary = {}
            for metric in metrics:
                for error in metric.errors:
                    error_summary[error] = error_summary.get(error, 0) + 1
            
            # Performance statistics
            duration_stats = {}
            if durations:
                duration_stats = {
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "median_duration": statistics.median(durations),
                    "std_dev_duration": statistics.stdev(durations) if len(durations) > 1 else 0.0
                }
            
            # Throughput statistics
            if durations and total_bytes > 0:
                throughput_mbps = [
                    (metrics[i].bytes_processed / durations[i]) / (1024 * 1024)
                    for i in range(len(metrics))
                    if i < len(durations) and durations[i] > 0
                ]
                
                if throughput_mbps:
                    throughput_stats = {
                        "average_throughput_mbps": statistics.mean(throughput_mbps),
                        "max_throughput_mbps": max(throughput_mbps),
                        "min_throughput_mbps": min(throughput_mbps)
                    }
                else:
                    throughput_stats = {}
            else:
                throughput_stats = {}
            
            aggregated_metrics = {
                "total_operations": total_operations,
                "total_files": total_files,
                "total_bytes": total_bytes,
                "average_duration": average_duration,
                "success_rate": overall_success_rate,
                "error_summary": error_summary,
                "time_window_hours": time_window_hours,
                "operation_type": operation_type,
                "calculated_at": datetime.now().isoformat(),
                "duration_statistics": duration_stats,
                "throughput_statistics": throughput_stats
            }
            
            return aggregated_metrics
            
        except Exception as e:
            raise AggregationError(
                f"Failed to aggregate metrics for operation_type: {operation_type}",
                aggregation_type="metrics_aggregation",
                original_error=e
            )
    
    def record_user_activity(self, activity: UserActivity) -> bool:
        """
        Record user activity information.
        
        Args:
            activity: UserActivity to record
            
        Returns:
            bool: True if recording successful
            
        Raises:
            ValidationError: When activity data is invalid
            RepositoryError: When data access fails
        """
        try:
            # Validate activity
            activity = UserActivity.model_validate(activity.model_dump())
            
            data = self.load_data()
            
            # Initialize user activities if needed
            if "user_activities" not in data:
                data["user_activities"] = []
            
            # Check if user activity already exists and update it
            existing_index = None
            for i, existing_activity in enumerate(data["user_activities"]):
                if existing_activity["username"] == activity.username:
                    existing_index = i
                    break
            
            activity_dict = self._activity_to_dict(activity)
            
            if existing_index is not None:
                # Update existing activity
                data["user_activities"][existing_index] = activity_dict
            else:
                # Add new activity
                data["user_activities"].append(activity_dict)
            
            # Update metadata
            data["last_updated"] = datetime.now().isoformat()
            
            # Save data
            self.save_data(data, "record_activity")
            
            logger.debug(f"Recorded user activity: {activity.username}")
            return True
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise wrap_repository_error(
                "user activity recording",
                e,
                {"username": activity.username}
            )
    
    def get_user_activities(
        self,
        username: Optional[str] = None,
        days_back: int = 30
    ) -> List[UserActivity]:
        """
        Get user activity information.
        
        Args:
            username: Filter by specific username (None for all users)
            days_back: Number of days to look back
            
        Returns:
            List[UserActivity]: List of user activities
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            activities = data.get("user_activities", [])
            
            # Filter by time window
            cutoff_time = datetime.now() - timedelta(days=days_back)
            
            result_activities = []
            for activity_data in activities:
                try:
                    activity = self._dict_to_activity(activity_data)
                    
                    # Apply filters
                    if username and activity.username != username:
                        continue
                    
                    if activity.last_seen < cutoff_time:
                        continue
                    
                    result_activities.append(activity)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid activity data: {e}")
            
            # Sort by last seen (most recent first)
            result_activities.sort(key=lambda x: x.last_seen, reverse=True)
            
            return result_activities
            
        except Exception as e:
            raise wrap_repository_error(
                "user activities retrieval",
                e,
                {"username": username, "days_back": days_back}
            )
    
    def record_watched_item(self, item: WatchedItem) -> bool:
        """
        Record a watched media item.
        
        Args:
            item: WatchedItem to record
            
        Returns:
            bool: True if recording successful
            
        Raises:
            ValidationError: When watched item data is invalid
            RepositoryError: When data access fails
        """
        try:
            # Validate item
            item = WatchedItem.model_validate(item.model_dump())
            
            data = self.load_data()
            
            # Initialize watched items if needed
            if "watched_items" not in data:
                data["watched_items"] = []
            
            # Add watched item
            data["watched_items"].append(self._watched_item_to_dict(item))
            
            # Sort by watched time to maintain chronological order
            data["watched_items"].sort(key=lambda x: x["watched_at"], reverse=True)
            
            # Update metadata
            data["last_updated"] = datetime.now().isoformat()
            
            # Save data
            self.save_data(data, "record_watched")
            
            logger.debug(f"Recorded watched item: {item.title} by {item.user}")
            return True
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise wrap_repository_error(
                "watched item recording",
                e,
                {"title": item.title, "user": item.user}
            )
    
    def get_watched_items(
        self,
        user: Optional[str] = None,
        media_type: Optional[str] = None,
        days_back: int = 30
    ) -> List[WatchedItem]:
        """
        Get watched media items.
        
        Args:
            user: Filter by specific user
            media_type: Filter by media type
            days_back: Number of days to look back
            
        Returns:
            List[WatchedItem]: List of watched items
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            watched_items = data.get("watched_items", [])
            
            # Filter by time window
            cutoff_time = datetime.now() - timedelta(days=days_back)
            
            result_items = []
            for item_data in watched_items:
                try:
                    item = self._dict_to_watched_item(item_data)
                    
                    # Apply filters
                    if user and item.user != user:
                        continue
                    
                    if media_type and item.media_type != media_type:
                        continue
                    
                    if item.watched_at < cutoff_time:
                        continue
                    
                    result_items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid watched item data: {e}")
            
            return result_items
            
        except Exception as e:
            raise wrap_repository_error(
                "watched items retrieval",
                e,
                {"user": user, "media_type": media_type, "days_back": days_back}
            )
    
    def cleanup_old_metrics(self, retention_days: int = 90) -> int:
        """
        Clean up old metric data beyond retention period.
        
        Args:
            retention_days: Number of days to retain metrics
            
        Returns:
            int: Number of metric records deleted
            
        Raises:
            CleanupError: When cleanup operation fails
        """
        try:
            data = self.load_data()
            
            # Update retention settings
            if "retention_settings" not in data:
                data["retention_settings"] = {}
            
            data["retention_settings"]["metrics_retention_days"] = retention_days
            
            # Perform cleanup
            removed_count = self._cleanup_old_data(data)
            
            if removed_count > 0:
                # Update metadata
                data["last_updated"] = datetime.now().isoformat()
                
                # Save data
                self.save_data(data, "cleanup_metrics")
                
                logger.info(f"Cleaned up {removed_count} old metrics records")
            
            return removed_count
            
        except Exception as e:
            raise CleanupError(
                "Failed to cleanup old metrics",
                retention_period=retention_days,
                original_error=e
            )
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """
        Get system health and performance metrics.
        
        Returns:
            Dict[str, Any]: System health metrics
            
        Raises:
            MetricsError: When unable to collect system metrics
        """
        try:
            # Collect current system metrics
            current_metrics = self._collect_current_system_metrics()
            
            # Load cached system health data
            data = self.load_data()
            
            # Update cached health data
            if "system_health" not in data:
                data["system_health"] = {}
            
            data["system_health"].update(current_metrics)
            data["system_health"]["last_updated"] = datetime.now().isoformat()
            
            # Get operation rates from recent metrics
            recent_metrics = self.get_metrics(limit=100)
            operation_rates = self._calculate_operation_rates(recent_metrics)
            data["system_health"]["operation_rates"] = operation_rates
            
            # Get error rates
            error_rates = self._calculate_error_rates(recent_metrics)
            data["system_health"]["error_rates"] = error_rates
            
            # Cache hit rates (if available from metrics)
            cache_hit_rates = self._calculate_cache_hit_rates(recent_metrics)
            data["system_health"]["cache_hit_rates"] = cache_hit_rates
            
            # Save updated health data
            self.save_data(data, "update_health")
            
            return data["system_health"]
            
        except Exception as e:
            raise MetricsError(
                "Failed to collect system health metrics",
                metric_type="system_health",
                original_error=e
            )
    
    def _collect_current_system_metrics(self) -> Dict[str, Any]:
        """Collect current system performance metrics."""
        try:
            # Disk usage
            disk_usage = shutil.disk_usage(self.data_file.parent)
            disk_stats = {
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "usage_percent": (disk_usage.used / disk_usage.total) * 100
            }
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_stats = {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "usage_percent": memory.percent
            }
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            return {
                "disk_usage": disk_stats,
                "memory_usage": memory_stats,
                "cpu_usage_percent": cpu_percent,
                "cpu_count": cpu_count,
                "collected_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return {
                "disk_usage": {},
                "memory_usage": {},
                "cpu_usage_percent": 0.0,
                "cpu_count": 0,
                "collected_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _calculate_operation_rates(self, metrics: List[MetricsData]) -> Dict[str, float]:
        """Calculate operation rates from recent metrics."""
        if not metrics:
            return {}
        
        operation_counts = {}
        time_window = 3600  # 1 hour in seconds
        
        for metric in metrics:
            op_type = metric.operation_type
            if op_type not in operation_counts:
                operation_counts[op_type] = 0
            operation_counts[op_type] += 1
        
        # Convert to operations per hour
        operation_rates = {
            op_type: (count / len(metrics)) * time_window
            for op_type, count in operation_counts.items()
        }
        
        return operation_rates
    
    def _calculate_error_rates(self, metrics: List[MetricsData]) -> Dict[str, float]:
        """Calculate error rates from recent metrics."""
        if not metrics:
            return {}
        
        error_counts = {}
        total_operations = {}
        
        for metric in metrics:
            op_type = metric.operation_type
            
            if op_type not in total_operations:
                total_operations[op_type] = 0
                error_counts[op_type] = 0
            
            total_operations[op_type] += 1
            
            # Count errors based on success rate
            if metric.success_rate < 1.0:
                error_counts[op_type] += (1.0 - metric.success_rate)
        
        # Calculate error rates
        error_rates = {}
        for op_type in total_operations:
            if total_operations[op_type] > 0:
                error_rates[op_type] = (error_counts[op_type] / total_operations[op_type]) * 100
            else:
                error_rates[op_type] = 0.0
        
        return error_rates
    
    def _calculate_cache_hit_rates(self, metrics: List[MetricsData]) -> Dict[str, float]:
        """Calculate cache hit rates from recent metrics."""
        cache_metrics = [m for m in metrics if "cache" in m.operation_type.lower()]
        
        if not cache_metrics:
            return {}
        
        # This is a simplified calculation - real implementation would depend
        # on specific cache metrics being recorded
        cache_operations = len(cache_metrics)
        successful_operations = sum(1 for m in cache_metrics if m.success_rate > 0.9)
        
        hit_rate = (successful_operations / cache_operations) * 100 if cache_operations > 0 else 0.0
        
        return {
            "overall_hit_rate": hit_rate,
            "total_cache_operations": cache_operations,
            "successful_operations": successful_operations
        }