"""
Detection service for finding shader cache directories.

This service handles the detection of shader cache directories using
a plugin-based provider system. Providers can be registered to detect
caches from various sources.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set, Dict

from .interfaces import CacheProvider, CacheLocation, CacheType, ProviderInfo
from .providers import (
    SteamProvider,
    NVIDIAProvider,
    AMDProvider,
    IntelProvider,
    UnrealEngineProvider,
    UnityProvider,
    SystemCacheProvider,
    CustomPathProvider,
    EpicGamesProvider,
    GOGProvider,
    EAProvider,
    BrowserCacheProvider,
)


class DetectionService:
    """
    Service for detecting shader cache directories via providers.
    
    This service manages a registry of cache detection providers and
    aggregates their results. Providers can be enabled/disabled and
    have configurable priorities.
    
    Usage:
        service = DetectionService()
        locations = service.get_all_cache_locations()
        
        # Disable a provider
        service.set_provider_enabled("nvidia", False)
        
        # Register a custom provider
        service.register_provider(my_custom_provider)
    """
    
    def __init__(self, config_manager=None, custom_paths: Optional[List[str]] = None):
        """
        Initialize the detection service.
        
        Args:
            config_manager: Optional config manager for persisting provider settings
            custom_paths: Optional list of custom paths to include in detection
        """
        self.logger = logging.getLogger(__name__)
        self._config_manager = config_manager
        self._providers: List[CacheProvider] = []
        self._disabled_providers: Set[str] = set()
        self._custom_provider: Optional[CustomPathProvider] = None
        
        # Register default providers
        self._register_default_providers(custom_paths)
        
        # Load disabled providers from config
        if config_manager:
            self._load_provider_settings()
    
    def _register_default_providers(self, custom_paths: Optional[List[str]] = None) -> None:
        """Register all default cache providers."""
        # GPU Vendor providers
        self.register_provider(NVIDIAProvider())
        self.register_provider(AMDProvider())
        self.register_provider(IntelProvider())
        
        # System caches
        self.register_provider(SystemCacheProvider())
        
        # Game platforms
        self.register_provider(SteamProvider())
        self.register_provider(EpicGamesProvider())
        self.register_provider(GOGProvider())
        self.register_provider(EAProvider())
        
        # Game engines
        self.register_provider(UnrealEngineProvider())
        self.register_provider(UnityProvider())
        
        # Browser caches (lower priority by default)
        self.register_provider(BrowserCacheProvider())
        
        # Custom paths (keep reference for updates)
        self._custom_provider = CustomPathProvider(custom_paths or [])
        self.register_provider(self._custom_provider)
    
    def _load_provider_settings(self) -> None:
        """Load provider settings from configuration."""
        if not self._config_manager:
            return
        
        disabled = self._config_manager.get_config_value("disabled_providers", [])
        self._disabled_providers = set(disabled)
    
    def _save_provider_settings(self) -> None:
        """Save provider settings to configuration."""
        if not self._config_manager:
            return
        
        self._config_manager.set_config_value(
            "disabled_providers", 
            list(self._disabled_providers)
        )
    
    def register_provider(self, provider: CacheProvider) -> None:
        """
        Register a cache provider.
        
        Args:
            provider: The provider to register
        """
        self._providers.append(provider)
        # Sort by priority (lower values first)
        self._providers.sort(key=lambda p: p.priority)
        self.logger.debug(f"Registered provider: {provider.name} (priority {provider.priority})")
    
    def unregister_provider(self, name: str) -> bool:
        """
        Unregister a provider by name.
        
        Args:
            name: Name of the provider to unregister
        
        Returns:
            True if provider was found and removed, False otherwise
        """
        initial_count = len(self._providers)
        self._providers = [p for p in self._providers if p.name != name]
        return len(self._providers) < initial_count
    
    def get_provider_info(self) -> List[ProviderInfo]:
        """
        Get information about all registered providers.
        
        Returns:
            List of ProviderInfo objects
        """
        return [
            ProviderInfo(
                name=p.name,
                display_name=p.display_name,
                priority=p.priority,
                cache_type=p.cache_type,
                is_available=p.is_available(),
                is_enabled=p.name not in self._disabled_providers
            )
            for p in self._providers
        ]
    
    def set_provider_enabled(self, name: str, enabled: bool) -> None:
        """
        Enable or disable a provider.
        
        Args:
            name: Name of the provider
            enabled: Whether to enable the provider
        """
        if enabled:
            self._disabled_providers.discard(name)
        else:
            self._disabled_providers.add(name)
        
        self._save_provider_settings()
        self.logger.info(f"Provider '{name}' {'enabled' if enabled else 'disabled'}")
    
    def is_provider_enabled(self, name: str) -> bool:
        """Check if a provider is enabled."""
        return name not in self._disabled_providers
    
    def set_custom_paths(self, paths: List[str]) -> None:
        """
        Update the custom paths for detection.
        
        Args:
            paths: List of custom path strings
        """
        if self._custom_provider:
            self._custom_provider.set_paths(paths)
    
    def get_all_cache_locations(self) -> List[CacheLocation]:
        """
        Get all cache locations from enabled providers.
        
        Returns:
            List of detected cache locations
        """
        locations: List[CacheLocation] = []
        seen_paths: Set[Path] = set()
        
        for provider in self._providers:
            # Skip disabled providers
            if provider.name in self._disabled_providers:
                self.logger.debug(f"Skipping disabled provider: {provider.name}")
                continue
            
            # Skip unavailable providers
            if not provider.is_available():
                self.logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue
            
            try:
                provider_locations = provider.detect()
                
                # Filter duplicates
                for loc in provider_locations:
                    resolved = loc.path.resolve()
                    if resolved not in seen_paths:
                        seen_paths.add(resolved)
                        locations.append(loc)
                
                self.logger.debug(
                    f"Provider '{provider.name}' found {len(provider_locations)} locations"
                )
            
            except Exception as e:
                self.logger.error(f"Provider '{provider.name}' failed: {e}")
        
        self.logger.info(f"Total cache locations found: {len(locations)}")
        return locations
    
    def get_locations_by_type(self, cache_type: CacheType) -> List[CacheLocation]:
        """
        Get cache locations filtered by type.
        
        Args:
            cache_type: The type of cache to filter for
        
        Returns:
            List of cache locations of the specified type
        """
        all_locations = self.get_all_cache_locations()
        return [loc for loc in all_locations if loc.cache_type == cache_type]
    
    # Legacy compatibility methods
    
    def get_all_drives(self) -> List[Path]:
        """
        Detect all available drives on the system.
        
        Returns:
            List of Path objects representing available drives
            
        Note: This is a legacy method for backward compatibility.
        """
        import platform
        drives = []
        if platform.system() == "Windows":
            import string
            for drive_letter in string.ascii_uppercase:
                drive_path = Path(f"{drive_letter}:\\")
                if drive_path.is_dir():
                    drives.append(drive_path)
        else:
            drives.append(Path("/"))
        return drives
    
    def get_all_shader_cache_directories(self) -> List[Path]:
        """
        Get all shader cache directories as Path objects.
        
        Returns:
            List of Path objects for all detected cache directories
            
        Note: This is a legacy method for backward compatibility.
              New code should use get_all_cache_locations().
        """
        locations = self.get_all_cache_locations()
        return [loc.path for loc in locations]
    
    def get_common_shader_cache_directories(self) -> List[Path]:
        """
        Get common shader cache directories.
        
        Returns:
            List of Path objects for common cache locations
            
        Note: This is a legacy method for backward compatibility.
        """
        locations = self.get_all_cache_locations()
        return [
            loc.path for loc in locations 
            if loc.cache_type in (CacheType.GPU_VENDOR, CacheType.SYSTEM)
        ]
