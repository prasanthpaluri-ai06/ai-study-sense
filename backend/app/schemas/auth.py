from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: Optional[str] = None
    institution: Optional[str] = None  # College / Institution
    course: Optional[str] = None       # Optional (removed from mandatory registration)
    year: Optional[str] = None         # Optional (removed from mandatory registration)
    semester: Optional[str] = None     # Optional (removed from mandatory registration)
    face_image_base64: Optional[str] = None
    face_embedding: Optional[List[float]] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean.isalnum() and not all(c.isalnum() or c == "_" for c in clean):
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        return clean

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: Optional[str], info) -> Optional[str]:
        if v is not None and "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class VerifyCredentialsRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class CredentialVerificationResponse(BaseModel):
    status: str = "verified"
    user_id: int
    username: str
    full_name: str
    has_face_enrolled: bool
    requires_face_step: bool = True
    session_challenge: str


class FaceLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    session_challenge: Optional[str] = None
    face_image_base64: Optional[str] = None
    face_embedding: Optional[List[float]] = None


class FaceEnrollRequest(BaseModel):
    face_image_base64: Optional[str] = None
    face_embedding: Optional[List[float]] = None


class FaceValidationRequest(BaseModel):
    face_image_base64: str = Field(..., min_length=1)


class FaceValidationResponse(BaseModel):
    valid: bool
    message: str
    has_embedding: bool = False


class FallbackLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    reason: Optional[str] = "Camera unavailable / Biometric fallback"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    auth_method: str = "password_plus_face"
    model_config = ConfigDict(from_attributes=True)
