"""
Configuration Migration Script for Cacherr.

This script provides comprehensive migration functionality for transitioning
from legacy configuration systems to the modern Pydantic v2.5 configuration
architecture. It handles environment variables, persistent configuration,
and validation of migrated settings.

Usage:
    python -m src.config.migration_script --help

Author: Cacherr Development Team
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from pydantic import ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('config_migration.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


class MigrationResult(Enum):
    """Enumeration of migration operation results."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class MigrationStats:
    """Statistics for migration operations."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    skipped_operations: int = 0
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_operations == 0:
            return 100.0
        return (self.successful_operations / self.total_operations) * 100

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(message)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        logger.error(message)


class ConfigurationMigrator:
    """
    Comprehensive configuration migration system.

    This class handles migration from legacy configuration systems to the
    modern Pydantic v2.5 architecture, including environment variables,
    persistent configuration files, and validation.
    """

    # Environment variable migration mapping
    ENV_VAR_MIGRATION_MAP = {
        # Old pattern -> New pattern
        'PLEXCACHE_CONFIG_DIR': 'CACHERR_CONFIG_DIR',
        'PLEXCACHE_DATA_DIR': 'CACHERR_DATA_DIR',
        'PLEXCACHE_LOG_LEVEL': 'CACHERR_LOG_LEVEL',
        'PLEXCACHE_DEBUG': 'CACHERR_DEBUG',
        'PLEXCACHE_TEST_MODE': 'TEST_MODE',
        'PLEXCACHE_WEB_HOST': 'WEB_HOST',
        'PLEXCACHE_WEB_PORT': 'WEB_PORT',

        # Legacy patterns with various prefixes
        'PLEXCACHEULTRA_CONFIG_DIR': 'CACHERR_CONFIG_DIR',
        'PLEXCACHEULTRA_DATA_DIR': 'CACHERR_DATA_DIR',
        'PLEXCACHEULTRA_LOG_LEVEL': 'CACHERR_LOG_LEVEL',
        'PLEXCACHEULTRA_DEBUG': 'CACHERR_DEBUG',
        'PLEXCACHEULTRA_TEST_MODE': 'TEST_MODE',
        'PLEXCACHEULTRA_WEB_HOST': 'WEB_HOST',
        'PLEXCACHEULTRA_WEB_PORT': 'WEB_PORT',
    }

    # Configuration file paths to check for legacy files
    LEGACY_CONFIG_PATHS = [
        'config.json',
        'settings.json',
        'plexcache_config.json',
        'plexcacheultra_config.json',
        'old_settings.json',
        'new_settings.json'
    ]

    def __init__(self, config_dir: Optional[str] = None, dry_run: bool = False):
        """
        Initialize the configuration migrator.

        Args:
            config_dir: Configuration directory path (optional)
            dry_run: If True, only simulate migrations without making changes
        """
        self.config_dir = Path(config_dir or '/config')
        self.dry_run = dry_run
        self.stats = MigrationStats()

        logger.info(f"Initialized ConfigurationMigrator (dry_run={dry_run})")
        logger.info(f"Configuration directory: {self.config_dir}")

    def migrate_all(self) -> MigrationStats:
        """
        Execute complete configuration migration.

        Returns:
            MigrationStats: Detailed statistics and results of migration
        """
        logger.info("Starting comprehensive configuration migration")

        try:
            # Phase 1: Environment variables migration
            self._migrate_environment_variables()

            # Phase 2: Persistent configuration migration
            self._migrate_persistent_config()

            # Phase 3: Legacy files cleanup
            self._cleanup_legacy_files()

            # Phase 4: Validation and verification
            self._validate_migration()

            # Phase 5: Generate migration report
            self._generate_migration_report()

        except Exception as e:
            logger.error(f"Migration failed with error: {e}")
            self.stats.add_error(f"Migration failed: {e}")
            self.stats.failed_operations += 1

        # Calculate total operations at the end
        actual_total = (
            self.stats.successful_operations +
            self.stats.failed_operations +
            self.stats.skipped_operations
        )

        # Update total operations (ensure it's not zero for success rate calculation)
        self.stats.total_operations = max(actual_total, 1)

        logger.info(f"Migration completed with {self.stats.success_rate:.1f}% success rate")
        return self.stats

    def _migrate_environment_variables(self) -> None:
        """
        Migrate environment variables from old patterns to new patterns.
        """
        logger.info("Phase 1: Migrating environment variables")

        migrated_vars = []
        skipped_vars = []

        for old_var, new_var in self.ENV_VAR_MIGRATION_MAP.items():
            if old_var in os.environ:
                old_value = os.environ[old_var]

                if new_var not in os.environ:
                    # Migrate: set new variable and keep old for compatibility
                    if not self.dry_run:
                        os.environ[new_var] = old_value
                        logger.info(f"Migrated {old_var} -> {new_var} = {old_value}")
                    else:
                        logger.info(f"DRY RUN: Would migrate {old_var} -> {new_var} = {old_value}")

                    migrated_vars.append(f"{old_var} -> {new_var}")
                    self.stats.successful_operations += 1
                else:
                    # New variable already exists, skip migration
                    logger.info(f"Skipped {old_var} -> {new_var} (new variable already exists)")
                    skipped_vars.append(old_var)
                    self.stats.skipped_operations += 1

        if migrated_vars:
            logger.info(f"Successfully migrated {len(migrated_vars)} environment variables")
            for var in migrated_vars:
                logger.info(f"  ✓ {var}")

        if skipped_vars:
            logger.info(f"Skipped {len(skipped_vars)} environment variables (already exist)")
            for var in skipped_vars:
                logger.info(f"  - {var}")

    def _migrate_persistent_config(self) -> None:
        """
        Migrate persistent configuration files.
        """
        logger.info("Phase 2: Migrating persistent configuration")

        migrated_files = []
        config_files_found = []

        # Check for legacy configuration files
        for config_file in self.LEGACY_CONFIG_PATHS:
            config_path = self.config_dir / config_file
            if config_path.exists():
                config_files_found.append(config_path)
                logger.info(f"Found legacy configuration file: {config_path}")

        if not config_files_found:
            logger.info("No legacy configuration files found to migrate")
            self.stats.skipped_operations += 1
            return

        # Create new configuration file path
        new_config_file = self.config_dir / "cacherr_config.json"

        # Merge all legacy configuration files
        merged_config = {}
        validation_errors = []

        for config_file in config_files_found:
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)

                # Validate and transform legacy configuration
                transformed_config = self._transform_legacy_config(config_data, config_file.name)

                # Merge into combined configuration
                merged_config.update(transformed_config)

                logger.info(f"Successfully processed legacy config: {config_file}")
                migrated_files.append(str(config_file))

            except Exception as e:
                error_msg = f"Failed to process {config_file}: {e}"
                logger.error(error_msg)
                validation_errors.append(error_msg)
                self.stats.failed_operations += 1

        if validation_errors:
            self.stats.add_error(f"Configuration validation errors: {validation_errors}")

        # Write merged configuration if we have data and not in dry run
        if merged_config and not self.dry_run:
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                with open(new_config_file, 'w') as f:
                    json.dump(merged_config, f, indent=2)

                logger.info(f"Created new configuration file: {new_config_file}")
                self.stats.successful_operations += 1

            except Exception as e:
                error_msg = f"Failed to write new configuration file: {e}"
                logger.error(error_msg)
                self.stats.add_error(error_msg)
                self.stats.failed_operations += 1

        elif merged_config and self.dry_run:
            logger.info(f"DRY RUN: Would create {new_config_file} with {len(merged_config)} configuration sections")

        # Backup and optionally remove legacy files
        for config_file in config_files_found:
            if not self.dry_run:
                try:
                    backup_file = config_file.with_suffix('.backup')
                    config_file.rename(backup_file)
                    logger.info(f"Backed up legacy config: {config_file} -> {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to backup {config_file}: {e}")
            else:
                logger.info(f"DRY RUN: Would backup {config_file}")

        if migrated_files:
            logger.info(f"Successfully migrated {len(migrated_files)} configuration files")
            for file_path in migrated_files:
                logger.info(f"  ✓ {file_path}")

    def _transform_legacy_config(self, config_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Transform legacy configuration format to new format.

        Args:
            config_data: Legacy configuration data
            filename: Source filename for context

        Returns:
            Transformed configuration data
        """
        transformed = {}

        # Handle different legacy formats based on filename
        if 'plexcache' in filename.lower() or 'plexcacheultra' in filename.lower():
            transformed = self._transform_plexcache_config(config_data)
        elif 'old_settings' in filename.lower():
            transformed = self._transform_old_settings_config(config_data)
        elif 'new_settings' in filename.lower():
            transformed = self._transform_new_settings_config(config_data)
        else:
            # Generic transformation
            transformed = self._transform_generic_config(config_data)

        return transformed

    def _transform_plexcache_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform legacy PlexCache configuration."""
        transformed = {}

        # Transform Plex configuration
        if 'plex' in config_data:
            plex_config = config_data['plex']
            transformed['plex'] = {
                'url': plex_config.get('url', ''),
                'token': plex_config.get('token', ''),
                'timeout': plex_config.get('timeout', 30),
                'verify_ssl': plex_config.get('verify_ssl', True)
            }

        # Transform media configuration
        if 'media' in config_data:
            media_config = config_data['media']
            transformed['media'] = {
                'copy_to_cache': media_config.get('copy_to_cache', True),
                'delete_from_cache_when_done': media_config.get('delete_from_cache_when_done', True),
                'file_extensions': media_config.get('file_extensions', ['mp4', 'mkv', 'avi', 'mov'])
            }

        return transformed

    def _transform_old_settings_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform old settings format."""
        # This would handle the specific format of the old settings system
        # Implementation depends on the exact format of the old system
        return config_data  # Pass through for now

    def _transform_new_settings_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform new settings format (should be mostly compatible)."""
        return config_data

    def _transform_generic_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic transformation for unknown formats."""
        return config_data

    def _cleanup_legacy_files(self) -> None:
        """
        Clean up legacy configuration files that are no longer needed.
        """
        logger.info("Phase 3: Cleaning up legacy configuration files")

        # Files that should be removed after successful migration
        legacy_files_to_remove = [
            'old_settings.py',
            'old_settings.pyc',
            '__pycache__/old_settings.cpython-*.pyc'
        ]

        removed_files = []

        for legacy_file in legacy_files_to_remove:
            legacy_path = self.config_dir / legacy_file
            if legacy_path.exists():
                if not self.dry_run:
                    try:
                        if legacy_path.is_file():
                            legacy_path.unlink()
                        else:
                            # Handle glob patterns for __pycache__ files
                            for pyc_file in self.config_dir.glob(legacy_file):
                                pyc_file.unlink()
                        removed_files.append(str(legacy_path))
                        logger.info(f"Removed legacy file: {legacy_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {legacy_path}: {e}")
                else:
                    logger.info(f"DRY RUN: Would remove {legacy_path}")
                    removed_files.append(str(legacy_path))

        if removed_files:
            logger.info(f"Cleaned up {len(removed_files)} legacy files")
            for file_path in removed_files:
                logger.info(f"  ✓ {file_path}")
            self.stats.successful_operations += len(removed_files)
        else:
            logger.info("No legacy files found to clean up")
            self.stats.skipped_operations += 1

    def _validate_migration(self) -> None:
        """
        Validate that migration was successful and configuration is valid.
        """
        logger.info("Phase 4: Validating migration results")

        try:
            # Import the new configuration system
            from .settings import Config

            # Try to create a configuration instance
            config = Config()

            # Validate the configuration
            validation_result = config.validate_all()

            if validation_result['valid']:
                logger.info("✓ Configuration validation successful")
                logger.info(f"  Validated {len(validation_result['sections'])} configuration sections")
                self.stats.successful_operations += 1
            else:
                error_msg = f"Configuration validation failed: {validation_result['errors']}"
                logger.error(error_msg)
                self.stats.add_error(error_msg)
                self.stats.failed_operations += 1

        except ImportError as e:
            error_msg = f"Failed to import configuration system: {e}"
            logger.error(error_msg)
            self.stats.add_error(error_msg)
            self.stats.failed_operations += 1

        except ValidationError as e:
            error_msg = f"Configuration validation error: {e}"
            logger.error(error_msg)
            self.stats.add_error(error_msg)
            self.stats.failed_operations += 1

        except Exception as e:
            error_msg = f"Unexpected validation error: {e}"
            logger.error(error_msg)
            self.stats.add_error(error_msg)
            self.stats.failed_operations += 1

    def _generate_migration_report(self) -> None:
        """
        Generate a comprehensive migration report.
        """
        logger.info("Phase 5: Generating migration report")

        report_file = self.config_dir / "migration_report.json"

        report = {
            'migration_timestamp': str(Path(__file__).stat().st_mtime),
            'success_rate': self.stats.success_rate,
            'statistics': {
                'total_operations': self.stats.total_operations,
                'successful_operations': self.stats.successful_operations,
                'failed_operations': self.stats.failed_operations,
                'skipped_operations': self.stats.skipped_operations
            },
            'warnings': self.stats.warnings,
            'errors': self.stats.errors,
            'dry_run': self.dry_run,
            'migrated_environment_variables': [
                f"{old} -> {new}"
                for old, new in self.ENV_VAR_MIGRATION_MAP.items()
                if old in os.environ and new not in os.environ
            ],
            'configuration_status': 'validated' if self.stats.success_rate == 100.0 else 'needs_attention'
        }

        if not self.dry_run:
            try:
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"Migration report saved to: {report_file}")
                self.stats.successful_operations += 1
            except Exception as e:
                logger.error(f"Failed to save migration report: {e}")
                self.stats.failed_operations += 1
        else:
            logger.info("DRY RUN: Would save migration report")
            logger.info(f"Report contents: {json.dumps(report, indent=2)}")


