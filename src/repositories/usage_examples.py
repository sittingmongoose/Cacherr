"""
Repository system usage examples for PlexCacheUltra.

This module demonstrates how to use the repository pattern implementations
with the dependency injection system. It shows both direct usage and
integration with the DI container.

These examples are for documentation and testing purposes.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Example usage without DI container
def basic_repository_usage():
    """Demonstrate basic repository usage without DI container."""
    from .cache_repository import CacheFileRepository
    from .config_repository import ConfigFileRepository
    from .metrics_repository import MetricsFileRepository
    from ..core.repositories import CacheEntry, ConfigurationItem, MetricsData
    
    print("=== Basic Repository Usage Examples ===\n")
    
    # Cache Repository Example
    print("1. Cache Repository:")
    cache_repo = CacheFileRepository(
        data_file=Path("/tmp/cache_data.json"),
        auto_backup=True
    )
    
    # Add cache entry
    cache_entry = CacheEntry(
        file_path="/media/movies/example.mkv",
        cache_path="/cache/movies/example.mkv",
        original_size=1000000000,  # 1GB
        cached_at=datetime.now(),
        operation_type="move",
        checksum="abc123"
    )
    
    success = cache_repo.add_cache_entry(cache_entry)
    print(f"   Added cache entry: {success}")
    
    # Retrieve cache entry
    retrieved = cache_repo.get_cache_entry("/media/movies/example.mkv")
    print(f"   Retrieved entry: {retrieved.file_path if retrieved else 'None'}")
    
    # Get cache statistics
    stats = cache_repo.get_cache_statistics()
    print(f"   Cache statistics: {stats.get('total_entries', 0)} entries")
    
    print()
    
    # Config Repository Example  
    print("2. Config Repository:")
    config_repo = ConfigFileRepository(
        data_file=Path("/tmp/config_data.json"),
        auto_backup=True,
        max_history_entries=10
    )
    
    # Set configuration
    config_item = ConfigurationItem(
        section="plex",
        key="server_url",
        value="http://localhost:32400",
        last_updated=datetime.now(),
        updated_by="admin"
    )
    
    success = config_repo.set_configuration(config_item)
    print(f"   Set configuration: {success}")
    
    # Get configuration
    retrieved_config = config_repo.get_configuration("plex", "server_url")
    print(f"   Retrieved config: {retrieved_config.value if retrieved_config else 'None'}")
    
    # Get section configuration
    section_config = config_repo.get_section_configuration("plex")
    print(f"   Section config: {section_config}")
    
    print()
    
    # Metrics Repository Example
    print("3. Metrics Repository:")
    metrics_repo = MetricsFileRepository(
        data_file=Path("/tmp/metrics_data.json"),
        auto_backup=True,
        metrics_retention_days=30
    )
    
    # Record metric
    metric = MetricsData(
        timestamp=datetime.now(),
        operation_type="cache_move",
        files_processed=1,
        bytes_processed=1000000000,
        duration_seconds=45.5,
        success_rate=1.0,
        errors=[]
    )
    
    success = metrics_repo.record_metric(metric)
    print(f"   Recorded metric: {success}")
    
    # Get metrics
    recent_metrics = metrics_repo.get_metrics(limit=5)
    print(f"   Recent metrics: {len(recent_metrics)} entries")
    
    # Get aggregated metrics
    aggregated = metrics_repo.get_aggregated_metrics("cache_move", 24)
    print(f"   Aggregated metrics: {aggregated.get('total_operations', 0)} operations")
    
    print()


def dependency_injection_usage():
    """Demonstrate repository usage with DI container."""
    print("=== Dependency Injection Usage Examples ===\n")
    
    from ..core.container import DIContainer
    from ..config.interfaces import PathConfiguration, PathConfigurationModel
    from .service_registration import register_repository_services
    
    # Create a mock path configuration
    class MockPathConfiguration(PathConfiguration):
        def get_default_paths(self) -> PathConfigurationModel:
            return PathConfigurationModel(
                plex_source="/media",
                cache_destination="/cache"
            )
        
        # Implement required abstract methods (minimal)
        def validate_path(self, path, must_exist=True, must_be_writable=False, must_be_readable=True):
            return True
        def normalize_path(self, path):
            return Path(path)
        def resolve_relative_path(self, path, base=None):
            return Path(path)
        def create_directory_if_missing(self, path, parents=True):
            return True
        def get_available_space(self, path):
            return 1000000000
        def is_network_path(self, path):
            return False
        def is_same_filesystem(self, path1, path2):
            return True
        def get_mount_point(self, path):
            return Path("/")
        
        # Config provider methods (minimal implementation)
        def get_string(self, key, default=None, section=None):
            return default
        def get_int(self, key, default=None, section=None):
            return default
        def get_bool(self, key, default=None, section=None):
            return default
        def get_list(self, key, default=None, section=None, separator=","):
            return default
        def set_value(self, key, value, section=None, persist=False):
            return True
        def has_key(self, key, section=None):
            return False
        def get_all_keys(self, section=None):
            return []
        def reload(self):
            return True
        
        # Environment methods (minimal implementation)
        def detect_environment(self):
            return "development"
        def is_docker_environment(self):
            return False
        def is_development_environment(self):
            return True
        def get_platform_info(self):
            return {}
        def validate_environment_requirements(self):
            return {}
        def get_resource_limits(self):
            return {}
    
    # Create and configure container
    container = DIContainer()
    
    # Register path configuration
    container.register_singleton(PathConfiguration, MockPathConfiguration)
    
    # Register repository services
    registration = register_repository_services(container)
    
    print("1. Service Registration:")
    status = registration.get_registration_status()
    print(f"   Repository factory registered: {status['factory_registered']}")
    print(f"   Cache repository registered: {status['cache_repository_registered']}")
    print(f"   Config repository registered: {status['config_repository_registered']}")
    print(f"   Metrics repository registered: {status['metrics_repository_registered']}")
    print(f"   Total services: {status['total_repository_services']}")
    
    print()
    
    # Use repositories through DI
    print("2. Using Repositories via DI:")
    
    try:
        from ..core.repositories import CacheRepository, ConfigRepository, MetricsRepository
        
        # Get cache repository
        cache_repo = container.resolve(CacheRepository)
        print(f"   Resolved CacheRepository: {type(cache_repo).__name__}")
        
        # Get config repository  
        config_repo = container.resolve(ConfigRepository)
        print(f"   Resolved ConfigRepository: {type(config_repo).__name__}")
        
        # Get metrics repository
        metrics_repo = container.resolve(MetricsRepository)
        print(f"   Resolved MetricsRepository: {type(metrics_repo).__name__}")
        
        print("   All repositories resolved successfully!")
        
    except Exception as e:
        print(f"   Error resolving repositories: {e}")
    
    print()


def factory_pattern_usage():
    """Demonstrate repository factory pattern usage."""
    print("=== Factory Pattern Usage Examples ===\n")
    
    from ..config.interfaces import PathConfigurationModel
    from .factory import RepositoryFactory, RepositoryType, RepositoryConfig
    
    # Create a minimal path configuration
    class MinimalPathConfig:
        def get_default_paths(self) -> PathConfigurationModel:
            return PathConfigurationModel(
                plex_source="/media",
                cache_destination="/cache"
            )
    
    # Create factory
    factory = RepositoryFactory(MinimalPathConfig())
    
    print("1. Factory Creation:")
    print(f"   Factory initialized: {factory is not None}")
    
    # Get repository status
    status = factory.get_repository_status()
    print(f"   Default configurations available: {len(status['default_configurations'])}")
    
    print()
    
    # Create repositories using factory
    print("2. Creating Repositories:")
    
    try:
        # Create cache repository
        cache_repo = factory.get_or_create_repository(RepositoryType.CACHE)
        print(f"   Created cache repository: {type(cache_repo).__name__}")
        
        # Create config repository
        config_repo = factory.get_or_create_repository(RepositoryType.CONFIG)
        print(f"   Created config repository: {type(config_repo).__name__}")
        
        # Create metrics repository
        metrics_repo = factory.get_or_create_repository(RepositoryType.METRICS)
        print(f"   Created metrics repository: {type(metrics_repo).__name__}")
        
        print("   All repositories created successfully!")
        
        # Show cached repositories
        updated_status = factory.get_repository_status()
        print(f"   Cached repositories: {updated_status['cached_repositories']}")
        
    except Exception as e:
        print(f"   Error creating repositories: {e}")
    
    print()


def advanced_usage_examples():
    """Demonstrate advanced repository features."""
    print("=== Advanced Usage Examples ===\n")
    
    from .cache_repository import CacheFileRepository
    from .config_repository import ConfigFileRepository
    from ..core.repositories import CacheEntry, ConfigurationItem
    
    # Advanced cache repository features
    print("1. Advanced Cache Repository:")
    cache_repo = CacheFileRepository(
        data_file=Path("/tmp/advanced_cache.json"),
        auto_backup=True,
        backup_retention_days=7
    )
    
    # Add multiple entries
    for i in range(5):
        entry = CacheEntry(
            file_path=f"/media/movie_{i}.mkv",
            cache_path=f"/cache/movie_{i}.mkv",
            original_size=1000000 * (i + 1),
            cached_at=datetime.now() - timedelta(days=i),
            operation_type="copy" if i % 2 else "move",
            access_count=i * 2
        )
        cache_repo.add_cache_entry(entry)
    
    # Query with filters
    large_files = cache_repo.get_entries_by_size_range(min_size=2000000)
    print(f"   Large files (>2MB): {len(large_files)}")
    
    old_files = cache_repo.find_entries_by_age(max_age_hours=72)
    print(f"   Files older than 3 days: {len(old_files)}")
    
    move_operations = cache_repo.get_entries_by_operation_type("move")
    print(f"   Move operations: {len(move_operations)}")
    
    print()
    
    # Advanced config repository features
    print("2. Advanced Config Repository:")
    config_repo = ConfigFileRepository(
        data_file=Path("/tmp/advanced_config.json"),
        auto_backup=True,
        max_history_entries=5
    )
    
    # Set configurations in multiple sections
    sections = ["plex", "cache", "performance"]
    for section in sections:
        for i in range(3):
            config_item = ConfigurationItem(
                section=section,
                key=f"setting_{i}",
                value=f"value_{i}_{section}",
                last_updated=datetime.now(),
                updated_by="system"
            )
            config_repo.set_configuration(config_item)
    
    # List all sections
    all_sections = config_repo.list_sections()
    print(f"   Configuration sections: {all_sections}")
    
    # Search configurations
    search_results = config_repo.search_configurations("plex", search_in_values=True)
    print(f"   Search results for 'plex': {len(search_results)}")
    
    # Export configuration
    export_path = Path("/tmp/exported_config.json")
    success = config_repo.export_configuration(export_path)
    print(f"   Configuration exported: {success}")
    
    # Get configuration summary
    summary = config_repo.get_configuration_summary()
    print(f"   Config summary: {summary['total_configurations']} configs in {summary['total_sections']} sections")
    
    print()


if __name__ == "__main__":
    """Run all usage examples."""
    print("Repository System Usage Examples")
    print("=" * 50)
    print()
    
    try:
        basic_repository_usage()
        print("\n" + "=" * 50 + "\n")
        
        dependency_injection_usage()
        print("\n" + "=" * 50 + "\n")
        
        factory_pattern_usage()
        print("\n" + "=" * 50 + "\n")
        
        advanced_usage_examples()
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"\nExample execution failed: {e}")
        import traceback
        traceback.print_exc()