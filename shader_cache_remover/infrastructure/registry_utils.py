"""
Registry utilities for Windows-specific operations.

This module provides utilities for reading Windows registry keys,
particularly for detecting installed applications and their paths.
"""

import logging
import platform
from typing import Optional, Dict, Any

try:
    import winreg  # For reading the registry on Windows
except ImportError:
    winreg = None


class RegistryUtils:
    """Utilities for Windows registry operations."""

    def __init__(self):
        """Initialize the registry utilities."""
        self.logger = logging.getLogger(__name__)
        if not winreg:
            self.logger.warning(
                "winreg module not available. Registry operations will not work."
            )

    def is_windows(self) -> bool:
        """Check if running on Windows.

        Returns:
            True if running on Windows, False otherwise
        """
        return platform.system() == "Windows" and winreg is not None

    def read_registry_value(
        self, hive: int, key_path: str, value_name: str, expected_type: type = str
    ) -> Optional[Any]:
        """Read a value from the Windows registry.

        Args:
            hive: Registry hive (e.g., winreg.HKEY_CURRENT_USER)
            key_path: Path to the registry key
            value_name: Name of the value to read
            expected_type: Expected type of the value

        Returns:
            Registry value or None if not found/error occurred
        """
        if not self.is_windows():
            self.logger.warning("Registry operations only supported on Windows.")
            return None

        try:
            with winreg.OpenKey(hive, key_path) as reg_key:
                value, reg_type = winreg.QueryValueEx(reg_key, value_name)

                # Convert to expected type if possible
                if expected_type == str:
                    return str(value)
                elif expected_type == int:
                    return int(value)
                else:
                    return value

        except FileNotFoundError:
            self.logger.debug(f"Registry key not found: {key_path}\\{value_name}")
            return None
        except Exception as e:
            self.logger.error(
                f"Error reading registry value {key_path}\\{value_name}: {e}"
            )
            return None

    def get_steam_install_path(self) -> Optional[str]:
        """Get Steam installation path from registry.

        Returns:
            Steam installation path or None if not found
        """
        return self.read_registry_value(
            winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"
        )

    def get_uninstall_entry(self, program_name: str) -> Optional[Dict[str, str]]:
        """Get uninstall information for a program.

        Args:
            program_name: Name of the program to search for

        Returns:
            Dictionary with uninstall information or None if not found
        """
        if not self.is_windows():
            return None

        try:
            # Search in both 32-bit and 64-bit uninstall keys
            uninstall_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ]

            for key_path in uninstall_keys:
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, key_path
                    ) as base_key:
                        # Enumerate subkeys to find the program
                        for i in range(winreg.QueryInfoKey(base_key)[0]):
                            subkey_name = winreg.EnumKey(base_key, i)
                            subkey_path = f"{key_path}\\{subkey_name}"

                            try:
                                with winreg.OpenKey(
                                    winreg.HKEY_LOCAL_MACHINE, subkey_path
                                ) as sub_key:
                                    try:
                                        display_name = winreg.QueryValueEx(
                                            sub_key, "DisplayName"
                                        )[0]
                                        if program_name.lower() in display_name.lower():
                                            return {
                                                "name": display_name,
                                                "install_location": self.read_registry_value(
                                                    winreg.HKEY_LOCAL_MACHINE,
                                                    subkey_path,
                                                    "InstallLocation",
                                                    str,
                                                ),
                                                "uninstall_string": self.read_registry_value(
                                                    winreg.HKEY_LOCAL_MACHINE,
                                                    subkey_path,
                                                    "UninstallString",
                                                    str,
                                                ),
                                                "version": self.read_registry_value(
                                                    winreg.HKEY_LOCAL_MACHINE,
                                                    subkey_path,
                                                    "DisplayVersion",
                                                    str,
                                                ),
                                            }
                                    except FileNotFoundError:
                                        continue
                            except Exception as e:
                                self.logger.debug(
                                    f"Error reading uninstall subkey {subkey_path}: {e}"
                                )
                                continue

                except Exception as e:
                    self.logger.debug(f"Error reading uninstall key {key_path}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error searching for uninstall entry: {e}")

        return None

    def get_program_files_paths(self) -> Dict[str, str]:
        """Get common Program Files paths.

        Returns:
            Dictionary with ProgramFilesDir and ProgramFilesDir (x86) paths
        """
        paths = {}

        if self.is_windows():
            try:
                # Get Program Files directories
                paths["ProgramFiles"] = self.read_registry_value(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion",
                    "ProgramFilesDir",
                )

                paths["ProgramFilesX86"] = self.read_registry_value(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion",
                    "ProgramFilesDir (x86)",
                )

            except Exception as e:
                self.logger.error(f"Error getting Program Files paths: {e}")

        return paths
