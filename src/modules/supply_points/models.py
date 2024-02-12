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
from src.modules.rates.models import EnergyType


class CounterType(str, enum.Enum):
    normal = "normal"
    telematic = "telematic"


class OwnerType(str, enum.Enum):
    self = "self"
    marketer = "marketer"
    other = "other"


class SupplyPoint(Base):
    __tablename__ = "supply_point"

    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=True, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="supply_points")

    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    client = relationship("Client", back_populates="supply_points")

    energy_type = Column(
        Enum(EnergyType),
        default=EnergyType.electricity,
        nullable=False,
    )

    cups = Column(String(124), nullable=False, unique=True)
    alias = Column(String(64), nullable=True)

    # Address
    supply_address = Column(String(256))
    supply_postal_code = Column(String(10))
    supply_city = Column(String(256))
    supply_province = Column(String(256))

    # Finance Information
    bank_account_holder = Column(String(64))
    bank_account_number = Column(String(64))
    fiscal_address = Column(String(256))

    # Technical information
    is_renewable = Column(Boolean, default=False, nullable=False)
    max_available_power = Column(Integer)
    voltage = Column(Integer)

    # Counter
    counter_type = Column(
        Enum(CounterType),
        default=CounterType.normal,
        nullable=True,
    )
    counter_property = Column(
        Enum(OwnerType),
        default=OwnerType.self,
        nullable=True,
    )
    counter_price = Column(Numeric(10, 2))

    contracts = relationship("Contract", back_populates="supply_point")

    def __str__(self):
        return f"{self.__class__.__name__}: {self.alias} - {self.cups}"
