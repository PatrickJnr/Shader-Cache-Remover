"""
Logging configuration for the Shader Cache Remover application.

This module provides centralized logging configuration and utilities
for managing log output and formatting.
"""

import logging
import logging.handlers
from typing import Optional
from pathlib import Path


class LoggingConfig:
    """Configuration and utilities for application logging."""

    def __init__(self, log_level: str = "INFO", detailed: bool = True):
        """Initialize logging configuration.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            detailed: Whether to enable detailed logging format
        """
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.detailed = detailed
        self.logger = logging.getLogger(__name__)

    def setup_logging(
        self, log_to_file: bool = False, log_file: Optional[Path] = None
    ) -> None:
        """Set up logging configuration for the application.

        Args:
            log_to_file: Whether to also log to a file
            log_file: Optional path to log file. If not provided, uses default location.
        """
        # Clear existing handlers to avoid duplicates
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set root logger level
        root_logger.setLevel(self.log_level)

        # Create formatters
        if self.detailed:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
        else:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler (optional)
        if log_to_file:
            if log_file is None:
                log_file = Path.home() / "shader_cache_remover.log"

            try:
                # Ensure log directory exists
                log_file.parent.mkdir(parents=True, exist_ok=True)

                # Use rotating file handler to prevent log files from getting too large
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=10 * 1024 * 1024,
                    backupCount=5,  # 10MB max, 5 backups
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                self.logger.info(f"Logging to file: {log_file}")

            except Exception as e:
                self.logger.error(f"Failed to set up file logging: {e}")

        self.logger.info(
            f"Logging configured with level: {logging.getLevelName(self.log_level)}"
        )

    def set_log_level(self, level: str) -> None:
        """Set the logging level.

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(self.log_level)
        self.logger.info(
            f"Log level changed to: {logging.getLevelName(self.log_level)}"
        )

    def enable_detailed_logging(self) -> None:
        """Enable detailed logging format."""
        self.detailed = True
        self._update_formatters()

    def disable_detailed_logging(self) -> None:
        """Disable detailed logging format."""
        self.detailed = False
        self._update_formatters()

    def _update_formatters(self) -> None:
        """Update formatters for all handlers with current detailed setting."""
        if self.detailed:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
        else:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Update all handlers
        for handler in logging.getLogger().handlers:
            handler.setFormatter(formatter)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name.

        Args:
            name: Name for the logger

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def create_queue_handler(self, log_queue) -> logging.Handler:
        """Create a queue handler for GUI logging.

        Args:
            log_queue: Queue to send log messages to

        Returns:
            QueueHandler instance
        """
        queue_handler = logging.handlers.QueueHandler(log_queue)

        if self.detailed:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
        else:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        queue_handler.setFormatter(formatter)
        return queue_handler