def main():
    """Main entry point for the configuration migration script."""
    parser = argparse.ArgumentParser(
        description="Cacherr Configuration Migration Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.config.migration_script --dry-run
  python -m src.config.migration_script --config-dir /custom/config
  python -m src.config.migration_script --dry-run --verbose
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without making actual changes'
    )

    parser.add_argument(
        '--config-dir',
        type=str,
        default='/config',
        help='Configuration directory path (default: /config)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if validation fails'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("CACHERR CONFIGURATION MIGRATION SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Dry run mode: {args.dry_run}")
    logger.info(f"Configuration directory: {args.config_dir}")
    logger.info("")

    # Initialize migrator
    migrator = ConfigurationMigrator(
        config_dir=args.config_dir,
        dry_run=args.dry_run
    )

    # Execute migration
    stats = migrator.migrate_all()

    # Print final summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Success Rate: {stats.success_rate:.1f}%")
    print(f"Total Operations: {stats.total_operations}")
    print(f"Successful: {stats.successful_operations}")
    print(f"Failed: {stats.failed_operations}")
    print(f"Skipped: {stats.skipped_operations}")

    if stats.warnings:
        print(f"\nWarnings ({len(stats.warnings)}):")
        for warning in stats.warnings:
            print(f"  ⚠️  {warning}")

    if stats.errors:
        print(f"\nErrors ({len(stats.errors)}):")
        for error in stats.errors:
            print(f"  ❌ {error}")

    print("\n" + "=" * 60)

    # Exit with appropriate code
    if stats.success_rate == 100.0:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    elif stats.success_rate >= 80.0:
        print("⚠️  Migration completed with minor issues")
        sys.exit(0)
    else:
        print("❌ Migration failed or encountered significant issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
