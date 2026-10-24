from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ai.academic.analytics_engine import AnalyticsEngine, LongTermAnalyticsReport, SessionPerformanceReport
from ai.academic.coach import AICoach
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.academic import Assignment, Mark, Subject
from backend.app.models.analytics import StudyHealthScore
from backend.app.models.quiz import QuizAttempt
from backend.app.models.session import SessionMetric, SpacedRepetitionCard, StudySession
from backend.app.models.syllabus import Syllabus
from backend.app.models.user import User
from backend.app.schemas.ai import StudyHealthResponse

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """
    Returns aggregate student growth summary: total study hours, streak,
    study health score, average productivity, and coursework completion.
    """
    # 1. Fetch study sessions
    sess_stmt = (
        select(StudySession)
        .options(selectinload(StudySession.metric))
        .where(StudySession.user_id == current_user.id)
    )
    sess_res = await db.execute(sess_stmt)
    sessions = sess_res.scalars().all()

    total_mins = sum(s.duration_minutes for s in sessions)
    session_dates = [s.start_time for s in sessions if s.start_time]
    streak_data = AnalyticsEngine.calculate_study_streak(session_dates, tz_name=x_timezone)

    prod_scores = [s.metric.productivity_score for s in sessions if s.metric and s.metric.productivity_score]
    avg_prod = round(sum(prod_scores) / len(prod_scores), 1) if prod_scores else 85.0

    # 2. Fetch Assignments
    assign_stmt = (
        select(Assignment)
        .join(Subject, Assignment.subject_id == Subject.id)
        .where(Subject.user_id == current_user.id)
    )
    assign_res = await db.execute(assign_stmt)
    assignments = assign_res.scalars().all()
    completed_tasks = sum(1 for a in assignments if a.status == "Completed")
    total_tasks = len(assignments)
    completion_rate = round((completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 100.0, 1)

    # 3. Calculate Study Health Score
    focus_scores = [s.metric.focus_score for s in sessions if s.metric and s.metric.focus_score is not None]
    posture_scores = [s.metric.posture_score for s in sessions if s.metric and s.metric.posture_score is not None]

    avg_focus = (sum(focus_scores) / len(focus_scores)) if focus_scores else 85.0
    avg_posture = (sum(posture_scores) / len(posture_scores)) if posture_scores else 80.0
    consistency_score = min(100.0, max(40.0, streak_data["current_streak"] * 20.0 + 30.0))

    health_data = AICoach.calculate_study_health_score(
        focus_avg=avg_focus,
        consistency_avg=consistency_score,
        academics_avg=85.0,
        posture_avg=avg_posture,
        task_completion_rate=completion_rate,
        revision_rate=80.0,
    )

    return {
        "total_study_minutes": round(total_mins, 1),
        "total_study_hours": round(total_mins / 60.0, 2),
        "total_sessions": len(sessions),
        "current_streak_days": streak_data["current_streak"],
        "longest_streak_days": streak_data["longest_streak"],
        "average_productivity_score": avg_prod,
        "completed_tasks_count": completed_tasks,
        "total_tasks_count": total_tasks,
        "task_completion_rate": completion_rate,
        "study_health_score": health_data["overall_score"],
        "study_health_interpretation": health_data["ai_interpretation"],
        "study_health_breakdown": health_data,
    }


@router.get("/trends", response_model=LongTermAnalyticsReport)
async def get_long_term_trends(
    timeframe: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """
    Returns aggregated daily, weekly, or monthly study time, focus quality,
    posture compliance, and quiz accuracy trends with AI summary.
    """
    # 1. Fetch sessions
    sess_stmt = (
        select(StudySession)
        .options(selectinload(StudySession.metric))
        .where(StudySession.user_id == current_user.id)
        .order_by(StudySession.start_time.asc())
    )
    sess_res = await db.execute(sess_stmt)
    sessions = [
        {
            "start_time": s.start_time,
            "duration_minutes": s.duration_minutes,
            "focus_score": s.metric.focus_score if s.metric else 100.0,
            "posture_score": s.metric.posture_score if s.metric else 100.0,
            "productivity_score": s.metric.productivity_score if s.metric else 85.0,
        }
        for s in sess_res.scalars().all()
    ]

    # 2. Fetch quizzes
    quiz_stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.created_at.asc())
    )
    quiz_res = await db.execute(quiz_stmt)
    quizzes = [
        {
            "created_at": q.created_at,
            "percentage": q.percentage,
        }
        for q in quiz_res.scalars().all()
    ]

    return AnalyticsEngine.aggregate_long_term_trends(
        sessions=sessions,
        quizzes=quizzes,
        timeframe=timeframe,
        tz_name=x_timezone,
    )


