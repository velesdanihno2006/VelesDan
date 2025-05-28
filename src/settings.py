# settings.py
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import logging

# Загружаем .env
load_dotenv()


@dataclass
class Settings:
    tg_token: str = os.getenv("TG_TOKEN", "").strip()
    openai_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    max_voice_sec: int = 60

    def validate(self):
        if not (self.tg_token and self.openai_key):
            raise RuntimeError("TG_TOKEN or OPENAI_API_KEY missing in .env")


settings = Settings()
settings.validate()

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
