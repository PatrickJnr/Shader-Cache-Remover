"""
Intel shader cache provider.

Detects Intel GPU shader cache locations on Windows.
"""

import platform
from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class IntelProvider(BaseCacheProvider):
    """Provider for Intel shader caches."""
    
    @property
    def name(self) -> str:
        return "intel"
    
    @property
    def display_name(self) -> str:
        return "Intel"
    
    @property
    def priority(self) -> int:
        return 22
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.GPU_VENDOR
    
    def is_available(self) -> bool:
        """Intel caches are only present on Windows."""
        return platform.system() == "Windows"
    
    def detect(self) -> List[CacheLocation]:
        """Detect Intel shader cache locations."""
        if not self.is_available():
            return []
        
        home = Path.home()
        
        cache_paths = [
            (home / "AppData" / "Local" / "Intel" / "ShaderCache", "Shader Cache"),
            (home / "AppData" / "LocalLow" / "Intel" / "ShaderCache", "Shader Cache (LocalLow)"),
        ]
        
        locations = self._check_paths(cache_paths)
        
        if locations:
            self.logger.info(f"Found {len(locations)} Intel cache locations")
        
        return locations
