import json
import time
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ai.vision.camera_service import VisionFrameAnalysis, laptop_camera_service
from ai.vision.posture_analyzer import PostureCalibration
from backend.app.api.deps import get_current_user, get_current_user_optional, get_db
from backend.app.core.websocket_manager import ws_manager
from backend.app.models.session import SessionMetric, StudySession
from backend.app.models.user import FaceTemplate, User

router = APIRouter()


class LandmarkInput(BaseModel):
    x: float
    y: float
    z: Optional[float] = 0.0


class VisionTelemetryRequest(BaseModel):
    session_id: Optional[int] = None
    nose: Optional[LandmarkInput] = None
    left_eye: Optional[LandmarkInput] = None
    right_eye: Optional[LandmarkInput] = None
    left_ear: Optional[LandmarkInput] = None
    right_ear: Optional[LandmarkInput] = None
    left_shoulder: Optional[LandmarkInput] = None
    right_shoulder: Optional[LandmarkInput] = None
    mouth_center: Optional[LandmarkInput] = None
    eye_aspect_ratio: Optional[float] = None
    current_frame_embedding: Optional[List[float]] = None


class FrameProcessRequest(BaseModel):
    image_base64: str
    session_id: Optional[int] = None
    verify_face: Optional[bool] = False
    is_break: Optional[bool] = False
    timer_mode: Optional[str] = "work"


class FrameCalibrationRequest(BaseModel):
    image_base64: str
    is_bad_reference: Optional[bool] = False


class DualFrameCalibrationRequest(BaseModel):
    good_image_base64: str
    bad_image_base64: str


class CalibrationRequest(BaseModel):
    ear: LandmarkInput
    shoulder: LandmarkInput
    left_shoulder: Optional[LandmarkInput] = None
    right_shoulder: Optional[LandmarkInput] = None


class FaceVerifySessionRequest(BaseModel):
    image_base64: Optional[str] = None
    embedding: Optional[List[float]] = None


