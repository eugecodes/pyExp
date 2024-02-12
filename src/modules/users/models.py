import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.database import Base
from src.modules.costs.models import EnergyCost
from src.modules.marketers.models import Marketer
from src.modules.rates.models import RateType
from src.modules.contracts.models import Contract
from src.modules.saving_studies.models import SavingStudy
from src.modules.supply_points.models import SupplyPoint
from src.modules.clients.models import Client
from src.modules.contacts.models import Contact


class UserRole(str, enum.Enum):
    admin = "admin"
    super_admin = "super_admin"
    marketer_manager = "marketer_manager"
    back_office = "back_office"
    energy_manager = "energy_manager"


class User(Base):
    __tablename__ = "user_table"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(32), index=True, nullable=False)
    last_name = Column(String(64), index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256))
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responsible_id = Column(Integer, ForeignKey("user_table.id"))
    role = Column(String(20), Enum(UserRole))

    responsible = relationship("User", remote_side=[id], order_by=id)
    token = relationship("Token", back_populates="user", uselist=False)
    contracts = relationship(Contract, back_populates="user")
    rate_types = relationship(RateType, back_populates="user")
    energy_costs = relationship(EnergyCost, back_populates="user")
    marketers = relationship(Marketer, back_populates="user")
    saving_studies = relationship(SavingStudy, back_populates="user_creator")
    clients = relationship(Client, back_populates="user")
    contacts = relationship(Contact, back_populates="user")
    supply_points = relationship(SupplyPoint, back_populates="user")


class Token(Base):
    __tablename__ = "token"

    id = Column(Integer, primary_key=True)
    token = Column(String(128), nullable=False, unique=True)

    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="token")
