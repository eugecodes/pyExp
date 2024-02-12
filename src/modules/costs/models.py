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

from src.infrastructure.sqlalchemy.common import ArrayOfEnum
from src.infrastructure.sqlalchemy.database import Base
from src.modules.rates.models import ClientType


class EnergyCost(Base):
    __tablename__ = "energy_cost"

    id = Column(Integer, primary_key=True)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    is_protected = Column(Boolean, default=False, nullable=False)
    concept = Column(String(124), index=True, nullable=False, unique=True)
    amount = Column(Numeric(14, 6))
    code = Column(String(32), unique=True)

    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="energy_costs")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.concept}"


class OtherCostType(str, enum.Enum):
    eur_month = "eur/month"
    percentage = "percentage"
    eur_kwh = "eur/kwh"


other_cost_rates_association = Table(
    "other_costs_rates",
    Base.metadata,
    Column("other_cost_id", ForeignKey("other_cost.id")),
    Column("rate_id", ForeignKey("rate.id")),
    UniqueConstraint("other_cost_id", "rate_id"),
)


class OtherCost(Base):
    __tablename__ = "other_cost"

    id = Column(Integer, primary_key=True)
    name = Column(String(124), unique=True, nullable=False)
    mandatory = Column(Boolean, nullable=False)
    client_types = Column(ArrayOfEnum(Enum(ClientType)), nullable=False)
    min_power = Column(Numeric(10, 2))
    max_power = Column(Numeric(10, 2))
    type = Column(String(10), Enum(OtherCostType), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    extra_fee = Column(Numeric(10, 2))
    rates = relationship(
        "Rate", secondary=other_cost_rates_association, backref="other_costs"
    )

    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    @property
    def marketer_id(self):
        return self.rates[0].marketer_id

    @property
    def energy_type(self):
        return self.rates[0].rate_type.energy_type
