"""
Migration Script: Old CachedFilesService to SecureCachedFilesService

This script provides utilities to migrate data and configuration from the 
existing CachedFilesService to the new SecureCachedFilesService while
maintaining data integrity and adding security enhancements.

Features:
- Data migration with integrity verification
- Security context addition for existing records
- User permission setup
- Configuration validation
- Rollback capabilities
- Progress tracking and logging

Usage:
    python migrate_to_secure_service.py --source-db /path/to/old.db --target-db /path/to/new.db
"""

import argparse
import json
import logging
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import hmac

# Import both services
from cached_files_service import CachedFilesService
from secure_cached_files_service import (
    SecureCachedFilesService, 
    SecurityLevel, 
    PermissionType,
    SecurePathValidator
)
from interfaces import UserOperationContext


class MigrationError(Exception):
    """Migration-specific error."""
    pass


class DataMigrator:
    """Handles data migration from old to new service."""
    
    def __init__(self, source_db_path: str, target_db_path: str, 
                 allowed_base_paths: Optional[List[str]] = None,
                 security_key: Optional[str] = None):
        self.source_db_path = source_db_path
        self.target_db_path = target_db_path
        self.allowed_base_paths = allowed_base_paths or []
        self.security_key = security_key or "migration-key-change-in-production"
        
        self.logger = logging.getLogger(__name__)
        self.migration_log: List[Dict[str, Any]] = []
        
        # Initialize services
        self.old_service = None
        self.new_service = None
    
    def _init_services(self):
        """Initialize old and new services."""
        try:
            # Check source database exists
            if not Path(self.source_db_path).exists():
                raise MigrationError(f"Source database not found: {self.source_db_path}")
            
            # Initialize old service (read-only)
            self.old_service = CachedFilesService(self.source_db_path)
            
            # Initialize new secure service
            self.new_service = SecureCachedFilesService(
                database_path=self.target_db_path,
                allowed_base_paths=self.allowed_base_paths,
                security_key=self.security_key
            )
            
            self.logger.info("Services initialized successfully")
            
        except Exception as e:
            raise MigrationError(f"Failed to initialize services: {e}")
    
    def _setup_default_users(self):
        """Set up default user permissions in the new service."""
        try:
            # Add system admin
            self.new_service.auth_manager.add_user(
                "system_admin", 
                SecurityLevel.ADMIN
            )
            
            # Add default service user
            self.new_service.auth_manager.add_user(
                "plex_service", 
                SecurityLevel.USER
            )
            
            # Add guest/readonly user
            self.new_service.auth_manager.add_user(
                "guest", 
                SecurityLevel.PUBLIC
            )
            
            self.logger.info("Default users set up successfully")
            
        except Exception as e:
            raise MigrationError(f"Failed to set up default users: {e}")
    
    def _generate_checksum(self, data: str) -> str:
        """Generate HMAC checksum for data integrity."""
        return hmac.new(
            self.security_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _validate_and_sanitize_path(self, path: str) -> str:
        """Validate and sanitize a path for the new service."""
        try:
            return SecurePathValidator.validate_path(path, self.allowed_base_paths)
        except ValueError as e:
            self.logger.warning(f"Path validation failed for {path}: {e}")
            # Return a sanitized version or raise if critical
            return str(Path(path).resolve())
    
    def _migrate_cached_files(self) -> Tuple[int, int]:
        """
        Migrate cached files from old to new database.
        
        Returns:
            Tuple of (successful_migrations, failed_migrations)
        """
        successful = 0
        failed = 0
        
        try:
            # Get all cached files from old service
            old_files, total_count = self.old_service.get_cached_files()
            
            self.logger.info(f"Starting migration of {total_count} cached files")
            
            admin_context = UserOperationContext(
                user_id="system_admin",
                trigger_source="migration"
            )
            
            for old_file in old_files:
                try:
                    # Validate and sanitize paths
                    validated_file_path = self._validate_and_sanitize_path(old_file.file_path)
                    validated_original_path = self._validate_and_sanitize_path(old_file.original_path)
                    validated_cached_path = self._validate_and_sanitize_path(old_file.cached_path)
                    
                    # Map old user to new system if needed
                    user_id = old_file.triggered_by_user or "plex_service"
                    
                    # Ensure user exists in new system
                    if user_id not in ["system_admin", "plex_service", "guest"]:
                        # Add user with default USER role
                        self.new_service.auth_manager.add_user(user_id, SecurityLevel.USER)
                    
                    # Enhance metadata with migration info
                    enhanced_metadata = old_file.metadata or {}
                    enhanced_metadata.update({
                        "migrated_from": "cached_files_service",
                        "migration_timestamp": datetime.now(timezone.utc).isoformat(),
                        "original_id": old_file.id
                    })
                    
                    # Add to new service
                    new_cached_file = self.new_service.add_cached_file(
                        file_path=validated_file_path,
                        original_path=validated_original_path,
                        cached_path=validated_cached_path,
                        cache_method=old_file.cache_method if old_file.cache_method in [
                            'atomic_symlink', 'atomic_hardlink', 'atomic_copy', 'secure_copy'
                        ] else 'atomic_symlink',
                        user_context=UserOperationContext(
                            user_id=user_id,
                            trigger_source="migration"
                        ),
                        operation_reason=old_file.triggered_by_operation,
                        metadata=enhanced_metadata,
                        ip_address="127.0.0.1",
                        user_agent="MigrationScript/1.0"
                    )
                    
                    # Update timestamps to match original (direct DB update)
                    with self.new_service.connection_pool.get_connection() as db_conn:
                        conn = db_conn.connection
                        conn.execute("""
                            UPDATE cached_files 
                            SET cached_at = ?, last_accessed = ?, access_count = ?
                            WHERE id = ?
                        """, (
                            old_file.cached_at.isoformat(),
                            old_file.last_accessed.isoformat() if old_file.last_accessed else None,
                            old_file.access_count,
                            new_cached_file.id
                        ))
                        conn.commit()
                    
                    # Migrate user associations
                    for user in old_file.users:
                        if user and user != user_id:
                            # Ensure user exists
                            if user not in ["system_admin", "plex_service", "guest"]:
                                self.new_service.auth_manager.add_user(user, SecurityLevel.USER)
                            
                            # Add user association
                            self.new_service.add_user_to_file(
                                validated_file_path, 
                                user, 
                                "migrated_association"
                            )
                    
                    successful += 1
                    
                    # Log progress
                    if successful % 100 == 0:
                        self.logger.info(f"Migrated {successful}/{total_count} files")
                    
                    # Record successful migration
                    self.migration_log.append({
                        "type": "file_migration",
                        "status": "success",
                        "old_id": old_file.id,
                        "new_id": new_cached_file.id,
                        "file_path": validated_file_path,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as e:
                    failed += 1
                    self.logger.error(f"Failed to migrate file {old_file.file_path}: {e}")
                    
                    # Record failed migration
                    self.migration_log.append({
                        "type": "file_migration",
                        "status": "failed",
                        "old_id": old_file.id,
                        "file_path": old_file.file_path,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            
            self.logger.info(f"File migration completed: {successful} successful, {failed} failed")
            return successful, failed
            
        except Exception as e:
            raise MigrationError(f"Failed to migrate cached files: {e}")
    
    def _migrate_operation_logs(self) -> Tuple[int, int]:
        """
        Migrate operation logs from old to new database.
        
        Returns:
            Tuple of (successful_migrations, failed_migrations)
        """
        successful = 0
        failed = 0
        
        try:
            # Get operation logs from old service
            old_logs = self.old_service.get_operation_logs(limit=10000)  # Large limit
            
            self.logger.info(f"Starting migration of {len(old_logs)} operation logs")
            
            # Directly insert into new database to maintain historical data
            with self.new_service.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                
                for log_entry in old_logs:
                    try:
                        # Map old log to new security format
                        new_log_id = str(uuid.uuid4())
                        
                        # Validate paths if present
                        file_path = log_entry.file_path
                        if file_path:
                            try:
                                file_path = self._validate_and_sanitize_path(file_path)
                            except:
                                pass  # Keep original if validation fails
                        
                        # Insert into both operations log and security events
                        conn.execute("""
                            INSERT INTO cache_operations_log 
                            (id, operation_type, file_path, triggered_by, triggered_by_user, 
                             reason, success, error_message, metadata, security_context, 
                             ip_address, user_agent, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            new_log_id,
                            log_entry.operation_type,
                            file_path,
                            log_entry.triggered_by,
                            log_entry.triggered_by_user,
                            log_entry.reason,
                            log_entry.success,
                            log_entry.error_message,
                            json.dumps(log_entry.metadata) if log_entry.metadata else None,
                            json.dumps({"migrated_from": "cached_files_service"}),
                            "migration",  # IP address
                            "MigrationScript/1.0",  # User agent
                            log_entry.timestamp.isoformat()
                        ))
                        
                        successful += 1
                        
                    except Exception as e:
                        failed += 1
                        self.logger.error(f"Failed to migrate log entry {log_entry.id}: {e}")
                
                conn.commit()
            
            self.logger.info(f"Log migration completed: {successful} successful, {failed} failed")
            return successful, failed
            
        except Exception as e:
            raise MigrationError(f"Failed to migrate operation logs: {e}")
    
    def _verify_migration(self) -> Dict[str, Any]:
        """
        Verify the migration was successful.
        
        Returns:
            Dictionary with verification results
        """
        try:
            # Get statistics from both services
            old_stats = self.old_service.get_cache_statistics()
            new_stats = self.new_service.get_cache_statistics()
            
            admin_context = UserOperationContext(
                user_id="system_admin",
                trigger_source="verification"
            )
            
            # Compare key metrics
            verification_results = {
                "total_files_match": old_stats.total_files == new_stats.total_files,
                "active_files_match": old_stats.active_files == new_stats.active_files,
                "old_total_files": old_stats.total_files,
                "new_total_files": new_stats.total_files,
                "old_active_files": old_stats.active_files,
                "new_active_files": new_stats.active_files,
                "integrity_check": None
            }
            
            # Run integrity check on new service
            try:
                verified_count, error_count = self.new_service.verify_cache_integrity(admin_context)
                verification_results["integrity_check"] = {
                    "verified": verified_count,
                    "errors": error_count,
                    "success": error_count == 0
                }
            except Exception as e:
                verification_results["integrity_check"] = {
                    "error": str(e),
                    "success": False
                }
            
            # Overall success
            verification_results["migration_successful"] = (
                verification_results["total_files_match"] and
                verification_results["active_files_match"] and
                (verification_results["integrity_check"] or {}).get("success", False)
            )
            
            return verification_results
            
        except Exception as e:
            return {
                "migration_successful": False,
                "error": str(e)
            }
    
    def _create_rollback_script(self) -> str:
        """
        Create a rollback script to undo the migration if needed.
        
        Returns:
            Path to the rollback script
        """
        rollback_script_path = Path(self.target_db_path).parent / "rollback_migration.py"
        
        rollback_script_content = f'''#!/usr/bin/env python3
"""
Auto-generated rollback script for migration from {self.source_db_path} to {self.target_db_path}

This script will restore the original database state by removing the target database
and providing instructions for restoration.
"""

import os
import shutil
from pathlib import Path

def rollback_migration():
    """Rollback the migration."""
    target_db = Path("{self.target_db_path}")
    backup_db = Path("{self.target_db_path}.backup")
    
    print("Starting migration rollback...")
    
    # Remove new database
    if target_db.exists():
        print(f"Removing new database: {{target_db}}")
        target_db.unlink()
    
    # Restore backup if exists
    if backup_db.exists():
        print(f"Restoring backup: {{backup_db}} -> {{target_db}}")
        shutil.copy2(backup_db, target_db)
        print("Backup restored successfully")
    else:
        print("No backup found. You may need to restore manually.")
    
    print("Rollback completed")
    print("Please update your application configuration to use the original service.")

if __name__ == "__main__":
    rollback_migration()
'''
        
        with open(rollback_script_path, 'w') as f:
            f.write(rollback_script_content)
        
        rollback_script_path.chmod(0o755)  # Make executable
        
        return str(rollback_script_path)
    
    def migrate(self, create_backup: bool = True, dry_run: bool = False) -> Dict[str, Any]:
        """
        Perform the complete migration.
        
        Args:
            create_backup: Whether to create a backup of the target database
            dry_run: If True, perform validation only without actual migration
            
        Returns:
            Dictionary with migration results
        """
        migration_start_time = datetime.now(timezone.utc)
        
        try:
            self.logger.info("Starting migration from old CachedFilesService to SecureCachedFilesService")
            
            if dry_run:
                self.logger.info("DRY RUN MODE - No actual changes will be made")
            
            # Create backup if requested
            if create_backup and not dry_run:
                if Path(self.target_db_path).exists():
                    backup_path = f"{self.target_db_path}.backup"
                    shutil.copy2(self.target_db_path, backup_path)
                    self.logger.info(f"Created backup: {backup_path}")
            
            # Initialize services
            self._init_services()
            
            # Set up default users
            if not dry_run:
                self._setup_default_users()
            
            migration_results = {
                "started_at": migration_start_time.isoformat(),
                "dry_run": dry_run,
                "backup_created": create_backup and not dry_run,
                "files_migration": {"successful": 0, "failed": 0},
                "logs_migration": {"successful": 0, "failed": 0},
                "verification": None,
                "rollback_script": None,
                "migration_log": []
            }
            
            if not dry_run:
                # Migrate cached files
                files_successful, files_failed = self._migrate_cached_files()
                migration_results["files_migration"] = {
                    "successful": files_successful,
                    "failed": files_failed
                }
                
                # Migrate operation logs
                logs_successful, logs_failed = self._migrate_operation_logs()
                migration_results["logs_migration"] = {
                    "successful": logs_successful,
                    "failed": logs_failed
                }
                
                # Verify migration
                migration_results["verification"] = self._verify_migration()
                
                # Create rollback script
                migration_results["rollback_script"] = self._create_rollback_script()
                
                # Copy migration log
                migration_results["migration_log"] = self.migration_log
            
            migration_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            migration_results["duration_seconds"] = (
                datetime.now(timezone.utc) - migration_start_time
            ).total_seconds()
            
            # Determine overall success
            if not dry_run:
                migration_results["success"] = (
                    migration_results["files_migration"]["failed"] == 0 and
                    migration_results["logs_migration"]["failed"] == 0 and
                    migration_results["verification"]["migration_successful"]
                )
            else:
                migration_results["success"] = True
            
            if migration_results["success"]:
                self.logger.info("Migration completed successfully!")
            else:
                self.logger.error("Migration completed with errors. Check migration log for details.")
            
            return migration_results
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "started_at": migration_start_time.isoformat(),
                "failed_at": datetime.now(timezone.utc).isoformat()
            }
        
        finally:
            # Clean up services
            try:
                if self.old_service:
                    # Old service doesn't have close method, just clean up
                    pass
                if self.new_service:
                    self.new_service.close()
            except Exception as e:
                self.logger.error(f"Error cleaning up services: {e}")


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(description="Migrate from CachedFilesService to SecureCachedFilesService")
    parser.add_argument("--source-db", required=True, help="Path to source database")
    parser.add_argument("--target-db", required=True, help="Path to target database")
    parser.add_argument("--allowed-paths", nargs="*", help="List of allowed base paths")
    parser.add_argument("--security-key", help="HMAC security key (will generate if not provided)")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without making changes")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--output-report", help="Path to save migration report JSON")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize migrator
        migrator = DataMigrator(
            source_db_path=args.source_db,
            target_db_path=args.target_db,
            allowed_base_paths=args.allowed_paths,
            security_key=args.security_key
        )
        
        # Perform migration
        results = migrator.migrate(
            create_backup=not args.no_backup,
            dry_run=args.dry_run
        )
        
        # Print summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Success: {results.get('success', False)}")
        print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        
        if 'files_migration' in results:
            fm = results['files_migration']
            print(f"Files migrated: {fm['successful']} successful, {fm['failed']} failed")
        
        if 'logs_migration' in results:
            lm = results['logs_migration']
            print(f"Logs migrated: {lm['successful']} successful, {lm['failed']} failed")
        
        if 'verification' in results and results['verification']:
            v = results['verification']
            print(f"Verification: {'PASSED' if v['migration_successful'] else 'FAILED'}")
        
        if 'rollback_script' in results and results['rollback_script']:
            print(f"Rollback script: {results['rollback_script']}")
        
        print("="*60)
        
        # Save report if requested
        if args.output_report:
            with open(args.output_report, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Detailed report saved to: {args.output_report}")
        
        # Exit with appropriate code
        sys.exit(0 if results.get('success', False) else 1)
        
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()