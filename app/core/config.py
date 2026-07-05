import os
import logging
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
    )

    LOG_LEVEL: str = "DEBUG"

    UPLOADED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/uploaded"))
    EDITED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/edited"))
    DETECTED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/detected"))

    DATABASE_URL: str = "sqlite:///./app/data/images.db"

    MODEL_NAME: str = "facebook/detr-resnet-50"
    MODEL_REVISION: str | None = None
    CONFIDENCE_THRESHOLD: float = 0.5
    INFERENCE_DEVICE: str = "cpu"
    MAX_IMAGE_DIMENSION: int = 1333
    WARMUP_ON_STARTUP: bool = True

    FORMAT_EXTENSIONS: dict[str, str] = {
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",  
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "WEBP": ".webp",
    }

    @property
    def directories(self) -> dict[str, Path]:
        dirs = {
            "uploaded": self.UPLOADED_FOLDER,
            "edited": self.EDITED_FOLDER,
            "detected": self.DETECTED_FOLDER,
        }
        logger.debug("Configured directories: %s", dirs)
        return dirs

    @property
    def format_extensions(self) -> dict[str, str]:
        logger.debug("Supported format extensions: %s", self.FORMAT_EXTENSIONS)
        return self.FORMAT_EXTENSIONS

    def setup(self) -> None:
        for path in [self.UPLOADED_FOLDER, self.EDITED_FOLDER, self.DETECTED_FOLDER]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info("Created directory: %s", path)
            else:
                logger.debug("Directory already exists: %s", path)

        if self.DATABASE_URL.startswith("sqlite:///./"):
            db_path = Path(self.DATABASE_URL.removeprefix("sqlite:///./"))
            db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.setup()
    return settings


settings = get_settings()