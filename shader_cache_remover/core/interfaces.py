"""
Core interfaces and protocols for the Shader Cache Remover.

This module defines the abstract interfaces that components must implement,
enabling a plugin-based architecture for cache detection and cleanup.
"""

from typing import Protocol, List, Optional, runtime_checkable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto


class CacheType(Enum):
    """Categories of shader cache."""
    GPU_VENDOR = auto()      # NVIDIA, AMD, Intel
    GAME_PLATFORM = auto()   # Steam
    GAME_ENGINE = auto()     # Unreal, Unity
    SYSTEM = auto()          # Windows DirectX/OpenGL caches
    CUSTOM = auto()          # User-defined paths


@dataclass
class CacheLocation:
    """Represents a detected cache location."""
    path: Path
    provider_name: str
    display_name: str
    cache_type: CacheType = CacheType.CUSTOM
    estimated_size: int = 0
    enabled: bool = True
    
    def __hash__(self):
        return hash(self.path)
    
    def __eq__(self, other):
        if isinstance(other, CacheLocation):
            return self.path == other.path
        return False


@runtime_checkable
class CacheProvider(Protocol):
    """
    Protocol for cache detection providers.
    
    Implement this protocol to add new cache detection capabilities.
    Providers are discovered and used by the DetectionService.
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for this provider (e.g., 'nvidia', 'steam')."""
        ...
    
    @property
    def display_name(self) -> str:
        """Human-readable name for UI display (e.g., 'NVIDIA')."""
        ...
    
    @property
    def priority(self) -> int:
        """
        Detection priority (lower values run first).
        
        Recommended ranges:
        - 1-10: Critical system caches
        - 11-50: GPU vendor caches
        - 51-100: Game platform caches
        - 101-200: Game engine caches
        - 200+: Custom/user-defined
        """
        ...
    
    @property
    def cache_type(self) -> CacheType:
        """The type/category of cache this provider handles."""
        ...
    
    def is_available(self) -> bool:
        """
        Check if this provider is available on the current system.
        
        Returns:
            True if the provider can run on this system, False otherwise.
            For example, NVIDIA provider returns False on non-Windows systems.
        """
        ...
    
    def detect(self) -> List[CacheLocation]:
        """
        Detect cache locations for this provider.
        
        Returns:
            List of discovered cache locations. Empty list if none found.
        """
        ...


@dataclass
class ProviderInfo:
    """Information about a registered provider."""
    name: str
    display_name: str
    priority: int
    cache_type: CacheType
    is_available: bool
    is_enabled: bool = True


class FileSystemProtocol(Protocol):
    """
    Protocol for filesystem operations.
    
    This abstraction allows for mocking filesystem operations in tests
    and provides a single point of control for all file operations.
    """
    
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        ...
    
    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        ...
    
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        ...
    
    def iterdir(self, path: Path) -> List[Path]:
        """List directory contents."""
        ...
    
    def rglob(self, path: Path, pattern: str) -> List[Path]:
        """Recursively glob for files matching pattern."""
        ...
    
    def stat_size(self, path: Path) -> int:
        """Get file size in bytes."""
        ...
    
    def unlink(self, path: Path) -> None:
        """Delete a file."""
        ...
    
    def rmtree(self, path: Path) -> None:
        """Recursively delete a directory."""
        ...
    
    def copytree(self, src: Path, dst: Path, dirs_exist_ok: bool = False) -> None:
        """Copy a directory tree."""
        ...
    
    def copy2(self, src: Path, dst: Path) -> None:
        """Copy a file preserving metadata."""
        ...
    
    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        ...
