import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ai.academic.coach import AICoach
from ai.academic.method_recommender import StudyMethodRecommender
from ai.academic.quiz_generator import QuizGenerator
from ai.academic.resource_finder import ResourceFinder
from ai.academic.revision_generator import RevisionGenerator
from ai.academic.weakness_detector import WeaknessDetector
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.academic import Assignment, Mark, Subject
from backend.app.models.quiz import QuizAttempt, QuizQuestion
from backend.app.models.session import StudySession
from backend.app.models.syllabus import Module, Syllabus, Topic, TopicProgress
from backend.app.models.user import User
from backend.app.schemas.ai import (
    ComprehensiveCoachReport,
    QuizAttemptHistoryItem,
    QuizGenerateRequest,
    QuizGeneratedResponse,
    QuizSubmitRequest,
    QuizSubmissionResult,
    ResourceFinderResponse,
    RevisionRequest,
    RevisionResponse,
    StudyHealthResponse,
    StudyMethodRecommendation,
    StudyMethodRequest,
    WeaknessAnalysisReport,
)

router = APIRouter()


# =========================================================================
# 1. AI Resource Finder
# =========================================================================
@router.get("/resources", response_model=ResourceFinderResponse)
async def find_resources(query: str = Query(..., min_length=1)):
    """
    Categorizes and retrieves verified academic resources (Videos, Practice, Reference, Articles)
    for a topic without fabricating URLs.
    """
    return ResourceFinder.find_resources(topic=query)


# =========================================================================
# 2. AI Revision Generator
# =========================================================================
@router.post("/revision/generate", response_model=RevisionResponse)
async def generate_revision(payload: RevisionRequest):
    """
    Generates structured 8-step revision notes (definitions, core ideas, formulas,
    pitfalls, active recall questions, and recap).
    """
    rev = RevisionGenerator.generate_revision(topic_title=payload.topic_title)
    return RevisionResponse(
        topic_title=rev.topic_title,
        category=rev.category,
        definition=rev.definition,
        core_idea=rev.core_idea,
        important_points=rev.important_points,
        formula_or_syntax=rev.formulas_or_syntax,
        example=rev.example,
        common_mistakes=rev.common_mistakes,
        quick_questions=[
            {"question": q.question, "answer": q.answer, "explanation": q.explanation}
            for q in rev.quick_questions
        ],
        final_recap=rev.final_recap,
    )


# =========================================================================
# 3. AI Quiz Generator & Persistence
# =========================================================================
@router.post("/quiz/generate", response_model=QuizGeneratedResponse)
async def generate_quiz(payload: QuizGenerateRequest):
    """
    Generates structured MCQs, short answers, conceptual questions, and coding problems
    with configurable difficulty for any syllabus topic.
    """
    return QuizGenerator.generate_quiz(
        topic_title=payload.topic_title,
        difficulty=payload.difficulty or "Medium",
        num_questions=payload.num_questions or 5,
    )


