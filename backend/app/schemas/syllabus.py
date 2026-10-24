from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TopicProgressUpdate(BaseModel):
    status: str = Field(..., description="Not Started, In Progress, Completed, Needs Revision")
    notes: Optional[str] = None
    confidence_level: Optional[int] = Field(None, ge=1, le=5)


class TopicOut(BaseModel):
    id: int
    module_id: int
    title: str
    subtopics: List[str] = []
    is_core: bool = False
    difficulty_level: str = "Medium"
    recommended_study_method: str = "Active Recall"
    conceptual_dependencies: List[str] = []
    status: str = "Not Started"  # Not Started, In Progress, Completed, Needs Revision
    is_completed: bool = False
    notes: Optional[str] = None
    order_index: int = 1
    model_config = ConfigDict(from_attributes=True)


class ModuleRoadmapOut(BaseModel):
    id: int
    syllabus_id: int
    name: str
    module_number: int
    description: Optional[str] = None
    order_index: int
    topics: List[TopicOut] = []
    completed_count: int = 0
    total_count: int = 0
    progress_percent: float = 0.0
    conceptual_chain: List[str] = []
    model_config = ConfigDict(from_attributes=True)


class SyllabusRoadmapOut(BaseModel):
    id: int
    user_id: int
    subject_id: int
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    title: str
    file_name: Optional[str] = None
    created_at: datetime
    modules: List[ModuleRoadmapOut] = []
    total_topics: int = 0
    completed_topics: int = 0
    in_progress_topics: int = 0
    needs_revision_topics: int = 0
    not_started_topics: int = 0
    overall_progress_percent: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class SyllabusUploadTextRequest(BaseModel):
    subject_id: int
    title: str = Field(..., min_length=1, max_length=150)
    content_text: str = Field(..., min_length=10)


class SyllabusSummaryItem(BaseModel):
    id: int
    subject_id: int
    subject_name: Optional[str] = None
    title: str
    file_name: Optional[str] = None
    created_at: datetime
    modules_count: int = 0
    topics_count: int = 0
    completed_count: int = 0
    progress_percent: float = 0.0
    model_config = ConfigDict(from_attributes=True)


# --- Preview and Registration Schemas ---
class SyllabusPreviewTopic(BaseModel):
    title: str
    subtopics: List[str] = []
    is_core: bool = False
    difficulty_level: str = "Medium"
    recommended_study_method: str = "Active Recall"
    conceptual_dependencies: List[str] = []


class SyllabusPreviewModule(BaseModel):
    module_number: int = 1
    name: str
    description: Optional[str] = ""
    topics: List[SyllabusPreviewTopic] = []


class SyllabusExtractPreviewOut(BaseModel):
    raw_text_preview: str
    modules_count: int
    topics_count: int
    subtopics_count: int
    modules: List[SyllabusPreviewModule]


class SubjectWithSyllabusCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    semester: Optional[str] = Field("Semester 1", max_length=50)
    credits: Optional[float] = Field(3.0, ge=0.5, le=30.0)
    color: Optional[str] = Field("#5A6E52", max_length=20)
    description: Optional[str] = None
    syllabus_title: Optional[str] = None
    file_name: Optional[str] = None
    modules: List[SyllabusPreviewModule]

