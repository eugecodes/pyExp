from typing import List

from config.settings.base import TestBaseSettings


class Settings(TestBaseSettings):
    BACKEND_CORS_ORIGINS: List[str] = None
    EMAIL_MODE: str = "EXTERNAL_API"