@router.post("/quiz/submit", response_model=QuizSubmissionResult)
async def submit_quiz(
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates quiz submissions, calculates scores, identifies strong/weak areas,
    and persists the attempt and question records in the database.
    """
    # 1. Run evaluation
    result = QuizGenerator.evaluate_quiz_submission(
        topic_title=payload.topic_title,
        questions=payload.questions,
        student_answers=payload.student_answers,
    )

    # 2. Persist QuizAttempt record
    attempt = QuizAttempt(
        user_id=current_user.id,
        topic_title=payload.topic_title,
        score=result.total_score,
        total_score=result.max_score,
        percentage=result.percentage,
        strong_areas=json.dumps(result.strong_areas),
        weak_areas=json.dumps(result.weak_areas),
        recommendation=result.recommendation,
    )
    db.add(attempt)
    await db.flush()  # Populates attempt.id

    # 3. Persist individual QuizQuestion answers
    for ev in result.evaluations:
        # Find original question
        matching_q = next((q for q in payload.questions if q.id == ev.question_id), None)
        if matching_q:
            qq = QuizQuestion(
                attempt_id=attempt.id,
                question_text=matching_q.question_text,
                question_type=matching_q.question_type,
                options=json.dumps(matching_q.options) if matching_q.options else None,
                correct_answer=matching_q.correct_answer,
                student_answer=ev.student_answer,
                is_correct=ev.score,
                explanation=ev.feedback,
            )
            db.add(qq)

    await db.commit()
    result.attempt_id = attempt.id
    return result


@router.get("/quiz/history", response_model=List[QuizAttemptHistoryItem])
async def get_quiz_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all past quiz attempts for the authenticated student."""
    stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.created_at.desc())
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()

    return [
        QuizAttemptHistoryItem(
            id=a.id,
            topic_title=a.topic_title,
            score=a.score,
            total_score=a.total_score,
            percentage=a.percentage,
            recommendation=a.recommendation,
            created_at=a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
        )
        for a in attempts
    ]


