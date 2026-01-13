"""
Scheduler service for Windows Task Scheduler integration.

Allows scheduling automatic shader cache cleanup at regular intervals.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional


class SchedulerService:
    """Service for managing scheduled cleanup tasks via Windows Task Scheduler."""

    TASK_NAME = "ShaderCacheRemoverCleanup"

    def __init__(self):
        """Initialize the scheduler service."""
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if Task Scheduler is available."""
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/?"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def is_scheduled(self) -> bool:
        """Check if cleanup task is currently scheduled."""
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.TASK_NAME],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def schedule_cleanup(
        self,
        frequency: str = "WEEKLY",
        day: str = "SUN",
        time: str = "03:00",
    ) -> bool:
        """Schedule automatic cleanup.

        Args:
            frequency: DAILY, WEEKLY, or MONTHLY
            day: Day of week (e.g., SUN, MON) for weekly
            time: Time in HH:MM format

        Returns:
            True if scheduled successfully
        """
        try:
            # Get path to the script
            script_path = Path(sys.executable).parent / "Scripts" / "shader-cache-remover.exe"
            if not script_path.exists():
                # Try the python script directly
                script_path = Path(__file__).parent.parent.parent / "remove_shader_cache.py"
                if not script_path.exists():
                    self.logger.error("Could not find cleanup script")
                    return False
                command = f'"{sys.executable}" "{script_path}" --cleanup --quiet'
            else:
                command = f'"{script_path}" --cleanup --quiet'

            # Build schtasks command
            schtasks_args = [
                "schtasks", "/Create",
                "/TN", self.TASK_NAME,
                "/TR", command,
                "/SC", frequency,
                "/ST", time,
                "/F",  # Force overwrite
            ]

            if frequency == "WEEKLY":
                schtasks_args.extend(["/D", day])

            result = subprocess.run(
                schtasks_args,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info(f"Scheduled cleanup: {frequency} at {time}")
                return True
            else:
                self.logger.error(f"Failed to schedule: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to schedule cleanup: {e}")
            return False

    def unschedule_cleanup(self) -> bool:
        """Remove the scheduled cleanup task.

        Returns:
            True if removed successfully
        """
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", self.TASK_NAME, "/F"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("Removed scheduled cleanup task")
                return True
            else:
                self.logger.error(f"Failed to remove task: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to unschedule cleanup: {e}")
            return False

    def get_schedule_info(self) -> Optional[dict]:
        """Get information about the current schedule.

        Returns:
            Dict with schedule info or None if not scheduled
        """
        if not self.is_scheduled():
            return None

        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.TASK_NAME, "/FO", "LIST", "/V"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                info = {}
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key in ["Next Run Time", "Schedule Type", "Start Time"]:
                                info[key] = value
                return info

        except Exception as e:
            self.logger.error(f"Failed to get schedule info: {e}")

        return None
