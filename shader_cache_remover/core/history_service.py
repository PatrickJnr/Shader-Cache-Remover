"""
Cleanup history service for tracking past cleanup operations.

Stores cleanup history in a JSON file for persistence.
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional
import os


@dataclass
class CleanupHistoryEntry:
    """Record of a single cleanup operation."""
    timestamp: str
    files_deleted: int
    directories_deleted: int
    bytes_freed: int
    errors: int
    skipped: int
    duration_seconds: float
    was_dry_run: bool = False
    providers_used: List[str] = field(default_factory=list)


class HistoryService:
    """
    Service for managing cleanup history.
    
    Stores history in a JSON file in the user's app data directory.
    """
    
    DEFAULT_HISTORY_FILE = ".shader_cache_remover_history.json"
    MAX_HISTORY_ENTRIES = 100  # Keep last 100 cleanups
    
    def __init__(self, history_file: Optional[Path] = None):
        """Initialize the history service."""
        self.logger = logging.getLogger(__name__)
        
        if history_file:
            self.history_file = history_file
        else:
            self.history_file = Path.home() / self.DEFAULT_HISTORY_FILE
        
        self._history: List[CleanupHistoryEntry] = []
        self._load_history()
    
    def _load_history(self) -> None:
        """Load history from file."""
        if not self.history_file.exists():
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._history = [
                CleanupHistoryEntry(**entry) for entry in data.get("entries", [])
            ]
            self.logger.debug(f"Loaded {len(self._history)} history entries")
            
        except Exception as e:
            self.logger.warning(f"Failed to load history: {e}")
            self._history = []
    
    def _save_history(self) -> None:
        """Save history to file."""
        try:
            data = {
                "version": 1,
                "entries": [asdict(entry) for entry in self._history]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(self._history)} history entries")
            
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")
    
    def record_cleanup(
        self,
        files_deleted: int,
        directories_deleted: int,
        bytes_freed: int,
        errors: int,
        skipped: int,
        duration_seconds: float,
        was_dry_run: bool = False,
        providers_used: Optional[List[str]] = None
    ) -> None:
        """
        Record a cleanup operation.
        
        Args:
            files_deleted: Number of files deleted
            directories_deleted: Number of directories deleted
            bytes_freed: Total bytes freed
            errors: Number of errors encountered
            skipped: Number of items skipped
            duration_seconds: Duration of the cleanup
            was_dry_run: Whether this was a dry run
            providers_used: List of provider names used
        """
        entry = CleanupHistoryEntry(
            timestamp=datetime.now().isoformat(),
            files_deleted=files_deleted,
            directories_deleted=directories_deleted,
            bytes_freed=bytes_freed,
            errors=errors,
            skipped=skipped,
            duration_seconds=duration_seconds,
            was_dry_run=was_dry_run,
            providers_used=providers_used or []
        )
        
        self._history.append(entry)
        
        # Trim old entries
        if len(self._history) > self.MAX_HISTORY_ENTRIES:
            self._history = self._history[-self.MAX_HISTORY_ENTRIES:]
        
        self._save_history()
        self.logger.info(f"Recorded cleanup: {files_deleted} files, {self._format_bytes(bytes_freed)}")

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable string (e.g., 607.7 MB)."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def get_history(self, limit: Optional[int] = None) -> List[CleanupHistoryEntry]:
        """
        Get cleanup history.
        
        Args:
            limit: Optional limit on number of entries (most recent first)
        
        Returns:
            List of history entries, most recent first
        """
        entries = list(reversed(self._history))
        if limit:
            return entries[:limit]
        return entries
    
    def get_total_stats(self) -> dict:
        """
        Get aggregate statistics across all history.
        
        Returns:
            Dictionary with total stats
        """
        total_files = sum(e.files_deleted for e in self._history if not e.was_dry_run)
        total_dirs = sum(e.directories_deleted for e in self._history if not e.was_dry_run)
        total_bytes = sum(e.bytes_freed for e in self._history if not e.was_dry_run)
        cleanup_count = sum(1 for e in self._history if not e.was_dry_run)
        
        return {
            "total_cleanups": cleanup_count,
            "total_files_deleted": total_files,
            "total_directories_deleted": total_dirs,
            "total_bytes_freed": total_bytes,
        }
    
    def clear_history(self) -> None:
        """Clear all history."""
        self._history = []
        self._save_history()
        self.logger.info("History cleared")
