import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class HeadPose(BaseModel):
    yaw: float = 0.0  # Horizontal turn (-90 left to +90 right)
    pitch: float = 0.0  # Vertical tilt (-90 down to +90 up)
    roll: float = 0.0  # Head tilt sideways
    screen_facing: bool = True


class FocusState:
    FOCUSED = "FOCUSED"
    DISTRACTED = "DISTRACTED"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


class FocusTracker:
    """
    Presence and screen-facing focus estimator based on visual geometry and head pose.
    Includes temporal hysteresis debouncing to prevent brief glances from triggering alerts.
    
    DISCLAIMER: This system estimates visual orientation and physical presence;
    it does not inspect or claim to interpret internal student cognitive states.
    """

    def __init__(
        self,
        absence_threshold_seconds: float = 4.0,  # No face for 4s -> ABSENT
        distraction_threshold_seconds: float = 3.0,  # Looking away for 3s -> DISTRACTED
        recovery_threshold_seconds: float = 1.0,  # Screen facing for 1s -> FOCUSED
        yaw_threshold: float = 25.0,  # degrees
        pitch_threshold: float = 20.0,  # degrees
        smoothing_alpha: float = 0.30,
    ):
        self.absence_threshold = absence_threshold_seconds
        self.distraction_threshold = distraction_threshold_seconds
        self.recovery_threshold = recovery_threshold_seconds
        self.yaw_threshold = yaw_threshold
        self.pitch_threshold = pitch_threshold
        self.smoothing_alpha = smoothing_alpha

        self.current_state: str = FocusState.FOCUSED
        self.smoothed_yaw: float = 0.0
        self.smoothed_pitch: float = 0.0
        self.smoothed_roll: float = 0.0

        self.last_face_seen_time: float = time.time()
        self.distraction_start_time: Optional[float] = None
        self.recovery_start_time: Optional[float] = None

    @classmethod
    def estimate_head_pose_from_landmarks(
        cls,
        nose: Tuple[float, float],
        left_eye: Tuple[float, float],
        right_eye: Tuple[float, float],
        left_ear: Tuple[float, float],
        right_ear: Tuple[float, float],
        mouth_center: Optional[Tuple[float, float]] = None,
    ) -> HeadPose:
        """
        Estimates approximate 3D head yaw, pitch, and roll angles from 2D facial landmarks.
        """
        # Eye midpoint and distance
        eye_mid_x = (left_eye[0] + right_eye[0]) / 2.0
        eye_mid_y = (left_eye[1] + right_eye[1]) / 2.0
        interocular_dist = math_hypot(right_eye[0] - left_eye[0], right_eye[1] - left_eye[1])
        interocular_dist = max(1e-4, interocular_dist)

        # Yaw estimation: asymmetry of nose relative to eye midpoint
        nose_offset_x = (nose[0] - eye_mid_x) / interocular_dist
        yaw_deg = nose_offset_x * 90.0  # empirical scaling

        # Roll estimation: slope of line connecting the two eyes
        d_eye_y = right_eye[1] - left_eye[1]
        d_eye_x = right_eye[0] - left_eye[0]
        roll_deg = math_atan2(d_eye_y, d_eye_x) * (180.0 / 3.14159)

        # Pitch estimation: vertical ratio between eyes, nose, and mouth
        pitch_deg = 0.0
        if mouth_center:
            eye_to_nose = abs(nose[1] - eye_mid_y)
            nose_to_mouth = abs(mouth_center[1] - nose[1])
            ratio = (eye_to_nose / (nose_to_mouth + 1e-4))
            pitch_deg = (ratio - 1.0) * 45.0

        is_screen_facing = (abs(yaw_deg) <= 25.0) and (abs(pitch_deg) <= 20.0)

        return HeadPose(
            yaw=round(yaw_deg, 1),
            pitch=round(pitch_deg, 1),
            roll=round(roll_deg, 1),
            screen_facing=is_screen_facing,
        )

    def process_frame_state(
        self,
        face_detected: bool,
        head_pose: Optional[HeadPose] = None,
        current_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Processes frame presence and head pose with temporal smoothing and debouncing.
        """
        now = current_time if current_time is not None else time.time()

        if not face_detected:
            # Face not visible
            elapsed_away = now - self.last_face_seen_time
            if elapsed_away >= self.absence_threshold:
                self.current_state = FocusState.ABSENT
                confidence = 0.95
            else:
                confidence = 0.70  # Still debouncing brief blink or occlusion

            return {
                "state": self.current_state,
                "face_present": False,
                "confidence": confidence,
                "head_pose": {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "screen_facing": False},
                "disclaimer": "Visual presence indicator only; non-cognitive.",
            }

        # Face is detected
        self.last_face_seen_time = now

        pose = head_pose or HeadPose()
        # EMA smoothing on angles
        alpha = self.smoothing_alpha
        self.smoothed_yaw = (alpha * pose.yaw) + ((1.0 - alpha) * self.smoothed_yaw)
        self.smoothed_pitch = (alpha * pose.pitch) + ((1.0 - alpha) * self.smoothed_pitch)
        self.smoothed_roll = (alpha * pose.roll) + ((1.0 - alpha) * self.smoothed_roll)

        is_looking_away = (abs(self.smoothed_yaw) > self.yaw_threshold) or (abs(self.smoothed_pitch) > self.pitch_threshold)

        if is_looking_away:
            self.recovery_start_time = None
            if self.distraction_start_time is None:
                self.distraction_start_time = now

            elapsed_distracted = now - self.distraction_start_time
            if elapsed_distracted >= self.distraction_threshold:
                self.current_state = FocusState.DISTRACTED
                confidence = 0.88
            else:
                # Still in debounce window, retain previous state
                confidence = 0.75
        else:
            # Looking towards screen
            self.distraction_start_time = None
            if self.current_state != FocusState.FOCUSED:
                if self.recovery_start_time is None:
                    self.recovery_start_time = now

                elapsed_rec = now - self.recovery_start_time
                if elapsed_rec >= self.recovery_threshold:
                    self.current_state = FocusState.FOCUSED
                    self.recovery_start_time = None
                    confidence = 0.92
                else:
                    confidence = 0.80
            else:
                confidence = 0.92

        return {
            "state": self.current_state,
            "face_present": True,
            "confidence": confidence,
            "head_pose": {
                "yaw": round(self.smoothed_yaw, 1),
                "pitch": round(self.smoothed_pitch, 1),
                "roll": round(self.smoothed_roll, 1),
                "screen_facing": not is_looking_away,
            },
            "disclaimer": "Visual presence indicator only; non-cognitive.",
        }

    @staticmethod
    def estimate_focus(face_detected: bool, head_orientation_degrees: float) -> Tuple[str, float]:
        """Backwards compatibility simple method."""
        if not face_detected:
            return FocusState.ABSENT, 0.95
        if abs(head_orientation_degrees) > 30.0:
            return FocusState.DISTRACTED, 0.85
        return FocusState.FOCUSED, 0.90


def math_hypot(dx: float, dy: float) -> float:
    import math
    return math.hypot(dx, dy)


def math_atan2(dy: float, dx: float) -> float:
    import math
    return math.atan2(dy, dx)
