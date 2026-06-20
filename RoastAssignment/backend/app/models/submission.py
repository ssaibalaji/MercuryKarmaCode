"""Submission model."""
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin


class SyncStatus(enum.Enum):
    pending = "pending"
    synced = "synced"
    error = "error"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_name = Column(String(200), nullable=False)
    student_email = Column(String(255), nullable=False, index=True)
    assignment_name = Column(String(200), nullable=False)
    github_repo_url = Column(String(500), nullable=False)
    google_form_response_id = Column(String(255), unique=True, index=True, nullable=False)
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.pending, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", back_populates="submissions")
    evaluation = relationship(
        "Evaluation",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_submissions_user_submitted", "user_id", "submitted_at"),
    )
