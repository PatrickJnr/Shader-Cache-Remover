"""
Core services for the Shader Cache Remover application.

This module contains the main business logic services for detecting,
cleaning, and backing up shader cache files.
"""

from .interfaces import CacheProvider, CacheLocation, CacheType, ProviderInfo
from .detection_service import DetectionService
from .cleanup_service import CleanupService, CleanupStats
from .backup_service import BackupService, BackupStats
from .validation_service import ValidationService, ValidationResult, ValidationReport
from .cancellation import CancellationToken, CancelledException, CancellationTokenSource
from .deletion_gate import DeletionGate, DeletionRequest

__all__ = [
    # Interfaces
    "CacheProvider",
    "CacheLocation",
    "CacheType",
    "ProviderInfo",
    # Services
    "DetectionService",
    "CleanupService",
    "CleanupStats",
    "BackupService",
    "BackupStats",
    "ValidationService",
    "ValidationResult",
    "ValidationReport",
    # Execution control
    "CancellationToken",
    "CancelledException",
    "CancellationTokenSource",
    "DeletionGate",
    "DeletionRequest",
]

