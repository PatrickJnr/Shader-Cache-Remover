"""
Base class for cache providers.

This module provides a base implementation that other providers can extend.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ..interfaces import CacheProvider, CacheLocation, CacheType


class BaseCacheProvider(ABC):
    """
    Abstract base class for cache providers.
    
    Provides common functionality and enforces the CacheProvider protocol.
    Subclasses must implement the abstract methods.
    """
    
    def __init__(self):
        """Initialize the provider."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this provider."""
        ...
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI display."""
        ...
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Detection priority (lower values run first)."""
        ...
    
    @property
    @abstractmethod
    def cache_type(self) -> CacheType:
        """The type/category of cache this provider handles."""
        ...
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the current system."""
        ...
    
    @abstractmethod
    def detect(self) -> List[CacheLocation]:
        """Detect cache locations for this provider."""
        ...
    
    def _check_path(self, path: Path, display_suffix: str = "") -> List[CacheLocation]:
        """
        Helper to check a single path and return CacheLocation if it exists.
        
        Args:
            path: Path to check
            display_suffix: Optional suffix for display name
        
        Returns:
            List with one CacheLocation if path exists, empty list otherwise.
        """
        if path.exists() and path.is_dir():
            display = self.display_name
            if display_suffix:
                display = f"{display} - {display_suffix}"
            
            return [CacheLocation(
                path=path,
                provider_name=self.name,
                display_name=display,
                cache_type=self.cache_type,
            )]
        return []
    
    def _check_paths(self, paths: List[tuple]) -> List[CacheLocation]:
        """
        Helper to check multiple paths.
        
        Args:
            paths: List of (Path, display_suffix) tuples
        
        Returns:
            List of CacheLocations for paths that exist.
        """
        locations = []
        for path, suffix in paths:
            locations.extend(self._check_path(path, suffix))
        return locations
