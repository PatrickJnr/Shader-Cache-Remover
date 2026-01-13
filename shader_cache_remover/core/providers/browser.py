"""Browser WebGPU/shader cache provider."""

import os
from pathlib import Path
from typing import List

from shader_cache_remover.core.interfaces import CacheLocation, CacheType
from shader_cache_remover.core.providers.base import BaseCacheProvider


class BrowserCacheProvider(BaseCacheProvider):
    """Detects browser WebGPU and shader cache locations."""

    @property
    def name(self) -> str:
        return "browser"

    @property
    def display_name(self) -> str:
        return "Browser Cache"

    @property
    def priority(self) -> int:
        return 150  # Lower priority - browsers usually manage their own cache

    @property
    def cache_type(self) -> CacheType:
        return CacheType.SYSTEM

    def is_available(self) -> bool:
        """Check if browser cache detection is available."""
        import os
        return os.name == "nt"  # Windows only for now

    def detect(self) -> List[CacheLocation]:
        """Detect browser shader/GPU cache directories."""
        locations = []

        # Only check on Windows for now
        if os.name != "nt":
            return locations

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            return locations

        local = Path(local_app_data)

        # Chrome GPU cache
        chrome_paths = [
            local / "Google" / "Chrome" / "User Data" / "ShaderCache",
            local / "Google" / "Chrome" / "User Data" / "GpuCache",
            local / "Google" / "Chrome" / "User Data" / "Default" / "GPUCache",
        ]
        for path in chrome_paths:
            locations.extend(self._check_path(path, "Chrome GPU Cache"))

        # Microsoft Edge GPU cache
        edge_paths = [
            local / "Microsoft" / "Edge" / "User Data" / "ShaderCache",
            local / "Microsoft" / "Edge" / "User Data" / "GpuCache",
            local / "Microsoft" / "Edge" / "User Data" / "Default" / "GPUCache",
        ]
        for path in edge_paths:
            locations.extend(self._check_path(path, "Edge GPU Cache"))

        # Firefox shader cache (in profile folders)
        firefox_profiles = local / "Mozilla" / "Firefox" / "Profiles"
        if firefox_profiles.exists():
            for profile in firefox_profiles.iterdir():
                if profile.is_dir():
                    shader_cache = profile / "shader-cache"
                    locations.extend(self._check_path(shader_cache, f"Firefox Shader Cache ({profile.name})"))
                    
                    startup_cache = profile / "startupCache"
                    locations.extend(self._check_path(startup_cache, f"Firefox Startup Cache ({profile.name})"))

        # Brave GPU cache
        brave_paths = [
            local / "BraveSoftware" / "Brave-Browser" / "User Data" / "ShaderCache",
            local / "BraveSoftware" / "Brave-Browser" / "User Data" / "GpuCache",
        ]
        for path in brave_paths:
            locations.extend(self._check_path(path, "Brave GPU Cache"))

        # Opera GPU cache
        opera_paths = [
            local / "Opera Software" / "Opera Stable" / "ShaderCache",
            local / "Opera Software" / "Opera Stable" / "GPUCache",
        ]
        for path in opera_paths:
            locations.extend(self._check_path(path, "Opera GPU Cache"))

        if locations:
            self.logger.info(f"Found {len(locations)} browser cache locations")

        return locations
