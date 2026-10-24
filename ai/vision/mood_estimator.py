import math
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class MoodState:
    ENGAGED = "Engaged"
    CALM = "Calm"
    FATIGUED = "Fatigued / Tired-Looking"
    NEUTRAL = "Neutral"


class MoodEstimator:
    """
    Optional, non-diagnostic visual engagement and facial alertness estimator.
    
    IMPORTANT SAFETY & ETHICAL BOUNDARY:
    This service only estimates surface-level visual alertness (e.g. eye openness,
    head stillness) as a study-habit aid. It NEVER diagnoses mental health conditions,
    affective disorders, or emotional status.
    """

    @classmethod
    def estimate_engagement(
        cls,
        face_detected: bool,
        eye_aspect_ratio: Optional[float] = 0.28,
        head_stability: Optional[float] = 0.90,
        mouth_curvature: Optional[float] = 0.0,
    ) -> Dict[str, Any]:
        if not face_detected:
            return {
                "state": MoodState.NEUTRAL,
                "confidence": 0.50,
                "disclaimer": "Non-diagnostic engagement proxy only.",
            }

        # Eye Aspect Ratio (EAR): normal open eye ~ 0.25 to 0.35, droopy/fatigued < 0.20
        ear = eye_aspect_ratio if eye_aspect_ratio is not None else 0.28
        stability = head_stability if head_stability is not None else 0.90

        if ear < 0.20:
            state = MoodState.FATIGUED
            confidence = 0.82
            note = "Eyes appear droopy or prolonged blinking detected. Consider a 5-minute break or hydration."
        elif stability > 0.85 and ear >= 0.26:
            state = MoodState.ENGAGED
            confidence = 0.88
            note = "Attentive head posture and alert gaze detected."
        elif stability > 0.70:
            state = MoodState.CALM
            confidence = 0.85
            note = "Steady study focus."
        else:
            state = MoodState.NEUTRAL
            confidence = 0.75
            note = "Baseline appearance."

        return {
            "state": state,
            "confidence": confidence,
            "note": note,
            "eye_aspect_ratio": round(ear, 3),
            "disclaimer": "Non-diagnostic visual appearance estimate only.",
        }
