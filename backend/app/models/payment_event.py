from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # in paise
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), nullable=False, index=True)
    failure_reason = Column(String(255), nullable=True)
    external_event_id = Column(String(255), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="payment_events")
    recovery_case = relationship("RecoveryCase", back_populates="payment_event", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PaymentEvent(id={self.id}, type='{self.event_type}', amount={self.amount}, status='{self.status}')>"
