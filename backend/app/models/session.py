import json
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    topic_name = Column(String(200), nullable=True)
    study_method = Column(String(50), default="Pomodoro", nullable=False)  # Pomodoro, 52/17, Active Recall, Spaced Repetition, Feynman Technique
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, default=0.0)
    status = Column(String(20), default="active", nullable=False)  # active, paused, completed, cancelled
    method_metadata = Column(JSON, nullable=True)  # Stores method-specific data (SM-2 scores, Active Recall questions, Feynman stages)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="study_sessions")
    subject = relationship("Subject", back_populates="study_sessions")
    metric = relationship("SessionMetric", back_populates="session", uselist=False, cascade="all, delete-orphan")
    focus_records = relationship("FocusRecord", back_populates="session", cascade="all, delete-orphan")
    posture_records = relationship("PostureRecord", back_populates="session", cascade="all, delete-orphan")


class SpacedRepetitionCard(Base):
    __tablename__ = "spaced_repetition_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    front_prompt = Column(Text, nullable=False)  # Question, formula, concept prompt
    back_answer = Column(Text, nullable=False)  # Expected recall explanation
    ease_factor = Column(Float, default=2.5, nullable=False)
    interval_days = Column(Integer, default=0, nullable=False)
    repetitions_count = Column(Integer, default=0, nullable=False)
    last_quality_rating = Column(Integer, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subject = relationship("Subject")


class SessionMetric(Base):
    __tablename__ = "session_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    focus_score = Column(Float, default=100.0)  # 0 to 100%
    posture_score = Column(Float, default=100.0)  # 0 to 100%
    productivity_score = Column(Float, default=80.0)  # 0 to 100
    good_posture_seconds = Column(Integer, default=0)
    buffer_posture_seconds = Column(Integer, default=0)
    bad_posture_seconds = Column(Integer, default=0)
    posture_alerts_count = Column(Integer, default=0)
    distraction_count = Column(Integer, default=0)
    ai_feedback_summary = Column(Text, nullable=True)

    session = relationship("StudySession", back_populates="metric")


class FocusRecord(Base):
    __tablename__ = "focus_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="focused")  # focused, distracted, away, unknown
    confidence = Column(Float, default=1.0)

    session = relationship("StudySession", back_populates="focus_records")


class PostureRecord(Base):
    __tablename__ = "posture_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    state = Column(String(20), default="good")  # good, buffer, bad
    angle_degrees = Column(Float, default=0.0)
    led_color = Column(String(10), default="GREEN")  # GREEN, YELLOW, RED

    session = relationship("StudySession", back_populates="posture_records")
