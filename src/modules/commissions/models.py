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
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.database import Base


class MarginType(str, enum.Enum):
    rate_type = "rate_type"
    consume_range = "consume_range"


class RangeType(str, enum.Enum):
    power = "power"
    consumption = "consumption"


commissions_rates_association = Table(
    "commissions_rates",
    Base.metadata,
    Column("commission_id", ForeignKey("commission.id")),
    Column("rate_id", ForeignKey("rate.id")),
    UniqueConstraint("commission_id", "rate_id"),
)


class Commission(Base):
    __tablename__ = "commission"

    id = Column(Integer, primary_key=True)
    name = Column(String(124), nullable=False)
    percentage_Test_commission = Column(Integer)
    rate_type_segmentation = Column(Boolean)
    range_type = Column(String(11), Enum(RangeType))
    min_consumption = Column(Numeric(14, 2))
    max_consumption = Column(Numeric(14, 2))
    min_power = Column(Numeric(14, 2))
    max_power = Column(Numeric(14, 2))
    Test_commission = Column(Numeric(14, 2))
    is_deleted = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rate_type_id = Column(Integer, ForeignKey("rate_type.id"))

    rate_type = relationship("RateType", back_populates="commissions")
    rates = relationship(
        "Rate", secondary=commissions_rates_association, backref="commissions"
    )

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name}"

    @property
    def marketer_id(self):
        try:
            return self.rates[0].marketer_id
        except IndexError:
            return None

    @property
    def rate_type__energy_type(self):
        try:
            return self.rate_type.energy_type
        except (IndexError, AttributeError):
            return None

    @property
    def rates__energy_type(self):
        try:
            return self.rates[0].rate_type.energy_type
        except (IndexError, AttributeError):
            return None

    @property
    def price_type(self):
        try:
            return self.rates[0].price_type
        except IndexError:
            return None
