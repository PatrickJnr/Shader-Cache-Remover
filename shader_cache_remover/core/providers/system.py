"""
System shader cache provider.

Detects Windows system-level DirectX and OpenGL shader caches.
"""

import platform
from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class SystemCacheProvider(BaseCacheProvider):
    """Provider for Windows system shader caches."""
    
    @property
    def name(self) -> str:
        return "system"
    
    @property
    def display_name(self) -> str:
        return "Windows System"
    
    @property
    def priority(self) -> int:
        return 10  # High priority - system caches are common
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.SYSTEM
    
    def is_available(self) -> bool:
        """System caches are only on Windows."""
        return platform.system() == "Windows"
    
    def detect(self) -> List[CacheLocation]:
        """Detect Windows system shader cache locations."""
        if not self.is_available():
            return []
        
        home = Path.home()
        temp_dir = home / "AppData" / "Local" / "Temp"
        
        cache_paths = [
            (temp_dir / "DXCache", "DirectX Cache"),
            (temp_dir / "D3DSCache", "Direct3D Shader Cache"),
            (temp_dir / "OpenGLCache", "OpenGL Cache"),
            (home / "AppData" / "Local" / "D3DSCache", "D3DS Cache (Local)"),
            (home / "AppData" / "LocalLow" / "Microsoft" / "DirectX Shader Compiler", "DXC"),
        ]
        
        locations = self._check_paths(cache_paths)
        
        if locations:
            self.logger.info(f"Found {len(locations)} system cache locations")
        
        return locations
