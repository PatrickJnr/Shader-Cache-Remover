"""
AMD shader cache provider.

Detects AMD GPU shader cache locations on Windows.
"""

import platform
from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class AMDProvider(BaseCacheProvider):
    """Provider for AMD shader caches."""
    
    @property
    def name(self) -> str:
        return "amd"
    
    @property
    def display_name(self) -> str:
        return "AMD"
    
    @property
    def priority(self) -> int:
        return 21
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.GPU_VENDOR
    
    def is_available(self) -> bool:
        """AMD caches are only present on Windows."""
        return platform.system() == "Windows"
    
    def detect(self) -> List[CacheLocation]:
        """Detect AMD shader cache locations."""
        if not self.is_available():
            return []
        
        home = Path.home()
        
        cache_paths = [
            (home / "AppData" / "Local" / "AMD" / "DxCache", "DirectX Cache"),
            (home / "AppData" / "Local" / "AMD" / "GLCache", "OpenGL Cache"),
            (home / "AppData" / "Local" / "AMD" / "VkCache", "Vulkan Cache"),
            (home / "AppData" / "Local" / "AMD" / "DxcCache", "DXC Cache"),
        ]
        
        locations = self._check_paths(cache_paths)
        
        if locations:
            self.logger.info(f"Found {len(locations)} AMD cache locations")
        
        return locations
