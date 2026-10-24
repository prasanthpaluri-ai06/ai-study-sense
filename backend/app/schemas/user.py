from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class StudentProfileBase(BaseModel):
    institution: Optional[str] = None
    course: Optional[str] = None
    year: Optional[str] = None
    semester: Optional[str] = None
    target_study_hours_daily: Optional[int] = 4
    preferred_method: Optional[str] = "Pomodoro"


class StudentProfileOut(StudentProfileBase):
    id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    profile: Optional[StudentProfileOut] = None
    has_face_enrolled: bool = False
    model_config = ConfigDict(from_attributes=True)
