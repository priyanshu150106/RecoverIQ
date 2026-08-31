from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    recovery_case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    external_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="recovery_actions")

    def __repr__(self):
        return f"<RecoveryAction(id={self.id}, case_id={self.recovery_case_id}, type='{self.action_type}', status='{self.status}')>"
