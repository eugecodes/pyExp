import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.database import Base


class MarginType(str, enum.Enum):
    rate_type = "rate_type"
    consume_range = "consume_range"


class Margin(Base):
    __tablename__ = "margin"

    id = Column(Integer, primary_key=True)
    type = Column(String(13), Enum(MarginType), nullable=False)
    min_consumption = Column(Numeric(14, 2))
    max_consumption = Column(Numeric(14, 2))
    min_margin = Column(Numeric(14, 4), default=0, nullable=False)
    max_margin = Column(Numeric(14, 4), default=100, nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rate_id = Column(Integer, ForeignKey("rate.id"), nullable=False)

    rate = relationship("Rate", back_populates="margin")

    def __str__(self):
        return f"{self.__class__.__name__}: {self.type} for rate_id {self.rate_id}"
