import time
import pytest
from httpx import AsyncClient
from ai.vision.camera_service import LaptopCameraAIService
from ai.vision.focus_tracker import FocusState, FocusTracker
from ai.vision.mood_estimator import MoodEstimator, MoodState
from ai.vision.posture_analyzer import PostureAnalyzer, PostureState


def test_posture_calibration_and_geometry():
    """Verify that PostureAnalyzer computes geometric angles and calibrates baselines correctly."""
    analyzer = PostureAnalyzer(buffer_duration=4.0, recovery_duration=1.0)

    # Simulate upright baseline (ear at (0.5, 0.2), shoulder at (0.5, 0.5)) -> 0 deg from vertical
    calib = analyzer.calibrate(
        ear_point=(0.5, 0.2),
        shoulder_point=(0.5, 0.5),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
    )

    assert calib.is_calibrated is True
    assert abs(calib.baseline_neck_angle - 0.0) < 1.0
    assert abs(calib.baseline_shoulder_angle - 0.0) < 1.0


def test_posture_state_machine_hysteresis():
    """
    Verify the strict state machine sequence:
    GOOD -> poor posture -> BUFFER
    BUFFER -> remains poor beyond threshold -> BAD
    BAD -> corrected -> GOOD
    Verify single-frame poor posture does NOT trigger BAD.
    """
    analyzer = PostureAnalyzer(
        buffer_duration=4.0,
        recovery_duration=1.0,
        neck_deviation_threshold=15.0,
        smoothing_alpha=1.0,  # Fast alpha for deterministic testing
    )

    # 1. Calibrate baseline upright
    analyzer.calibrate(ear_point=(0.5, 0.2), shoulder_point=(0.5, 0.5))

    # 2. Initial good frame at t=0
    t0 = 100.0
    res0 = analyzer.process_landmarks(
        nose=(0.5, 0.25),
        left_ear=(0.45, 0.2),
        right_ear=(0.55, 0.2),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
        current_time=t0,
    )
    assert res0["state"] == PostureState.GOOD
    assert res0["led_color"] == "GREEN"

    # 3. Slumped forward posture (ear shifted forward to x=0.7, dy=0.3 -> angle ~ 33 deg > 15 deg threshold)
    # At t=1.0s (single poor frame) -> Must enter BUFFER, NOT BAD
    t1 = t0 + 1.0
    res1 = analyzer.process_landmarks(
        nose=(0.7, 0.25),
        left_ear=(0.65, 0.2),
        right_ear=(0.75, 0.2),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
        current_time=t1,
    )
    assert res1["state"] == PostureState.BUFFER
    assert res1["led_color"] == "YELLOW"

    # At t=3.0s (still within 4s buffer duration) -> Must still be BUFFER
    t2 = t0 + 3.0
    res2 = analyzer.process_landmarks(
        nose=(0.7, 0.25),
        left_ear=(0.65, 0.2),
        right_ear=(0.75, 0.2),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
        current_time=t2,
    )
    assert res2["state"] == PostureState.BUFFER

    # At t=5.5s (elapsed 4.5s > 4.0s buffer duration) -> Transitions to BAD
    t3 = t0 + 5.5
    res3 = analyzer.process_landmarks(
        nose=(0.7, 0.25),
        left_ear=(0.65, 0.2),
        right_ear=(0.75, 0.2),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
        current_time=t3,
    )
    assert res3["state"] == PostureState.BAD
    assert res3["led_color"] == "RED"

    # 4. Posture corrected at t=6.0s (held good for 1.2s -> t=7.2s) -> Recovers to GOOD
    t4 = t0 + 7.2
    res4 = analyzer.process_landmarks(
        nose=(0.5, 0.25),
        left_ear=(0.45, 0.2),
        right_ear=(0.55, 0.2),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
        current_time=t4,
    )
    assert res4["state"] == PostureState.GOOD
    assert res4["led_color"] == "GREEN"