@router.get("/streak")
async def get_streak_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """Retrieves active study streak and 30-day activity map."""
    stmt = (
        select(StudySession.start_time)
        .where(StudySession.user_id == current_user.id)
        .order_by(StudySession.start_time.asc())
    )
    res = await db.execute(stmt)
    dates = res.scalars().all()
    return AnalyticsEngine.calculate_study_streak(dates, tz_name=x_timezone)


@router.get("/session/{session_id}/report", response_model=SessionPerformanceReport)
async def get_session_performance_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a comprehensive session performance report with deterministic
    productivity score and ergonomic posture breakdown.
    """
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.metric), selectinload(StudySession.subject))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    metric = session.metric
    focus_score = metric.focus_score if metric else 100.0
    posture_score = metric.posture_score if metric else 100.0
    distractions = metric.distraction_count if metric else 0
    alerts = metric.posture_alerts_count if metric else 0

    prod_data = AnalyticsEngine.calculate_productivity_score(
        duration_minutes=session.duration_minutes,
        focus_score=focus_score,
        posture_score=posture_score,
        distraction_count=distractions,
        posture_alerts_count=alerts,
        task_completed=session.status == "completed",
    )

    ai_summary = (
        f"{session.study_method} study block on '{session.topic_name}' completed ({session.duration_minutes:.1f} mins). "
        f"Productivity Score: {prod_data['productivity_score']}/100. "
        f"Maintained {posture_score:.0f}% posture quality with {alerts} posture correction alerts."
    )

    return SessionPerformanceReport(
        session_id=session.id,
        topic_name=session.topic_name or "General Study",
        study_method=session.study_method,
        duration_minutes=session.duration_minutes,
        focus_score=focus_score,
        posture_score=posture_score,
        productivity_score=prod_data["productivity_score"],
        good_posture_seconds=metric.good_posture_seconds if metric else int(session.duration_minutes * 60),
        buffer_posture_seconds=metric.buffer_posture_seconds if metric else 0,
        bad_posture_seconds=metric.bad_posture_seconds if metric else 0,
        distraction_count=distractions,
        posture_alerts_count=alerts,
        mathematical_breakdown=prod_data["mathematical_breakdown"],
        ai_summary=ai_summary,
    )


@router.post("/health/calculate", response_model=StudyHealthResponse)
async def recalculate_study_health_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Recalculates and persists the student's non-medical Study Health Score.
    """
    overview = await get_analytics_overview(current_user=current_user, db=db)
    breakdown = overview["study_health_breakdown"]

    # Persist in DB
    score_record = StudyHealthScore(
        user_id=current_user.id,
        overall_score=breakdown["overall_score"],
        focus_component=breakdown["focus"],
        consistency_component=breakdown["consistency"],
        academic_component=breakdown["academics"],
        posture_component=breakdown["posture"],
        task_component=breakdown["tasks"],
        revision_component=breakdown["revision"],
        ai_interpretation=breakdown["ai_interpretation"],
    )
    db.add(score_record)
    await db.commit()

    return StudyHealthResponse(**breakdown)
