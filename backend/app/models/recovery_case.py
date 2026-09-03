from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    payment_event_id = Column(Integer, ForeignKey("payment_events.id"), nullable=False, unique=True, index=True)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    recovery_probability = Column(Float, nullable=False)  # 0.0 to 1.0
    recommended_action = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    status = Column(String(50), default="DETECTED", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="recovery_cases")
    payment_event = relationship("PaymentEvent", back_populates="recovery_case")
    recovery_actions = relationship("RecoveryAction", back_populates="recovery_case", cascade="all, delete-orphan")
    approvals = relationship("RecoveryApproval", back_populates="recovery_case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RecoveryCase(id={self.id}, risk={self.risk_score}, prob={self.recovery_probability}, status='{self.status}')>"
