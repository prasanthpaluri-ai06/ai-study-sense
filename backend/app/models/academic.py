from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True)
    semester = Column(String(50), default="Semester 1", nullable=False)
    credits = Column(Float, default=3.0, nullable=False)
    color = Column(String(20), default="#5A6E52")  # Restrained pastel theme color
    target_score = Column(Float, default=85.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subjects")
    marks = relationship("Mark", back_populates="subject", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")
    syllabi = relationship("Syllabus", back_populates="subject", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="subject")


class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    assessment_name = Column(String(100), nullable=False)  # e.g., "CAT 1", "Quiz 2", "Midterm"
    assessment_type = Column(String(50), default="CAT/internal", nullable=False)  # CAT/internal, Quiz, Assignment, Lab, Midterm, End semester, Other
    scored_marks = Column(Float, nullable=False)
    total_marks = Column(Float, nullable=False)
    weightage_percent = Column(Float, nullable=True)  # Configurable weighting % (e.g., 20.0 for 20%)
    notes = Column(Text, nullable=True)
    recorded_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subject = relationship("Subject", back_populates="marks")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    priority = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    status = Column(String(20), default="Not Started")  # Not Started, In Progress, Completed, Overdue
    progress_percent = Column(Integer, default=0)  # Completion percentage (0-100)
    estimated_effort_hours = Column(Float, default=2.0)  # Estimated effort in hours
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subject = relationship("Subject", back_populates="assignments")
