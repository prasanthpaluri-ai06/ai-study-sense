from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI StudySense"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "studysense-dev-secret-key-change-in-production-min32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days for continuous desktop study session experience
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./studysense.db"

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Hardware & ESP32
    ESP32_API_KEY: str = "studysense_esp32_device_secret_2026"
    ESP32_WS_PATH: str = "/ws/esp32"

    # Vision & Posture Engine Config
    POSTURE_BUFFER_SECONDS: float = 5.0
    POSTURE_BAD_THRESHOLD_SECONDS: float = 10.0
    POSTURE_ANGLE_THRESHOLD: float = 25.0
    CAMERA_INDEX: int = 0
    ENABLE_MOOD_ANALYSIS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
