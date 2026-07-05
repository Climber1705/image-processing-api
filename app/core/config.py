from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.media.domain.enums import ImageFolder


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
    MAX_CONCURRENT_INFERENCES: int = 2

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
        return {
            ImageFolder.UPLOADED: self.UPLOADED_FOLDER,
            ImageFolder.EDITED: self.EDITED_FOLDER,
            ImageFolder.DETECTED: self.DETECTED_FOLDER,
        }

    @property
    def format_extensions(self) -> dict[str, str]:
        return self.FORMAT_EXTENSIONS

    def setup(self) -> None:
        for path in [self.UPLOADED_FOLDER, self.EDITED_FOLDER, self.DETECTED_FOLDER]:
            path.mkdir(parents=True, exist_ok=True)

        if self.DATABASE_URL.startswith("sqlite:///./"):
            db_path = Path(self.DATABASE_URL.removeprefix("sqlite:///./"))
            db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.setup()
    return settings


settings = get_settings()
