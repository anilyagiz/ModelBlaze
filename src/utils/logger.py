"""
Logger - Centralized logging configuration
Structured logging for debugging and monitoring
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ModelBlazeLogger:
    """
    Centralized logging configuration for ModelBlaze

    Features:
    - Console output (INFO level)
    - File output (DEBUG level)
    - Structured log format
    - Automatic log rotation by day
    """

    _instance: Optional[logging.Logger] = None
    _log_dir: Optional[Path] = None

    @classmethod
    def get_logger(cls, name: str = "modelblaze") -> logging.Logger:
        """
        Get or create logger instance (Singleton pattern)

        Args:
            name: Logger name

        Returns:
            Configured logger instance
        """
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance

    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        """
        Setup logger with console and file handlers

        Args:
            name: Logger name

        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers if logger already configured
        if logger.handlers:
            return logger

        # Console handler (INFO level for user-friendly output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # File handler (DEBUG level for detailed debugging)
        try:
            log_dir = cls._get_log_directory()
            log_file = log_dir / f"modelblaze_{datetime.now():%Y%m%d}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")

        except (OSError, PermissionError) as e:
            # If file logging fails, only use console
            logger.warning(f"Could not setup file logging: {e}")

        logger.addHandler(console_handler)

        return logger

    @classmethod
    def _get_log_directory(cls) -> Path:
        """
        Get or create log directory

        Returns:
            Log directory Path
        """
        if cls._log_dir is None:
            # Try user home directory first
            log_dir = Path.home() / ".modelblaze" / "logs"

            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                cls._log_dir = log_dir
            except (OSError, PermissionError):
                # Fallback to current directory
                log_dir = Path.cwd() / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                cls._log_dir = log_dir

        return cls._log_dir

    @classmethod
    def set_log_level(cls, level: str):
        """
        Set logging level

        Args:
            level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        if cls._instance:
            numeric_level = getattr(logging, level.upper(), logging.INFO)
            cls._instance.setLevel(numeric_level)

    @classmethod
    def disable_file_logging(cls):
        """Disable file logging (keep only console)"""
        if cls._instance:
            # Remove file handlers
            cls._instance.handlers = [
                h for h in cls._instance.handlers
                if not isinstance(h, logging.FileHandler)
            ]


# Convenience function
def get_logger(name: str = "modelblaze") -> logging.Logger:
    """
    Get logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return ModelBlazeLogger.get_logger(name)
