"""
Cleanup service for removing shader cache files and directories.

This service handles the safe removal of shader cache files and directories,
with support for dry runs, backup operations, progress tracking, and
cancellation via tokens.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass
import datetime

from .cancellation import CancellationToken, CancelledException
from .deletion_gate import DeletionGate
from .interfaces import CacheLocation
from ..infrastructure.filesystem import RealFileSystem


@dataclass
class CleanupStats:
    """Statistics for cleanup operation."""

    files_deleted: int = 0
    directories_deleted: int = 0
    bytes_freed: int = 0
    errors: int = 0
    skipped: int = 0
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    was_cancelled: bool = False


class CleanupService:
    """
    Service for cleaning shader cache files and directories.
    
    This service provides safe file deletion with:
    - Cancellation token support for cooperative cancellation
    - Centralized deletion gate for safety checks
    - Dry run mode for previewing changes
    - Backup integration
    - Progress callbacks
    
    Usage:
        service = CleanupService()
        token = CancellationToken()
        
        # Start cleanup in a thread
        stats = service.cleanup_directories(
            directories,
            dry_run=False,
            cancellation_token=token,
            progress_callback=update_ui
        )
        
        # To cancel:
        token.cancel()
    """

    def __init__(self, backup_service=None, filesystem=None):
        """
        Initialize the cleanup service.

        Args:
            backup_service: Optional backup service for creating backups
            filesystem: Optional filesystem abstraction (for testing)
        """
        self.backup_service = backup_service
        self.fs = filesystem or RealFileSystem()
        self.logger = logging.getLogger(__name__)
        self.stats = CleanupStats()
        self._current_token: Optional[CancellationToken] = None
        self._deletion_gate: Optional[DeletionGate] = None

    def calculate_directory_size(self, directory: Path) -> int:
        """
        Calculate the total size of a directory.

        Args:
            directory: Path to the directory to calculate size for

        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for item in self.fs.rglob(directory, "*"):
                if self.fs.is_file(item):
                    try:
                        total_size += self.fs.stat_size(item)
                    except (FileNotFoundError, OSError):
                        continue
        except Exception as e:
            self.logger.error(f"Error calculating size for {directory}: {e}")
        return total_size

    def format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes to human-readable format.

        Args:
            bytes_value: Size in bytes

        Returns:
            Formatted size string
        """
        if bytes_value < 1024:
            return f"{bytes_value} B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def remove_files_in_directory(
        self, 
        directory: Path, 
        dry_run: bool = False,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """
        Delete all files and subdirectories in the specified directory.

        Args:
            directory: Path to the directory to clean
            dry_run: If True, only log what would be deleted without actually deleting
            cancellation_token: Optional token for cancellation
        """
        if not self.fs.exists(directory):
            self.logger.warning(f"Directory does not exist: {directory}")
            return

        token = cancellation_token or self._current_token

        try:
            items = self.fs.iterdir(directory)

            for item in items:
                # Check for cancellation
                if token and token.is_cancelled:
                    self.logger.info("Cleanup cancelled by user.")
                    self.stats.was_cancelled = True
                    break

                try:
                    item_size = 0
                    if self.fs.is_file(item):
                        item_size = self.fs.stat_size(item)
                    elif self.fs.is_dir(item):
                        item_size = self.calculate_directory_size(item)

                    # Create backup if backup service is available and not in dry run mode
                    if self.backup_service and not dry_run:
                        self.backup_service.backup_item(item)

                    # Check with deletion gate (handles both dry run logging and safety checks)
                    if self._deletion_gate:
                        gate_approved = self._deletion_gate.request_deletion(item, "cleanup cache")
                        
                        # In dry run mode, the gate returns False but logs "would delete"
                        # We still want to count these as "would be freed"
                        if dry_run:
                            # Track what would be deleted
                            self.stats.bytes_freed += item_size
                            if self.fs.is_file(item):
                                self.stats.files_deleted += 1
                            else:
                                self.stats.directories_deleted += 1
                            continue
                        
                        # In real mode, if gate blocks, skip
                        if not gate_approved:
                            self.logger.debug(f"Deletion blocked by safety gate: {item}")
                            self.stats.skipped += 1
                            continue

                    # Perform actual deletion (only reached if not dry_run and gate approved)
                    self._delete_with_retry(item)
                    self.stats.bytes_freed += item_size

                except FileNotFoundError:
                    self.logger.warning(
                        f"File not found during deletion (already removed?): {item}"
                    )
                    continue
                except CancelledException:
                    self.stats.was_cancelled = True
                    raise
                except Exception as e:
                    self.logger.error(f"Error removing {item}: {e}")
                    self.stats.errors += 1

        except CancelledException:
            self.logger.info("Cleanup cancelled.")
            raise
        except Exception as e:
            self.logger.error(f"Error accessing directory {directory}: {e}")
            self.stats.errors += 1

    def _delete_with_retry(
        self, 
        item: Path, 
        max_retries: int = 3, 
        retry_delay: float = 1.0
    ) -> None:
        """
        Delete a file or directory with retry logic for locked files.
        
        Args:
            item: Path to delete
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
        """
        for attempt in range(max_retries + 1):
            try:
                if self.fs.is_file(item):
                    self.fs.unlink(item)
                    self.stats.files_deleted += 1
                    self.logger.debug(f"Deleted file: {item}")
                    return
                elif self.fs.is_dir(item):
                    self.fs.rmtree(item)
                    self.stats.directories_deleted += 1
                    self.logger.debug(f"Deleted directory: {item}")
                    return
            except PermissionError as e:
                if attempt < max_retries:
                    self.logger.warning(
                        f"File {item} is locked (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(
                        f"Failed to delete {item} after {max_retries + 1} attempts: {e}"
                    )
                    self.stats.errors += 1
                    return
            except Exception as e:
                self.logger.error(f"Error removing {item}: {e}")
                self.stats.errors += 1
                return

    def cleanup_directories(
        self,
        directories: List[Path],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CleanupStats:
        """
        Clean multiple shader cache directories.

        Args:
            directories: List of directories to clean
            dry_run: If True, only simulate the cleanup
            progress_callback: Optional callback function for progress updates
            cancellation_token: Optional token for cancellation

        Returns:
            CleanupStats object with operation statistics
        """
        self._current_token = cancellation_token or CancellationToken()
        self._deletion_gate = DeletionGate(dry_run=dry_run)
        self.stats = CleanupStats(start_time=datetime.datetime.now())

        try:
            total_dirs = len(directories)

            for i, cache_dir in enumerate(directories):
                # Check cancellation
                if self._current_token.is_cancelled:
                    self.stats.was_cancelled = True
                    break

                self.logger.info(f"Processing shader cache in: {cache_dir}")
                
                try:
                    self.remove_files_in_directory(
                        cache_dir, 
                        dry_run, 
                        self._current_token
                    )
                except CancelledException:
                    self.stats.was_cancelled = True
                    break

                # Update progress
                if progress_callback:
                    progress = (i + 1) / total_dirs * 100
                    progress_callback(progress)

            self.stats.end_time = datetime.datetime.now()
            elapsed_time = self.stats.end_time - self.stats.start_time

            if self.stats.was_cancelled:
                final_message = "Cleanup cancelled by user."
            elif dry_run:
                final_message = "Dry run completed."
            else:
                final_message = "Cleanup completed."

            self.logger.info(f"{final_message} in {elapsed_time.seconds} seconds.")
            self.logger.info(
                "Summary: "
                f"{self.stats.files_deleted} files, "
                f"{self.stats.directories_deleted} directories deleted. "
                f"Total space freed: {self.format_bytes(self.stats.bytes_freed)}. "
                f"Errors: {self.stats.errors}, Skipped: {self.stats.skipped}"
            )

        except Exception as e:
            self.logger.error(
                f"A fatal error occurred during cleanup: {e}", exc_info=True
            )
        finally:
            self._current_token = None

        return self.stats

    def cleanup_locations(
        self,
        locations: List[CacheLocation],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CleanupStats:
        """
        Clean multiple cache locations (filtering by enabled status).
        
        Args:
            locations: List of CacheLocation objects
            dry_run: If True, only simulate the cleanup
            progress_callback: Optional callback function for progress updates
            cancellation_token: Optional token for cancellation
        
        Returns:
            CleanupStats object with operation statistics
        """
        enabled_paths = [loc.path for loc in locations if loc.enabled]
        return self.cleanup_directories(
            enabled_paths, 
            dry_run, 
            progress_callback, 
            cancellation_token
        )

    def stop_cleanup(self) -> None:
        """Stop the current cleanup operation."""
        if self._current_token:
            self._current_token.cancel()
            self.logger.info("Cleanup stop requested.")
        else:
            self.logger.warning("No cleanup operation in progress.")

    # Legacy property for backward compatibility
    @property
    def is_running(self) -> bool:
        """Check if cleanup is currently running."""
        return self._current_token is not None and not self._current_token.is_cancelled
