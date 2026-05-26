import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    UPLOAD_DIR: str = "./temp_uploads"
    LOG_LEVEL: str = "INFO"
    MAX_CONTENT_LENGTH: int = 524288000  # Default 500 MB in bytes
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure upload directory exists relative to current working directory or absolute
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
