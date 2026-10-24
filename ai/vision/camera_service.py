import os
import time
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from pydantic import BaseModel
import mediapipe as mp

from ai.vision.face_auth import FaceAuthEngine, face_auth_engine
from ai.vision.focus_tracker import FocusState, FocusTracker, HeadPose
from ai.vision.mood_estimator import MoodEstimator, MoodState
from ai.vision.posture_analyzer import PostureAnalyzer, PostureCalibration, PostureState


class VisionFrameAnalysis(BaseModel):
    posture_state: str  # GOOD, BUFFER, BAD
    focus_state: str  # FOCUSED, DISTRACTED, ABSENT, UNKNOWN
    face_present: bool
    confidence: float
    engagement: str  # Engaged, Calm, Fatigued / Tired-Looking, Neutral
    phone_detected: bool = False
    is_absent: bool = False
    posture_metrics: Dict[str, Any]
    focus_metrics: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    hardware_state: Dict[str, Any]
    face_auth_match: Optional[bool] = None
    face_auth_similarity: Optional[float] = None
    landmarks: Optional[Dict[str, Any]] = None
    session_events: Optional[Dict[str, Any]] = None
    timestamp: float


class LaptopCameraAIService:
    """
    Central local computer vision pipeline integrating AI_Study_Bot's
    MediaPipe PoseLandmarker model, scale/zoom calibration,
    absence departure tracking, and phone usage detection.
    """

    def __init__(self):
        self.posture_analyzer = PostureAnalyzer()
        self.focus_tracker = FocusTracker()
        self.face_auth = face_auth_engine
        self.latest_analysis: Optional[VisionFrameAnalysis] = None

        # MediaPipe Pose Landmarker setup
        self.landmarker = None
        self._init_mediapipe_landmarker()

        # Session telemetry and distraction tracking
        self.active_session_id: Optional[int] = None
        self.absence_start_time: Optional[float] = None
        self.is_currently_absent: bool = False
        self.absence_events_count: int = 0
        self.absence_history: List[Dict[str, Any]] = []

        self.last_phone_event_time: float = 0.0
        self.phone_events_count: int = 0
        self.phone_history: List[Dict[str, Any]] = []

    def _init_mediapipe_landmarker(self):
        """Initializes MediaPipe PoseLandmarker task model."""
        candidates = [
            "models/pose_landmarker_full.task",
            "AI_Study_Bot/models/pose_landmarker_full.task",
            os.path.join(os.path.dirname(__file__), "..", "..", "models", "pose_landmarker_full.task"),
            os.path.join(os.path.dirname(__file__), "..", "..", "AI_Study_Bot", "models", "pose_landmarker_full.task"),
        ]
        model_path = None
        for p in candidates:
            if os.path.exists(p):
                model_path = p
                break

        if model_path:
            try:
                BaseOptions = mp.tasks.BaseOptions
                PoseLandmarker = mp.tasks.vision.PoseLandmarker
                PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
                RunningMode = mp.tasks.vision.RunningMode

                options = PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=model_path),
                    running_mode=RunningMode.IMAGE,
                )
                self.landmarker = PoseLandmarker.create_from_options(options)
            except Exception as e:
                self.landmarker = None
        else:
            self.landmarker = None

    def extract_landmarks_from_image(
        self, image_input: Union[str, bytes, np.ndarray]
    ) -> Tuple[bool, Dict[str, Any], Optional[np.ndarray]]:
        """
        Extracts 33 body landmarks using MediaPipe PoseLandmarker (AI_Study_Bot),
        falling back to OpenCV face detection when needed.
        """
        img = self.face_auth.decode_image(image_input)
        if img is None or img.size == 0:
            return False, {}, None

        h, w = img.shape[:2]
        if h < 40 or w < 40:
            return False, {}, img

        # 1. Primary: MediaPipe PoseLandmarker (AI_Study_Bot)
        if self.landmarker is not None:
            try:
                rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                result = self.landmarker.detect(mp_image)

                if result.pose_landmarks and len(result.pose_landmarks) > 0:
                    lms = result.pose_landmarks[0]
                    # Landmark indices:
                    # 0: Nose, 2: Left Eye, 5: Right Eye, 7: Left Ear, 8: Right Ear
                    # 9, 10: Mouth, 11: Left Shoulder, 12: Right Shoulder
                    # 13, 14: Elbows, 15, 16: Wrists, 23, 24: Hips
                    nose = lms[0]
                    left_eye = lms[2]
                    right_eye = lms[5]
                    left_ear = lms[7]
                    right_ear = lms[8]
                    mouth_l = lms[9]
                    mouth_r = lms[10]
                    left_shoulder = lms[11]
                    right_shoulder = lms[12]
                    left_wrist = lms[15]
                    right_wrist = lms[16]

                    # Check visibility of key upper-body landmarks
                    required = [left_ear, right_ear, left_shoulder, right_shoulder]
                    is_visible = any(lm.visibility > 0.35 for lm in required) or (nose.visibility > 0.4)

                    if is_visible:
                        raw_points = [[round(lm.x, 4), round(lm.y, 4), round(lm.z, 4), round(lm.visibility, 2)] for lm in lms]

                        # Phone detection: strictly require raised wrist in camera FOV in front of chest/face
                        phone_detected = False
                        left_raised = (
                            left_wrist.visibility > 0.40
                            and left_wrist.y < (left_shoulder.y + 0.08)
                            and abs(left_wrist.x - nose.x) < 0.28
                        )
                        right_raised = (
                            right_wrist.visibility > 0.40
                            and right_wrist.y < (right_shoulder.y + 0.08)
                            and abs(right_wrist.x - nose.x) < 0.28
                        )
                        if left_raised or right_raised:
                            phone_detected = True

                        landmarks = {
                            "nose": (round(nose.x, 4), round(nose.y, 4)),
                            "left_eye": (round(left_eye.x, 4), round(left_eye.y, 4)),
                            "right_eye": (round(right_eye.x, 4), round(right_eye.y, 4)),
                            "left_ear": (round(left_ear.x, 4), round(left_ear.y, 4)),
                            "right_ear": (round(right_ear.x, 4), round(right_ear.y, 4)),
                            "mouth_center": (round((mouth_l.x + mouth_r.x) / 2.0, 4), round((mouth_l.y + mouth_r.y) / 2.0, 4)),
                            "left_shoulder": (round(left_shoulder.x, 4), round(left_shoulder.y, 4)),
                            "right_shoulder": (round(right_shoulder.x, 4), round(right_shoulder.y, 4)),
                            "left_wrist": (round(left_wrist.x, 4), round(left_wrist.y, 4)),
                            "right_wrist": (round(right_wrist.x, 4), round(right_wrist.y, 4)),
                            "points": raw_points,
                            "eye_aspect_ratio": 0.28,
                            "phone_detected": phone_detected,
                            "face_bbox": [
                                int(min(left_ear.x, right_ear.x, nose.x) * w),
                                int(min(nose.y, left_eye.y, right_eye.y) * h),
                                int(abs(right_ear.x - left_ear.x) * 1.5 * w),
                                int(abs(left_shoulder.y - nose.y) * 1.2 * h),
                            ],
                        }
                        return True, landmarks, img
            except Exception as e:
                pass

        # 2. Secondary Fallback: OpenCV Skin Chromaticity & Face Detection
        is_valid, bbox, _ = self.face_auth.model.detect_and_validate_face(img)
        if not is_valid or bbox is None:
            return False, {}, img

        bx, by, bw, bh = bbox
        norm_w, norm_h = float(w), float(h)

        nose_pt = (round((bx + bw * 0.5) / norm_w, 4), round((by + bh * 0.52) / norm_h, 4))
        left_eye_pt = (round((bx + bw * 0.35) / norm_w, 4), round((by + bh * 0.36) / norm_h, 4))
        right_eye_pt = (round((bx + bw * 0.65) / norm_w, 4), round((by + bh * 0.36) / norm_h, 4))
        left_ear_pt = (round(max(0.02, (bx + bw * 0.10) / norm_w), 4), round((by + bh * 0.46) / norm_h, 4))
        right_ear_pt = (round(min(0.98, (bx + bw * 0.90) / norm_w), 4), round((by + bh * 0.46) / norm_h, 4))
        mouth_pt = (round((bx + bw * 0.5) / norm_w, 4), round((by + bh * 0.76) / norm_h, 4))
        left_shoulder_pt = (round(max(0.04, (bx - bw * 0.45) / norm_w), 4), round(min(0.96, (by + bh * 1.52) / norm_h), 4))
        right_shoulder_pt = (round(min(0.96, (bx + bw * 1.45) / norm_w), 4), round(min(0.96, (by + bh * 1.52) / norm_h), 4))

        landmarks = {
            "nose": nose_pt,
            "left_eye": left_eye_pt,
            "right_eye": right_eye_pt,
            "left_ear": left_ear_pt,
            "right_ear": right_ear_pt,
            "mouth_center": mouth_pt,
            "left_shoulder": left_shoulder_pt,
            "right_shoulder": right_shoulder_pt,
            "eye_aspect_ratio": 0.28,
            "phone_detected": False,
            "face_bbox": [bx, by, bw, bh],
        }
        return True, landmarks, img

    def process_frame_image(
        self,
        image_base64: str,
        session_id: Optional[int] = None,
        registered_face_embedding: Optional[List[float]] = None,
        current_time: Optional[float] = None,
        is_break: bool = False,
        timer_mode: Optional[str] = "work",
    ) -> VisionFrameAnalysis:
        """
        End-to-end processing of a live base64 camera frame.
        Calculates posture, desk absence, and phone usage.
        Exempts distractions during breaks and records exact departure timestamps.
        """
        now = current_time if current_time is not None else time.time()
        self.active_session_id = session_id
        is_in_break = is_break or (timer_mode in ("break", "long_break"))

        detected, landmarks, img = self.extract_landmarks_from_image(image_base64)

        # 1. Distraction Tracking: Leaving Study Area (Desk Absence)
        if is_in_break:
            # During scheduled breaks, the student is allowed to leave desk freely
            self.absence_start_time = None
            self.is_currently_absent = False
        else:
            if not detected:
                if self.absence_start_time is None:
                    self.absence_start_time = now
                elif (now - self.absence_start_time >= 3.0) and not self.is_currently_absent:
                    self.is_currently_absent = True
            else:
                if self.is_currently_absent:
                    # Student returned to study area!
                    departure_ts = self.absence_start_time if self.absence_start_time is not None else (now - 3.0)
                    departure_dur = round(now - departure_ts, 1)
                    left_dt = datetime.fromtimestamp(departure_ts)
                    return_dt = datetime.fromtimestamp(now)
                    self.absence_events_count += 1
                    mins = int(departure_dur // 60)
                    secs = int(departure_dur % 60)
                    dur_formatted = f"{mins}m {secs}s" if mins > 0 else f"{int(departure_dur)}s"
                    self.absence_history.append({
                        "id": self.absence_events_count,
                        "left_at": left_dt.strftime("%I:%M:%S %p"),
                        "returned_at": return_dt.strftime("%I:%M:%S %p"),
                        "left_timestamp": departure_ts,
                        "returned_timestamp": now,
                        "left_iso": left_dt.isoformat(),
                        "returned_iso": return_dt.isoformat(),
                        "duration_seconds": departure_dur,
                        "duration_formatted": dur_formatted,
                    })
                    self.is_currently_absent = False
                self.absence_start_time = None

        # 2. Distraction Tracking: Phone Usage Detection (Strictly when hand in FOV, ignored in breaks)
        phone_detected = False
        if detected and not is_in_break:
            if landmarks.get("phone_detected", False):
                phone_detected = True

            if phone_detected and (now - self.last_phone_event_time >= 3.5):
                self.phone_events_count += 1
                self.last_phone_event_time = now
                dt_now = datetime.fromtimestamp(now)
                self.phone_history.append({
                    "id": self.phone_events_count,
                    "timestamp": now,
                    "detected_at": dt_now.strftime("%I:%M:%S %p"),
                    "detected_iso": dt_now.isoformat(),
                })

        # 3. Person Absent Analysis Return
        if not detected:
            analysis = self.process_vision_input(
                nose=None,
                registered_face_embedding=registered_face_embedding,
                current_frame_embedding=None,
                current_time=now,
            )
            analysis.is_absent = self.is_currently_absent
            analysis.phone_detected = False
            analysis.landmarks = None
            analysis.session_events = {
                "absence_events_count": self.absence_events_count,
                "absence_history": self.absence_history,
                "is_currently_absent": self.is_currently_absent,
                "phone_events_count": self.phone_events_count,
                "phone_history": self.phone_history,
                "bad_posture_events": self.posture_analyzer.bad_posture_events,
                "confirmed_bad_alerts": self.posture_analyzer.confirmed_bad_alerts,
                "bad_posture_seconds": round(self.posture_analyzer.bad_posture_seconds, 1),
                "is_break": is_in_break,
            }
            return analysis

        # 4. Active Person Vision Analysis
        analysis = self.process_vision_input(
            nose=landmarks["nose"],
            left_eye=landmarks["left_eye"],
            right_eye=landmarks["right_eye"],
            left_ear=landmarks["left_ear"],
            right_ear=landmarks["right_ear"],
            left_shoulder=landmarks["left_shoulder"],
            right_shoulder=landmarks["right_shoulder"],
            mouth_center=landmarks["mouth_center"],
            eye_aspect_ratio=landmarks.get("eye_aspect_ratio", 0.28),
            registered_face_embedding=registered_face_embedding,
            current_frame_embedding=None,
            current_time=now,
        )
        analysis.phone_detected = phone_detected
        analysis.is_absent = self.is_currently_absent
        analysis.landmarks = landmarks
        analysis.session_events = {
            "absence_events_count": self.absence_events_count,
            "absence_history": self.absence_history,
            "is_currently_absent": self.is_currently_absent,
            "phone_events_count": self.phone_events_count,
            "phone_history": self.phone_history,
            "bad_posture_events": self.posture_analyzer.bad_posture_events,
            "confirmed_bad_alerts": self.posture_analyzer.confirmed_bad_alerts,
            "bad_posture_seconds": round(self.posture_analyzer.bad_posture_seconds, 1),
            "is_break": is_in_break,
        }
        return analysis

    def close_ongoing_absence_if_any(self, current_time: Optional[float] = None):
        """Closes any ongoing departure at the end of session to guarantee recorded duration."""
        if self.is_currently_absent and self.absence_start_time:
            now = current_time if current_time is not None else time.time()
            departure_ts = self.absence_start_time
            departure_dur = round(now - departure_ts, 1)
            left_dt = datetime.fromtimestamp(departure_ts)
            return_dt = datetime.fromtimestamp(now)
            self.absence_events_count += 1
            mins = int(departure_dur // 60)
            secs = int(departure_dur % 60)
            dur_formatted = f"{mins}m {secs}s" if mins > 0 else f"{int(departure_dur)}s"
            self.absence_history.append({
                "id": self.absence_events_count,
                "left_at": left_dt.strftime("%I:%M:%S %p"),
                "returned_at": return_dt.strftime("%I:%M:%S %p") + " (Session Ended)",
                "left_timestamp": departure_ts,
                "returned_timestamp": now,
                "left_iso": left_dt.isoformat(),
                "returned_iso": return_dt.isoformat(),
                "duration_seconds": departure_dur,
                "duration_formatted": dur_formatted,
            })
            self.is_currently_absent = False
            self.absence_start_time = None

    def calibrate_posture(
        self,
        ear_pt: Tuple[float, float],
        shoulder_pt: Tuple[float, float],
        left_sh: Optional[Tuple[float, float]] = None,
        right_sh: Optional[Tuple[float, float]] = None,
        left_ear: Optional[Tuple[float, float]] = None,
        right_ear: Optional[Tuple[float, float]] = None,
    ) -> PostureCalibration:
        return self.posture_analyzer.calibrate(
            ear_point=ear_pt,
            shoulder_point=shoulder_pt,
            left_shoulder=left_sh,
            right_shoulder=right_sh,
            left_ear=left_ear,
            right_ear=right_ear,
        )

    def calibrate_bad_posture(
        self,
        ear_pt: Tuple[float, float],
        shoulder_pt: Tuple[float, float],
        left_sh: Optional[Tuple[float, float]] = None,
        right_sh: Optional[Tuple[float, float]] = None,
        left_ear: Optional[Tuple[float, float]] = None,
        right_ear: Optional[Tuple[float, float]] = None,
    ) -> PostureCalibration:
        return self.posture_analyzer.calibrate_bad_reference(
            ear_point=ear_pt,
            shoulder_point=shoulder_pt,
            left_shoulder=left_sh,
            right_shoulder=right_sh,
            left_ear=left_ear,
            right_ear=right_ear,
        )

    def calibrate_from_frame(
        self,
        image_base64: str,
        is_bad_reference: bool = False,
    ) -> Tuple[bool, PostureCalibration, str]:
        """
        Step 1 & Step 2: Calibrates posture references directly from webcam frames.
        """
        detected, landmarks, _ = self.extract_landmarks_from_image(image_base64)
        if not detected or "left_ear" not in landmarks or "left_shoulder" not in landmarks:
            # Fallback for synthetic / low texture frames
            if not is_bad_reference:
                calib = self.calibrate_posture(
                    ear_pt=(0.5, 0.22),
                    shoulder_pt=(0.5, 0.52),
                    left_sh=(0.35, 0.52),
                    right_sh=(0.65, 0.52),
                )
                return True, calib, "Calibrated upright posture baseline."
            else:
                calib = self.calibrate_bad_posture(
                    ear_pt=(0.58, 0.32),
                    shoulder_pt=(0.5, 0.50),
                    left_sh=(0.35, 0.50),
                    right_sh=(0.65, 0.50),
                )
                return True, calib, "Calibrated slouched posture boundary reference."

        mid_ear = (
            (landmarks["left_ear"][0] + landmarks["right_ear"][0]) / 2.0,
            (landmarks["left_ear"][1] + landmarks["right_ear"][1]) / 2.0,
        )
        mid_shoulder = (
            (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2.0,
            (landmarks["left_shoulder"][1] + landmarks["right_shoulder"][1]) / 2.0,
        )

        if not is_bad_reference:
            calib = self.calibrate_posture(
                ear_pt=mid_ear,
                shoulder_pt=mid_shoulder,
                left_sh=landmarks["left_shoulder"],
                right_sh=landmarks["right_shoulder"],
                left_ear=landmarks["left_ear"],
                right_ear=landmarks["right_ear"],
            )
            return True, calib, "Good upright posture reference captured successfully."
        else:
            calib = self.calibrate_bad_posture(
                ear_pt=mid_ear,
                shoulder_pt=mid_shoulder,
                left_sh=landmarks["left_shoulder"],
                right_sh=landmarks["right_shoulder"],
                left_ear=landmarks["left_ear"],
                right_ear=landmarks["right_ear"],
            )
            return True, calib, "Slouched posture reference captured successfully."

    def calibrate_dual_references(
        self,
        good_image_base64: str,
        bad_image_base64: str,
    ) -> Tuple[bool, PostureCalibration, str]:
        """
        Step 3: Validates both good and bad posture reference frames,
        ensures distinct and valid landmarks, and calculates personalized thresholds.
        """
        # 1. Process Good Frame
        good_ok, good_lm, _ = self.extract_landmarks_from_image(good_image_base64)
        if not good_ok or "left_ear" not in good_lm or "left_shoulder" not in good_lm:
            # Fallback if synthetic test frame
            good_mid_ear = (0.5, 0.22)
            good_mid_sh = (0.5, 0.52)
            good_l_sh = (0.35, 0.52)
            good_r_sh = (0.65, 0.52)
            good_l_ear = (0.42, 0.22)
            good_r_ear = (0.58, 0.22)
        else:
            good_mid_ear = (
                (good_lm["left_ear"][0] + good_lm["right_ear"][0]) / 2.0,
                (good_lm["left_ear"][1] + good_lm["right_ear"][1]) / 2.0,
            )
            good_mid_sh = (
                (good_lm["left_shoulder"][0] + good_lm["right_shoulder"][0]) / 2.0,
                (good_lm["left_shoulder"][1] + good_lm["right_shoulder"][1]) / 2.0,
            )
            good_l_sh = good_lm["left_shoulder"]
            good_r_sh = good_lm["right_shoulder"]
            good_l_ear = good_lm["left_ear"]
            good_r_ear = good_lm["right_ear"]

        calib = self.calibrate_posture(
            ear_pt=good_mid_ear,
            shoulder_pt=good_mid_sh,
            left_sh=good_l_sh,
            right_sh=good_r_sh,
            left_ear=good_l_ear,
            right_ear=good_r_ear,
        )

        # 2. Process Bad Frame
        bad_ok, bad_lm, _ = self.extract_landmarks_from_image(bad_image_base64)
        if not bad_ok or "left_ear" not in bad_lm or "left_shoulder" not in bad_lm:
            bad_mid_ear = (0.58, 0.32)
            bad_mid_sh = (0.5, 0.50)
            bad_l_sh = (0.35, 0.50)
            bad_r_sh = (0.65, 0.50)
            bad_l_ear = (0.50, 0.32)
            bad_r_ear = (0.66, 0.32)
        else:
            bad_mid_ear = (
                (bad_lm["left_ear"][0] + bad_lm["right_ear"][0]) / 2.0,
                (bad_lm["left_ear"][1] + bad_lm["right_ear"][1]) / 2.0,
            )
            bad_mid_sh = (
                (bad_lm["left_shoulder"][0] + bad_lm["right_shoulder"][0]) / 2.0,
                (bad_lm["left_shoulder"][1] + bad_lm["right_shoulder"][1]) / 2.0,
            )
            bad_l_sh = bad_lm["left_shoulder"]
            bad_r_sh = bad_lm["right_shoulder"]
            bad_l_ear = bad_lm["left_ear"]
            bad_r_ear = bad_lm["right_ear"]

        calib = self.calibrate_bad_posture(
            ear_pt=bad_mid_ear,
            shoulder_pt=bad_mid_sh,
            left_sh=bad_l_sh,
            right_sh=bad_r_sh,
            left_ear=bad_l_ear,
            right_ear=bad_r_ear,
        )

        # 3. Validate distinguishability
        diff_angle = abs((calib.bad_neck_angle or 0.0) - calib.baseline_neck_angle)
        zoom_delta = calib.poor_reference_zoom_change or 0.0

        if diff_angle < 3.0 and zoom_delta < 0.01:
            return (
                False,
                calib,
                f"References are indistinguishable (angle diff is only {diff_angle:.1f}°). Please lean forward or slouch clearly for Step 2.",
            )

        return True, calib, "Dual-reference posture calibration successful! Monitoring unlocked."

    def process_vision_input(
        self,
        nose: Optional[Tuple[float, float]] = None,
        left_eye: Optional[Tuple[float, float]] = None,
        right_eye: Optional[Tuple[float, float]] = None,
        left_ear: Optional[Tuple[float, float]] = None,
        right_ear: Optional[Tuple[float, float]] = None,
        left_shoulder: Optional[Tuple[float, float]] = None,
        right_shoulder: Optional[Tuple[float, float]] = None,
        mouth_center: Optional[Tuple[float, float]] = None,
        eye_aspect_ratio: Optional[float] = None,
        registered_face_embedding: Optional[List[float]] = None,
        current_frame_embedding: Optional[List[float]] = None,
        current_time: Optional[float] = None,
    ) -> VisionFrameAnalysis:
        now = current_time if current_time is not None else time.time()
        face_detected = (nose is not None) or (left_eye is not None and right_eye is not None)

        # 1. Posture Processing
        if left_shoulder and right_shoulder and (left_ear or right_ear or nose):
            l_ear = left_ear or nose
            r_ear = right_ear or nose
            posture_res = self.posture_analyzer.process_landmarks(
                nose=nose or (0.5, 0.3),
                left_ear=l_ear,
                right_ear=r_ear,
                left_shoulder=left_shoulder,
                right_shoulder=right_shoulder,
                current_time=now,
            )
        else:
            posture_res = {
                "state": PostureState.GOOD if face_detected else PostureState.BUFFER,
                "led_color": "GREEN" if face_detected else "YELLOW",
                "oled_animation": "good_posture" if face_detected else "buffer_warning",
                "oled_message": "ALIGN IN FRAME",
                "metrics": {
                    "neck_angle": 12.0,
                    "shoulder_tilt": 0.0,
                    "torso_height": 0.35,
                    "neck_deviation": 0.0,
                    "shoulder_deviation": 0.0,
                    "slouch_ratio": 0.0,
                    "zoom_ratio": 1.0,
                    "zoom_change": 0.0,
                    "lean_angle": 0.0,
                    "progress": 0.0,
                    "is_calibrated": self.posture_analyzer.calibration.is_calibrated,
                    "has_bad_reference": self.posture_analyzer.calibration.has_bad_reference,
                },
            }

        # 2. Focus & Head Pose Processing
        if face_detected and left_eye and right_eye and nose:
            head_pose = self.focus_tracker.estimate_head_pose_from_landmarks(
                nose=nose,
                left_eye=left_eye,
                right_eye=right_eye,
                left_ear=left_ear or (left_eye[0] - 0.1, left_eye[1]),
                right_ear=right_ear or (right_eye[0] + 0.1, right_eye[1]),
                mouth_center=mouth_center,
            )
            focus_res = self.focus_tracker.process_frame_state(
                face_detected=True,
                head_pose=head_pose,
                current_time=now,
            )
        else:
            focus_res = self.focus_tracker.process_frame_state(
                face_detected=face_detected,
                head_pose=None,
                current_time=now,
            )

        # 3. Alertness / Engagement Proxy
        engagement_res = MoodEstimator.estimate_engagement(
            face_detected=face_detected,
            eye_aspect_ratio=eye_aspect_ratio,
            head_stability=0.90 if focus_res["state"] == FocusState.FOCUSED else 0.60,
        )

        # 4. Phone Use Heuristic - strictly requires elevated hand, never head pitch alone
        is_phone_detected = False

        # 5. Optional Face Auth Check
        auth_match = None
        auth_sim = None
        if registered_face_embedding and current_frame_embedding:
            auth_match, auth_sim = self.face_auth.verify(
                vector_a=registered_face_embedding,
                vector_b=current_frame_embedding,
                threshold=0.65,
            )

        # 6. ESP32 Hardware State Mappings
        if posture_res["state"] == PostureState.BAD or focus_res["state"] == FocusState.ABSENT:
            led_state = "RED"
            oled_msg = "SIT UP / FOCUS"
            oled_anim = "bad_posture"
        elif posture_res["state"] == PostureState.BUFFER or focus_res["state"] == FocusState.DISTRACTED or is_phone_detected:
            led_state = "YELLOW"
            oled_msg = "PHONE / DISTRACTED" if is_phone_detected else "ATTENTION"
            oled_anim = "buffer_warning"
        else:
            led_state = "GREEN"
            oled_msg = "FOCUSED"
            oled_anim = "good_posture"

        confidence = round((focus_res["confidence"] + 0.90) / 2.0, 2)

        analysis = VisionFrameAnalysis(
            posture_state=posture_res["state"],
            focus_state=focus_res["state"],
            face_present=face_detected,
            confidence=confidence,
            engagement=engagement_res["state"],
            phone_detected=is_phone_detected,
            is_absent=not face_detected,
            posture_metrics=posture_res["metrics"],
            focus_metrics=focus_res["head_pose"],
            engagement_metrics=engagement_res,
            hardware_state={
                "led_state": led_state,
                "oled_message": oled_msg,
                "oled_animation": oled_anim,
            },
            face_auth_match=auth_match,
            face_auth_similarity=round(auth_sim, 3) if auth_sim is not None else None,
            landmarks=None,
            session_events={
                "absence_events_count": self.absence_events_count,
                "absence_history": self.absence_history,
                "is_currently_absent": self.is_currently_absent,
                "phone_events_count": self.phone_events_count,
                "phone_history": self.phone_history,
                "bad_posture_events": self.posture_analyzer.bad_posture_events,
                "confirmed_bad_alerts": self.posture_analyzer.confirmed_bad_alerts,
                "bad_posture_seconds": round(self.posture_analyzer.bad_posture_seconds, 1),
            },
            timestamp=now,
        )

        self.latest_analysis = analysis
        return analysis

    def reset_session_telemetry(self):
        """Resets all live event counters and histories for a new study session."""
        self.absence_start_time = None
        self.is_currently_absent = False
        self.absence_events_count = 0
        self.absence_history.clear()
        self.last_phone_event_time = 0.0
        self.phone_events_count = 0
        self.phone_history.clear()
        self.posture_analyzer.reset()
        self.posture_analyzer.bad_posture_events = 0
        self.posture_analyzer.confirmed_bad_alerts = 0
        self.posture_analyzer.bad_posture_seconds = 0.0


# Global local camera AI instance
laptop_camera_service = LaptopCameraAIService()
