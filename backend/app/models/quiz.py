from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_title = Column(String(200), nullable=False)
    score = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    strong_areas = Column(Text, nullable=True)  # JSON or summary
    weak_areas = Column(Text, nullable=True)    # JSON or summary
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="quiz_attempts")
    questions = relationship("QuizQuestion", back_populates="attempt", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), default="MCQ")  # MCQ, ShortAnswer, Concept
    options = Column(Text, nullable=True)  # JSON string of choices
    correct_answer = Column(Text, nullable=False)
    student_answer = Column(Text, nullable=True)
    is_correct = Column(Float, default=0.0)
    explanation = Column(Text, nullable=True)

    attempt = relationship("QuizAttempt", back_populates="questions")
