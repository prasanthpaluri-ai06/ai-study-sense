from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class StudyHealthScore(Base):
    """
    Holistic composite score (0-100) representing the student's study habits:
    Focus, Consistency, Academics, Posture, Task Completion, Revision.
    Non-medical habit metric.
    """
    __tablename__ = "study_health_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)
    focus_component = Column(Float, default=80.0)
    consistency_component = Column(Float, default=80.0)
    academic_component = Column(Float, default=80.0)
    posture_component = Column(Float, default=80.0)
    task_component = Column(Float, default=80.0)
    revision_component = Column(Float, default=80.0)
    ai_interpretation = Column(Text, nullable=True)
    calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="health_scores")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="Study Action")  # Weakness, Revision, Deadline, Study Method
    content = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    recommended_method = Column(String(50), nullable=True)
    topic_ref = Column(String(100), nullable=True)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="recommendations")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # deadline, revision, habit, achievement
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")
