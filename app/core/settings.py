from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings # type: ignore
from pydantic import Field

class APISettings(BaseSettings):

    # Base application settings
    APP_NAME: str = "Image Processing API"
    DEBUG: bool = Field(False, env="API_DEBUG")
    VERSION: str = "1.0.0"

    # Server configuration
    #HOST: str = "0.0.0.0"
    #PORT: int = 8000
    #WORKERS: int = 4
    
    # Security settings
    #SECRET_KEY: str = Field("changeme_in_production", env="API_SECRET_KEY")
    #ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    #API_KEYS: Dict[str, str] = {}  # For API key auth
    
    # Database settings
    #DB_URL: str = Field("sqlite:///./app.db", env="API_DB_URL")
    #DB_POOL_SIZE: int = 5
    #DB_MAX_OVERFLOW: int = 10

    # File storage settings
    UPLOAD_FOLDER: Path = Field(default_factory=lambda: Path("app/static/uploads"))
    PROCESSED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/processed"))
    ANALYZED_FOLDER: Path = Field(default_factory=lambda: Path("app/static/analysed"))

    SUPPORTED_FORMATS: Dict[str, str] = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "WEBP": ".webp",
    }


    # Performance tuning
    #RATE_LIMIT_UPLOADS: int = 10  # per minute
    #RATE_LIMIT_PROCESSES: int = 20  # per minute
    #REQUEST_TIMEOUT: int = 60  # seconds

    # Logging configuration
    #LOG_LEVEL: str = "INFO"
    #LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    #LOG_FILE: Path = Field(default_factory=lambda: Path("logs/api.log"))

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_prefix = "API_"
        case_sensitive = True

    def setup(self) -> None:
        """Create necessary directories for file storage."""
        for path in [self.UPLOAD_FOLDER, self.PROCESSED_FOLDER, self.ANALYZED_FOLDER]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {path}")

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        """Return FastAPI kwargs for app initialization."""
        return {
            "debug": self.DEBUG,
            "title": self.APP_NAME,
            "version": self.VERSION,
        }
    
settings = APISettings()
settings.setup()

default = settings