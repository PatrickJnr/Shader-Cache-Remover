"""
Configuration manager for the Shader Cache Remover application.

This module handles loading, saving, and managing application configuration
settings from a JSON file in the user's home directory.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manager for application configuration settings."""

    # Configuration version - increment when making schema changes
    CONFIG_VERSION = 2

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the configuration manager.

        Args:
            config_path: Optional custom path for the config file.
                        If not provided, uses default location in home directory.
        """
        self.config_path = (
            config_path or Path.home() / ".shader_cache_remover_config.json"
        )
        self.logger = logging.getLogger(__name__)

        # Default configuration values
        self._default_config = {
            "_version": self.CONFIG_VERSION,
            "auto_backup": False,
            "backup_location": str(Path.home() / "ShaderCacheBackups"),
            "show_progress": True,
            "detailed_logging": True,
            "custom_paths": [],
            # New in v2: provider settings
            "disabled_providers": [],
            "provider_priorities": {},
        }

        self._config = None

    @property
    def config(self) -> Dict[str, Any]:
        """Get the current configuration, loading it if necessary.

        Returns:
            Current configuration dictionary
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary with defaults applied
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_config = self._default_config.copy()
                    merged_config.update(config)
                    # Apply migrations if needed
                    merged_config = self._migrate_config(merged_config)
                    self.logger.info(f"Configuration loaded from: {self.config_path}")
                    return merged_config
        except Exception as e:
            self.logger.warning(f"Could not load config from {self.config_path}: {e}")

        self.logger.info("Using default configuration.")
        return self._default_config.copy()

    def _migrate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply migrations for older config versions.
        
        Args:
            config: Current configuration dictionary
        
        Returns:
            Migrated configuration dictionary
        """
        version = config.get("_version", 1)
        
        if version < 2:
            # Migration from v1 to v2: add provider settings
            config["disabled_providers"] = config.get("disabled_providers", [])
            config["provider_priorities"] = config.get("provider_priorities", {})
            config["_version"] = 2
            self.logger.info("Migrated config from v1 to v2")
            # Save the migrated config
            self._config = config
            self.save_config()
        
        return config

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file.

        Args:
            config: Optional configuration to save. If not provided, saves current config.
        """
        if config is not None:
            self._config = config

        try:
            # Ensure the directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)

            self.logger.info(f"Configuration saved to: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Could not save config to {self.config_path}: {e}")
            raise

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.

        Args:
            updates: Dictionary of configuration keys to update
        """
        current_config = self.config
        current_config.update(updates)
        self.save_config(current_config)

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self._default_config.copy()
        self.save_config()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a specific configuration value.

        Args:
            key: Configuration key to set
            value: Value to set
        """
        self.update_config({key: value})

    def get_backup_location(self) -> Path:
        """Get the backup location as a Path object.

        Returns:
            Path object for the backup location
        """
        return Path(self.get_config_value("backup_location"))

    def set_backup_location(self, location: Path) -> None:
        """Set the backup location.

        Args:
            location: Path to the backup directory
        """
        self.set_config_value("backup_location", str(location))

    def get_custom_paths(self) -> list:
        """Get the list of custom shader cache paths.

        Returns:
            List of custom paths
        """
        return self.get_config_value("custom_paths", [])

    def add_custom_path(self, path: str) -> None:
        """Add a custom shader cache path.

        Args:
            path: Path to add to custom paths list
        """
        custom_paths = self.get_custom_paths()
        if path not in custom_paths:
            custom_paths.append(path)
            self.set_config_value("custom_paths", custom_paths)
            self.logger.info(f"Added custom path: {path}")

    def clear_custom_paths(self) -> None:
        """Clear all custom shader cache paths.

        This method removes all custom paths from the configuration.
        """
        self.set_config_value("custom_paths", [])
        self.logger.info("Cleared all custom paths")

    def is_auto_backup_enabled(self) -> bool:
        """Check if auto-backup is enabled.

        Returns:
            True if auto-backup is enabled, False otherwise
        """
        return self.get_config_value("auto_backup", False)

    def set_auto_backup(self, enabled: bool) -> None:
        """Enable or disable auto-backup.

        Args:
            enabled: Whether to enable auto-backup
        """
        self.set_config_value("auto_backup", enabled)

    def is_detailed_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled.

        Returns:
            True if detailed logging is enabled, False otherwise
        """
        return self.get_config_value("detailed_logging", True)

    def set_detailed_logging(self, enabled: bool) -> None:
        """Enable or disable detailed logging.

        Args:
            enabled: Whether to enable detailed logging
        """
        self.set_config_value("detailed_logging", enabled)

    def should_show_progress(self) -> bool:
        """Check if progress bar should be shown.

        Returns:
            True if progress should be shown, False otherwise
        """
        return self.get_config_value("show_progress", True)

    def set_show_progress(self, enabled: bool) -> None:
        """Set whether to show progress bar.

        Args:
            enabled: Whether to show progress bar
        """
        self.set_config_value("show_progress", enabled)

    def get_disabled_providers(self) -> list:
        """Get the list of disabled provider names.

        Returns:
            List of provider names that are disabled
        """
        return self.get_config_value("disabled_providers", [])

    def set_disabled_providers(self, providers: list) -> None:
        """Set the list of disabled providers.

        Args:
            providers: List of provider names to disable
        """
        self.set_config_value("disabled_providers", providers)

    def add_disabled_provider(self, provider_name: str) -> None:
        """Add a provider to the disabled list.

        Args:
            provider_name: Name of the provider to disable
        """
        disabled = self.get_disabled_providers()
        if provider_name not in disabled:
            disabled.append(provider_name)
            self.set_disabled_providers(disabled)

    def remove_disabled_provider(self, provider_name: str) -> None:
        """Remove a provider from the disabled list (enable it).

        Args:
            provider_name: Name of the provider to enable
        """
        disabled = self.get_disabled_providers()
        if provider_name in disabled:
            disabled.remove(provider_name)
            self.set_disabled_providers(disabled)

    def is_provider_disabled(self, provider_name: str) -> bool:
        """Check if a provider is disabled.

        Args:
            provider_name: Name of the provider to check

        Returns:
            True if provider is disabled, False otherwise
        """
        return provider_name in self.get_disabled_providers()

