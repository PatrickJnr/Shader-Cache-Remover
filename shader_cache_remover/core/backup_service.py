"""
Backup service for creating backups of shader cache files.

This service handles the creation of backup copies of shader cache files
and directories before they are deleted during cleanup operations.
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Optional


class BackupStats:
    """Statistics for backup operations."""

    def __init__(self):
        """Initialize backup statistics."""
        self.files_backed_up = 0
        self.directories_backed_up = 0
        self.bytes_backed_up = 0
        self.errors = 0
        self.start_time = None
        self.end_time = None


class BackupService:
    """Service for backing up shader cache files and directories."""

    def __init__(self, backup_root: Optional[Path] = None):
        """Initialize the backup service.

        Args:
            backup_root: Root directory for storing backups
        """
        self.backup_root = backup_root
        self.logger = logging.getLogger(__name__)

    def set_backup_root(self, backup_root: Path) -> None:
        """Set the root directory for storing backups.

        Args:
            backup_root: Root directory for storing backups
        """
        self.backup_root = backup_root
        self.logger.info(f"Backup root set to: {backup_root}")

    def create_backup_directory(self, source: Path) -> Optional[Path]:
        """Create a backup directory structure for the source path.

        Args:
            source: Source path to create backup structure for

        Returns:
            Path to the backup location, or None if backup_root is not set
        """
        if not self.backup_root:
            self.logger.warning("No backup root directory set.")
            return None

        try:
            # Create a relative path to maintain directory structure in the backup
            relative_path = source.relative_to(Path(source.anchor))
            backup_path = self.backup_root / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            return backup_path
        except Exception as e:
            self.logger.error(f"Error creating backup directory structure: {e}")
            return None

    def backup_item(
        self, source: Path, max_retries: int = 3, retry_delay: float = 1.0
    ) -> bool:
        """Backup a file or directory to the backup location.

        Args:
            source: Source file or directory to backup
            max_retries: Maximum number of retry attempts for locked files
            retry_delay: Delay in seconds between retry attempts

        Returns:
            True if backup was successful, False otherwise
        """
        if not self.backup_root:
            self.logger.warning("Cannot backup: no backup root directory set.")
            return False

        try:
            backup_path = self.create_backup_directory(source)
            if not backup_path:
                return False

            # Retry logic for locked files
            for attempt in range(max_retries + 1):
                try:
                    if source.is_file():
                        shutil.copy2(source, backup_path)
                        self.logger.debug(f"Backed up file: {source} -> {backup_path}")
                        return True
                    elif source.is_dir():
                        if backup_path.exists():
                            shutil.rmtree(backup_path)
                        shutil.copytree(source, backup_path, dirs_exist_ok=True)
                        self.logger.debug(
                            f"Backed up directory: {source} -> {backup_path}"
                        )
                        return True

                except PermissionError as e:
                    if attempt < max_retries:
                        self.logger.warning(
                            f"File {source} is locked (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        continue
                    else:
                        self.logger.error(
                            f"Failed to backup {source} after {max_retries + 1} attempts: {e}"
                        )
                        return False
                except Exception as e:
                    self.logger.error(f"Failed to backup {source}: {e}")
                    return False

            return False
        except Exception as e:
            self.logger.error(f"Failed to backup {source}: {e}")
            return False

    def create_backup_name(self, base_name: str) -> str:
        """Create a timestamped backup name.

        Args:
            base_name: Base name for the backup

        Returns:
            Timestamped backup name
        """
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"

    def backup_directories(
        self, directories: list, progress_callback=None
    ) -> BackupStats:
        """Backup multiple directories to the backup location.

        Args:
            directories: List of directories to backup
            progress_callback: Optional callback function for progress updates

        Returns:
            BackupStats object with backup operation statistics
        """
        import time

        stats = BackupStats()
        stats.start_time = time.time()

        if not self.backup_root:
            self.logger.error("Cannot backup: no backup root directory set.")
            stats.errors = len(directories)
            return stats

        total_dirs = len(directories)

        for i, directory in enumerate(directories):
            try:
                if progress_callback:
                    progress = (i / total_dirs) * 100
                    progress_callback(progress)

                self.logger.info(f"Backing up directory: {directory}")

                if directory.exists() and directory.is_dir():
                    if self.backup_item(directory):
                        stats.directories_backed_up += 1

                        # Count files in the directory
                        for file_path in directory.rglob("*"):
                            if file_path.is_file():
                                stats.files_backed_up += 1
                                stats.bytes_backed_up += file_path.stat().st_size
                    else:
                        stats.errors += 1
                else:
                    self.logger.warning(
                        f"Directory does not exist or is not a directory: {directory}"
                    )
                    stats.errors += 1

            except Exception as e:
                self.logger.error(f"Error backing up directory {directory}: {e}")
                stats.errors += 1

        stats.end_time = time.time()
        self.logger.info(
            f"Backup completed. Backed up {stats.files_backed_up} files from {stats.directories_backed_up} directories."
        )

        if progress_callback:
            progress_callback(100)

        return stats

    def get_backup_info(self) -> dict:
        """Get information about the current backup configuration.

        Returns:
            Dictionary containing backup configuration info
        """
        return {
            "backup_root": str(self.backup_root) if self.backup_root else None,
            "backup_enabled": self.backup_root is not None,
        }
