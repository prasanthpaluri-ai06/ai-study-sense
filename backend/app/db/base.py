# Import Base and all models to ensure metadata registration for migrations & table creation
from backend.app.db.session import Base
from backend.app.models.user import User, StudentProfile, FaceTemplate
from backend.app.models.academic import Subject, Mark, Assignment
from backend.app.models.syllabus import Syllabus, Module, Topic, TopicProgress
from backend.app.models.session import StudySession, SessionMetric, FocusRecord, PostureRecord
from backend.app.models.quiz import QuizAttempt, QuizQuestion
from backend.app.models.analytics import Recommendation, Notification, StudyHealthScore
from backend.app.models.planner import SemesterConfig, BlackoutDate, PlannedTask
