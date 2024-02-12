from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.database import Base


class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    type = Column(String(16))
    name = Column(String(128))
    number = Column(Integer)
    subdivision = Column(String(64))
    others = Column(String(64))
    postal_code = Column(String(16))
    city = Column(String(64))
    province = Column(String(64))

    marketer = relationship("Marketer", back_populates="address", uselist=False)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name} {self.type} {self.number}, {self.city}"


class Marketer(Base):
    __tablename__ = "marketer"

    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    name = Column(String(64), nullable=False)
    fiscal_name = Column(String(64), index=True, unique=True)
    cif = Column(String(9), unique=True)
    email = Column(String(256))
    fee = Column(Numeric(14, 6))
    max_consume = Column(Numeric(12, 2))
    consume_range_datetime = Column(DateTime)
    # TODO: Remove it
    surplus_price = Column(Numeric(14, 6))

    address_id = Column(Integer, ForeignKey("address.id"))
    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)

    address = relationship("Address", back_populates="marketer")
    user = relationship("User", back_populates="marketers")
    rate = relationship("Rate", back_populates="marketer", uselist=False)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.fiscal_name}"
