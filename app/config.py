# app/config.py
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field("", description="Telegram bot token")
    DB_DSN: str = Field("sqlite+aiosqlite:///./bot.db", description="SQLAlchemy DSN")
    REDIS_DSN: str = Field("redis://redis:6379/0", description="Redis DSN used by the app")
    RANKS_FILE: str = Field("./data/ranks.json", description="Path to ranks JSON")
    ADMINS: str = Field("", description="Comma-separated list of admin Telegram IDs, e.g. '123,456'")

    # pydantic v2 settings
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # ignore extra env keys (so REDIS_URL etc won't break)
    }

    def admin_ids(self) -> List[int]:
        """Return list of admin ids parsed from ADMINS (safe int conversion)."""
        if not self.ADMINS:
            return []
        parts = [p.strip() for p in self.ADMINS.replace(" ", ",").split(",") if p.strip()]
        ids: List[int] = []
        for p in parts:
            try:
                ids.append(int(p))
            except ValueError:
                # skip invalid values silently
                continue
        return ids

# Instantiate settings
settings = Settings()

# Support alternative env names for Redis (REDIS_URL or REDIS_URI).
_alt_redis = os.getenv("REDIS_URL") or os.getenv("REDIS_URI")
if _alt_redis:
    # override only if user didn't set a custom REDIS_DSN explicitly different from default
    # or unconditionally if you prefer alt to win — currently we let alt override always
    settings.REDIS_DSN = _alt_redis
