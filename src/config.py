import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_path: str = "db/retail.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Ensure database directory exists
db_dir = Path(settings.database_path).parent
db_dir.mkdir(parents=True, exist_ok=True)

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)