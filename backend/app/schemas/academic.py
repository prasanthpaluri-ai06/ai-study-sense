from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Subject Schemas ---
class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    semester: Optional[str] = Field("Semester 1", max_length=50)
    credits: Optional[float] = Field(3.0, ge=0.5, le=30.0)
    color: Optional[str] = Field("#5A6E52", max_length=20)
    target_score: Optional[float] = Field(85.0, ge=0.0, le=100.0)
    description: Optional[str] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = None
    semester: Optional[str] = None
    credits: Optional[float] = Field(None, ge=0.5, le=30.0)
    color: Optional[str] = None
    target_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    description: Optional[str] = None


class SubjectOut(SubjectBase):
    id: int
    user_id: int
    created_at: datetime
    average_score: Optional[float] = None
    weighted_score: Optional[float] = None
    total_weightage_recorded: Optional[float] = 0.0
    marks_count: Optional[int] = 0
    assignments_count: Optional[int] = 0
    has_syllabus: bool = False
    syllabus_id: Optional[int] = None
    syllabus_progress_percent: Optional[float] = None
    syllabus_total_topics: Optional[int] = 0
    syllabus_completed_topics: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


# --- Mark Schemas ---
class MarkBase(BaseModel):
    subject_id: int
    assessment_name: str = Field(..., min_length=1, max_length=100)
    assessment_type: str = Field("CAT/internal", description="CAT/internal, Quiz, Assignment, Lab, Midterm, End semester, Other")
    scored_marks: float = Field(..., ge=0.0)
    total_marks: float = Field(..., gt=0.0)
    weightage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None
    recorded_date: Optional[datetime] = None


class MarkCreate(MarkBase):
    pass


class MarkUpdate(BaseModel):
    assessment_name: Optional[str] = None
    assessment_type: Optional[str] = None
    scored_marks: Optional[float] = Field(None, ge=0.0)
    total_marks: Optional[float] = Field(None, gt=0.0)
    weightage_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None
    recorded_date: Optional[datetime] = None


class MarkOut(MarkBase):
    id: int
    recorded_date: datetime
    percentage: float = 0.0
    weighted_contribution: Optional[float] = None
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SubjectPerformanceOut(BaseModel):
    subject_id: int
    subject_name: str
    subject_code: Optional[str] = None
    semester: str
    credits: float
    target_score: float
    simple_average: Optional[float] = None
    weighted_average: Optional[float] = None
    total_weightage_used: float = 0.0
    performance_status: str  # Exceeding Target, On Track, Needs Review, Critical
    performance_trend: str  # Improving, Stable, Declining, Insufficient Data
    marks_count: int
    marks: List[MarkOut] = []


# --- Assignment Schemas ---
class AssignmentBase(BaseModel):
    subject_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: datetime
    priority: Optional[str] = Field("Medium", description="Low, Medium, High, Critical")
    status: Optional[str] = Field("Not Started", description="Not Started, In Progress, Completed, Overdue")
    progress_percent: Optional[int] = Field(0, ge=0, le=100)
    estimated_effort_hours: Optional[float] = Field(2.0, ge=0.1, le=100.0)
    notes: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    subject_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    estimated_effort_hours: Optional[float] = Field(None, ge=0.1, le=100.0)
    notes: Optional[str] = None


class AssignmentOut(AssignmentBase):
    id: int
    created_at: datetime
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    is_overdue: bool = False
    hours_remaining: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


# --- AI Prioritized Assignment & Dashboard Summary Schemas ---
class ScoreComponent(BaseModel):
    score: float
    weight_percent: int
    detail: str


class ScoreBreakdown(BaseModel):
    urgency: ScoreComponent
    priority: ScoreComponent
    academic_importance: ScoreComponent
    estimated_effort: ScoreComponent
    workload_pressure: ScoreComponent


class AIPrioritizedAssignmentOut(BaseModel):
    assignment_id: int
    title: str
    subject_id: int
    subject_name: str
    subject_color: str
    due_date: datetime
    priority: str
    status: str
    progress_percent: int
    estimated_effort_hours: float
    is_overdue: bool
    hours_remaining: float
    priority_score: float
    score_breakdown: ScoreBreakdown
    recommendation_reason: str


class AcademicSummaryOut(BaseModel):
    total_subjects: int
    total_assignments: int
    pending_assignments_count: int
    overdue_assignments_count: int
    completed_assignments_count: int
    completion_rate_percent: float
    overall_academic_average: Optional[float] = None
    overall_weighted_gpa_score: Optional[float] = None
    upcoming_deadlines: List[AssignmentOut] = []
    overdue_tasks: List[AssignmentOut] = []
    subject_performances: List[SubjectPerformanceOut] = []
    top_priority_assignments: List[AIPrioritizedAssignmentOut] = []


class SubjectDetailOut(SubjectOut):
    marks: List[MarkOut] = []
    assignments: List[AssignmentOut] = []
