from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class Syllabus(Base):
    __tablename__ = "syllabi"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    raw_content = Column(Text, nullable=True)
    file_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="syllabi")
    subject = relationship("Subject", back_populates="syllabi")
    modules = relationship("Module", back_populates="syllabus", cascade="all, delete-orphan", order_by="Module.order_index")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    syllabus_id = Column(Integer, ForeignKey("syllabi.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    module_number = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=1)

    syllabus = relationship("Syllabus", back_populates="modules")
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan", order_by="Topic.order_index")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    subtopics = Column(JSON, nullable=True)  # List of subtopics e.g. ["BST insertion", "BST deletion"]
    is_core = Column(Boolean, default=False)  # Important/core topic flag
    difficulty_level = Column(String(20), default="Medium")  # Easy, Medium, Hard
    recommended_study_method = Column(String(50), default="Active Recall")  # Pomodoro, 52/17, Active Recall, Spaced Repetition, Feynman
    conceptual_dependencies = Column(JSON, nullable=True)  # List of prerequisite topic names in order
    prerequisites = Column(Text, nullable=True)
    order_index = Column(Integer, default=1)

    module = relationship("Module", back_populates="topics")
    progress = relationship("TopicProgress", back_populates="topic", cascade="all, delete-orphan")


class TopicProgress(Base):
    __tablename__ = "topic_progress"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Status: Not Started, In Progress, Completed, Needs Revision
    status = Column(String(30), default="Not Started", nullable=False)
    is_completed = Column(Boolean, default=False)
    confidence_level = Column(Integer, default=3)  # 1 to 5 scale
    notes = Column(Text, nullable=True)
    last_studied_at = Column(DateTime, nullable=True)
    next_revision_at = Column(DateTime, nullable=True)
    total_study_minutes = Column(Integer, default=0)

    topic = relationship("Topic", back_populates="progress")
