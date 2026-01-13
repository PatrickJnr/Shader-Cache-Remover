"""EA App (formerly Origin) cache provider."""

import os
from pathlib import Path
from typing import List

from shader_cache_remover.core.interfaces import CacheLocation, CacheType
from shader_cache_remover.core.providers.base import BaseCacheProvider


class EAProvider(BaseCacheProvider):
    """Detects EA App and Origin cache locations."""

    @property
    def name(self) -> str:
        return "ea"

    @property
    def display_name(self) -> str:
        return "EA App"

    @property
    def priority(self) -> int:
        return 62

    @property
    def cache_type(self) -> CacheType:
        return CacheType.GAME_ENGINE

    def is_available(self) -> bool:
        """Check if EA App/Origin is available."""
        import os
        return os.name == "nt"  # Windows only

    def detect(self) -> List[CacheLocation]:
        """Detect EA App and Origin cache directories."""
        locations = []

        # Only check on Windows
        if os.name != "nt":
            return locations

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_data = os.environ.get("PROGRAMDATA", "")

        if local_app_data:
            local = Path(local_app_data)
            
            # EA App cache locations (actual shader/GPU caches only)
            ea_cache = local / "Electronic Arts" / "EA Desktop" / "cache"
            locations.extend(self._check_path(ea_cache, "EA Desktop Cache"))

            # Legacy Origin cache
            origin_cache = local / "Origin" / "cache"
            locations.extend(self._check_path(origin_cache, "Origin Cache"))

            # Origin ThinSetup contains download cache
            origin_dxcache = local / "Origin" / "ThinSetup"
            locations.extend(self._check_path(origin_dxcache, "Origin Setup Cache"))

        if program_data:
            pd = Path(program_data)
            
            # EA shared cache
            ea_shared = pd / "Electronic Arts" / "EA Desktop" / "cache"
            locations.extend(self._check_path(ea_shared, "EA Shared Cache"))

        if locations:
            self.logger.info(f"Found {len(locations)} EA/Origin cache locations")

        return locations

