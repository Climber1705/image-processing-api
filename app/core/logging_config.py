
from app.core.config import settings

import logging
from logging.handlers import RotatingFileHandler
import os


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file_path = os.path.join(LOG_DIR, "app.log")

logger = logging.getLogger("logging_config")
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)

file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

if settings.DEBUG:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG) 
    logger.addHandler(console_handler)

if not logger.hasHandlers():
    logger.addHandler(file_handler)

def get_logger(name: str = None) -> logging.Logger:
    """
    Retrieve a logger instance, either the main app logger or a child logger.

    @param name: Optional name for a child logger.
    @return: The logger instance (either the main logger or a child logger).
    """
    # If a name is provided, return a child logger; otherwise, return the main logger
    return logger if not name else logger.getChild(name)
