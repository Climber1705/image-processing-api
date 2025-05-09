from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

import logging
import os

# Initialize logger
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the 'logs' folder exists

log_file_path = os.path.join(LOG_DIR, "app.log")  # Define the log file path in the 'logs' folder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Set up the file handler to write logs to the 'logs/app.log'
file_handler = logging.FileHandler(log_file_path) 
file_handler.setLevel(logging.DEBUG)

# Formatter for the logs
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or default values.
    Handles setup of application-level configuration and required directories.
    """

    APP_NAME: str = "FastAPI App"
    DEBUG: bool = True  # Set to False in production
    LOG_LEVEL: str = "DEBUG"  # Options: "DEBUG", "INFO", "WARNING", etc.

    UPLOADED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/uploaded"))
    EDITED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/edited"))
    DETECTED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/detected"))

    class Config:
        """
        Configuration for loading environment variables.
        """
        env_file = ".env"
        extra = "allow"

    def setup(self) -> None:
        """
        Creates necessary directories for file storage if they don't exist.

        @return: None
        """
        for path in [self.UPLOADED_FOLDER, self.EDITED_FOLDER, self.DETECTED_FOLDER]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            else:
                logger.debug(f"Directory already exists: {path}")

# Initialize settings
settings = Settings()
settings.setup()

# Expose as default for global access
default = settings
