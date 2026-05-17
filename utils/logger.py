import logging
import logging.handlers
import os
from pathlib import Path
from pythonjsonlogger import jsonlogger


def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """Setup logger with both console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        json_format = jsonlogger.JsonFormatter()
        file_handler.setFormatter(json_format)
        logger.addHandler(file_handler)

    return logger
