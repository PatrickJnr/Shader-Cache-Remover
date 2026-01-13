"""GOG Galaxy cache provider."""

import os
from pathlib import Path
from typing import List

from shader_cache_remover.core.interfaces import CacheLocation, CacheType
from shader_cache_remover.core.providers.base import BaseCacheProvider


class GOGProvider(BaseCacheProvider):
    """Detects GOG Galaxy cache locations."""

    @property
    def name(self) -> str:
        return "gog"

    @property
    def display_name(self) -> str:
        return "GOG Galaxy"

    @property
    def priority(self) -> int:
        return 61

    @property
    def cache_type(self) -> CacheType:
        return CacheType.GAME_ENGINE

    def is_available(self) -> bool:
        """Check if GOG Galaxy is available."""
        import os
        return os.name == "nt"  # Windows only

    def detect(self) -> List[CacheLocation]:
        """Detect GOG Galaxy cache directories."""
        locations = []

        # Only check on Windows
        if os.name != "nt":
            return locations

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_data = os.environ.get("PROGRAMDATA", "")

        if local_app_data:
            # GOG Galaxy webcache
            webcache = Path(local_app_data) / "GOG.com" / "Galaxy" / "webcache"
            locations.extend(self._check_path(webcache, "GOG Galaxy Webcache"))

            # GOG Galaxy cache
            cache = Path(local_app_data) / "GOG.com" / "Galaxy" / "cache"
            locations.extend(self._check_path(cache, "GOG Galaxy Cache"))

            # Storage folder
            storage = Path(local_app_data) / "GOG.com" / "Galaxy" / "storage"
            locations.extend(self._check_path(storage, "GOG Galaxy Storage"))

        if program_data:
            # Shared cache in ProgramData
            shared = Path(program_data) / "GOG.com" / "Galaxy" / "webcache"
            locations.extend(self._check_path(shared, "GOG Shared Cache"))

        if locations:
            self.logger.info(f"Found {len(locations)} GOG Galaxy cache locations")

        return locations
