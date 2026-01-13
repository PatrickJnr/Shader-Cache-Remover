"""
Unity shader cache provider.

Detects Unity engine shader and asset cache locations.
"""

import platform
from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class UnityProvider(BaseCacheProvider):
    """Provider for Unity shader caches."""
    
    @property
    def name(self) -> str:
        return "unity"
    
    @property
    def display_name(self) -> str:
        return "Unity"
    
    @property
    def priority(self) -> int:
        return 101
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.GAME_ENGINE
    
    def is_available(self) -> bool:
        """Unity caches are present on Windows."""
        return platform.system() == "Windows"
    
    def detect(self) -> List[CacheLocation]:
        """Detect Unity shader cache locations."""
        if not self.is_available():
            return []
        
        home = Path.home()
        
        cache_paths = [
            (home / "AppData" / "LocalLow" / "Unity" / "Caches", "Shader Caches"),
            (home / "AppData" / "Local" / "Unity" / "cache", "Local Cache"),
            (home / "AppData" / "Local" / "Unity" / "Editor" / "ShaderCache", "Editor Shader Cache"),
        ]
        
        locations = self._check_paths(cache_paths)
        
        if locations:
            self.logger.info(f"Found {len(locations)} Unity cache locations")
        
        return locations
