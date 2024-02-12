from datetime import datetime

from pydantic import BaseModel, Field

from config.settings import settings


class HealthCheck(BaseModel):
    status: str = "OK"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestCheck(BaseModel):
    status: str = "OK"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    test: str = settings.SENDIN_BLUE_API_KEY
