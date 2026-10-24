from dataclasses import dataclass


@dataclass
class AIConfig:
    # Posture state timing thresholds in seconds
    POSTURE_BUFFER_SECONDS: float = 5.0
    POSTURE_BAD_THRESHOLD_SECONDS: float = 10.0
    
    # Angle in degrees for posture deviation (e.g. forward neck / slouch)
    POSTURE_SLOUCH_ANGLE_THRESHOLD: float = 25.0
    
    # Face authentication similarity threshold
    FACE_SIMILARITY_THRESHOLD: float = 0.70
    
    # Study methods supported in system
    SUPPORTED_STUDY_METHODS = [
        "Pomodoro",
        "52/17",
        "Active Recall",
        "Spaced Repetition",
        "Feynman Technique",
    ]


ai_config = AIConfig()
