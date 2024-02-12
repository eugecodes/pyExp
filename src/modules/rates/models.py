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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.common import ArrayOfEnum
from src.infrastructure.sqlalchemy.database import Base


class EnergyType(str, enum.Enum):
    electricity = "electricity"
    gas = "gas"


class PriceType(str, enum.Enum):
    fixed_fixed = "fixed_fixed"
    fixed_base = "fixed_base"


class ClientType(str, enum.Enum):
    company = "company"
    self_employed = "self-employed"
    particular = "particular"
    community_owners = "community_owners"


class PriceName(str, enum.Enum):
    energy_price_1 = "energy_price_1"
    energy_price_2 = "energy_price_2"
    energy_price_3 = "energy_price_3"
    energy_price_4 = "energy_price_4"
    energy_price_5 = "energy_price_5"
    energy_price_6 = "energy_price_6"
    power_price_1 = "power_price_1"
    power_price_2 = "power_price_2"
    power_price_3 = "power_price_3"
    power_price_4 = "power_price_4"
    power_price_5 = "power_price_5"
    power_price_6 = "power_price_6"
    fixed_term_price = "fixed_term_price"


class RateType(Base):
    __tablename__ = "rate_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    energy_type = Column(String(11), Enum(EnergyType), nullable=False)
    max_power = Column(Numeric(10, 2))
    min_power = Column(Numeric(10, 2))
    enable = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)

    user = relationship("User", back_populates="rate_types")
    commissions = relationship("Commission", back_populates="rate_type")
    rate = relationship("Rate", back_populates="rate_type", uselist=False)
    saving_studies = relationship("SavingStudy", back_populates="current_rate_type")

    __table_args__ = (UniqueConstraint("name", "energy_type"),)


class Rate(Base):
    __tablename__ = "rate"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)
    price_type = Column(String(11), Enum(PriceType), nullable=False)
    client_types = Column(
        ArrayOfEnum(Enum(ClientType)), nullable=False, default=[ClientType.particular]
    )
    min_power = Column(Numeric(10, 2))
    max_power = Column(Numeric(10, 2))
    min_consumption = Column(Numeric(10, 2))
    max_consumption = Column(Numeric(10, 2))
    energy_price_1 = Column(Numeric(14, 6))
    energy_price_2 = Column(Numeric(14, 6))
    energy_price_3 = Column(Numeric(14, 6))
    energy_price_4 = Column(Numeric(14, 6))
    energy_price_5 = Column(Numeric(14, 6))
    energy_price_6 = Column(Numeric(14, 6))
    power_price_1 = Column(Numeric(14, 6))
    power_price_2 = Column(Numeric(14, 6))
    power_price_3 = Column(Numeric(14, 6))
    power_price_4 = Column(Numeric(14, 6))
    power_price_5 = Column(Numeric(14, 6))
    power_price_6 = Column(Numeric(14, 6))
    fixed_term_price = Column(Numeric(14, 6))
    permanency = Column(Boolean, nullable=False)
    length = Column(Integer, nullable=False)
    is_full_renewable = Column(Boolean)
    compensation_surplus = Column(Boolean)
    compensation_surplus_value = Column(Numeric(14, 6))

    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rate_type_id = Column(Integer, ForeignKey("rate_type.id"), nullable=False)
    marketer_id = Column(Integer, ForeignKey("marketer.id"), nullable=False)

    rate_type = relationship("RateType", back_populates="rate")
    marketer = relationship("Marketer", back_populates="rate")
    margin = relationship("Margin", back_populates="rate")
    historical_rate = relationship(
        "HistoricalRate", back_populates="rate", uselist=False
    )

    contracts = relationship("Contract", back_populates="rate")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"


class HistoricalRate(Base):
    __tablename__ = "historical_rate"

    id = Column(Integer, primary_key=True)
    price_name = Column(String(16), Enum(PriceName), nullable=False)
    price = Column(Numeric(14, 6))
    modified_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rate_id = Column(Integer, ForeignKey("rate.id"), nullable=False)
    rate = relationship("Rate", back_populates="historical_rate")

    __table_args__ = (UniqueConstraint("price_name", "price", "modified_at"),)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.rate_id}.{self.price_name} = {self.price}"
