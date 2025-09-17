"""Production logging configuration with file rotation."""

import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """Setup basic logging configuration for production"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/buildflow.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )

    # Simple formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Configure logger
    logger = logging.getLogger("buildflow")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger