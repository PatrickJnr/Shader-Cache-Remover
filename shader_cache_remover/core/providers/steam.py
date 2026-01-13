"""
Steam shader cache provider.

Detects Steam shader cache from registry and common installation paths.
"""

import platform
import string
from pathlib import Path
from typing import List, Optional

from ..interfaces import CacheLocation, CacheType
from .base import BaseCacheProvider

try:
    import winreg
except ImportError:
    winreg = None


class SteamProvider(BaseCacheProvider):
    """Provider for Steam shader caches."""
    
    @property
    def name(self) -> str:
        return "steam"
    
    @property
    def display_name(self) -> str:
        return "Steam"
    
    @property
    def priority(self) -> int:
        return 50
    
    @property
    def cache_type(self) -> CacheType:
        return CacheType.GAME_PLATFORM
    
    def is_available(self) -> bool:
        """Steam caches are available on Windows and Linux."""
        return platform.system() in ("Windows", "Linux")
    
    def detect(self) -> List[CacheLocation]:
        """Detect Steam shader cache locations."""
        if not self.is_available():
            return []
        
        locations = []
        
        # Try to get Steam path from registry (Windows)
        registry_path = self._get_steam_path_from_registry()
        if registry_path:
            shader_cache = registry_path / "steamapps" / "shadercache"
            locations.extend(self._check_path(shader_cache, "Primary Installation"))
        
        # Check common Steam installation paths on all drives
        locations.extend(self._scan_common_paths())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_locations = []
        for loc in locations:
            if loc.path not in seen:
                seen.add(loc.path)
                unique_locations.append(loc)
        
        if unique_locations:
            self.logger.info(f"Found {len(unique_locations)} Steam cache locations")
        
        return unique_locations
    
    def _get_steam_path_from_registry(self) -> Optional[Path]:
        """Get Steam installation path from Windows registry."""
        if not winreg or platform.system() != "Windows":
            return None
        
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
            ) as reg_key:
                steam_path, _ = winreg.QueryValueEx(reg_key, "SteamPath")
                return Path(steam_path)
        except FileNotFoundError:
            self.logger.debug("Steam registry key not found")
            return None
        except Exception as e:
            self.logger.warning(f"Error reading Steam registry: {e}")
            return None
    
    def _scan_common_paths(self) -> List[CacheLocation]:
        """Scan common Steam installation paths on all drives."""
        locations = []
        
        if platform.system() == "Windows":
            # Get all available drives
            for drive_letter in string.ascii_uppercase:
                drive = Path(f"{drive_letter}:\\")
                if drive.is_dir():
                    paths_to_check = [
                        (drive / "Program Files (x86)" / "Steam" / "steamapps" / "shadercache",
                         f"Drive {drive_letter}"),
                        (drive / "Program Files" / "Steam" / "steamapps" / "shadercache",
                         f"Drive {drive_letter}"),
                        (drive / "Steam" / "steamapps" / "shadercache",
                         f"Drive {drive_letter}"),
                        (drive / "SteamLibrary" / "steamapps" / "shadercache",
                         f"Library {drive_letter}"),
                    ]
                    locations.extend(self._check_paths(paths_to_check))
        
        elif platform.system() == "Linux":
            home = Path.home()
            linux_paths = [
                (home / ".steam" / "steam" / "steamapps" / "shadercache", "Linux"),
                (home / ".local" / "share" / "Steam" / "steamapps" / "shadercache", "Linux Local"),
            ]
            locations.extend(self._check_paths(linux_paths))
        
        return locations
