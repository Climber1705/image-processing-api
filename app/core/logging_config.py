import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import settings

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file_path = os.path.join(LOG_DIR, "app.log")

logger = logging.getLogger("logging_config")
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]")

file_handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

if logger.level == logging.DEBUG:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

if not logger.hasHandlers():
    logger.addHandler(file_handler)


def get_logger(name: str | None = None) -> logging.Logger:
    return logger if not name else logger.getChild(name)
