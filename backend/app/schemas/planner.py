from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SemesterConfigCreate(BaseModel):
    start_date: str = Field(..., description="Semester start date YYYY-MM-DD")
    end_date: str = Field(..., description="Semester end date YYYY-MM-DD")
    study_days: Optional[List[str]] = Field(
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        description="Active study weekdays",
    )
    max_daily_tasks: Optional[int] = Field(default=3, ge=1, le=10)
    target_study_hours_daily: Optional[float] = Field(default=3.0, ge=0.5, le=16.0)


class SemesterConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    start_date: str
    end_date: str
    study_days: List[str]
    max_daily_tasks: int
    target_study_hours_daily: float
    is_configured: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BlackoutDateCreate(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    reason: str = Field(..., min_length=1, max_length=150)
    blackout_type: Optional[str] = Field(default="holiday", description="holiday, exam, personal, break")


class BlackoutDateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    reason: str
    blackout_type: str


class PlannedTaskCreate(BaseModel):
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    assignment_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=250)
    module_name: Optional[str] = None
    task_type: Optional[str] = Field(default="learning", description="learning, practice, revision, assignment, custom")
    scheduled_date: str = Field(..., description="YYYY-MM-DD")
    priority: Optional[str] = Field(default="Medium", description="Critical, High, Medium, Low")
    estimated_minutes: Optional[int] = Field(default=45, ge=5, le=360)
    notes: Optional[str] = None


class PlannedTaskReschedule(BaseModel):
    scheduled_date: str = Field(..., description="YYYY-MM-DD")


class PlannedTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    subject_color: Optional[str] = None
    topic_id: Optional[int] = None
    assignment_id: Optional[int] = None
    title: str
    module_name: Optional[str] = None
    task_type: str
    scheduled_date: str
    priority: str
    estimated_minutes: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    is_manual_override: bool
    notes: Optional[str] = None
    order_index: int


class RebalancePreviewResponse(BaseModel):
    shifted_tasks: List[Dict[str, Any]]
    newly_scheduled: List[Dict[str, Any]]
    warnings: List[str]
    total_days_available: int
    average_daily_workload: float
    summary: str


class PlannerOverviewResponse(BaseModel):
    is_configured: bool
    semester: Optional[SemesterConfigOut] = None
    days_total: int = 0
    days_elapsed: int = 0
    days_remaining: int = 0
    semester_progress_percent: float = 0.0
    syllabus_progress_percent: float = 0.0
    total_topics_count: int = 0
    completed_topics_count: int = 0
    today_tasks: List[PlannedTaskOut] = []
    overdue_assignments: List[Dict[str, Any]] = []
    upcoming_assignments: List[Dict[str, Any]] = []
    subject_cards: List[Dict[str, Any]] = []
    blackout_dates: List[BlackoutDateOut] = []
    ai_insights: List[Dict[str, Any]] = []
    workload_warnings: List[str] = []
