from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.infrastructure.sqlalchemy.database import Base


class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=False, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    name = Column(String(128), nullable=False)
    email = Column(String(256))
    phone = Column(String(30))

    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    client = relationship("Client", back_populates="contacts", uselist=False)
    is_main_contact = Column(Boolean, default=False, nullable=False)

    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="contacts")

    def __str__(self):
        return f"{self.__class__.__name__}: {self.name}"
