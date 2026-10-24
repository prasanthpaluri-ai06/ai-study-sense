from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class SemesterConfig(Base):
    __tablename__ = "semester_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    start_date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    end_date = Column(String(10), nullable=False)    # "YYYY-MM-DD"
    study_days = Column(JSON, default=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
    max_daily_tasks = Column(Integer, default=3)
    target_study_hours_daily = Column(Float, default=3.0)
    is_configured = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="semester_config")


class BlackoutDate(Base):
    __tablename__ = "blackout_dates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    reason = Column(String(150), nullable=False)  # e.g., "Midterm Exams", "Diwali Break", "Personal Day"
    blackout_type = Column(String(50), default="holiday")  # "holiday", "exam", "personal", "break"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="blackout_dates")


class PlannedTask(Base):
    __tablename__ = "planned_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(250), nullable=False)
    module_name = Column(String(150), nullable=True)
    task_type = Column(String(50), default="learning")  # "learning", "practice", "revision", "assignment", "custom"
    scheduled_date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    priority = Column(String(20), default="Medium")  # "Critical", "High", "Medium", "Low"
    estimated_minutes = Column(Integer, default=45)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    is_manual_override = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="planned_tasks")
    subject = relationship("Subject")
    topic = relationship("Topic")
    assignment = relationship("Assignment")
