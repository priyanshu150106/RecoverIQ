from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecoveryOutcome(Base):
    """Tracks measurable outcomes and analytics for recovery strategy executions."""

    __tablename__ = "recovery_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    recovery_case_id = Column(Integer, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    recovery_action_id = Column(Integer, ForeignKey("recovery_actions.id", ondelete="SET NULL"), nullable=True, index=True)
    strategy_type = Column(String(100), nullable=False)
    outcome_status = Column(String(50), default="PENDING", nullable=False, index=True)  # RECOVERED, PARTIALLY_RECOVERED, FAILED, EXPIRED, CANCELLED, PENDING
    amount_at_risk = Column(Integer, nullable=False)  # in paise
    amount_recovered = Column(Integer, default=0, nullable=False)  # in paise
    recovery_percentage = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    execution_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    recovery_timestamp = Column(DateTime, nullable=True)
    time_to_recovery_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="outcomes")
    recovery_action = relationship("RecoveryAction")

    def __repr__(self):
        return f"<RecoveryOutcome(id={self.id}, case_id={self.recovery_case_id}, status='{self.outcome_status}', recovered={self.amount_recovered}/{self.amount_at_risk})>"
