"""
AI StudySense - Ergonomic Posture Analyzer & Calibration Engine
Integrated with AI_Study_Bot dual-reference scale calibration, temporal smoothing,
and hysteresis state machine.
"""

import math
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class PostureLandmark(BaseModel):
    x: float
    y: float
    z: Optional[float] = 0.0
    visibility: Optional[float] = 1.0


class PostureCalibration(BaseModel):
    is_calibrated: bool = False
    baseline_face_width: Optional[float] = None
    baseline_shoulder_width: Optional[float] = None
    baseline_scale: float = 1.0
    poor_reference_scale: Optional[float] = None
    poor_reference_zoom_change: Optional[float] = None
    calibration_poor_angle: float = 20.0
    baseline_neck_angle: float = 12.0
    baseline_shoulder_angle: float = 0.0
    baseline_torso_height: float = 0.35
    bad_neck_angle: Optional[float] = None
    bad_torso_height: Optional[float] = None
    has_bad_reference: bool = False
    calibrated_at: Optional[float] = None


class PostureState:
    GOOD = "GOOD"
    BUFFER = "BUFFER"
    BAD = "BAD"


class PostureAnalyzer:
    """
    Ergonomic posture analyzer integrating AI_Study_Bot dual-reference zoom/scale
    and 3D geometric landmark tracking with hysteresis state transitions.
    """

    def __init__(
        self,
        buffer_duration: float = 3.0,  # POOR_POSTURE_TIME from AI_Study_Bot
        recovery_duration: float = 1.0,
        poor_threshold_percent: float = 0.80,  # POOR_THRESHOLD_PERCENT
        good_threshold_percent: float = 0.55,  # GOOD_THRESHOLD_PERCENT
        smoothing_frames: int = 10,  # SMOOTHING_FRAMES
        calibration_poor_angle: float = 20.0,  # CALIBRATION_POOR_ANGLE
        neck_deviation_threshold: float = 15.0,
        shoulder_tilt_threshold: float = 8.0,
        slouch_deviation_threshold: float = 0.15,
        smoothing_alpha: float = 0.25,
        # Backwards compatibility parameters
        bad_threshold_duration: Optional[float] = None,
        angle_threshold: Optional[float] = None,
    ):
        self.buffer_duration = bad_threshold_duration if bad_threshold_duration is not None else buffer_duration
        self.recovery_duration = recovery_duration
        self.poor_threshold_percent = poor_threshold_percent
        self.good_threshold_percent = good_threshold_percent
        self.smoothing_frames = smoothing_frames
        self.calibration_poor_angle = calibration_poor_angle
        self.neck_deviation_threshold = neck_deviation_threshold
        self.shoulder_tilt_threshold = shoulder_tilt_threshold
        self.slouch_deviation_threshold = slouch_deviation_threshold
        self.smoothing_alpha = smoothing_alpha
        self.angle_threshold = angle_threshold if angle_threshold is not None else (self.neck_deviation_threshold + 12.0)

        self.calibration = PostureCalibration(calibration_poor_angle=calibration_poor_angle)

        # State tracking
        self.current_state: str = PostureState.GOOD
        self.poor_posture_start_time: Optional[float] = None
        self.good_posture_start_time: Optional[float] = None
        self.warning: bool = False

        # Session event stats
        self.bad_posture_events: int = 0
        self.confirmed_bad_alerts: int = 0
        self.bad_posture_seconds: float = 0.0

        # Smoothing history
        self.scale_history: List[float] = []
        self.smoothed_neck_angle: float = 12.0
        self.smoothed_shoulder_tilt: float = 0.0
        self.smoothed_torso_height: float = 0.35

        self.last_update_time: float = time.time()

    @staticmethod
    def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two 2D points."""
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    @staticmethod
    def calculate_angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate angle in degrees of line (p1 -> p2) relative to vertical axis."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        rad = math.atan2(abs(dx), abs(dy) if abs(dy) > 1e-5 else 1e-5)
        return math.degrees(rad)

    @staticmethod
    def calculate_shoulder_tilt(left_sh: Tuple[float, float], right_sh: Tuple[float, float]) -> float:
        """Calculate shoulder slant angle relative to horizontal axis."""
        dx = abs(right_sh[0] - left_sh[0])
        dy = abs(right_sh[1] - left_sh[1])
        rad = math.atan2(dy, dx if dx > 1e-5 else 1e-5)
        return math.degrees(rad)

    def calibrate(
        self,
        ear_point: Tuple[float, float],
        shoulder_point: Tuple[float, float],
        left_shoulder: Optional[Tuple[float, float]] = None,
        right_shoulder: Optional[Tuple[float, float]] = None,
        left_ear: Optional[Tuple[float, float]] = None,
        right_ear: Optional[Tuple[float, float]] = None,
    ) -> PostureCalibration:
        """
        Step 1: Calibrate upright posture baseline dimensions & angles.
        """
        l_ear = left_ear or (ear_point[0] - 0.08, ear_point[1])
        r_ear = right_ear or (ear_point[0] + 0.08, ear_point[1])
        l_sh = left_shoulder or (shoulder_point[0] - 0.15, shoulder_point[1])
        r_sh = right_shoulder or (shoulder_point[0] + 0.15, shoulder_point[1])

        face_width = self.calculate_distance(l_ear, r_ear)
        shoulder_width = self.calculate_distance(l_sh, r_sh)

        neck_angle = self.calculate_angle(shoulder_point, ear_point)
        shoulder_tilt = self.calculate_shoulder_tilt(l_sh, r_sh)
        torso_height = abs(shoulder_point[1] - ear_point[1])

        self.calibration.is_calibrated = True
        self.calibration.baseline_face_width = round(max(0.01, face_width), 5)
        self.calibration.baseline_shoulder_width = round(max(0.01, shoulder_width), 5)
        self.calibration.baseline_scale = 1.0
        self.calibration.poor_reference_scale = None
        self.calibration.poor_reference_zoom_change = None
        self.calibration.has_bad_reference = False

        self.calibration.baseline_neck_angle = round(neck_angle, 2)
        self.calibration.baseline_shoulder_angle = round(shoulder_tilt, 2)
        self.calibration.baseline_torso_height = round(torso_height, 4)
        self.calibration.calibrated_at = time.time()

        self.scale_history.clear()
        self.smoothed_neck_angle = neck_angle
        self.smoothed_shoulder_tilt = shoulder_tilt
        self.smoothed_torso_height = torso_height
        self.reset()
        return self.calibration

    def calibrate_bad_reference(
        self,
        ear_point: Tuple[float, float],
        shoulder_point: Tuple[float, float],
        left_shoulder: Optional[Tuple[float, float]] = None,
        right_shoulder: Optional[Tuple[float, float]] = None,
        left_ear: Optional[Tuple[float, float]] = None,
        right_ear: Optional[Tuple[float, float]] = None,
    ) -> PostureCalibration:
        """
        Step 2: Calibrate slouched / forward-leaning reference boundary.
        """
        l_ear = left_ear or (ear_point[0] - 0.08, ear_point[1])
        r_ear = right_ear or (ear_point[0] + 0.08, ear_point[1])
        l_sh = left_shoulder or (shoulder_point[0] - 0.15, shoulder_point[1])
        r_sh = right_shoulder or (shoulder_point[0] + 0.15, shoulder_point[1])

        bad_angle = self.calculate_angle(shoulder_point, ear_point)
        bad_height = abs(shoulder_point[1] - ear_point[1])

        self.calibration.bad_neck_angle = round(bad_angle, 2)
        self.calibration.bad_torso_height = round(bad_height, 4)
        self.calibration.has_bad_reference = True

        # Calculate AI_Study_Bot zoom change relative to upright baseline
        base_fw = self.calibration.baseline_face_width
        base_sw = self.calibration.baseline_shoulder_width

        if base_fw and base_sw:
            cur_fw = self.calculate_distance(l_ear, r_ear)
            cur_sw = self.calculate_distance(l_sh, r_sh)
            face_scale = cur_fw / base_fw
            shoulder_scale = cur_sw / base_sw
            poor_scale = 0.40 * face_scale + 0.60 * shoulder_scale
            poor_zoom_change = poor_scale - 1.0
            self.calibration.poor_reference_scale = round(poor_scale, 4)
            self.calibration.poor_reference_zoom_change = round(max(0.015, poor_zoom_change), 4)

        # Dynamic angular deviation threshold
        if self.calibration.is_calibrated:
            diff_angle = abs(bad_angle - self.calibration.baseline_neck_angle)
            if diff_angle >= 4.0:
                self.neck_deviation_threshold = max(8.0, min(22.0, round(diff_angle * 0.55, 1)))

            base_h = self.calibration.baseline_torso_height
            if base_h > 0:
                diff_h = (base_h - bad_height) / base_h
                if diff_h > 0.04:
                    self.slouch_deviation_threshold = max(0.08, min(0.25, round(diff_h * 0.6, 2)))

        return self.calibration

    def process_landmarks(
        self,
        nose: Tuple[float, float],
        left_ear: Tuple[float, float],
        right_ear: Tuple[float, float],
        left_shoulder: Tuple[float, float],
        right_shoulder: Tuple[float, float],
        current_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Process normalized body landmarks, calculate AI_Study_Bot scale/zoom progress,
        apply EMA and rolling window smoothing, and evaluate the state machine.
        """
        now = current_time if current_time is not None else time.time()
        dt = max(0.0, now - self.last_update_time) if self.last_update_time else 0.1

        # 1. Dual scale & zoom calculation (AI_Study_Bot algorithm)
        face_width = self.calculate_distance(left_ear, right_ear)
        shoulder_width = self.calculate_distance(left_shoulder, right_shoulder)

        current_scale = 1.0
        current_zoom_change = 0.0
        current_progress = 0.0
        estimated_angle = 12.0

        if (
            self.calibration.baseline_face_width
            and self.calibration.baseline_shoulder_width
            and face_width > 0.001
            and shoulder_width > 0.001
        ):
            face_scale = face_width / self.calibration.baseline_face_width
            shoulder_scale = shoulder_width / self.calibration.baseline_shoulder_width
            raw_scale = 0.40 * face_scale + 0.60 * shoulder_scale

            # Rolling window smoothing
            self.scale_history.append(raw_scale)
            if len(self.scale_history) > self.smoothing_frames:
                self.scale_history.pop(0)
            current_scale = sum(self.scale_history) / len(self.scale_history)
            current_zoom_change = current_scale - 1.0

            if (
                self.calibration.poor_reference_zoom_change
                and self.calibration.poor_reference_zoom_change > 0.001
            ):
                current_progress = current_zoom_change / self.calibration.poor_reference_zoom_change
                current_progress = max(0.0, min(current_progress, 1.5))
                estimated_angle = current_progress * self.calibration_poor_angle

        # 2. Geometric neck angle & torso height (geometric complement)
        mid_ear = ((left_ear[0] + right_ear[0]) / 2.0, (left_ear[1] + right_ear[1]) / 2.0)
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2.0, (left_shoulder[1] + right_shoulder[1]) / 2.0)

        raw_neck_angle = self.calculate_angle(mid_shoulder, mid_ear)
        raw_shoulder_tilt = self.calculate_shoulder_tilt(left_shoulder, right_shoulder)
        raw_torso_height = abs(mid_shoulder[1] - mid_ear[1])

        alpha = self.smoothing_alpha
        self.smoothed_neck_angle = (alpha * raw_neck_angle) + ((1.0 - alpha) * self.smoothed_neck_angle)
        self.smoothed_shoulder_tilt = (alpha * raw_shoulder_tilt) + ((1.0 - alpha) * self.smoothed_shoulder_tilt)
        self.smoothed_torso_height = (alpha * raw_torso_height) + ((1.0 - alpha) * self.smoothed_torso_height)

        base_neck = self.calibration.baseline_neck_angle
        base_shoulder = self.calibration.baseline_shoulder_angle
        base_height = self.calibration.baseline_torso_height

        neck_deviation = abs(self.smoothed_neck_angle - base_neck)
        shoulder_deviation = abs(self.smoothed_shoulder_tilt - base_shoulder)
        slouch_ratio = (base_height - self.smoothed_torso_height) / base_height if base_height > 0 else 0.0

        # Determine if posture exceeds poor threshold:
        # If calibrated via zoom change: use current_progress >= 0.80
        # Otherwise: use angular/slouch deviation thresholds
        if self.calibration.has_bad_reference and self.calibration.poor_reference_zoom_change:
            is_poor_entry = current_progress >= self.poor_threshold_percent
            is_poor_recovery = current_progress < self.good_threshold_percent
        else:
            is_poor_entry = (
                neck_deviation > self.neck_deviation_threshold
                or shoulder_deviation > self.shoulder_tilt_threshold
                or slouch_ratio > self.slouch_deviation_threshold
            )
            is_poor_recovery = not is_poor_entry

        # 3. State Machine (GOOD -> BUFFER -> BAD with hysteresis)
        if self.current_state == PostureState.GOOD:
            if is_poor_entry:
                self.current_state = PostureState.BUFFER
                self.poor_posture_start_time = now
                self.bad_posture_events += 1
                self.warning = False
            else:
                self.poor_posture_start_time = None
                self.warning = False

        elif self.current_state == PostureState.BUFFER:
            if is_poor_recovery:
                self.current_state = PostureState.GOOD
                self.poor_posture_start_time = None
                self.warning = False
            else:
                poor_dur = now - (self.poor_posture_start_time or now)
                if poor_dur >= self.buffer_duration:
                    self.current_state = PostureState.BAD
                    self.confirmed_bad_alerts += 1
                    self.warning = True
                self.bad_posture_seconds += dt

        elif self.current_state == PostureState.BAD:
            if is_poor_recovery:
                self.current_state = PostureState.GOOD
                self.poor_posture_start_time = None
                self.warning = False
            else:
                self.warning = True
                self.bad_posture_seconds += dt

        # Remaining buffer time
        poor_elapsed = now - (self.poor_posture_start_time or now) if self.poor_posture_start_time else 0.0
        remaining_buffer = max(0.0, self.buffer_duration - poor_elapsed)

        # Hardware mappings
        if self.current_state == PostureState.GOOD:
            led = "GREEN"
            oled_anim = "good_posture"
            msg = "GOOD POSTURE"
        elif self.current_state == PostureState.BUFFER:
            led = "YELLOW"
            oled_anim = "buffer_warning"
            msg = f"CHECKING ({remaining_buffer:.1f}s)"
        else:
            led = "RED"
            oled_anim = "bad_posture"
            msg = "SIT UPRIGHT!"

        self.last_update_time = now

        return {
            "state": self.current_state,
            "led_color": led,
            "oled_animation": oled_anim,
            "oled_message": msg,
            "metrics": {
                "neck_angle": round(self.smoothed_neck_angle, 1),
                "shoulder_tilt": round(self.smoothed_shoulder_tilt, 1),
                "torso_height": round(self.smoothed_torso_height, 3),
                "neck_deviation": round(neck_deviation, 1),
                "shoulder_deviation": round(shoulder_deviation, 1),
                "slouch_ratio": round(slouch_ratio * 100.0, 1),
                "zoom_ratio": round(current_scale, 3),
                "zoom_change": round(current_zoom_change * 100.0, 1),
                "lean_angle": round(estimated_angle, 1),
                "progress": round(current_progress, 2),
                "remaining_buffer": round(remaining_buffer, 1),
                "bad_events_count": self.bad_posture_events,
                "confirmed_bad_count": self.confirmed_bad_alerts,
                "bad_posture_seconds": round(self.bad_posture_seconds, 1),
                "is_calibrated": self.calibration.is_calibrated,
                "has_bad_reference": self.calibration.has_bad_reference,
            },
        }

    def process_angle(self, measured_angle: float, current_time: Optional[float] = None) -> Tuple[str, str, str]:
        """Process direct measured angle for backwards compatibility."""
        return self.process_angle_simple(measured_angle, current_time)

    def process_angle_simple(self, measured_angle: float, current_time: Optional[float] = None) -> Tuple[str, str, str]:
        """Simple angle interface for backwards compatibility with test harnesses."""
        now = current_time if current_time is not None else time.time()
        is_poor = measured_angle > getattr(self, "angle_threshold", 25.0)

        if not is_poor:
            self.current_state = PostureState.GOOD
            self.poor_posture_start_time = None
            led = "GREEN"
            anim = "good_posture"
        else:
            if self.poor_posture_start_time is None:
                self.poor_posture_start_time = now
            elapsed = now - self.poor_posture_start_time
            if elapsed >= self.buffer_duration:
                self.current_state = PostureState.BAD
                led = "RED"
                anim = "bad_posture"
            else:
                self.current_state = PostureState.BUFFER
                led = "YELLOW"
                anim = "buffer_warning"

        return self.current_state, led, anim

    def reset(self):
        self.current_state = PostureState.GOOD
        self.poor_posture_start_time = None
        self.good_posture_start_time = None
        self.scale_history.clear()
        self.warning = False
        self.last_update_time = time.time()
