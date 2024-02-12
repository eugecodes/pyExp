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


class ContractStatusEnum(str, enum.Enum):
    INCOMPLETE = "incomplete"
    REQUESTED = "requested"
    WAITING_MARKETER = "waiting-marketer"
    WAITING_CLIENT_SIGN = "waiting-client-sign"
    SIGNED = "signed"
    ACTIVATED = "activated"
    FINISHED = "finished"
    MARKETER_ISSUE = "marketer-issue"
    DISTRIBUTOR_ISSUE = "distributor-issue"
    CANCELLED = "cancelled"


class Contract(Base):
    __tablename__ = "contract"

    status = Column(
        Enum(ContractStatusEnum),
        default=ContractStatusEnum.INCOMPLETE,
        nullable=False,
    )

    id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=True, nullable=False)
    create_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_id = Column(Integer, ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="contracts")

    # client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    # client = relationship("Client", back_populates="contracts")

    supply_point_id = Column(Integer, ForeignKey("supply_point.id"), nullable=False)
    supply_point = relationship("SupplyPoint", back_populates="contracts")

    rate_id = Column(Integer, ForeignKey("rate.id"), nullable=False)
    rate = relationship("Rate", back_populates="contracts")

    saving_study_id = Column(Integer, ForeignKey("saving_study.id"), nullable=True)
    saving_study = relationship("SavingStudy", back_populates="contract")

    power_1 = Column(Numeric(14, 6))
    power_2 = Column(Numeric(14, 6))
    power_3 = Column(Numeric(14, 6))
    power_4 = Column(Numeric(14, 6))
    power_5 = Column(Numeric(14, 6))
    power_6 = Column(Numeric(14, 6))

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    expected_end_date = Column(DateTime, nullable=True)
    preferred_start_date = Column(DateTime, nullable=True)
    period = Column(Integer)

    signature_first_name = Column(String(128), nullable=False)
    signature_last_name = Column(String(128), nullable=False)
    signature_dni = Column(String(20))
    signature_email = Column(String(256))
    signature_phone = Column(String(30))

    status_message = Column(String(256))

    def __str__(self):
        return f"{self.__class__.__name__}: {self.id}"
