"""
Notifications infrastructure for Windows toast notifications.

Uses win10toast or plyer for cross-platform notification support.
"""

import logging
from typing import Optional


class NotificationService:
    """Service for displaying system notifications."""

    def __init__(self):
        """Initialize the notification service."""
        self.logger = logging.getLogger(__name__)
        self._notifier = None
        self._available = False
        self._init_notifier()

    def _init_notifier(self):
        """Initialize the notification backend."""
        # Try win10toast first (Windows-specific, higher quality)
        try:
            from win10toast import ToastNotifier
            self._notifier = ToastNotifier()
            self._available = True
            self.logger.debug("Using win10toast for notifications")
            return
        except ImportError:
            pass

        # Fall back to plyer (cross-platform)
        try:
            from plyer import notification
            self._notifier = notification
            self._available = True
            self.logger.debug("Using plyer for notifications")
            return
        except ImportError:
            pass

        self.logger.warning("No notification backend available. Install win10toast or plyer.")

    def is_available(self) -> bool:
        """Check if notifications are available."""
        return self._available

    def notify(
        self,
        title: str,
        message: str,
        duration: int = 5,
        icon_path: Optional[str] = None,
    ) -> bool:
        """Show a notification.

        Args:
            title: Notification title
            message: Notification message
            duration: How long to show (seconds)
            icon_path: Optional path to icon

        Returns:
            True if notification was shown, False otherwise
        """
        if not self._available:
            self.logger.debug(f"Notification (not shown): {title} - {message}")
            return False

        try:
            if hasattr(self._notifier, "show_toast"):
                # win10toast
                self._notifier.show_toast(
                    title,
                    message,
                    duration=duration,
                    icon_path=icon_path,
                    threaded=True,
                )
            else:
                # plyer
                self._notifier.notify(
                    title=title,
                    message=message,
                    timeout=duration,
                    app_icon=icon_path,
                )
            return True

        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            return False

    def notify_cleanup_complete(
        self,
        files_deleted: int,
        bytes_freed: int,
        was_dry_run: bool = False,
    ) -> bool:
        """Show a notification for cleanup completion.

        Args:
            files_deleted: Number of files deleted
            bytes_freed: Bytes freed
            was_dry_run: Whether this was a dry run

        Returns:
            True if notification was shown
        """
        # Format bytes
        if bytes_freed >= 1024 * 1024 * 1024:
            size_str = f"{bytes_freed / (1024**3):.1f} GB"
        elif bytes_freed >= 1024 * 1024:
            size_str = f"{bytes_freed / (1024**2):.1f} MB"
        elif bytes_freed >= 1024:
            size_str = f"{bytes_freed / 1024:.1f} KB"
        else:
            size_str = f"{bytes_freed} B"

        if was_dry_run:
            title = "Dry Run Complete"
            message = f"Would delete {files_deleted} files ({size_str})"
        else:
            title = "Cleanup Complete"
            message = f"Deleted {files_deleted} files, freed {size_str}"

        return self.notify(title, message)
