from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StudySessionCreate(BaseModel):
    subject_id: Optional[int] = None
    topic_name: Optional[str] = Field(None, max_length=200)
    study_method: str = Field("Pomodoro", description="Pomodoro, 52/17, Active Recall, Spaced Repetition, Feynman Technique")
    method_metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class StudySessionEnd(BaseModel):
    duration_minutes: Optional[float] = None
    method_metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class StudySessionStatusUpdate(BaseModel):
    status: str = Field(..., description="active, paused, completed, cancelled")
    method_metadata: Optional[Dict[str, Any]] = None


class PostureUpdate(BaseModel):
    state: str  # good, buffer, bad
    angle_degrees: float
    led_color: Optional[str] = None


class FocusUpdate(BaseModel):
    status: str  # focused, distracted, away, unknown
    confidence: Optional[float] = 1.0


class SessionMetricOut(BaseModel):
    focus_score: float
    posture_score: float
    productivity_score: float
    good_posture_seconds: int
    buffer_posture_seconds: int
    bad_posture_seconds: int
    posture_alerts_count: int
    distraction_count: int
    ai_feedback_summary: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class StudySessionOut(BaseModel):
    id: int
    user_id: int
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    topic_name: Optional[str] = None
    study_method: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: float
    status: str
    method_metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    metric: Optional[SessionMetricOut] = None
    model_config = ConfigDict(from_attributes=True)


# --- Spaced Repetition (SM-2) Schemas ---
class SM2CalculateRequest(BaseModel):
    quality_rating: int = Field(..., ge=0, le=5, description="Recall score 0 (blackout) to 5 (perfect recall)")
    repetition_number: Optional[int] = Field(0, ge=0)
    ease_factor: Optional[float] = Field(2.5, ge=1.3)
    interval_days: Optional[int] = Field(0, ge=0)


class SM2CalculateResponse(BaseModel):
    quality_rating: int
    quality_description: str
    repetition_number: int
    ease_factor: float
    interval_days: int
    next_review_date: datetime
    is_successful: bool


class SpacedRepetitionCardCreate(BaseModel):
    subject_id: int
    front_prompt: str = Field(..., min_length=1)
    back_answer: str = Field(..., min_length=1)


class SpacedRepetitionCardReview(BaseModel):
    quality_rating: int = Field(..., ge=0, le=5)


class SpacedRepetitionCardOut(BaseModel):
    id: int
    user_id: int
    subject_id: int
    subject_name: Optional[str] = None
    front_prompt: str
    back_answer: str
    ease_factor: float
    interval_days: int
    repetitions_count: int
    last_quality_rating: Optional[int] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_date: datetime
    is_due: bool = False
    model_config = ConfigDict(from_attributes=True)
