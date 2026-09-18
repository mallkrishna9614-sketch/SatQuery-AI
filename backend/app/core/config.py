from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SatQuery AI Backend"
    APP_VERSION: str = "0.1.0"

    API_PREFIX: str = "/api/v1"

    DATA_DIR: str = "data"

    MAX_UPLOAD_MB: int = 512

    CORS_ORIGINS: str = "*"

    # Remote ML inference service
    ML_BASE_URL: str = ""
    ML_TIMEOUT_SECONDS: float = 120.0
    ML_POLL_INTERVAL_SECONDS: float = 2.0
    ML_DEFAULT_COMPARE_YEAR: str = "2024"
    ML_DEFAULT_CURRENT_YEAR: str = "2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def upload_dir(self) -> Path:
        path = Path(self.DATA_DIR) / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def report_dir(self) -> Path:
        path = Path(self.DATA_DIR) / "reports"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
