"""
NVIDIA shader cache provider.

Detects NVIDIA GPU shader cache locations on Windows.
"""

import platform
from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class NVIDIAProvider(BaseCacheProvider):
    """Provider for NVIDIA shader caches."""
    
    @property
    def name(self) -> str:
        return "nvidia"
    
    @property
    def display_name(self) -> str:
        return "NVIDIA"
    
    @property
    def priority(self) -> int:
        return 20
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.GPU_VENDOR
    
    def is_available(self) -> bool:
        """NVIDIA caches are only present on Windows."""
        return platform.system() == "Windows"
    
    def detect(self) -> List[CacheLocation]:
        """Detect NVIDIA shader cache locations."""
        if not self.is_available():
            return []
        
        home = Path.home()
        
        cache_paths = [
            (home / "AppData" / "Local" / "NVIDIA" / "DXCache", "DirectX Cache"),
            (home / "AppData" / "Local" / "NVIDIA" / "GLCache", "OpenGL Cache"),
            (home / "AppData" / "Local" / "NVIDIA Corporation" / "NV_Cache", "NV Cache"),
            (home / "AppData" / "Local" / "Temp" / "NVIDIA Corporation" / "NV_Cache", "Temp NV Cache"),
        ]
        
        locations = self._check_paths(cache_paths)
        
        if locations:
            self.logger.info(f"Found {len(locations)} NVIDIA cache locations")
        
        return locations
