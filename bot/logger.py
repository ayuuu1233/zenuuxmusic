"""
Logging configuration for Zenuux Music Bot.
Provides structured logging to console and files.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import config

# Ensure logs directory exists
config.LOGS_DIR.mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color codes."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        
        record.levelname = f"{color}{levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str,
    log_level: str = config.LOG_LEVEL,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log file
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file or True:  # Always create file handler
        log_filename = log_file or f"{name.replace('.', '_')}.log"
        log_path = config.LOGS_DIR / log_filename
        
        try:
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")

    return logger


# Global logger for the bot
logger = setup_logger("zenuuxmusic.bot")

# Module-specific loggers
db_logger = setup_logger("zenuuxmusic.db", log_file="database.log")
music_logger = setup_logger("zenuuxmusic.music", log_file="music.log")
handler_logger = setup_logger("zenuuxmusic.handlers", log_file="handlers.log")
utils_logger = setup_logger("zenuuxmusic.utils", log_file="utils.log")


async def log_error(
    error: Exception,
    context: str = "",
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
) -> None:
    """
    Log an error with context information.
    
    Args:
        error: The exception to log
        context: Additional context string
        user_id: Telegram user ID (optional)
        chat_id: Telegram chat ID (optional)
    """
    error_msg = f"{context} | Error: {str(error)}"
    
    if user_id:
        error_msg += f" | User: {user_id}"
    
    if chat_id:
        error_msg += f" | Chat: {chat_id}"
    
    logger.error(error_msg, exc_info=True)
