from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from pathlib import Path

import logging
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file_path = os.path.join(LOG_DIR, "app.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI App"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    UPLOADED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/uploaded"))
    EDITED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/edited"))
    DETECTED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/detected"))

    MODEL_NAME: str = "facebook/detr-resnet-50"
    MODEL_REVISION: str | None = None
    CONFIDENCE_THRESHOLD: float = 0.5
    INFERENCE_DEVICE: str = "cpu"
    MAX_IMAGE_DIMENSION: int = 1333
    WARMUP_ON_STARTUP: bool = True

    model_config = ConfigDict(
        env_file=".env",
        extra="allow",
    )

    def setup(self) -> None:
        for path in [self.UPLOADED_FOLDER, self.EDITED_FOLDER, self.DETECTED_FOLDER]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            else:
                logger.debug(f"Directory already exists: {path}")


settings = Settings()
settings.setup()

default = settings
