"""
Centralized deletion gate for all file deletion operations.

This module provides a single point of control and auditing for all
file deletions in the application, ensuring safety checks are always applied.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import platform


@dataclass
class DeletionRequest:
    """Record of a deletion request."""
    path: Path
    reason: str
    approved: bool
    timestamp: datetime = field(default_factory=datetime.now)
    rejection_reason: Optional[str] = None


class DeletionGate:
    """
    Centralized safety gate for ALL file deletions.
    
    Every deletion in the application MUST go through this gate.
    This provides:
    - Protection against deleting system-critical paths
    - Audit logging of all deletion attempts
    - Dry-run support
    - Consistent validation across all code paths
    
    Usage:
        gate = DeletionGate(dry_run=False)
        
        if gate.request_deletion(path, "cleanup cache"):
            # Safe to delete
            path.unlink()
        else:
            # Deletion was blocked
            pass
    """
    
    # Paths that can NEVER be deleted under any circumstances
    # These are checked case-insensitively on Windows
    ABSOLUTE_BLOCKLIST: Set[str] = {
        "C:\\Windows",
        "C:\\Windows\\System32",
        "C:\\Windows\\SysWOW64",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Users\\Default",
        "C:\\Users\\Public",
        "C:\\ProgramData\\Microsoft",
        # Unix paths for cross-platform safety
        "/bin",
        "/sbin",
        "/usr",
        "/etc",
        "/var",
        "/lib",
        "/lib64",
        "/boot",
        "/root",
    }
    
    # Path components that indicate a cache directory (case-insensitive)
    CACHE_PATH_INDICATORS = {
        "shadercache", "shader_cache", "shader-cache",
        "dxcache", "dx_cache", "d3dscache",
        "glcache", "gl_cache", "openglcache",
        "nv_cache", "nvidia",
        "amd", "ati",
        "intel",
        "cache", "caches",
        "temp", "tmp",
    }
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the deletion gate.
        
        Args:
            dry_run: If True, no deletions will be approved but all
                    requests will be logged.
        """
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        self._deletion_log: List[DeletionRequest] = []
        self._is_windows = platform.system() == "Windows"
    
    def request_deletion(self, path: Path, reason: str) -> bool:
        """
        Request permission to delete a path.
        
        This method performs safety checks and records the request.
        
        Args:
            path: The path to delete.
            reason: Human-readable reason for the deletion.
        
        Returns:
            True if deletion is approved, False otherwise.
        """
        path = path.resolve()
        
        # Check absolute blocklist
        if self._is_blocked_path(path):
            self._log_request(path, reason, approved=False,
                            rejection="Path is in absolute blocklist")
            self.logger.critical(
                f"BLOCKED: Attempted deletion of protected system path: {path}"
            )
            return False
        
        # Check if path is inside user's home directory or known safe locations
        if not self._is_safe_location(path):
            self._log_request(path, reason, approved=False,
                            rejection="Path is outside safe locations")
            self.logger.warning(
                f"BLOCKED: Path is outside known safe locations: {path}"
            )
            return False
        
        # Warn if path doesn't look like a cache (but still allow)
        if not self._looks_like_cache(path):
            self.logger.warning(
                f"NOTICE: Path doesn't look like a typical cache directory: {path}"
            )
        
        # Dry run mode - log but don't approve
        if self.dry_run:
            self._log_request(path, reason, approved=False,
                            rejection="Dry run mode")
            self.logger.info(f"DRY RUN: Would delete {path} ({reason})")
            return False
        
        # All checks passed
        self._log_request(path, reason, approved=True)
        self.logger.debug(f"APPROVED: Deletion of {path} ({reason})")
        return True
    
    def _is_blocked_path(self, path: Path) -> bool:
        """Check if path is in the absolute blocklist."""
        path_str = str(path)
        
        for blocked in self.ABSOLUTE_BLOCKLIST:
            if self._is_windows:
                # Case-insensitive comparison on Windows
                if path_str.lower().startswith(blocked.lower()):
                    return True
            else:
                if path_str.startswith(blocked):
                    return True
        
        return False
    
    def _is_safe_location(self, path: Path) -> bool:
        """
        Check if path is in a known safe location.
        
        Safe locations include:
        - User's home directory (AppData, etc.)
        - Steam installation directories
        - Temp directories
        """
        path_str = str(path)
        home = str(Path.home())
        
        # Always safe: inside user's home directory
        if self._is_windows:
            if path_str.lower().startswith(home.lower()):
                return True
        else:
            if path_str.startswith(home):
                return True
        
        # Safe: Steam directories on any drive
        path_lower = path_str.lower()
        if "steam" in path_lower and "shadercache" in path_lower:
            return True
        
        # Safe: AppData paths (even if home detection failed)
        if self._is_windows and "appdata" in path_lower:
            return True
        
        return False
    
    def _looks_like_cache(self, path: Path) -> bool:
        """Check if path looks like a cache directory based on name."""
        path_lower = str(path).lower()
        
        for indicator in self.CACHE_PATH_INDICATORS:
            if indicator in path_lower:
                return True
        
        return False
    
    def _log_request(self, path: Path, reason: str, approved: bool,
                     rejection: Optional[str] = None) -> None:
        """Log a deletion request."""
        request = DeletionRequest(
            path=path,
            reason=reason,
            approved=approved,
            rejection_reason=rejection
        )
        self._deletion_log.append(request)
    
    def get_deletion_log(self) -> List[DeletionRequest]:
        """
        Get the audit log of all deletion requests.
        
        Returns:
            Copy of the deletion request log.
        """
        return self._deletion_log.copy()
    
    def get_blocked_count(self) -> int:
        """Get count of blocked deletion requests."""
        return sum(1 for r in self._deletion_log if not r.approved)
    
    def get_approved_count(self) -> int:
        """Get count of approved deletion requests."""
        return sum(1 for r in self._deletion_log if r.approved)
    
    def clear_log(self) -> None:
        """Clear the deletion log."""
        self._deletion_log.clear()
