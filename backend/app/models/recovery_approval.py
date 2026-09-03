from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecoveryApproval(Base):
    """Represents a Human-in-the-Loop operator approval record for recovery strategy execution."""

    __tablename__ = "recovery_approvals"

    id = Column(Integer, primary_key=True, index=True)
    recovery_case_id = Column(Integer, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_type = Column(String(100), nullable=False)
    requested_by = Column(String(100), default="merchant_operator", nullable=False)
    approved_by = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, EXECUTED, EXPIRED
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Relationship to RecoveryCase
    recovery_case = relationship("RecoveryCase", back_populates="approvals")

    def __repr__(self):
        return f"<RecoveryApproval(id={self.id}, case_id={self.recovery_case_id}, strategy='{self.strategy_type}', status='{self.status}')>"
