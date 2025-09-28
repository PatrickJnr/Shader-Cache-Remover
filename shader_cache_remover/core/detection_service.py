"""
Detection service for finding shader cache directories.

This service handles the detection of shader cache directories from various
sources including Windows registry, common system paths, and custom user paths.
"""

import logging
import platform
from pathlib import Path
from typing import List, Optional, Set

try:
    import winreg  # For reading the registry on Windows
except ImportError:
    winreg = None


class DetectionService:
    """Service for detecting shader cache directories."""

    def __init__(self, custom_paths: Optional[List[str]] = None):
        """Initialize the detection service.

        Args:
            custom_paths: Optional list of custom paths to include in detection
        """
        self.custom_paths = custom_paths or []
        self.logger = logging.getLogger(__name__)

    def get_all_drives(self) -> List[Path]:
        """Detect all available drives on the system.

        Returns:
            List of Path objects representing available drives
        """
        drives = []
        if platform.system() == "Windows":
            import string

            for drive_letter in string.ascii_uppercase:
                drive_path = Path(f"{drive_letter}:\\")
                if drive_path.is_dir():
                    drives.append(drive_path)
        else:  # For Unix-like systems
            drives.append(Path("/"))
        return drives

    def get_steam_shader_cache_path(self) -> Optional[Path]:
        """Retrieve Steam installation path from the registry and construct shader cache path.

        Returns:
            Path to Steam shader cache directory, or None if not found
        """
        if not winreg or platform.system() != "Windows":
            return None

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
            ) as reg_key:
                steam_path, _ = winreg.QueryValueEx(reg_key, "SteamPath")

            shader_cache_path = Path(steam_path) / "steamapps" / "shadercache"
            if shader_cache_path.exists():
                self.logger.info(f"Steam shader cache found at: {shader_cache_path}")
                return shader_cache_path
            else:
                self.logger.warning("Steam shader cache directory not found.")
                return None
        except FileNotFoundError:
            self.logger.warning("Steam registry key not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error reading Steam registry path: {e}")
            return None

    def get_common_shader_cache_directories(self) -> List[Path]:
        """Get common shader cache directories based on the operating system.

        Returns:
            List of Path objects for common shader cache locations
        """
        directories = []

        if platform.system() == "Windows":
            home = Path.home()
            common_dirs = [
                home / "AppData" / "Local" / "NVIDIA" / "DXCache",
                home / "AppData" / "Local" / "NVIDIA" / "GLCache",
                home / "AppData" / "Local" / "AMD" / "DxCache",
                home / "AppData" / "Local" / "AMD" / "GLCache",
                home / "AppData" / "Local" / "UnrealEngine" / "ShaderCache",
                home / "AppData" / "LocalLow" / "Unity" / "Caches",
                home / "AppData" / "Local" / "Temp" / "NVIDIA Corporation" / "NV_Cache",
                home / "AppData" / "Local" / "Temp" / "DXCache",
                home / "AppData" / "Local" / "Temp" / "D3DSCache",
                home / "AppData" / "Local" / "Temp" / "OpenGLCache",
                home / "AppData" / "Local" / "Intel" / "ShaderCache",
            ]

            for directory in common_dirs:
                if directory.exists():
                    directories.append(directory)

        return directories

    def get_additional_steam_paths(self) -> List[Path]:
        """Check all drives for additional Steam installations.

        Returns:
            List of additional Steam shader cache paths found
        """
        additional_paths = []

        # Check all drives for additional Steam installations
        for drive in self.get_all_drives():
            for steam_path_part in [
                "Program Files (x86)/Steam",
                "Program Files/Steam",
                "Steam",
            ]:
                potential_path = drive / steam_path_part / "steamapps" / "shadercache"
                if potential_path.exists():
                    additional_paths.append(potential_path)

        return additional_paths

    def get_custom_shader_cache_directories(self) -> List[Path]:
        """Get shader cache directories from custom user paths.

        Returns:
            List of valid custom shader cache directories
        """
        directories = []

        for custom_path in self.custom_paths:
            try:
                path = Path(custom_path)
                if path.is_dir():
                    directories.append(path)
                    self.logger.info(f"Added custom shader cache directory: {path}")
                else:
                    self.logger.warning(
                        f"Custom path does not exist or is not a directory: {path}"
                    )
            except Exception as e:
                self.logger.error(f"Error processing custom path '{custom_path}': {e}")

        return directories

    def get_all_shader_cache_directories(self) -> List[Path]:
        """Get all shader cache directories to clean.

        Returns:
            List of all detected shader cache directories
        """
        directories = set()

        # Add common system directories
        directories.update(self.get_common_shader_cache_directories())

        # Add Steam shader cache from registry
        steam_cache = self.get_steam_shader_cache_path()
        if steam_cache:
            directories.add(steam_cache)

        # Add additional Steam paths from all drives
        directories.update(self.get_additional_steam_paths())

        # Add custom paths
        directories.update(self.get_custom_shader_cache_directories())

        # Convert to sorted list and remove duplicates
        result = sorted(list(directories))

        self.logger.info(f"Found {len(result)} shader cache directories to process.")
        return result
