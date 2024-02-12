# Sqlalchemy model for saving studies
import enum
from datetime import datetime
from decimal import Decimal

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
from src.modules.rates.models import ClientType, EnergyType, PriceType


class SavingStudyStatusEnum(str, enum.Enum):
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"


class MarginType(str, enum.Enum):
    rate_type = "rate_type"
    consume_range = "consume_range"


class SavingStudy(Base):
    __tablename__ = "saving_study"

    id = Column(Integer, primary_key=True)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_creator_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    is_deleted = Column(Boolean, default=False)
    status = Column(
        Enum(SavingStudyStatusEnum),
        default=SavingStudyStatusEnum.IN_PROGRESS,
        nullable=False,
    )
    energy_type = Column(
        Enum(EnergyType),
        default=EnergyType.electricity,
        nullable=False,
    )

    is_existing_client = Column(Boolean, nullable=False, default=False)
    is_from_sips = Column(Boolean, nullable=False, default=False)
    is_compare_conditions = Column(Boolean, nullable=False, default=False)

    cups = Column(String(124), nullable=False)
    analyzed_days = Column(Integer)
    current_rate_type_id = Column(Integer, ForeignKey("rate_type.id"))
    current_marketer = Column(String(124))

    # client data
    client_type = Column(Enum(ClientType))
    client_name = Column(String(124))
    client_nif = Column(String(10))

    # energy
    consumption_p1 = Column(Integer)
    consumption_p2 = Column(Integer)
    consumption_p3 = Column(Integer)
    consumption_p4 = Column(Integer)
    consumption_p5 = Column(Integer)
    consumption_p6 = Column(Integer)
    annual_consumption = Column(Numeric(10, 2), nullable=False, default=0)
    energy_price_1 = Column(Numeric(10, 6))
    energy_price_2 = Column(Numeric(10, 6))
    energy_price_3 = Column(Numeric(10, 6))
    energy_price_4 = Column(Numeric(10, 6))
    energy_price_5 = Column(Numeric(10, 6))
    energy_price_6 = Column(Numeric(10, 6))
    # power
    power_1 = Column(Numeric(10, 2))
    power_2 = Column(Numeric(10, 2))
    power_3 = Column(Numeric(10, 2))
    power_4 = Column(Numeric(10, 2))
    power_5 = Column(Numeric(10, 2))
    power_6 = Column(Numeric(10, 2))
    power_price_1 = Column(Numeric(10, 6))
    power_price_2 = Column(Numeric(10, 6))
    power_price_3 = Column(Numeric(10, 6))
    power_price_4 = Column(Numeric(10, 6))
    power_price_5 = Column(Numeric(10, 6))
    power_price_6 = Column(Numeric(10, 6))

    fixed_price = Column(Numeric(14, 6))
    other_cost_kwh = Column(Numeric(14, 6))
    other_cost_percentage = Column(Numeric(14, 6))
    other_cost_eur_month = Column(Numeric(14, 6))

    user_creator = relationship("User", back_populates="saving_studies")
    suggested_rates = relationship("SuggestedRate", back_populates="saving_study")
    current_rate_type = relationship("RateType", back_populates="saving_studies")
    contract = relationship("Contract", back_populates="saving_study")

    def __str__(self) -> str:
        return f"SavingStudy(id={self.id}, cups={self.cups})"

    @property
    def total_consumption(self) -> int:
        if self.current_rate_type.energy_type == EnergyType.gas:
            return self.consumption_p1 or Decimal("0.0")

        total_consumption = Decimal("0.0")
        for i in range(1, 7):
            if consumption := getattr(self, f"consumption_p{i}"):
                total_consumption += consumption

        return total_consumption

    @property
    def selected_suggested_rate(self):
        for suggested_rate in self.suggested_rates:
            if suggested_rate.is_selected:
                return suggested_rate
        return None


class SuggestedRate(Base):
    __tablename__ = "suggested_rate"

    id = Column(Integer, primary_key=True)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_selected = Column(Boolean, default=False, nullable=False)
    saving_study_id = Column(Integer, ForeignKey("saving_study.id"), nullable=False)

    marketer_name = Column(String(124), nullable=False)
    has_contractual_commitment = Column(Boolean, nullable=False)
    duration = Column(Integer, nullable=False)
    rate_name = Column(String(124), nullable=False)
    is_full_renewable = Column(Boolean, nullable=False)
    has_net_metering = Column(Boolean, nullable=False)
    net_metering_value = Column(Numeric(10, 2), nullable=False)

    # margin
    profit_margin_type = Column(String(13), Enum(MarginType))
    min_profit_margin = Column(Numeric(14, 6), nullable=False)
    max_profit_margin = Column(Numeric(14, 6), nullable=False)
    applied_profit_margin = Column(Numeric(10, 2), nullable=False)

    # rate
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
    price_type = Column(String(11), Enum(PriceType))

    # computed data
    final_cost = Column(Numeric(10, 2))
    energy_cost = Column(Numeric(10, 2))
    power_cost = Column(Numeric(10, 2))
    fixed_cost = Column(Numeric(10, 2))
    other_costs = Column(Numeric(10, 2))
    ie_cost = Column(Numeric(10, 2))
    ih_cost = Column(Numeric(10, 2))
    iva_cost = Column(Numeric(10, 2))

    total_commission = Column(Numeric(10, 2))
    theoretical_commission = Column(Numeric(10, 2))
    other_costs_commission = Column(Numeric(10, 2))

    saving_relative = Column(Numeric(10, 2))
    saving_absolute = Column(Numeric(10, 2))

    saving_study = relationship("SavingStudy", back_populates="suggested_rates")

    def __str__(self) -> str:
        return f"SuggestedRate(id={self.id}, rate_name={self.rate_name})"
