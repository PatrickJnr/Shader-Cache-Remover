"""
Cleanup service for removing shader cache files and directories.

This service handles the safe removal of shader cache files and directories,
with support for dry runs, backup operations, and progress tracking.
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass
import datetime


@dataclass
class CleanupStats:
    """Statistics for cleanup operation."""

    files_deleted: int = 0
    directories_deleted: int = 0
    bytes_freed: int = 0
    errors: int = 0
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None


class CleanupService:
    """Service for cleaning shader cache files and directories."""

    def __init__(self, backup_service=None):
        """Initialize the cleanup service.

        Args:
            backup_service: Optional backup service for creating backups
        """
        self.backup_service = backup_service
        self.logger = logging.getLogger(__name__)
        self.stats = CleanupStats()
        self.is_running = False

    def calculate_directory_size(self, directory: Path) -> int:
        """Calculate the total size of a directory.

        Args:
            directory: Path to the directory to calculate size for

        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except FileNotFoundError:
                        continue  # File might have been deleted by another process
        except Exception as e:
            self.logger.error(f"Error calculating size for {directory}: {e}")
        return total_size

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format.

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

    def remove_files_in_directory(self, directory: Path, dry_run: bool = False) -> None:
        """Delete all files and subdirectories in the specified directory.

        Args:
            directory: Path to the directory to clean
            dry_run: If True, only log what would be deleted without actually deleting
        """
        if not directory.exists():
            self.logger.warning(f"Directory does not exist: {directory}")
            return

        try:
            items = list(directory.iterdir())
            total_items = len(items)

            for i, item in enumerate(items):
                if not self.is_running:
                    self.logger.info("Cleanup stopped by user.")
                    break

                try:
                    item_size = 0
                    if item.is_file():
                        item_size = item.stat().st_size
                    elif item.is_dir():
                        item_size = self.calculate_directory_size(item)

                    # Create backup if backup service is available and not in dry run mode
                    if self.backup_service and not dry_run:
                        self.backup_service.backup_item(item)

                    if dry_run:
                        self.logger.info(f"Would delete: {item}")
                    else:
                        # Retry logic for locked files
                        max_retries = 3
                        retry_delay = 1.0

                        for attempt in range(max_retries + 1):
                            try:
                                if item.is_file():
                                    item.unlink()
                                    self.stats.files_deleted += 1
                                    break
                                elif item.is_dir():
                                    shutil.rmtree(item)
                                    self.stats.directories_deleted += 1
                                    break
                            except PermissionError as e:
                                if attempt < max_retries:
                                    self.logger.warning(
                                        f"File {item} is locked (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay}s..."
                                    )
                                    time.sleep(retry_delay)
                                    continue
                                else:
                                    self.logger.error(
                                        f"Failed to delete {item} after {max_retries + 1} attempts: {e}"
                                    )
                                    self.stats.errors += 1
                                    break
                            except Exception as e:
                                self.logger.error(f"Error removing {item}: {e}")
                                self.stats.errors += 1
                                break

                    self.stats.bytes_freed += item_size

                except FileNotFoundError:
                    self.logger.warning(
                        f"File not found during deletion (already removed?): {item}"
                    )
                    continue
                except Exception as e:
                    self.logger.error(f"Error removing {item}: {e}")
                    self.stats.errors += 1

        except Exception as e:
            self.logger.error(f"Error accessing directory {directory}: {e}")
            self.stats.errors += 1

    def cleanup_directories(
        self,
        directories: List[Path],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> CleanupStats:
        """Clean multiple shader cache directories.

        Args:
            directories: List of directories to clean
            dry_run: If True, only simulate the cleanup
            progress_callback: Optional callback function for progress updates

        Returns:
            CleanupStats object with operation statistics
        """
        self.is_running = True
        self.stats = CleanupStats(start_time=datetime.datetime.now())

        try:
            total_dirs = len(directories)

            for i, cache_dir in enumerate(directories):
                if not self.is_running:
                    break

                self.logger.info(f"Processing shader cache in: {cache_dir}")
                self.remove_files_in_directory(cache_dir, dry_run)

                # Update progress
                if progress_callback:
                    progress = (i + 1) / total_dirs * 100
                    progress_callback(progress)

            if self.is_running:
                self.stats.end_time = datetime.datetime.now()
                elapsed_time = self.stats.end_time - self.stats.start_time

                if dry_run:
                    final_message = "Dry run completed."
                else:
                    final_message = "Cleanup completed."

                self.logger.info(f"{final_message} in {elapsed_time.seconds} seconds.")
                self.logger.info(
                    "Summary: "
                    f"{self.stats.files_deleted} files, "
                    f"{self.stats.directories_deleted} directories deleted. "
                    f"Total space freed: {self.format_bytes(self.stats.bytes_freed)}. "
                    f"Errors: {self.stats.errors}"
                )

        except Exception as e:
            self.logger.error(
                f"A fatal error occurred during cleanup: {e}", exc_info=True
            )
        finally:
            self.is_running = False

        return self.stats

    def stop_cleanup(self) -> None:
        """Stop the current cleanup operation."""
        self.is_running = False
        self.logger.info("Cleanup stopped by user.")
