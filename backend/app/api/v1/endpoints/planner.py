from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ai.academic.planner_engine import AcademicPlannerEngine
from backend.app.api.deps import get_current_user, get_db
from backend.app.core.timezone_utils import now_utc, today_local_date, today_local_str
from backend.app.models.academic import Assignment, Subject
from backend.app.models.planner import BlackoutDate, PlannedTask, SemesterConfig
from backend.app.models.syllabus import Module, Syllabus, Topic, TopicProgress
from backend.app.models.user import User
from backend.app.schemas.planner import (
    BlackoutDateCreate,
    BlackoutDateOut,
    PlannedTaskCreate,
    PlannedTaskOut,
    PlannedTaskReschedule,
    PlannerOverviewResponse,
    RebalancePreviewResponse,
    SemesterConfigCreate,
    SemesterConfigOut,
)

router = APIRouter()


async def _fetch_full_subject_data(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    """Helper to load all subjects, syllabi, modules, topics, and topic_progress for a user."""
    stmt = (
        select(Subject)
        .options(
            selectinload(Subject.syllabi)
            .selectinload(Syllabus.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.progress)
        )
        .where(Subject.user_id == user_id)
        .order_by(Subject.name)
    )
    res = await db.execute(stmt)
    subjects = res.scalars().all()

    result: List[Dict[str, Any]] = []
    for s in subjects:
        modules_list: List[Dict[str, Any]] = []
        for syl in s.syllabi:
            for mod in syl.modules:
                topics_list: List[Dict[str, Any]] = []
                for top in mod.topics:
                    user_prog = next((p for p in top.progress if p.user_id == user_id), None)
                    is_comp = (user_prog.is_completed or user_prog.status == "Completed") if user_prog else False
                    topics_list.append({
                        "id": top.id,
                        "title": top.title,
                        "order_index": top.order_index,
                        "is_core": top.is_core,
                        "difficulty_level": top.difficulty_level,
                        "conceptual_dependencies": top.conceptual_dependencies,
                        "is_completed": is_comp,
                        "status": user_prog.status if user_prog else "Not Started",
                    })
                modules_list.append({
                    "id": mod.id,
                    "name": mod.name,
                    "order_index": mod.order_index,
                    "topics": topics_list,
                })

        result.append({
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "color": s.color or "#5A6E52",
            "semester": s.semester,
            "credits": s.credits,
            "modules": modules_list,
        })
    return result


async def _fetch_assignments_data(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    """Helper to fetch assignments for a user with subject details."""
    stmt = (
        select(Assignment)
        .join(Subject, Assignment.subject_id == Subject.id)
        .options(selectinload(Assignment.subject))
        .where(Subject.user_id == user_id)
        .order_by(Assignment.due_date.asc())
    )
    res = await db.execute(stmt)
    assignments = res.scalars().all()

    result: List[Dict[str, Any]] = []
    for a in assignments:
        result.append({
            "id": a.id,
            "subject_id": a.subject_id,
            "subject_name": a.subject.name if a.subject else "Coursework",
            "subject_code": a.subject.code if a.subject else "",
            "subject_color": a.subject.color if a.subject else "#8C6D58",
            "title": a.title,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "priority": a.priority,
            "status": a.status,
            "estimated_effort_hours": a.estimated_effort_hours,
        })
    return result


def _task_to_out(t: PlannedTask) -> PlannedTaskOut:
    return PlannedTaskOut(
        id=t.id,
        subject_id=t.subject_id,
        subject_name=t.subject.name if t.subject else None,
        subject_code=t.subject.code if t.subject else None,
        subject_color=t.subject.color if t.subject else "#5A6E52",
        topic_id=t.topic_id,
        assignment_id=t.assignment_id,
        title=t.title,
        module_name=t.module_name,
        task_type=t.task_type or "learning",
        scheduled_date=t.scheduled_date,
        priority=t.priority or "Medium",
        estimated_minutes=t.estimated_minutes or 45,
        is_completed=bool(t.is_completed),
        completed_at=t.completed_at,
        is_manual_override=bool(t.is_manual_override),
        notes=t.notes,
        order_index=t.order_index or 0,
    )


# =========================================================================
# 1. Semester Configuration
# =========================================================================
@router.get("/semester")
async def get_semester_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the student's semester configuration and blackout dates."""
    stmt = select(SemesterConfig).where(SemesterConfig.user_id == current_user.id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id).order_by(BlackoutDate.date)
    b_res = await db.execute(b_stmt)
    blackouts = b_res.scalars().all()

    return {
        "is_configured": config is not None and config.is_configured,
        "semester": SemesterConfigOut.model_validate(config) if config else None,
        "blackout_dates": [BlackoutDateOut.model_validate(b) for b in blackouts],
    }


@router.post("/semester", response_model=SemesterConfigOut)
async def set_or_update_semester_config(
    payload: SemesterConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or update semester start and end dates and generate study schedule."""
    # Validate date formats and logic
    try:
        s_date = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    if s_date >= e_date:
        raise HTTPException(status_code=400, detail="Semester end date must be after start date.")

    stmt = select(SemesterConfig).where(SemesterConfig.user_id == current_user.id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    if not config:
        config = SemesterConfig(
            user_id=current_user.id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            study_days=payload.study_days,
            max_daily_tasks=payload.max_daily_tasks or 3,
            target_study_hours_daily=payload.target_study_hours_daily or 3.0,
            is_configured=True,
        )
        db.add(config)
    else:
        config.start_date = payload.start_date
        config.end_date = payload.end_date
        config.study_days = payload.study_days
        config.max_daily_tasks = payload.max_daily_tasks or config.max_daily_tasks
        config.target_study_hours_daily = payload.target_study_hours_daily or config.target_study_hours_daily
        config.is_configured = True

    await db.commit()
    await db.refresh(config)

    # Automatically generate schedule if no tasks exist
    t_stmt = select(PlannedTask).where(PlannedTask.user_id == current_user.id)
    t_res = await db.execute(t_stmt)
    existing_tasks = t_res.scalars().all()

    if not existing_tasks:
        # Load academic data
        subjects_data = await _fetch_full_subject_data(db, current_user.id)
        assignments_data = await _fetch_assignments_data(db, current_user.id)
        b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id)
        b_res = await db.execute(b_stmt)
        blackouts = [{"date": b.date, "reason": b.reason} for b in b_res.scalars().all()]

        plan_res = AcademicPlannerEngine.plan_topics_and_assignments(
            start_date_str=config.start_date,
            end_date_str=config.end_date,
            study_days=config.study_days,
            blackout_dates=blackouts,
            subjects_data=subjects_data,
            assignments_data=assignments_data,
            existing_tasks=[],
            max_daily_tasks=config.max_daily_tasks,
            from_today=False,
            preserve_manual=True,
        )

        for task_dict in plan_res["tasks_to_create"]:
            new_task = PlannedTask(
                user_id=current_user.id,
                subject_id=task_dict.get("subject_id"),
                topic_id=task_dict.get("topic_id"),
                assignment_id=task_dict.get("assignment_id"),
                title=task_dict["title"],
                module_name=task_dict.get("module_name"),
                task_type=task_dict.get("task_type", "learning"),
                scheduled_date=task_dict["scheduled_date"],
                priority=task_dict.get("priority", "Medium"),
                estimated_minutes=task_dict.get("estimated_minutes", 45),
                is_completed=False,
                is_manual_override=False,
                order_index=task_dict.get("order_index", 0),
            )
            db.add(new_task)

        await db.commit()

    return SemesterConfigOut.model_validate(config)


# =========================================================================
# 2. Plan Generation & Rebalancing
# =========================================================================
@router.post("/generate")
async def generate_study_plan(
    preserve_manual: bool = Query(True, description="Preserve manual schedule overrides"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Distributes unfinished syllabus topics and upcoming assignments across semester study days.
    Preserves completed topics and user manual overrides.
    """
    stmt = select(SemesterConfig).where(SemesterConfig.user_id == current_user.id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    if not config or not config.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Semester configuration required before generating study plan.",
        )

    subjects_data = await _fetch_full_subject_data(db, current_user.id)
    assignments_data = await _fetch_assignments_data(db, current_user.id)

    b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id)
    b_res = await db.execute(b_stmt)
    blackouts = [{"date": b.date, "reason": b.reason} for b in b_res.scalars().all()]

    t_stmt = select(PlannedTask).where(PlannedTask.user_id == current_user.id)
    t_res = await db.execute(t_stmt)
    existing_tasks = [
        {
            "id": t.id,
            "topic_id": t.topic_id,
            "assignment_id": t.assignment_id,
            "scheduled_date": t.scheduled_date,
            "is_completed": t.is_completed,
            "is_manual_override": t.is_manual_override,
        }
        for t in t_res.scalars().all()
    ]

    plan_res = AcademicPlannerEngine.plan_topics_and_assignments(
        start_date_str=config.start_date,
        end_date_str=config.end_date,
        study_days=config.study_days,
        blackout_dates=blackouts,
        subjects_data=subjects_data,
        assignments_data=assignments_data,
        existing_tasks=existing_tasks,
        max_daily_tasks=config.max_daily_tasks,
        from_today=True,
        preserve_manual=preserve_manual,
    )

    # Delete uncompleted, non-manual tasks so fresh allocation takes effect
    # Completed tasks and manual overrides are retained!
    del_stmt = select(PlannedTask).where(
        (PlannedTask.user_id == current_user.id)
        & (PlannedTask.is_completed == False)
    )
    if preserve_manual:
        del_stmt = del_stmt.where(PlannedTask.is_manual_override == False)

    del_res = await db.execute(del_stmt)
    for task_to_delete in del_res.scalars().all():
        await db.delete(task_to_delete)

    # Insert newly calculated tasks
    created_count = 0
    for task_dict in plan_res["tasks_to_create"]:
        new_task = PlannedTask(
            user_id=current_user.id,
            subject_id=task_dict.get("subject_id"),
            topic_id=task_dict.get("topic_id"),
            assignment_id=task_dict.get("assignment_id"),
            title=task_dict["title"],
            module_name=task_dict.get("module_name"),
            task_type=task_dict.get("task_type", "learning"),
            scheduled_date=task_dict["scheduled_date"],
            priority=task_dict.get("priority", "Medium"),
            estimated_minutes=task_dict.get("estimated_minutes", 45),
            is_completed=False,
            is_manual_override=False,
            order_index=task_dict.get("order_index", 0),
        )
        db.add(new_task)
        created_count += 1

    await db.commit()

    return {
        "message": f"Successfully planned {created_count} study tasks across the semester.",
        "created_count": created_count,
        "warnings": plan_res["workload_warnings"],
        "insights": plan_res["ai_insights"],
        "stats": plan_res["stats"],
    }


# =========================================================================
# 3. Overview & Academic Command Center
# =========================================================================
@router.get("/overview", response_model=PlannerOverviewResponse)
async def get_planner_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """
    Central academic command center synthesizing semester progress,
    subject mastery, today's schedule, pending assignments, and AI insights.
    """
    stmt = select(SemesterConfig).where(SemesterConfig.user_id == current_user.id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    today_str = today_local_str(x_timezone)

    # Fetch blackout dates
    b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id).order_by(BlackoutDate.date)
    b_res = await db.execute(b_stmt)
    blackouts = [BlackoutDateOut.model_validate(b) for b in b_res.scalars().all()]

    if not config or not config.is_configured:
        return PlannerOverviewResponse(
            is_configured=False,
            blackout_dates=blackouts,
            workload_warnings=["Semester setup pending. Enter semester start and end dates to activate dynamic planning."],
        )

    # Calculate semester timeline stats
    try:
        s_date = datetime.strptime(config.start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(config.end_date, "%Y-%m-%d").date()
        today_date = today_local_date(x_timezone)

        days_total = max(1, (e_date - s_date).days + 1)
        days_elapsed = max(0, min(days_total, (today_date - s_date).days))
        days_remaining = max(0, (e_date - today_date).days)
        sem_progress = round((days_elapsed / days_total) * 100.0, 1)
    except Exception:
        days_total, days_elapsed, days_remaining, sem_progress = 120, 30, 90, 25.0

    # Fetch all tasks with subject joins
    t_stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where(PlannedTask.user_id == current_user.id)
        .order_by(PlannedTask.scheduled_date.asc(), PlannedTask.order_index.asc())
    )
    t_res = await db.execute(t_stmt)
    all_tasks = t_res.scalars().all()

    today_tasks_out = [_task_to_out(t) for t in all_tasks if t.scheduled_date == today_str]

    # Fetch subjects and calculate syllabus completion
    subjects_data = await _fetch_full_subject_data(db, current_user.id)
    total_topics_count = 0
    completed_topics_count = 0
    subject_cards: List[Dict[str, Any]] = []

    for s in subjects_data:
        s_total = 0
        s_comp = 0
        for m in s["modules"]:
            for top in m["topics"]:
                s_total += 1
                if top["is_completed"]:
                    s_comp += 1

        total_topics_count += s_total
        completed_topics_count += s_comp

        # Count pending tasks for this subject
        s_pending = sum(
            1 for t in all_tasks if t.subject_id == s["id"] and not t.is_completed
        )

        prog_pct = round((s_comp / max(1, s_total)) * 100.0, 1) if s_total > 0 else 0.0
        subject_cards.append({
            "id": s["id"],
            "name": s["name"],
            "code": s["code"],
            "color": s["color"],
            "semester": s["semester"],
            "credits": s["credits"],
            "total_topics": s_total,
            "completed_topics": s_comp,
            "progress_percent": prog_pct,
            "pending_tasks_count": s_pending,
        })

    syl_progress = (
        round((completed_topics_count / max(1, total_topics_count)) * 100.0, 1)
        if total_topics_count > 0
        else 0.0
    )

    # Fetch assignments
    assignments_data = await _fetch_assignments_data(db, current_user.id)
    overdue_assignments = []
    upcoming_assignments = []

    for a in assignments_data:
        if a["status"] == "Completed":
            continue
        due_iso = a.get("due_date")
        if due_iso:
            try:
                due_d = datetime.fromisoformat(due_iso).date()
                if due_d < today_date:
                    overdue_assignments.append(a)
                elif (due_d - today_date).days <= 14:
                    upcoming_assignments.append(a)
            except Exception:
                upcoming_assignments.append(a)

    # AI Insights & Warnings
    ai_insights: List[Dict[str, Any]] = []
    workload_warnings: List[str] = []

    # Check for missed tasks in past
    missed_count = sum(
        1 for t in all_tasks if t.scheduled_date < today_str and not t.is_completed
    )
    if missed_count > 0:
        workload_warnings.append(
            f"You have {missed_count} uncompleted topic(s) from past dates. Click 'Rebalance Schedule' to redistribute them into upcoming study days."
        )

    # Pacing check
    if sem_progress > syl_progress + 15.0 and total_topics_count > 0:
        workload_warnings.append(
            f"Pacing Alert: {sem_progress}% of the semester has elapsed, but syllabus completion is {syl_progress}%. Boost daily study consistency to stay ahead of exams."
        )
    elif syl_progress >= sem_progress and total_topics_count > 0:
        ai_insights.append({
            "type": "momentum",
            "title": "Strong Academic Momentum",
            "description": f"Syllabus completion ({syl_progress}%) is outpacing semester timeline ({sem_progress}%). Excellent progress!",
        })

    if overdue_assignments:
        ai_insights.append({
            "type": "deadline",
            "title": f"{len(overdue_assignments)} Overdue Assignment(s)",
            "description": "Prioritize submitting overdue coursework to protect grade weighting.",
        })

    return PlannerOverviewResponse(
        is_configured=True,
        semester=SemesterConfigOut.model_validate(config),
        days_total=days_total,
        days_elapsed=days_elapsed,
        days_remaining=days_remaining,
        semester_progress_percent=sem_progress,
        syllabus_progress_percent=syl_progress,
        total_topics_count=total_topics_count,
        completed_topics_count=completed_topics_count,
        today_tasks=today_tasks_out,
        overdue_assignments=overdue_assignments,
        upcoming_assignments=upcoming_assignments,
        subject_cards=subject_cards,
        blackout_dates=blackouts,
        ai_insights=ai_insights,
        workload_warnings=workload_warnings,
    )


# =========================================================================
# 4. Schedule & Calendar Feed
# =========================================================================
@router.get("/schedule")
async def get_schedule(
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns tasks, assignments, and blackout dates for calendar rendering.
    Supports subject filtering and date range filtering.
    """
    stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where(PlannedTask.user_id == current_user.id)
    )

    if subject_id:
        stmt = stmt.where(PlannedTask.subject_id == subject_id)
    if start_date:
        stmt = stmt.where(PlannedTask.scheduled_date >= start_date)
    if end_date:
        stmt = stmt.where(PlannedTask.scheduled_date <= end_date)

    stmt = stmt.order_by(PlannedTask.scheduled_date.asc(), PlannedTask.order_index.asc())
    res = await db.execute(stmt)
    tasks = res.scalars().all()

    # Blackout dates
    b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id)
    if start_date:
        b_stmt = b_stmt.where(BlackoutDate.date >= start_date)
    if end_date:
        b_stmt = b_stmt.where(BlackoutDate.date <= end_date)
    b_res = await db.execute(b_stmt)
    blackouts = b_res.scalars().all()

    # Assignments
    a_stmt = (
        select(Assignment)
        .join(Subject, Assignment.subject_id == Subject.id)
        .options(selectinload(Assignment.subject))
        .where(Subject.user_id == current_user.id)
    )
    if subject_id:
        a_stmt = a_stmt.where(Assignment.subject_id == subject_id)
    a_res = await db.execute(a_stmt)
    assignments = a_res.scalars().all()

    assignments_out = [
        {
            "id": a.id,
            "title": a.title,
            "subject_id": a.subject_id,
            "subject_name": a.subject.name if a.subject else "Subject",
            "subject_color": a.subject.color if a.subject else "#8C6D58",
            "due_date": a.due_date.strftime("%Y-%m-%d") if a.due_date else None,
            "priority": a.priority,
            "status": a.status,
            "type": "assignment",
        }
        for a in assignments
    ]

    return {
        "tasks": [_task_to_out(t) for t in tasks],
        "blackout_dates": [BlackoutDateOut.model_validate(b) for b in blackouts],
        "assignments": assignments_out,
    }


# =========================================================================
# 5. Today's Consolidated Academic Checklist
# =========================================================================
@router.get("/today", response_model=List[PlannedTaskOut])
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """
    Returns all subjects' planned study tasks for today in one consolidated checklist.
    Used on both Dashboard and AI Academic Planner.
    """
    today_str = today_local_str(x_timezone)

    stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where(
            (PlannedTask.user_id == current_user.id)
            & (PlannedTask.scheduled_date == today_str)
        )
        .order_by(PlannedTask.order_index.asc(), PlannedTask.id.asc())
    )
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return [_task_to_out(t) for t in tasks]


# =========================================================================
# 6. Task Management: Toggle, Reschedule, Create, Delete
# =========================================================================
@router.patch("/tasks/{task_id}/toggle", response_model=PlannedTaskOut)
async def toggle_task_completion(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggles completion of a planned task.
    Synchronizes completion with TopicProgress and Syllabus checklist automatically.
    """
    stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where((PlannedTask.id == task_id) & (PlannedTask.user_id == current_user.id))
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_completed = not task.is_completed
    task.is_completed = new_completed
    task.completed_at = now_utc() if new_completed else None

    # If linked to a topic, sync with TopicProgress
    if task.topic_id:
        p_stmt = select(TopicProgress).where(
            (TopicProgress.topic_id == task.topic_id)
            & (TopicProgress.user_id == current_user.id)
        )
        p_res = await db.execute(p_stmt)
        prog = p_res.scalar_one_or_none()

        if not prog:
            prog = TopicProgress(
                topic_id=task.topic_id,
                user_id=current_user.id,
                status="Completed" if new_completed else "Not Started",
                is_completed=new_completed,
                last_studied_at=now_utc() if new_completed else None,
            )
            db.add(prog)
        else:
            prog.status = "Completed" if new_completed else "In Progress"
            prog.is_completed = new_completed
            if new_completed:
                prog.last_studied_at = now_utc()

    # If linked to an assignment, sync with Assignment model
    if task.assignment_id:
        a_stmt = select(Assignment).where(Assignment.id == task.assignment_id)
        a_res = await db.execute(a_stmt)
        assignment_item = a_res.scalar_one_or_none()
        if assignment_item:
            assignment_item.status = "Completed" if new_completed else "In Progress"
            assignment_item.progress_percent = 100 if new_completed else 50

    await db.commit()
    await db.refresh(task)
    return _task_to_out(task)


@router.patch("/tasks/{task_id}/reschedule", response_model=PlannedTaskOut)
async def reschedule_task(
    task_id: int,
    payload: PlannedTaskReschedule,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Moves a task to a different date.
    Marks is_manual_override = True to protect student's explicit scheduling choices.
    """
    # Validate date
    try:
        datetime.strptime(payload.scheduled_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where((PlannedTask.id == task_id) & (PlannedTask.user_id == current_user.id))
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.scheduled_date = payload.scheduled_date
    task.is_manual_override = True

    await db.commit()
    await db.refresh(task)
    return _task_to_out(task)


@router.post("/tasks", response_model=PlannedTaskOut)
async def create_custom_task(
    payload: PlannedTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a custom personal task, extra revision session, or practice block to the calendar."""
    try:
        datetime.strptime(payload.scheduled_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    new_task = PlannedTask(
        user_id=current_user.id,
        subject_id=payload.subject_id,
        topic_id=payload.topic_id,
        assignment_id=payload.assignment_id,
        title=payload.title,
        module_name=payload.module_name or "Personal Study",
        task_type=payload.task_type or "custom",
        scheduled_date=payload.scheduled_date,
        priority=payload.priority or "Medium",
        estimated_minutes=payload.estimated_minutes or 45,
        is_completed=False,
        is_manual_override=True,
        notes=payload.notes,
        order_index=99,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # Load subject relation
    stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where(PlannedTask.id == new_task.id)
    )
    res = await db.execute(stmt)
    loaded_task = res.scalar_one()

    return _task_to_out(loaded_task)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Removes a task from the calendar."""
    stmt = select(PlannedTask).where((PlannedTask.id == task_id) & (PlannedTask.user_id == current_user.id))
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"message": "Task removed from schedule"}


# =========================================================================
# 7. Blackout Dates (Holidays, Exams, Personal Leave)
# =========================================================================
@router.post("/blackout-dates", response_model=BlackoutDateOut)
async def add_blackout_date(
    payload: BlackoutDateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Adds a holiday, exam date, or personal unavailable day."""
    try:
        datetime.strptime(payload.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    # Check if already exists
    stmt = select(BlackoutDate).where(
        (BlackoutDate.user_id == current_user.id) & (BlackoutDate.date == payload.date)
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.reason = payload.reason
        existing.blackout_type = payload.blackout_type or "holiday"
        await db.commit()
        await db.refresh(existing)
        return BlackoutDateOut.model_validate(existing)

    new_b = BlackoutDate(
        user_id=current_user.id,
        date=payload.date,
        reason=payload.reason,
        blackout_type=payload.blackout_type or "holiday",
    )
    db.add(new_b)
    await db.commit()
    await db.refresh(new_b)
    return BlackoutDateOut.model_validate(new_b)


@router.delete("/blackout-dates/{date_id}")
async def delete_blackout_date(
    date_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes an unavailable/holiday date."""
    stmt = select(BlackoutDate).where((BlackoutDate.id == date_id) & (BlackoutDate.user_id == current_user.id))
    res = await db.execute(stmt)
    b = res.scalar_one_or_none()

    if not b:
        raise HTTPException(status_code=404, detail="Date record not found")

    await db.delete(b)
    await db.commit()
    return {"message": "Blackout date removed"}


# =========================================================================
# 8. Rebalancing: Preview & Apply
# =========================================================================
@router.post("/rebalance/preview", response_model=RebalancePreviewResponse)
async def preview_rebalance_schedule(
    preserve_manual: bool = Query(True, description="Preserve manual schedule overrides"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """
    Calculates a proposed rebalance for missed past tasks without saving to database.
    Allows students to preview proposed adjustments before applying.
    """
    stmt = select(SemesterConfig).where(SemesterConfig.user_id == current_user.id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    if not config or not config.is_configured:
        raise HTTPException(status_code=400, detail="Semester not configured.")

    today_str = today_local_str(x_timezone)

    b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id)
    b_res = await db.execute(b_stmt)
    blackouts = {b.date for b in b_res.scalars().all()}

    valid_days = AcademicPlannerEngine.get_valid_study_days(
        start_date_str=config.start_date,
        end_date_str=config.end_date,
        study_days=config.study_days,
        blackout_date_set=blackouts,
        from_date_str=today_str,
    )

    t_stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where(PlannedTask.user_id == current_user.id)
    )
    t_res = await db.execute(t_stmt)
    all_tasks = t_res.scalars().all()

    past_missed = [
        {
            "id": t.id,
            "title": t.title,
            "subject_name": t.subject.name if t.subject else "Topic",
            "scheduled_date": t.scheduled_date,
            "is_completed": t.is_completed,
            "is_manual_override": t.is_manual_override,
        }
        for t in all_tasks
        if t.scheduled_date < today_str and not t.is_completed
    ]

    future_tasks = [
        {
            "id": t.id,
            "title": t.title,
            "scheduled_date": t.scheduled_date,
            "is_completed": t.is_completed,
            "is_manual_override": t.is_manual_override,
        }
        for t in all_tasks
        if t.scheduled_date >= today_str
    ]

    rebal = AcademicPlannerEngine.rebalance_plan(
        valid_days=valid_days,
        uncompleted_past_tasks=past_missed,
        future_tasks=future_tasks,
        max_daily_tasks=config.max_daily_tasks,
        preserve_manual=preserve_manual,
    )

    return RebalancePreviewResponse(
        shifted_tasks=rebal["shifted_tasks"],
        newly_scheduled=[],
        warnings=rebal["warnings"],
        total_days_available=rebal["total_days_available"],
        average_daily_workload=rebal["average_daily_workload"],
        summary=rebal["summary"],
    )


@router.post("/rebalance/apply")
async def apply_rebalance_schedule(
    preserve_manual: bool = Query(True, description="Preserve manual schedule overrides"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_timezone: Optional[str] = Header(None, alias="X-Timezone"),
):
    """
    Applies the proposed rebalancing of missed past tasks into future available days.
    """
    stmt = select(SemesterConfig).where(SemesterConfig.user_id == current_user.id)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    if not config or not config.is_configured:
        raise HTTPException(status_code=400, detail="Semester not configured.")

    today_str = today_local_str(x_timezone)

    b_stmt = select(BlackoutDate).where(BlackoutDate.user_id == current_user.id)
    b_res = await db.execute(b_stmt)
    blackouts = {b.date for b in b_res.scalars().all()}

    valid_days = AcademicPlannerEngine.get_valid_study_days(
        start_date_str=config.start_date,
        end_date_str=config.end_date,
        study_days=config.study_days,
        blackout_date_set=blackouts,
        from_date_str=today_str,
    )

    t_stmt = (
        select(PlannedTask)
        .options(selectinload(PlannedTask.subject))
        .where(PlannedTask.user_id == current_user.id)
    )
    t_res = await db.execute(t_stmt)
    all_tasks = t_res.scalars().all()

    past_missed = [
        {
            "id": t.id,
            "title": t.title,
            "subject_name": t.subject.name if t.subject else "Topic",
            "scheduled_date": t.scheduled_date,
            "is_completed": t.is_completed,
            "is_manual_override": t.is_manual_override,
        }
        for t in all_tasks
        if t.scheduled_date < today_str and not t.is_completed
    ]

    future_tasks = [
        {
            "id": t.id,
            "title": t.title,
            "scheduled_date": t.scheduled_date,
            "is_completed": t.is_completed,
            "is_manual_override": t.is_manual_override,
        }
        for t in all_tasks
        if t.scheduled_date >= today_str
    ]

    rebal = AcademicPlannerEngine.rebalance_plan(
        valid_days=valid_days,
        uncompleted_past_tasks=past_missed,
        future_tasks=future_tasks,
        max_daily_tasks=config.max_daily_tasks,
        preserve_manual=preserve_manual,
    )

    task_map = {t.id: t for t in all_tasks}
    updated_count = 0
    for shift in rebal["shifted_tasks"]:
        t_id = shift["task_id"]
        if t_id in task_map:
            task_map[t_id].scheduled_date = shift["new_date"]
            task_map[t_id].is_manual_override = False  # Reset override as it was automatically rebalanced
            updated_count += 1

    await db.commit()

    return {
        "message": f"Successfully rebalanced {updated_count} study tasks.",
        "updated_count": updated_count,
        "summary": rebal["summary"],
    }