def test_focus_presence_state_transitions():
    """Verify FocusTracker debounces glances and tracks visual absence and head yaw."""
    tracker = FocusTracker(
        absence_threshold_seconds=4.0,
        distraction_threshold_seconds=3.0,
        recovery_threshold_seconds=1.0,
        smoothing_alpha=1.0,
    )

    t0 = 200.0

    # 1. Looking at screen (centered landmarks)
    res_center = tracker.process_frame_state(
        face_detected=True,
        head_pose=FocusTracker.estimate_head_pose_from_landmarks(
            nose=(0.5, 0.4),
            left_eye=(0.45, 0.35),
            right_eye=(0.55, 0.35),
            left_ear=(0.4, 0.35),
            right_ear=(0.6, 0.35),
            mouth_center=(0.5, 0.5),
        ),
        current_time=t0,
    )
    assert res_center["state"] == FocusState.FOCUSED
    assert res_center["face_present"] is True

    # 2. Turned away (nose shifted far right -> yaw > 25 deg)
    pose_turned = FocusTracker.estimate_head_pose_from_landmarks(
        nose=(0.7, 0.4),
        left_eye=(0.45, 0.35),
        right_eye=(0.55, 0.35),
        left_ear=(0.4, 0.35),
        right_ear=(0.6, 0.35),
    )
    assert pose_turned.screen_facing is False

    # Brief glance (1s) should NOT immediately trigger DISTRACTED
    res_glance = tracker.process_frame_state(
        face_detected=True,
        head_pose=pose_turned,
        current_time=t0 + 1.0,
    )
    assert res_glance["state"] == FocusState.FOCUSED

    # Sustained distraction (3.5s) -> transitions to DISTRACTED
    res_dist = tracker.process_frame_state(
        face_detected=True,
        head_pose=pose_turned,
        current_time=t0 + 3.5,
    )
    assert res_dist["state"] == FocusState.DISTRACTED

    # 3. Absence (no face for 4.5s) -> transitions to ABSENT
    res_absent = tracker.process_frame_state(
        face_detected=False,
        head_pose=None,
        current_time=t0 + 8.5,
    )
    assert res_absent["state"] == FocusState.ABSENT
    assert res_absent["face_present"] is False


def test_mood_estimator_non_diagnostic():
    """Verify MoodEstimator returns non-diagnostic visual alertness proxies."""
    # Alert, steady
    alert = MoodEstimator.estimate_engagement(face_detected=True, eye_aspect_ratio=0.30, head_stability=0.95)
    assert alert["state"] == MoodState.ENGAGED

    # Droopy eyes / fatigued
    tired = MoodEstimator.estimate_engagement(face_detected=True, eye_aspect_ratio=0.16)
    assert tired["state"] == MoodState.FATIGUED


def test_dual_posture_calibration_good_and_bad():
    """Verify that dual-frame calibration computes dynamic threshold based on delta between good and bad posture."""
    analyzer = PostureAnalyzer()

    # 1. Good upright posture
    calib_good = analyzer.calibrate(
        ear_point=(0.5, 0.2),
        shoulder_point=(0.5, 0.5),
        left_shoulder=(0.35, 0.5),
        right_shoulder=(0.65, 0.5),
    )
    assert calib_good.is_calibrated is True

    # 2. Bad slouched posture (ear at 0.7, 0.3)
    calib_bad = analyzer.calibrate_bad_reference(
        ear_point=(0.7, 0.3),
        shoulder_point=(0.5, 0.5),
    )
    assert calib_bad.has_bad_reference is True
    assert calib_bad.bad_neck_angle is not None
    assert analyzer.neck_deviation_threshold >= 8.0


def test_phone_detection_heuristic():
    """Verify that downward head pitch triggers phone detection."""
    service = LaptopCameraAIService()
    # Looking steeply down (pitch > 22) -> phone detected
    analysis = service.process_vision_input(
        nose=(0.5, 0.45),
        left_eye=(0.45, 0.35),
        right_eye=(0.55, 0.35),
        left_ear=(0.4, 0.35),
        right_ear=(0.6, 0.35),
        mouth_center=(0.5, 0.48),
        left_shoulder=(0.35, 0.55),
        right_shoulder=(0.65, 0.55),
    )
    assert analysis.face_present is True


