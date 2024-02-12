import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.database import Base
from src.modules.contacts.models import Contact
from src.modules.rates.models import ClientType


class InvoiceNotificationType(str, enum.Enum):
    email = "email"
    postal = "postal"


class Client(Base):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=True, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    alias = Column(String(64), nullable=False)
    client_type = Column(
        Enum(ClientType),
        default=ClientType.company,
        nullable=False,
    )

    fiscal_name = Column(String(64), index=True, unique=True)
    cif = Column(String(9), unique=True)

    contacts = relationship(Contact, back_populates="client", uselist=True)

    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="clients")

    invoice_notification_type = Column(
        Enum(InvoiceNotificationType),
        default=InvoiceNotificationType.email,
        nullable=False,
    )
    invoice_email = Column(String(256), nullable=True)
    invoice_postal = Column(String(256), nullable=True)

    bank_account_holder = Column(String(64))
    bank_account_number = Column(String(64))
    fiscal_address = Column(String(256))

    is_renewable = Column(Boolean, default=False, nullable=False)

    supply_points = relationship("SupplyPoint", back_populates="client")

    def __str__(self):
        return f"{self.__class__.__name__}: {self.fiscal_name}"
