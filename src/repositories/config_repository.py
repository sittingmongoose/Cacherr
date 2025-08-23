"""
Configuration repository implementation for PlexCacheUltra.

This module provides the ConfigFileRepository class that implements the
ConfigRepository interface using file-based JSON persistence. It manages
configuration settings with support for sections, history tracking, and
import/export functionality.

Key Features:
- File-based JSON persistence with atomic operations
- Section-based configuration organization
- Configuration history and audit trail
- Import/export functionality for configuration migration
- Thread-safe operations with proper locking
- Configuration validation and type checking
- Automatic backup and recovery capabilities
"""

from typing import List, Dict, Optional, Any, Type
from datetime import datetime
from pathlib import Path
import json
import logging

from pydantic import BaseModel, Field

from ..core.repositories import ConfigRepository, ConfigurationItem
from .base_repository import BaseFileRepository
from .exceptions import (
    EntryNotFoundError,
    ValidationError,
    ConfigurationError,
    ExportError,
    ImportError,
    wrap_repository_error
)

logger = logging.getLogger(__name__)


class ConfigData(BaseModel):
    """
    Root data model for configuration repository persistence.
    
    This model defines the structure of the configuration data file,
    containing all configuration sections and their history.
    """
    
    version: str = Field(default="1.0", description="Data format version")
    created_at: datetime = Field(default_factory=datetime.now, description="Repository creation time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last modification time")
    sections: Dict[str, Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Configuration sections with key-value pairs"
    )
    history: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Configuration change history indexed by section.key"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata and settings"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigFileRepository(BaseFileRepository[ConfigurationItem], ConfigRepository):
    """
    File-based implementation of ConfigRepository interface.
    
    This repository stores configuration settings in a JSON file with
    section-based organization, history tracking, and comprehensive
    import/export capabilities.
    
    Features:
    - JSON file-based persistence with atomic operations
    - Section-based configuration organization
    - Configuration history and audit trail tracking
    - Import/export functionality with validation
    - Thread-safe operations with file locking
    - Configuration validation and type checking
    - Automatic backup creation and cleanup
    - Search and filtering capabilities
    
    Configuration Structure:
    {
        "version": "1.0",
        "sections": {
            "database": {
                "host": {
                    "value": "localhost",
                    "last_updated": "2023-01-01T00:00:00",
                    "updated_by": "admin",
                    "is_persistent": true
                }
            }
        },
        "history": {
            "database.host": [
                {
                    "value": "old-host",
                    "last_updated": "2022-12-31T00:00:00",
                    "updated_by": "admin",
                    "is_persistent": true
                }
            ]
        }
    }
    
    Usage:
        config_repo = ConfigFileRepository(
            data_file=Path("/path/to/config_data.json"),
            auto_backup=True
        )
        
        # Set configuration
        config_item = ConfigurationItem(
            section="database",
            key="host",
            value="localhost",
            last_updated=datetime.now(),
            updated_by="admin"
        )
        config_repo.set_configuration(config_item)
        
        # Get configuration
        item = config_repo.get_configuration("database", "host")
        section_config = config_repo.get_section_configuration("database")
    """
    
    def __init__(
        self,
        data_file: Path,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        backup_retention_days: int = 30,
        max_history_entries: int = 50
    ):
        """
        Initialize configuration file repository.
        
        Args:
            data_file: Path to configuration data JSON file
            backup_dir: Directory for backup files
            auto_backup: Whether to automatically create backups
            backup_retention_days: Days to retain backup files
            max_history_entries: Maximum number of history entries per configuration item
        """
        self.max_history_entries = max_history_entries
        
        super().__init__(
            data_file=data_file,
            backup_dir=backup_dir,
            auto_backup=auto_backup,
            backup_retention_days=backup_retention_days,
            validate_on_load=True
        )
    
    def get_model_class(self) -> Type[ConfigurationItem]:
        """Get the Pydantic model class for configuration items."""
        return ConfigurationItem
    
    def get_default_data(self) -> Dict[str, Any]:
        """Get default data structure for new configuration files."""
        return ConfigData().model_dump()
    
    def _get_config_key(self, section: str, key: str) -> str:
        """Get the full configuration key for history tracking."""
        return f"{section}.{key}"
    
    def _item_to_dict(self, item: ConfigurationItem) -> Dict[str, Any]:
        """Convert ConfigurationItem to dictionary for storage."""
        return {
            "value": item.value,
            "last_updated": item.last_updated.isoformat(),
            "updated_by": item.updated_by,
            "is_persistent": item.is_persistent
        }
    
    def _dict_to_item(self, section: str, key: str, data: Dict[str, Any]) -> ConfigurationItem:
        """Convert dictionary to ConfigurationItem."""
        return ConfigurationItem(
            section=section,
            key=key,
            value=data["value"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
            updated_by=data.get("updated_by", "system"),
            is_persistent=data.get("is_persistent", True)
        )
    
    def _add_to_history(
        self,
        data: Dict[str, Any],
        section: str,
        key: str,
        old_item: Optional[ConfigurationItem]
    ) -> None:
        """
        Add configuration change to history.
        
        Args:
            data: Configuration data dictionary
            section: Configuration section
            key: Configuration key
            old_item: Previous configuration item (if any)
        """
        if old_item is None:
            return
        
        config_key = self._get_config_key(section, key)
        
        # Initialize history if needed
        if "history" not in data:
            data["history"] = {}
        
        if config_key not in data["history"]:
            data["history"][config_key] = []
        
        # Add old item to history
        history_entry = self._item_to_dict(old_item)
        data["history"][config_key].insert(0, history_entry)
        
        # Limit history size
        if len(data["history"][config_key]) > self.max_history_entries:
            data["history"][config_key] = data["history"][config_key][:self.max_history_entries]
    
    def get_configuration(self, section: str, key: str) -> Optional[ConfigurationItem]:
        """
        Retrieve a configuration item.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            
        Returns:
            Optional[ConfigurationItem]: ConfigurationItem if found, None otherwise
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            
            sections = data.get("sections", {})
            if section not in sections:
                return None
            
            section_data = sections[section]
            if key not in section_data:
                return None
            
            return self._dict_to_item(section, key, section_data[key])
            
        except Exception as e:
            raise wrap_repository_error(
                "configuration retrieval",
                e,
                {"section": section, "key": key}
            )
    
    def set_configuration(self, item: ConfigurationItem) -> bool:
        """
        Store a configuration item.
        
        Args:
            item: ConfigurationItem to store
            
        Returns:
            bool: True if storage successful
            
        Raises:
            ValidationError: When configuration item is invalid
            RepositoryError: When data access fails
        """
        try:
            # Validate the item
            item = ConfigurationItem.model_validate(item.model_dump())
            
            data = self.load_data()
            
            # Initialize sections if needed
            if "sections" not in data:
                data["sections"] = {}
            
            if item.section not in data["sections"]:
                data["sections"][item.section] = {}
            
            # Get old item for history
            old_item = None
            if item.key in data["sections"][item.section]:
                old_item = self._dict_to_item(
                    item.section,
                    item.key,
                    data["sections"][item.section][item.key]
                )
            
            # Store new item
            data["sections"][item.section][item.key] = self._item_to_dict(item)
            
            # Add to history
            self._add_to_history(data, item.section, item.key, old_item)
            
            # Update metadata
            data["last_updated"] = datetime.now().isoformat()
            
            # Save data
            self.save_data(data, "set_config")
            
            logger.info(f"Set configuration: {item.section}.{item.key}")
            return True
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise wrap_repository_error(
                "configuration storage",
                e,
                {"section": item.section, "key": item.key}
            )
    
    def get_section_configuration(self, section: str) -> Dict[str, Any]:
        """
        Retrieve all configuration items for a section.
        
        Args:
            section: Configuration section name
            
        Returns:
            Dict[str, Any]: Dictionary of key-value pairs for the section
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            sections = data.get("sections", {})
            
            if section not in sections:
                return {}
            
            # Extract values from section data
            section_config = {}
            for key, config_data in sections[section].items():
                section_config[key] = config_data["value"]
            
            return section_config
            
        except Exception as e:
            raise wrap_repository_error(
                "section configuration retrieval",
                e,
                {"section": section}
            )
    
    def update_configuration(
        self,
        section: str,
        key: str,
        value: Any,
        updated_by: str = "system"
    ) -> bool:
        """
        Update a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            value: New configuration value
            updated_by: Who/what updated the configuration
            
        Returns:
            bool: True if update successful
            
        Raises:
            ValidationError: When configuration value is invalid
            RepositoryError: When data access fails
        """
        try:
            # Get existing item or create new one
            existing_item = self.get_configuration(section, key)
            
            if existing_item:
                is_persistent = existing_item.is_persistent
            else:
                is_persistent = True
            
            # Create new configuration item
            new_item = ConfigurationItem(
                section=section,
                key=key,
                value=value,
                last_updated=datetime.now(),
                updated_by=updated_by,
                is_persistent=is_persistent
            )
            
            return self.set_configuration(new_item)
            
        except Exception as e:
            raise wrap_repository_error(
                "configuration update",
                e,
                {"section": section, "key": key, "updated_by": updated_by}
            )
    
    def delete_configuration(self, section: str, key: str) -> bool:
        """
        Delete a configuration item.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            
            sections = data.get("sections", {})
            if section not in sections:
                return False
            
            if key not in sections[section]:
                return False
            
            # Get item for history before deletion
            old_item = self._dict_to_item(section, key, sections[section][key])
            
            # Remove the item
            del sections[section][key]
            
            # Clean up empty section
            if not sections[section]:
                del sections[section]
            
            # Add deletion to history with special marker
            deletion_item = ConfigurationItem(
                section=section,
                key=key,
                value=None,
                last_updated=datetime.now(),
                updated_by="system",
                is_persistent=False
            )
            self._add_to_history(data, section, key, old_item)
            
            # Update metadata
            data["last_updated"] = datetime.now().isoformat()
            
            # Save data
            self.save_data(data, "delete_config")
            
            logger.info(f"Deleted configuration: {section}.{key}")
            return True
            
        except Exception as e:
            raise wrap_repository_error(
                "configuration deletion",
                e,
                {"section": section, "key": key}
            )
    
    def list_sections(self) -> List[str]:
        """
        List all configuration sections.
        
        Returns:
            List[str]: List of section names
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            sections = data.get("sections", {})
            return sorted(sections.keys())
            
        except Exception as e:
            raise wrap_repository_error(
                "section listing",
                e,
                {}
            )
    
    def export_configuration(self, file_path: Path) -> bool:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path where configuration should be exported
            
        Returns:
            bool: True if export successful
            
        Raises:
            ExportError: When export operation fails
        """
        try:
            data = self.load_data()
            
            # Create export structure with simplified format
            export_data = {
                "export_version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "source_version": data.get("version", "1.0"),
                "sections": {}
            }
            
            # Convert to simplified format for export
            sections = data.get("sections", {})
            for section_name, section_data in sections.items():
                export_data["sections"][section_name] = {}
                for key, config_data in section_data.items():
                    export_data["sections"][section_name][key] = {
                        "value": config_data["value"],
                        "updated_by": config_data.get("updated_by", "system"),
                        "is_persistent": config_data.get("is_persistent", True),
                        "last_updated": config_data["last_updated"]
                    }
            
            # Ensure export directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write export file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    export_data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    separators=(',', ': '),
                    sort_keys=True
                )
            
            logger.info(f"Exported configuration to: {file_path}")
            return True
            
        except Exception as e:
            raise ExportError(
                "Failed to export configuration",
                export_path=str(file_path),
                original_error=e
            )
    
    def import_configuration(self, file_path: Path, merge: bool = True) -> bool:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to configuration file
            merge: If True, merge with existing config; if False, replace
            
        Returns:
            bool: True if import successful
            
        Raises:
            ImportError: When import operation fails
            ValidationError: When imported configuration is invalid
        """
        try:
            if not file_path.exists():
                raise ImportError(
                    "Import file does not exist",
                    import_path=str(file_path)
                )
            
            # Read import file
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data structure
            if "sections" not in import_data:
                raise ImportError(
                    "Invalid import file format: missing 'sections'",
                    import_path=str(file_path)
                )
            
            # Get current data
            if merge:
                data = self.load_data()
            else:
                data = self.get_default_data()
            
            # Import configuration items
            imported_count = 0
            errors = []
            
            for section_name, section_data in import_data["sections"].items():
                for key, config_data in section_data.items():
                    try:
                        # Create configuration item
                        item = ConfigurationItem(
                            section=section_name,
                            key=key,
                            value=config_data["value"],
                            last_updated=datetime.fromisoformat(config_data["last_updated"]),
                            updated_by=config_data.get("updated_by", "import"),
                            is_persistent=config_data.get("is_persistent", True)
                        )
                        
                        # Store item (this will handle history automatically)
                        if self.set_configuration(item):
                            imported_count += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to import {section_name}.{key}: {e}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
            
            if errors and imported_count == 0:
                raise ImportError(
                    f"Import failed completely. Errors: {'; '.join(errors[:5])}",
                    import_path=str(file_path)
                )
            
            logger.info(f"Imported {imported_count} configuration items from: {file_path}")
            if errors:
                logger.warning(f"Import had {len(errors)} errors")
            
            return True
            
        except ImportError:
            raise  # Re-raise import errors
        except Exception as e:
            raise ImportError(
                "Failed to import configuration",
                import_path=str(file_path),
                original_error=e
            )
    
    def get_configuration_history(
        self,
        section: str,
        key: str,
        limit: int = 10
    ) -> List[ConfigurationItem]:
        """
        Get configuration change history.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            limit: Maximum number of history entries to return
            
        Returns:
            List[ConfigurationItem]: List of historical configuration items
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            history = data.get("history", {})
            
            config_key = self._get_config_key(section, key)
            if config_key not in history:
                return []
            
            # Convert history entries to ConfigurationItem objects
            history_items = []
            for history_entry in history[config_key][:limit]:
                try:
                    item = self._dict_to_item(section, key, history_entry)
                    history_items.append(item)
                except Exception as e:
                    logger.warning(f"Skipping invalid history entry: {e}")
            
            return history_items
            
        except Exception as e:
            raise wrap_repository_error(
                "configuration history retrieval",
                e,
                {"section": section, "key": key, "limit": limit}
            )
    
    def search_configurations(
        self,
        search_term: str,
        search_in_values: bool = True,
        search_in_keys: bool = True
    ) -> List[ConfigurationItem]:
        """
        Search for configuration items by term.
        
        Args:
            search_term: Term to search for
            search_in_values: Whether to search in configuration values
            search_in_keys: Whether to search in configuration keys
            
        Returns:
            List[ConfigurationItem]: Matching configuration items
        """
        try:
            data = self.load_data()
            sections = data.get("sections", {})
            results = []
            
            search_term_lower = search_term.lower()
            
            for section_name, section_data in sections.items():
                for key, config_data in section_data.items():
                    # Search in key
                    key_match = search_in_keys and search_term_lower in key.lower()
                    
                    # Search in value (convert to string for search)
                    value_str = str(config_data["value"]).lower()
                    value_match = search_in_values and search_term_lower in value_str
                    
                    if key_match or value_match:
                        try:
                            item = self._dict_to_item(section_name, key, config_data)
                            results.append(item)
                        except Exception as e:
                            logger.warning(f"Skipping invalid config item: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Configuration search failed: {e}")
            return []
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of configuration repository status.
        
        Returns:
            Dict[str, Any]: Configuration summary
        """
        try:
            data = self.load_data()
            sections = data.get("sections", {})
            history = data.get("history", {})
            
            # Count configurations
            total_configs = sum(len(section_data) for section_data in sections.values())
            section_count = len(sections)
            
            # History statistics
            total_history_entries = sum(len(entries) for entries in history.values())
            
            return {
                "total_sections": section_count,
                "total_configurations": total_configs,
                "total_history_entries": total_history_entries,
                "sections": list(sections.keys()),
                "last_updated": data.get("last_updated"),
                "version": data.get("version", "1.0")
            }
            
        except Exception as e:
            logger.error(f"Failed to get configuration summary: {e}")
            return {}
    
    def compact_history(self, max_entries_per_config: Optional[int] = None) -> int:
        """
        Compact configuration history by removing old entries.
        
        Args:
            max_entries_per_config: Maximum entries to keep per configuration
                                  (uses repository default if None)
            
        Returns:
            int: Number of history entries removed
        """
        if max_entries_per_config is None:
            max_entries_per_config = self.max_history_entries
        
        try:
            data = self.load_data()
            history = data.get("history", {})
            
            removed_count = 0
            
            for config_key, history_entries in history.items():
                if len(history_entries) > max_entries_per_config:
                    entries_to_remove = len(history_entries) - max_entries_per_config
                    history[config_key] = history_entries[:max_entries_per_config]
                    removed_count += entries_to_remove
            
            if removed_count > 0:
                # Update metadata
                data["last_updated"] = datetime.now().isoformat()
                
                # Save data
                self.save_data(data, "compact_history")
                
                logger.info(f"Compacted history: removed {removed_count} entries")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to compact history: {e}")
            return 0