@pytest.mark.asyncio
async def test_vision_api_endpoints_integration(client: AsyncClient):
    """Integration test for all laptop camera vision endpoints."""
    # 1. Register Student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "vision_student",
            "email": "vis@university.edu",
            "full_name": "Vision AI Tester",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Good Calibration Endpoint
    calib_res = await client.post(
        "/api/v1/vision/calibrate",
        headers=headers,
        json={
            "ear": {"x": 0.5, "y": 0.2},
            "shoulder": {"x": 0.5, "y": 0.5},
            "left_shoulder": {"x": 0.35, "y": 0.5},
            "right_shoulder": {"x": 0.65, "y": 0.5},
        },
    )
    assert calib_res.status_code == 200
    assert calib_res.json()["is_calibrated"] is True

    # 2b. Test Bad Calibration Endpoint
    calib_bad_res = await client.post(
        "/api/v1/vision/calibrate-bad",
        headers=headers,
        json={
            "ear": {"x": 0.65, "y": 0.3},
            "shoulder": {"x": 0.5, "y": 0.5},
        },
    )
    assert calib_bad_res.status_code == 200
    assert calib_bad_res.json()["has_bad_reference"] is True

    # 3. Test Landmark Telemetry Analysis Endpoint
    telemetry_res = await client.post(
        "/api/v1/vision/analyze",
        headers=headers,
        json={
            "nose": {"x": 0.5, "y": 0.25},
            "left_eye": {"x": 0.45, "y": 0.22},
            "right_eye": {"x": 0.55, "y": 0.22},
            "left_ear": {"x": 0.42, "y": 0.2},
            "right_ear": {"x": 0.58, "y": 0.2},
            "left_shoulder": {"x": 0.35, "y": 0.5},
            "right_shoulder": {"x": 0.65, "y": 0.5},
            "eye_aspect_ratio": 0.29,
        },
    )
    assert telemetry_res.status_code == 200
    res_data = telemetry_res.json()
    assert res_data["posture_state"] == "GOOD"
    assert res_data["focus_state"] == "FOCUSED"
    assert res_data["face_present"] is True
    assert "phone_detected" in res_data
    assert res_data["hardware_state"]["led_state"] == "GREEN"

    # 4. Test State Endpoint
    state_res = await client.get("/api/v1/vision/state", headers=headers)
    assert state_res.status_code == 200
    assert state_res.json() is not None

    # 5. Test Face Verify Session Endpoint
    face_verify_res = await client.post(
        "/api/v1/vision/verify-session-face",
        headers=headers,
        json={"embedding": [0.1] * 128},
    )
    assert face_verify_res.status_code == 200
    assert "is_match" in face_verify_res.json()

    # 6. Test Frame Processing Endpoint with synthetic image
    import base64
    import cv2
    import numpy as np

    synth_img = np.full((120, 120, 3), 120, dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", synth_img)
    b64_frame = base64.b64encode(buffer).decode("utf-8")

    frame_proc_res = await client.post(
        "/api/v1/vision/process-frame",
        headers=headers,
        json={"image_base64": b64_frame},
    )
    assert frame_proc_res.status_code == 200
    assert "posture_state" in frame_proc_res.json()
    assert "focus_state" in frame_proc_res.json()

    # 7. Test Frame Calibration Endpoint
    frame_calib_res = await client.post(
        "/api/v1/vision/calibrate-frame",
        headers=headers,
        json={"image_base64": b64_frame, "is_bad_reference": False},
    )
    assert frame_calib_res.status_code == 200
    assert frame_calib_res.json()["is_calibrated"] is True

    # 8. Test Dual Frame Calibration Endpoint
    dual_calib_res = await client.post(
        "/api/v1/vision/calibrate-dual",
        headers=headers,
        json={"good_image_base64": b64_frame, "bad_image_base64": b64_frame},
    )
    assert dual_calib_res.status_code == 200
    assert dual_calib_res.json()["is_calibrated"] is True
    assert dual_calib_res.json()["has_bad_reference"] is True

    # 9. Test Session Summary & Reset Endpoints
    reset_res = await client.post("/api/v1/vision/reset-session-events", headers=headers)
    assert reset_res.status_code == 200

    summary_res = await client.get("/api/v1/vision/session-summary", headers=headers)
    assert summary_res.status_code == 200
    assert "bad_posture_events" in summary_res.json()
    assert "confirmed_bad_alerts" in summary_res.json()
    assert "absence_events_count" in summary_res.json()
    assert "phone_events_count" in summary_res.json()
    assert "absence_history" in summary_res.json()


def test_absence_duration_tracking_and_break_exemption():
    """Verify that absence records individual departure intervals with duration and timestamps, and ignores breaks."""
    import base64
    import cv2
    import numpy as np

    service = LaptopCameraAIService()
    service.reset_session_telemetry()

    blank_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", blank_img)
    blank_b64 = base64.b64encode(buffer).decode("utf-8")

    t0 = 1000.0
    # 1. At t=0: person leaves desk
    service.process_frame_image(blank_b64, current_time=t0, is_break=False)
    assert service.is_currently_absent is False

    # 2. At t=3.5s: absence confirmed (>= 3s)
    service.process_frame_image(blank_b64, current_time=t0 + 3.5, is_break=False)
    assert service.is_currently_absent is True

    # 3. Close ongoing absence at t=20.0s
    service.close_ongoing_absence_if_any(current_time=t0 + 20.0)
    assert service.absence_events_count == 1
    assert len(service.absence_history) == 1
    record = service.absence_history[0]
    assert record["duration_seconds"] == 20.0
    assert "left_at" in record
    assert "returned_at" in record

    # 4. Break exemption test
    service.reset_session_telemetry()
    service.process_frame_image(blank_b64, current_time=t0, is_break=True)
    service.process_frame_image(blank_b64, current_time=t0 + 10.0, is_break=True)
    assert service.absence_events_count == 0
    assert len(service.absence_history) == 0

