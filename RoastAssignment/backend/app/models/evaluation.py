"""Evaluation model."""
import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin


class EvaluationStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    ai_roast_text = Column(Text, nullable=True)
    ai_score = Column(Float, nullable=True)
    static_analysis_report = Column(JSON, nullable=True)
    static_analysis_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.pending, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="evaluation")