@router.post("/process-frame", response_model=VisionFrameAnalysis)
async def process_camera_frame(
    payload: FrameProcessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Processes a live camera video frame (base64) using local computer vision,
    evaluating posture, distraction, face verification, and metrics.
    """
    registered_embedding = None
    if payload.verify_face:
        face_res = await db.execute(
            select(FaceTemplate).where(FaceTemplate.user_id == current_user.id)
        )
        face_record = face_res.scalar_one_or_none()
        if face_record and face_record.embedding_vector:
            try:
                registered_embedding = json.loads(face_record.embedding_vector)
            except Exception:
                pass

    analysis = laptop_camera_service.process_frame_image(
        image_base64=payload.image_base64,
        session_id=payload.session_id,
        registered_face_embedding=registered_embedding,
        current_time=time.time(),
        is_break=payload.is_break or (payload.timer_mode in ("break", "long_break")),
        timer_mode=payload.timer_mode or "work",
    )

    if payload.session_id:
        sess_stmt = select(StudySession).where(
            (StudySession.id == payload.session_id) & (StudySession.user_id == current_user.id)
        )
        sess_res = await db.execute(sess_stmt)
        session = sess_res.scalar_one_or_none()
        if session and session.status == "active":
            metric_res = await db.execute(
                select(SessionMetric).where(SessionMetric.session_id == session.id)
            )
            metric = metric_res.scalar_one_or_none()
            if metric:
                if analysis.posture_state == "GOOD":
                    metric.good_posture_seconds += 1
                elif analysis.posture_state == "BUFFER":
                    metric.buffer_posture_seconds += 1
                elif analysis.posture_state == "BAD":
                    metric.bad_posture_seconds += 1
                    metric.posture_alerts_count += 1

                if analysis.focus_state == "DISTRACTED" or analysis.focus_state == "ABSENT":
                    metric.distraction_count += 1

                await db.commit()

    is_break_active = payload.is_break or (payload.timer_mode in ("break", "long_break"))
    session_status = "break" if is_break_active else ("active" if payload.session_id else "idle")

    # If posture buffer is active, calculate countdown seconds for ESP32 OLED
    timer_sec = None
    if analysis.posture_state == "BUFFER" and analysis.posture_metrics:
        timer_sec = int(round(analysis.posture_metrics.get("remaining_buffer", 3.0)))

    await ws_manager.update_study_state(
        posture=analysis.posture_state.lower(),
        focus=analysis.focus_state.lower(),
        session=session_status,
        led_state=analysis.hardware_state["led_state"],
        oled_animation=analysis.hardware_state["oled_animation"],
        message=analysis.hardware_state["oled_message"],
        timer_seconds=timer_sec,
        session_id=payload.session_id,
    )

    return analysis


@router.post("/calibrate-frame", response_model=PostureCalibration)
async def calibrate_posture_from_frame(
    payload: FrameCalibrationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Calibrates ergonomic upright or slouched reference directly from a live camera frame.
    """
    success, calib, msg = laptop_camera_service.calibrate_from_frame(
        image_base64=payload.image_base64,
        is_bad_reference=payload.is_bad_reference or False,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return calib


@router.post("/calibrate-dual", response_model=PostureCalibration)
async def calibrate_dual_posture_frames(
    payload: DualFrameCalibrationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Step 3: Extracts MediaPipe landmarks from both Good & Bad reference frames,
    validates distinction, and calculates personalized posture thresholds.
    """
    success, calib, msg = laptop_camera_service.calibrate_dual_references(
        good_image_base64=payload.good_image_base64,
        bad_image_base64=payload.bad_image_base64,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return calib


@router.post("/analyze", response_model=VisionFrameAnalysis)
async def analyze_camera_telemetry(
    payload: VisionTelemetryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Processes real-time laptop camera landmarks locally on the laptop,
    evaluates posture & focus state machines, updates session metrics,
    and synchronizes ESP32 hardware via WebSocket.
    """
    # 1. Fetch registered face template if available
    registered_embedding = None
    if payload.current_frame_embedding:
        face_res = await db.execute(
            select(FaceTemplate).where(FaceTemplate.user_id == current_user.id)
        )
        face_record = face_res.scalar_one_or_none()
        if face_record and face_record.embedding_vector:
            try:
                registered_embedding = json.loads(face_record.embedding_vector)
            except Exception:
                pass

    # Helper tuple converter
    def to_tuple(lm: Optional[LandmarkInput]) -> Optional[Tuple[float, float]]:
        return (lm.x, lm.y) if lm else None

    # 2. Execute local vision processing pipeline
    analysis = laptop_camera_service.process_vision_input(
        nose=to_tuple(payload.nose),
        left_eye=to_tuple(payload.left_eye),
        right_eye=to_tuple(payload.right_eye),
        left_ear=to_tuple(payload.left_ear),
        right_ear=to_tuple(payload.right_ear),
        left_shoulder=to_tuple(payload.left_shoulder),
        right_shoulder=to_tuple(payload.right_shoulder),
        mouth_center=to_tuple(payload.mouth_center),
        eye_aspect_ratio=payload.eye_aspect_ratio,
        registered_face_embedding=registered_embedding,
        current_frame_embedding=payload.current_frame_embedding,
        current_time=time.time(),
    )

    # 3. Update active session metrics if session_id is provided
    if payload.session_id:
        sess_stmt = select(StudySession).where(
            (StudySession.id == payload.session_id) & (StudySession.user_id == current_user.id)
        )
        sess_res = await db.execute(sess_stmt)
        session = sess_res.scalar_one_or_none()
        if session and session.status == "active":
            metric_res = await db.execute(
                select(SessionMetric).where(SessionMetric.session_id == session.id)
            )
            metric = metric_res.scalar_one_or_none()
            if metric:
                if analysis.posture_state == "GOOD":
                    metric.good_posture_seconds += 1
                elif analysis.posture_state == "BUFFER":
                    metric.buffer_posture_seconds += 1
                elif analysis.posture_state == "BAD":
                    metric.bad_posture_seconds += 1
                    metric.posture_alerts_count += 1

                if analysis.focus_state == "DISTRACTED" or analysis.focus_state == "ABSENT":
                    metric.distraction_count += 1

                await db.commit()

    session_status = "active" if payload.session_id else "idle"
    timer_sec = None
    if analysis.posture_state == "BUFFER" and analysis.posture_metrics:
        timer_sec = int(round(analysis.posture_metrics.get("remaining_buffer", 3.0)))

    # 4. Broadcast live state to ESP32 and frontend WebSocket clients
    await ws_manager.update_study_state(
        posture=analysis.posture_state.lower(),
        focus=analysis.focus_state.lower(),
        session=session_status,
        led_state=analysis.hardware_state["led_state"],
        oled_animation=analysis.hardware_state["oled_animation"],
        message=analysis.hardware_state["oled_message"],
        timer_seconds=timer_sec,
        session_id=payload.session_id,
    )

    return analysis


@router.post("/calibrate", response_model=PostureCalibration)
async def calibrate_ergonomic_posture(
    payload: CalibrationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Calibrates baseline ergonomic angles while student sits in good upright posture.
    """
    def to_tuple(lm: Optional[LandmarkInput]) -> Optional[Tuple[float, float]]:
        return (lm.x, lm.y) if lm else None

    calibration = laptop_camera_service.calibrate_posture(
        ear_pt=to_tuple(payload.ear),
        shoulder_pt=to_tuple(payload.shoulder),
        left_sh=to_tuple(payload.left_shoulder),
        right_sh=to_tuple(payload.right_shoulder),
    )
    return calibration


@router.post("/calibrate-bad", response_model=PostureCalibration)
async def calibrate_bad_posture(
    payload: CalibrationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Calibrates slouched/poor posture reference frame to establish dynamic boundary thresholds.
    """
    def to_tuple(lm: Optional[LandmarkInput]) -> Optional[Tuple[float, float]]:
        return (lm.x, lm.y) if lm else None

    calibration = laptop_camera_service.calibrate_bad_posture(
        ear_pt=to_tuple(payload.ear),
        shoulder_pt=to_tuple(payload.shoulder),
        left_sh=to_tuple(payload.left_shoulder),
        right_sh=to_tuple(payload.right_shoulder),
    )
    return calibration


@router.get("/state", response_model=Optional[VisionFrameAnalysis])
async def get_latest_vision_state():
    """Retrieves the latest processed vision frame telemetry."""
    return laptop_camera_service.latest_analysis


@router.post("/verify-session-face")
async def verify_session_face(
    payload: FaceVerifySessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies that the face in front of the laptop camera matches the registered student.
    """
    face_res = await db.execute(
        select(FaceTemplate).where(FaceTemplate.user_id == current_user.id)
    )
    face_record = face_res.scalar_one_or_none()
    if not face_record or not face_record.embedding_vector:
        return {"enrolled": False, "is_match": True, "similarity": 1.0, "message": "No face enrolled"}

    registered_embedding = json.loads(face_record.embedding_vector)

    if payload.embedding:
        current_embedding = payload.embedding
    elif payload.image_base64:
        ok, current_embedding, msg = laptop_camera_service.face_auth.extract_embedding_from_image(payload.image_base64)
        if not ok:
            return {"enrolled": True, "is_match": False, "similarity": 0.0, "message": msg}
    else:
        raise HTTPException(status_code=400, detail="Provide image_base64 or embedding")

    is_match, similarity = laptop_camera_service.face_auth.verify(
        vector_a=registered_embedding,
        vector_b=current_embedding,
        threshold=0.65,
    )

    return {
        "enrolled": True,
        "is_match": is_match,
        "similarity": round(similarity, 3),
        "status": "VERIFIED" if is_match else "MISMATCH",
    }


@router.post("/reset-session-events")
async def reset_session_vision_events(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Resets real-time posture warnings, bad posture alerts, departures, and phone use counters."""
    laptop_camera_service.reset_session_telemetry()
    return {"status": "ok", "message": "Vision session telemetry reset."}


@router.get("/session-summary")
async def get_session_vision_summary(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieves detailed log of departure events, phone use events, and posture statistics."""
    laptop_camera_service.close_ongoing_absence_if_any()
    total_absence_sec = round(sum(item.get("duration_seconds", 0) for item in laptop_camera_service.absence_history), 1)
    return {
        "absence_events_count": laptop_camera_service.absence_events_count,
        "absence_history": laptop_camera_service.absence_history,
        "total_absence_seconds": total_absence_sec,
        "phone_events_count": laptop_camera_service.phone_events_count,
        "phone_history": laptop_camera_service.phone_history,
        "bad_posture_events": laptop_camera_service.posture_analyzer.bad_posture_events,
        "confirmed_bad_alerts": laptop_camera_service.posture_analyzer.confirmed_bad_alerts,
        "bad_posture_seconds": round(laptop_camera_service.posture_analyzer.bad_posture_seconds, 1),
        "calibration": laptop_camera_service.posture_analyzer.calibration.model_dump(),
    }

