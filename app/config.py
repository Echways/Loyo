from typing import Optional
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    DEBUG: bool = False
    DATABASE_URL: Optional[PostgresDsn] = None
    REDIS_URL: Optional[str] = None
    ADMIN_IDS: str = ""  # "1,2,3" — можно затем парсить

    # В pydantic v2 конфиг задаётся через model_config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # игнорировать лишние поля
    )

settings = Settings()
