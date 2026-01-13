"""
Custom path provider.

Allows users to specify custom shader cache paths.
"""

from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class CustomPathProvider(BaseCacheProvider):
    """Provider for user-defined custom cache paths."""
    
    def __init__(self, custom_paths: List[str] = None):
        """
        Initialize with custom paths.
        
        Args:
            custom_paths: List of custom path strings from configuration.
        """
        super().__init__()
        self._custom_paths = custom_paths or []
    
    @property
    def name(self) -> str:
        return "custom"
    
    @property
    def display_name(self) -> str:
        return "Custom Paths"
    
    @property
    def priority(self) -> int:
        return 200  # Low priority - runs after all built-in providers
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.CUSTOM
    
    def is_available(self) -> bool:
        """Custom paths are always available."""
        return True
    
    def set_paths(self, paths: List[str]) -> None:
        """
        Update the custom paths.
        
        Args:
            paths: New list of custom path strings.
        """
        self._custom_paths = paths
    
    def detect(self) -> List[CacheLocation]:
        """Detect custom shader cache locations."""
        locations = []
        
        for path_str in self._custom_paths:
            try:
                path = Path(path_str)
                if path.is_dir():
                    locations.append(CacheLocation(
                        path=path,
                        provider_name=self.name,
                        display_name=f"Custom - {path.name}",
                        cache_type=self.cache_type,
                    ))
                    self.logger.info(f"Added custom path: {path}")
                else:
                    self.logger.warning(f"Custom path not found or not a directory: {path}")
            except Exception as e:
                self.logger.error(f"Error processing custom path '{path_str}': {e}")
        
        return locations
