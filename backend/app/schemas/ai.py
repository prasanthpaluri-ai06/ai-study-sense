from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==========================================
# 1. Resource Finder Schemas
# ==========================================
class ResourceItem(BaseModel):
    category: str
    title: str
    url: str
    source: str
    description: str
    is_external: bool = True


class ResourceFinderResponse(BaseModel):
    topic: str
    domain: str
    ai_guidance: str
    resources: List[ResourceItem]


# ==========================================
# 2. Revision Generator Schemas
# ==========================================
class QuickQuestion(BaseModel):
    question: str
    answer: str
    explanation: str


class RevisionRequest(BaseModel):
    topic_title: str


class RevisionResponse(BaseModel):
    topic_title: str
    category: Optional[str] = "Academic Curriculum"
    definition: str
    core_idea: str
    important_points: List[str]
    formula_or_syntax: Optional[str] = None
    example: str
    common_mistakes: List[str]
    quick_questions: List[QuickQuestion] = []
    final_recap: str


# ==========================================
# 3. Quiz Generator & Evaluator Schemas
# ==========================================
class QuizQuestionItem(BaseModel):
    id: int
    question_text: str
    question_type: str  # MCQ, ShortAnswer, Conceptual, Coding
    options: List[str] = []
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "Medium"
    hints: Optional[str] = None
    sample_code_or_io: Optional[str] = None


class QuizGenerateRequest(BaseModel):
    topic_title: str
    difficulty: Optional[str] = "Medium"
    num_questions: Optional[int] = 5


class QuizGeneratedResponse(BaseModel):
    topic_title: str
    difficulty: str
    total_questions: int
    questions: List[QuizQuestionItem]


class QuizSubmitRequest(BaseModel):
    topic_title: str
    difficulty: Optional[str] = "Medium"
    questions: List[QuizQuestionItem]
    student_answers: Dict[int, str]  # question_id -> answer string


class QuizEvaluationItem(BaseModel):
    question_id: int
    student_answer: str
    is_correct: bool
    score: float
    feedback: str


class QuizSubmissionResult(BaseModel):
    attempt_id: Optional[int] = None
    topic_title: str
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    weak_areas: List[str]
    strong_areas: List[str]
    recommendation: str
    evaluations: List[QuizEvaluationItem]


class QuizAttemptHistoryItem(BaseModel):
    id: int
    topic_title: str
    score: float
    total_score: float
    percentage: float
    recommendation: Optional[str] = None
    created_at: str


# ==========================================
# 4. Weakness Detector Schemas
# ==========================================
class WeaknessItem(BaseModel):
    topic: str
    subject_name: Optional[str] = None
    severity: str
    weakness_score: float
    source: str
    reason: str
    mathematical_breakdown: str
    recommended_action: str
    recommended_method: str


class WeaknessAnalysisReport(BaseModel):
    total_weaknesses: int
    critical_count: int
    high_count: int
    moderate_count: int
    weaknesses: List[WeaknessItem]
    overall_health_diagnosis: str


# ==========================================
# 5. Study Method Recommender Schemas
# ==========================================
class StudyMethodRequest(BaseModel):
    topic_title: str
    student_score: Optional[float] = None
    learning_objective: Optional[str] = "Deep Understanding"
    fatigue_level: Optional[str] = "Normal"
    topic_type: Optional[str] = None


class StudyMethodRecommendation(BaseModel):
    primary_method: str
    secondary_method: Optional[str] = None
    topic_title: str
    learning_objective: Optional[str] = "Deep Understanding"
    fatigue_level: Optional[str] = "Normal"
    confidence_score: float
    why_recommended: str
    execution_protocol: List[str]
    estimated_duration_minutes: int
    scientific_rationale: str
    practical_exercises: List[str] = []
    expected_outcomes: List[str] = []
    self_assessment_questions: List[str] = []


# ==========================================
# 6. AI Study Coach Schemas
# ==========================================
class CoachRecommendation(BaseModel):
    title: str
    category: str
    priority: str
    content: str
    why_recommended: str
    action_type: str
    action_payload: Dict[str, Any] = {}
    recommended_method: str = "Pomodoro"
    estimated_time_minutes: int = 25


class StudyHealthResponse(BaseModel):
    overall_score: float
    focus: float
    consistency: float
    academics: float
    posture: float
    tasks: float
    revision: float
    ai_interpretation: str


class ComprehensiveCoachReport(BaseModel):
    study_health_score: float
    health_score_breakdown: Dict[str, float]
    health_interpretation: str
    top_priorities: List[CoachRecommendation]
    total_recommendations: int
    weaknesses_summary: Dict[str, Any]
    academics_summary: Dict[str, Any]
    study_pace_summary: Dict[str, Any]
