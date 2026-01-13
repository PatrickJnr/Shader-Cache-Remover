"""
Unreal Engine shader cache provider.

Detects Unreal Engine shader cache locations.
"""

import platform
from pathlib import Path
from typing import List

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider


class UnrealEngineProvider(BaseCacheProvider):
    """Provider for Unreal Engine shader caches."""
    
    @property
    def name(self) -> str:
        return "unreal"
    
    @property
    def display_name(self) -> str:
        return "Unreal Engine"
    
    @property
    def priority(self) -> int:
        return 100
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.GAME_ENGINE
    
    def is_available(self) -> bool:
        """Unreal caches are primarily on Windows."""
        return platform.system() == "Windows"
    
    def detect(self) -> List[CacheLocation]:
        """Detect Unreal Engine shader cache locations."""
        if not self.is_available():
            return []
        
        home = Path.home()
        locations = []
        
        # Main AppData location
        appdata_local = home / "AppData" / "Local"
        
        cache_paths = [
            (appdata_local / "UnrealEngine" / "ShaderCache", "Shader Cache"),
            (appdata_local / "UnrealEngineLauncher" / "Saved" / "Shaders", "Launcher Shaders"),
        ]
        
        locations.extend(self._check_paths(cache_paths))
        
        # Check for per-version Unreal Engine caches
        ue_versions_dir = appdata_local / "UnrealEngine"
        if ue_versions_dir.exists():
            for version_dir in ue_versions_dir.iterdir():
                if version_dir.is_dir():
                    shader_cache = version_dir / "Saved" / "ShaderCache"
                    if shader_cache.exists():
                        locations.append(CacheLocation(
                            path=shader_cache,
                            provider_name=self.name,
                            display_name=f"Unreal Engine - {version_dir.name}",
                            cache_type=self.cache_type,
                        ))
        
        if locations:
            self.logger.info(f"Found {len(locations)} Unreal Engine cache locations")
        
        return locations