# =========================================================================
# 4. AI Weakness Detector
# =========================================================================
@router.get("/weaknesses", response_model=WeaknessAnalysisReport)
async def get_weaknesses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Identifies weak topics across real quiz scores, marks, and syllabus progress
    using a transparent mathematical scoring model.
    """
    # 1. Fetch real quiz attempts
    q_stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(20)
    )
    q_res = await db.execute(q_stmt)
    quiz_data = [
        {"topic_title": q.topic_title, "percentage": q.percentage}
        for q in q_res.scalars().all()
    ]

    # 2. Fetch real subject marks
    m_stmt = (
        select(Mark, Subject.name)
        .join(Subject, Mark.subject_id == Subject.id)
        .where(Subject.user_id == current_user.id)
    )
    m_res = await db.execute(m_stmt)
    marks_data = [
        {
            "subject_name": row[1],
            "scored_marks": row[0].scored_marks,
            "total_marks": row[0].total_marks,
            "assessment_name": row[0].assessment_name,
            "weightage": row[0].weightage,
        }
        for row in m_res.all()
    ]

    # 3. Fetch syllabus topics in 'Needs Revision'
    syl_stmt = (
        select(Topic, TopicProgress.status, Subject.name)
        .join(Module, Topic.module_id == Module.id)
        .join(Syllabus, Module.syllabus_id == Syllabus.id)
        .join(Subject, Syllabus.subject_id == Subject.id)
        .outerjoin(TopicProgress, (TopicProgress.topic_id == Topic.id) & (TopicProgress.user_id == current_user.id))
        .where(Syllabus.user_id == current_user.id)
    )
    syl_res = await db.execute(syl_stmt)
    syllabus_topics = [
        {
            "title": row[0].title,
            "is_core": row[0].is_core,
            "status": row[1] or "Not Started",
            "subject_name": row[2],
        }
        for row in syl_res.all()
    ]

    return WeaknessDetector.analyze_weaknesses(
        quiz_attempts=quiz_data,
        subject_marks=marks_data,
        syllabus_topics=syllabus_topics,
    )


# =========================================================================
# 5. AI Study Method Recommender
# =========================================================================
@router.post("/method/recommend", response_model=StudyMethodRecommendation)
async def recommend_study_method(payload: StudyMethodRequest):
    """
    Recommends the optimal study method among the 5 approved methods
    (Pomodoro, 52/17, Active Recall, Spaced Repetition, Feynman Technique).
    """
    if not payload.topic_title or not payload.topic_title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic title cannot be empty.",
        )

    return StudyMethodRecommender.recommend_method(
        topic_title=payload.topic_title,
        student_score=payload.student_score,
        learning_objective=payload.learning_objective or "Deep Understanding",
        fatigue_level=payload.fatigue_level or "Normal",
        topic_type=payload.topic_type,
    )


# =========================================================================
# 6. AI Study Coach & Health Score
# =========================================================================
@router.get("/coach/plan", response_model=ComprehensiveCoachReport)
@router.get("/recommendations")
async def get_coach_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Synthesizes marks, assignments, syllabus roadmaps, weak topics, quizzes, and session history
    into prioritized, actionable recommendations with explicit explanations of WHY.
    """
    # 1. Fetch upcoming assignments
    assign_stmt = (
        select(Assignment, Subject.name)
        .join(Subject, Assignment.subject_id == Subject.id)
        .where(Subject.user_id == current_user.id)
        .order_by(Assignment.due_date.asc())
    )
    assign_res = await db.execute(assign_stmt)
    assignments = [
        {
            "id": row[0].id,
            "title": row[0].title,
            "subject_name": row[1],
            "subject_id": row[0].subject_id,
            "due_date": row[0].due_date.strftime("%Y-%m-%d"),
            "status": row[0].status,
            "priority": row[0].priority,
        }
        for row in assign_res.all()
    ]

    # 2. Fetch quiz attempts for weakness analysis
    q_stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(10)
    )
    q_res = await db.execute(q_stmt)
    quizzes = [
        {"topic_title": q.topic_title, "percentage": q.percentage}
        for q in q_res.scalars().all()
    ]

    # 3. Fetch marks
    m_stmt = (
        select(Mark, Subject.name)
        .join(Subject, Mark.subject_id == Subject.id)
        .where(Subject.user_id == current_user.id)
    )
    m_res = await db.execute(m_stmt)
    marks = [
        {
            "subject_name": row[1],
            "scored_marks": row[0].scored_marks,
            "total_marks": row[0].total_marks,
            "assessment_name": row[0].assessment_name,
            "weightage": row[0].weightage,
        }
        for row in m_res.all()
    ]

    # 4. Fetch syllabus roadmaps
    syl_stmt = (
        select(Syllabus)
        .options(selectinload(Syllabus.modules).selectinload(Module.topics))
        .where(Syllabus.user_id == current_user.id)
    )
    syl_res = await db.execute(syl_stmt)
    syllabi = syl_res.scalars().all()
    roadmaps = []
    for s in syllabi:
        roadmaps.append({
            "id": s.id,
            "title": s.title,
            "subject_id": s.subject_id,
            "subject_name": s.subject.name if s.subject else "Course",
            "modules": [
                {
                    "id": m.id,
                    "name": m.name,
                    "topics": [
                        {
                            "id": t.id,
                            "title": t.title,
                            "is_core": t.is_core,
                            "is_completed": False,  # Simplified for coach synthesis
                            "recommended_study_method": t.recommended_study_method,
                        }
                        for t in m.topics
                    ],
                }
                for m in s.modules
            ],
        })

    # 5. Fetch study sessions
    sess_stmt = (
        select(StudySession)
        .where(StudySession.user_id == current_user.id)
        .order_by(StudySession.start_time.desc())
        .limit(10)
    )
    sess_res = await db.execute(sess_stmt)
    sessions = [{"id": s.id, "method": s.study_method, "duration": s.duration_minutes} for s in sess_res.scalars().all()]

    # 6. Analyze Weaknesses
    weakness_report = WeaknessDetector.analyze_weaknesses(quizzes, marks)
    weaknesses_list = [w.model_dump() for w in weakness_report.weaknesses]

    # 7. Generate Coach Plan
    coach_plan = AICoach.generate_coach_plan(
        assignments=assignments,
        weaknesses=weaknesses_list,
        roadmaps=roadmaps,
        quizzes=quizzes,
        sessions=sessions,
    )

    return coach_plan


@router.get("/study-health", response_model=StudyHealthResponse)
async def get_study_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compute and retrieve the live composite Study Health Score."""
    health = AICoach.calculate_study_health_score()
    return StudyHealthResponse(**health)
