"""Epic Games Launcher shader cache provider."""

import os
from pathlib import Path
from typing import List

from shader_cache_remover.core.interfaces import CacheLocation, CacheType
from shader_cache_remover.core.providers.base import BaseCacheProvider


class EpicGamesProvider(BaseCacheProvider):
    """Detects Epic Games Launcher cache locations."""

    @property
    def name(self) -> str:
        return "epic"

    @property
    def display_name(self) -> str:
        return "Epic Games"

    @property
    def priority(self) -> int:
        return 60

    @property
    def cache_type(self) -> CacheType:
        return CacheType.GAME_ENGINE

    def is_available(self) -> bool:
        """Check if Epic Games Launcher is available."""
        import os
        return os.name == "nt"  # Windows only

    def detect(self) -> List[CacheLocation]:
        """Detect Epic Games Launcher cache directories."""
        locations = []

        # Only check on Windows
        if os.name != "nt":
            return locations

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            return locations

        # Epic Games Launcher webcache
        webcache = Path(local_app_data) / "EpicGamesLauncher" / "Saved" / "webcache"
        locations.extend(self._check_path(webcache, "Epic Launcher Webcache"))

        # Epic Games Launcher shader cache
        shader_cache = Path(local_app_data) / "EpicGamesLauncher" / "Saved" / "PersistentDownloadDir"
        locations.extend(self._check_path(shader_cache, "Epic Launcher Downloads"))

        # DX Shader Cache for EGS
        dx_cache = Path(local_app_data) / "EpicGamesLauncher" / "Saved" / "Logs"
        # Only include if it contains shader-related files
        if dx_cache.exists():
            # Check for known cache patterns
            for pattern in ["*.dxcache", "*.shadercache"]:
                if list(dx_cache.glob(pattern)):
                    locations.extend(self._check_path(dx_cache, "Epic DX Cache"))
                    break

        if locations:
            self.logger.info(f"Found {len(locations)} Epic Games cache locations")

        return locations
