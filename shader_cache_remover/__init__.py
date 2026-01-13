"""
Shader Cache Remover - A modular application for cleaning shader cache files.

This package provides a clean, modular architecture for detecting and removing
shader cache files from various applications and game engines.
"""

__version__ = "1.6.0"
__author__ = "PatrickJnr"

from .core.cleanup_service import CleanupService
from .core.detection_service import DetectionService
from .core.backup_service import BackupService
from .infrastructure.config_manager import ConfigManager
from .infrastructure.registry_utils import RegistryUtils
from .infrastructure.logging_config import LoggingConfig

__all__ = [
    "CleanupService",
    "DetectionService",
    "BackupService",
    "ConfigManager",
    "RegistryUtils",
    "LoggingConfig",
]
