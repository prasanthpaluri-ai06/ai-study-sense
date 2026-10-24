from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.academic import Assignment, Mark, Subject
from backend.app.models.syllabus import Module, Syllabus, Topic, TopicProgress
from backend.app.models.user import User
from backend.app.schemas.academic import (
    AcademicSummaryOut,
    AIPrioritizedAssignmentOut,
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
    MarkCreate,
    MarkOut,
    MarkUpdate,
    SubjectCreate,
    SubjectDetailOut,
    SubjectOut,
    SubjectPerformanceOut,
    SubjectUpdate,
)
from backend.app.schemas.syllabus import SubjectWithSyllabusCreate
from ai.academic.prioritizer import DeadlinePrioritizer
from ai.academic.syllabus_parser import SyllabusDocumentExtractor, SyllabusParser
from backend.app.api.v1.endpoints.syllabus import _build_syllabus_roadmap_out

router = APIRouter()


# Helper function to compute subject statistics
def _compute_subject_stats(subject: Subject) -> dict:
    if not subject.marks:
        return {
            "average_score": None,
            "weighted_score": None,
            "total_weightage": 0.0,
            "trend": "Insufficient Data",
            "status": "No Marks Recorded",
        }

    percentages = []
    weighted_sum = 0.0
    total_weights = 0.0

    # Sort marks by recorded_date ascending for trend analysis
    sorted_marks = sorted(subject.marks, key=lambda m: m.recorded_date or datetime.min.replace(tzinfo=timezone.utc))

    for m in sorted_marks:
        if m.total_marks > 0:
            pct = (m.scored_marks / m.total_marks) * 100.0
            percentages.append(pct)
            if m.weightage_percent and m.weightage_percent > 0:
                weighted_sum += pct * (m.weightage_percent / 100.0)
                total_weights += m.weightage_percent

    simple_avg = round(sum(percentages) / len(percentages), 2) if percentages else None
    
    if total_weights > 0:
        # Scale weighted sum to effective 100%
        weighted_avg = round((weighted_sum / (total_weights / 100.0)), 2)
    else:
        weighted_avg = simple_avg

    # Trend calculation
    trend = "Insufficient Data"
    if len(percentages) >= 2:
        midpoint = len(percentages) // 2
        first_half = percentages[:midpoint] if midpoint > 0 else [percentages[0]]
        second_half = percentages[midpoint:]
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        diff = second_avg - first_avg
        if diff >= 3.0:
            trend = "Improving"
        elif diff <= -3.0:
            trend = "Declining"
        else:
            trend = "Stable"

    # Status vs target score
    eff_score = weighted_avg if weighted_avg is not None else simple_avg
    if eff_score is not None:
        target = subject.target_score or 85.0
        if eff_score >= target:
            perf_status = "Exceeding Target"
        elif eff_score >= target - 10.0:
            perf_status = "On Track"
        elif eff_score >= 50.0:
            perf_status = "Needs Review"
        else:
            perf_status = "Critical"
    else:
        perf_status = "No Marks Recorded"

    return {
        "average_score": simple_avg,
        "weighted_score": weighted_avg,
        "total_weightage": round(total_weights, 1),
        "trend": trend,
        "status": perf_status,
    }


# ==========================================
def _compute_syllabus_stats(subject: Subject, user_id: int) -> dict:
    if not subject.syllabi:
        return {
            "has_syllabus": False,
            "syllabus_id": None,
            "progress_percent": None,
            "total_topics": 0,
            "completed_topics": 0,
            "latest_syllabus": None,
        }

    sorted_syllabi = sorted(subject.syllabi, key=lambda s: s.created_at, reverse=True)
    latest = sorted_syllabi[0]
    total_topics = 0
    completed_topics = 0

    for m in latest.modules:
        for t in m.topics:
            total_topics += 1
            user_p = next((p for p in t.progress if p.user_id == user_id), None)
            if user_p and (user_p.status == "Completed" or user_p.is_completed):
                completed_topics += 1

    progress_pct = round((completed_topics / total_topics * 100.0), 1) if total_topics > 0 else 0.0

    return {
        "has_syllabus": True,
        "syllabus_id": latest.id,
        "progress_percent": progress_pct,
        "total_topics": total_topics,
        "completed_topics": completed_topics,
        "latest_syllabus": latest,
    }


# ==========================================
# SUBJECTS CRUD
# ==========================================

@router.get("/subjects", response_model=List[SubjectOut])
async def list_subjects(
    semester: Optional[str] = Query(None, description="Filter by semester name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all subjects registered by the student with calculated scores and syllabus tracking."""
    stmt = (
        select(Subject)
        .options(
            selectinload(Subject.marks),
            selectinload(Subject.assignments),
            selectinload(Subject.syllabi)
            .selectinload(Syllabus.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.progress),
        )
        .where(Subject.user_id == current_user.id)
    )
    if semester:
        stmt = stmt.where(Subject.semester == semester)

    result = await db.execute(stmt)
    subjects = result.scalars().all()

    output = []
    for s in subjects:
        stats = _compute_subject_stats(s)
        syl_stats = _compute_syllabus_stats(s, current_user.id)
        output.append(
            SubjectOut(
                id=s.id,
                user_id=s.user_id,
                name=s.name,
                code=s.code,
                semester=s.semester or "Semester 1",
                credits=s.credits or 3.0,
                color=s.color or "#5A6E52",
                target_score=s.target_score or 85.0,
                description=s.description,
                created_at=s.created_at,
                average_score=stats["average_score"],
                weighted_score=stats["weighted_score"],
                total_weightage_recorded=stats["total_weightage"],
                marks_count=len(s.marks),
                assignments_count=len(s.assignments),
                has_syllabus=syl_stats["has_syllabus"],
                syllabus_id=syl_stats["syllabus_id"],
                syllabus_progress_percent=syl_stats["progress_percent"],
                syllabus_total_topics=syl_stats["total_topics"],
                syllabus_completed_topics=syl_stats["completed_topics"],
            )
        )
    return output


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new academic subject with semester association and credit weight."""
    subject = Subject(
        user_id=current_user.id,
        name=payload.name.strip(),
        code=payload.code.strip() if payload.code else None,
        semester=payload.semester.strip() if payload.semester else "Semester 1",
        credits=payload.credits or 3.0,
        color=payload.color or "#5A6E52",
        target_score=payload.target_score or 85.0,
        description=payload.description.strip() if payload.description else None,
    )
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return SubjectOut(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        code=subject.code,
        semester=subject.semester,
        credits=subject.credits,
        color=subject.color,
        target_score=subject.target_score,
        description=subject.description,
        created_at=subject.created_at,
        average_score=None,
        weighted_score=None,
        total_weightage_recorded=0.0,
        marks_count=0,
        assignments_count=0,
        has_syllabus=False,
        syllabus_id=None,
        syllabus_progress_percent=None,
        syllabus_total_topics=0,
        syllabus_completed_topics=0,
    )


@router.post("/subjects/with-syllabus", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject_with_syllabus(
    payload: SubjectWithSyllabusCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Atomically registers a new subject and its extracted/reviewed syllabus topics.
    Validates that syllabus contains valid topics.
    """
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Subject name is required.")

    total_topics = sum(len(m.topics) for m in payload.modules)
    if total_topics == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot register subject without syllabus topics. Please review and provide at least one topic."
        )

    # 1. Create Subject
    subject = Subject(
        user_id=current_user.id,
        name=payload.name.strip(),
        code=payload.code.strip() if payload.code else None,
        semester=payload.semester.strip() if payload.semester else "Semester 1",
        credits=payload.credits or 3.0,
        color=payload.color or "#5A6E52",
        description=payload.description.strip() if payload.description else None,
    )
    db.add(subject)
    await db.flush()

    # 2. Create Syllabus
    syl_title = payload.syllabus_title.strip() if payload.syllabus_title else f"{subject.name} Syllabus"
    syllabus = Syllabus(
        user_id=current_user.id,
        subject_id=subject.id,
        title=syl_title,
        file_name=payload.file_name or "Curriculum Plan",
        raw_content=f"Registered with {len(payload.modules)} modules and {total_topics} topics.",
    )
    db.add(syllabus)
    await db.flush()

    # 3. Create Modules, Topics, and TopicProgress
    for mod_idx, m_item in enumerate(payload.modules, 1):
        db_mod = Module(
            syllabus_id=syllabus.id,
            name=m_item.name,
            module_number=m_item.module_number or mod_idx,
            description=m_item.description or "",
            order_index=mod_idx,
        )
        db.add(db_mod)
        await db.flush()

        for top_idx, t_item in enumerate(m_item.topics, 1):
            db_top = Topic(
                module_id=db_mod.id,
                title=t_item.title,
                subtopics=t_item.subtopics,
                is_core=t_item.is_core,
                difficulty_level=t_item.difficulty_level,
                recommended_study_method=t_item.recommended_study_method,
                conceptual_dependencies=t_item.conceptual_dependencies,
                order_index=top_idx,
            )
            db.add(db_top)
            await db.flush()

            db_prog = TopicProgress(
                topic_id=db_top.id,
                user_id=current_user.id,
                status="Not Started",
                is_completed=False,
            )
            db.add(db_prog)

    await db.commit()
    await db.refresh(subject)

    return SubjectOut(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        code=subject.code,
        semester=subject.semester,
        credits=subject.credits,
        color=subject.color,
        target_score=subject.target_score,
        description=subject.description,
        created_at=subject.created_at,
        average_score=None,
        weighted_score=None,
        total_weightage_recorded=0.0,
        marks_count=0,
        assignments_count=0,
        has_syllabus=True,
        syllabus_id=syllabus.id,
        syllabus_progress_percent=0.0,
        syllabus_total_topics=total_topics,
        syllabus_completed_topics=0,
    )


@router.post("/subjects/register-with-file", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def register_subject_with_file(
    name: str = Form(...),
    code: Optional[str] = Form(None),
    semester: Optional[str] = Form("Semester 1"),
    credits: Optional[float] = Form(3.0),
    color: Optional[str] = Form("#5A6E52"),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new subject by extracting syllabus topics directly from an uploaded document.
    Aborts without creating an empty subject if extraction fails or yields no topics.
    """
    if not name.strip():
        raise HTTPException(status_code=400, detail="Subject name is required.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded syllabus file is empty.")

    filename = file.filename or "uploaded_syllabus.txt"
    try:
        extracted_text = SyllabusDocumentExtractor.extract_text(file_bytes, filename, file.content_type or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    parsed_modules = SyllabusParser.parse_syllabus(extracted_text)
    total_topics = sum(len(m.topics) for m in parsed_modules)
    if total_topics == 0:
        raise HTTPException(
            status_code=400,
            detail="No course topics could be identified in the syllabus document. Please ensure it contains topic listings or paste text directly."
        )

    # 1. Create Subject
    subject = Subject(
        user_id=current_user.id,
        name=name.strip(),
        code=code.strip() if code else None,
        semester=semester.strip() if semester else "Semester 1",
        credits=credits or 3.0,
        color=color or "#5A6E52",
        description=description.strip() if description else None,
    )
    db.add(subject)
    await db.flush()

    # 2. Create Syllabus
    syllabus = Syllabus(
        user_id=current_user.id,
        subject_id=subject.id,
        title=f"{subject.name} Syllabus ({filename})",
        file_name=filename,
        raw_content=extracted_text,
    )
    db.add(syllabus)
    await db.flush()

    # 3. Create Modules, Topics, and TopicProgress
    for mod_idx, m_item in enumerate(parsed_modules, 1):
        db_mod = Module(
            syllabus_id=syllabus.id,
            name=m_item.name,
            module_number=m_item.module_number or mod_idx,
            description=m_item.description or "",
            order_index=mod_idx,
        )
        db.add(db_mod)
        await db.flush()

        for top_idx, t_item in enumerate(m_item.topics, 1):
            db_top = Topic(
                module_id=db_mod.id,
                title=t_item.title,
                subtopics=t_item.subtopics,
                is_core=t_item.is_core,
                difficulty_level=t_item.difficulty_level,
                recommended_study_method=t_item.recommended_study_method,
                conceptual_dependencies=t_item.conceptual_dependencies,
                order_index=top_idx,
            )
            db.add(db_top)
            await db.flush()

            db_prog = TopicProgress(
                topic_id=db_top.id,
                user_id=current_user.id,
                status="Not Started",
                is_completed=False,
            )
            db.add(db_prog)

    await db.commit()
    await db.refresh(subject)

    return SubjectOut(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        code=subject.code,
        semester=subject.semester,
        credits=subject.credits,
        color=subject.color,
        target_score=subject.target_score,
        description=subject.description,
        created_at=subject.created_at,
        average_score=None,
        weighted_score=None,
        total_weightage_recorded=0.0,
        marks_count=0,
        assignments_count=0,
        has_syllabus=True,
        syllabus_id=syllabus.id,
        syllabus_progress_percent=0.0,
        syllabus_total_topics=total_topics,
        syllabus_completed_topics=0,
    )


@router.get("/subjects/{subject_id}", response_model=SubjectDetailOut)
async def get_subject_detail(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View subject details with all recorded marks, assignments, and weighted mastery."""
    stmt = (
        select(Subject)
        .options(
            selectinload(Subject.marks),
            selectinload(Subject.assignments),
            selectinload(Subject.syllabi)
            .selectinload(Syllabus.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.progress),
        )
        .where((Subject.id == subject_id) & (Subject.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    stats = _compute_subject_stats(subject)
    syl_stats = _compute_syllabus_stats(subject, current_user.id)
    now = datetime.now(timezone.utc)

    # Format marks
    formatted_marks = []
    for m in subject.marks:
        pct = round((m.scored_marks / m.total_marks * 100.0), 2) if m.total_marks > 0 else 0.0
        weighted_contrib = round((pct * (m.weightage_percent / 100.0)), 2) if m.weightage_percent else None
        formatted_marks.append(
            MarkOut(
                id=m.id,
                subject_id=m.subject_id,
                assessment_name=m.assessment_name,
                assessment_type=m.assessment_type or "CAT/internal",
                scored_marks=m.scored_marks,
                total_marks=m.total_marks,
                weightage_percent=m.weightage_percent,
                notes=m.notes,
                recorded_date=m.recorded_date,
                percentage=pct,
                weighted_contribution=weighted_contrib,
                subject_name=subject.name,
                subject_color=subject.color,
            )
        )

    # Format assignments
    formatted_assignments = []
    for a in subject.assignments:
        due = a.due_date.replace(tzinfo=timezone.utc) if a.due_date.tzinfo is None else a.due_date
        hrs_left = (due - now).total_seconds() / 3600.0
        is_over = hrs_left < 0 and a.status != "Completed"
        formatted_assignments.append(
            AssignmentOut(
                id=a.id,
                subject_id=a.subject_id,
                title=a.title,
                description=a.description,
                due_date=a.due_date,
                priority=a.priority,
                status="Overdue" if is_over else a.status,
                progress_percent=a.progress_percent,
                estimated_effort_hours=a.estimated_effort_hours,
                notes=a.notes,
                created_at=a.created_at,
                subject_name=subject.name,
                subject_color=subject.color,
                is_overdue=is_over,
                hours_remaining=round(hrs_left, 1),
            )
        )

    return SubjectDetailOut(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        code=subject.code,
        semester=subject.semester,
        credits=subject.credits,
        color=subject.color,
        target_score=subject.target_score,
        description=subject.description,
        created_at=subject.created_at,
        average_score=stats["average_score"],
        weighted_score=stats["weighted_score"],
        total_weightage_recorded=stats["total_weightage"],
        marks_count=len(subject.marks),
        assignments_count=len(subject.assignments),
        has_syllabus=syl_stats["has_syllabus"],
        syllabus_id=syl_stats["syllabus_id"],
        syllabus_progress_percent=syl_stats["progress_percent"],
        syllabus_total_topics=syl_stats["total_topics"],
        syllabus_completed_topics=syl_stats["completed_topics"],
        marks=formatted_marks,
        assignments=formatted_assignments,
    )


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit an existing academic subject."""
    stmt = (
        select(Subject)
        .options(selectinload(Subject.marks), selectinload(Subject.assignments))
        .where((Subject.id == subject_id) & (Subject.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(subject, field, val.strip() if isinstance(val, str) else val)

    await db.commit()
    await db.refresh(subject)
    stats = _compute_subject_stats(subject)

    return SubjectOut(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        code=subject.code,
        semester=subject.semester,
        credits=subject.credits,
        color=subject.color,
        target_score=subject.target_score,
        description=subject.description,
        created_at=subject.created_at,
        average_score=stats["average_score"],
        weighted_score=stats["weighted_score"],
        total_weightage_recorded=stats["total_weightage"],
        marks_count=len(subject.marks),
        assignments_count=len(subject.assignments),
    )


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_200_OK)
async def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an academic subject and cascade delete associated marks and assignments."""
    stmt = select(Subject).where((Subject.id == subject_id) & (Subject.user_id == current_user.id))
    result = await db.execute(stmt)
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    await db.delete(subject)
    await db.commit()
    return {"status": "success", "message": f"Subject '{subject.name}' and all associated records deleted successfully"}


# ==========================================
# MARKS CRUD & PERFORMANCE ANALYTICS
# ==========================================

@router.get("/marks", response_model=List[MarkOut])
async def list_marks(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List assessment marks for the authenticated user with individual percentages and weighted scores."""
    stmt = (
        select(Mark)
        .join(Subject)
        .options(selectinload(Mark.subject))
        .where(Subject.user_id == current_user.id)
        .order_by(Mark.recorded_date.desc())
    )
    if subject_id:
        stmt = stmt.where(Mark.subject_id == subject_id)
    if assessment_type:
        stmt = stmt.where(Mark.assessment_type == assessment_type)

    result = await db.execute(stmt)
    marks = result.scalars().all()

    output = []
    for m in marks:
        pct = round((m.scored_marks / m.total_marks * 100.0), 2) if m.total_marks > 0 else 0.0
        weighted_contrib = round((pct * (m.weightage_percent / 100.0)), 2) if m.weightage_percent else None
        output.append(
            MarkOut(
                id=m.id,
                subject_id=m.subject_id,
                assessment_name=m.assessment_name,
                assessment_type=m.assessment_type or "CAT/internal",
                scored_marks=m.scored_marks,
                total_marks=m.total_marks,
                weightage_percent=m.weightage_percent,
                notes=m.notes,
                recorded_date=m.recorded_date,
                percentage=pct,
                weighted_contribution=weighted_contrib,
                subject_name=m.subject.name if m.subject else None,
                subject_color=m.subject.color if m.subject else None,
            )
        )
    return output


@router.post("/marks", response_model=MarkOut, status_code=status.HTTP_201_CREATED)
async def create_mark(
    payload: MarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a new assessment score with configurable weighting and assessment type."""
    # Verify subject ownership
    res = await db.execute(select(Subject).where((Subject.id == payload.subject_id) & (Subject.user_id == current_user.id)))
    subject = res.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found or does not belong to user")

    mark = Mark(
        subject_id=payload.subject_id,
        assessment_name=payload.assessment_name.strip(),
        assessment_type=payload.assessment_type.strip() if payload.assessment_type else "CAT/internal",
        scored_marks=payload.scored_marks,
        total_marks=payload.total_marks,
        weightage_percent=payload.weightage_percent,
        notes=payload.notes.strip() if payload.notes else None,
        recorded_date=payload.recorded_date or datetime.now(timezone.utc),
    )
    db.add(mark)
    await db.commit()
    await db.refresh(mark)

    pct = round((mark.scored_marks / mark.total_marks * 100.0), 2) if mark.total_marks > 0 else 0.0
    weighted_contrib = round((pct * (mark.weightage_percent / 100.0)), 2) if mark.weightage_percent else None

    return MarkOut(
        id=mark.id,
        subject_id=mark.subject_id,
        assessment_name=mark.assessment_name,
        assessment_type=mark.assessment_type,
        scored_marks=mark.scored_marks,
        total_marks=mark.total_marks,
        weightage_percent=mark.weightage_percent,
        notes=mark.notes,
        recorded_date=mark.recorded_date,
        percentage=pct,
        weighted_contribution=weighted_contrib,
        subject_name=subject.name,
        subject_color=subject.color,
    )


@router.put("/marks/{mark_id}", response_model=MarkOut)
@router.patch("/marks/{mark_id}", response_model=MarkOut)
async def update_mark(
    mark_id: int,
    payload: MarkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit an existing assessment score."""
    stmt = (
        select(Mark)
        .join(Subject)
        .options(selectinload(Mark.subject))
        .where((Mark.id == mark_id) & (Subject.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    mark = result.scalar_one_or_none()
    if not mark:
        raise HTTPException(status_code=404, detail="Mark entry not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(mark, field, val.strip() if isinstance(val, str) else val)

    await db.commit()
    await db.refresh(mark)

    pct = round((mark.scored_marks / mark.total_marks * 100.0), 2) if mark.total_marks > 0 else 0.0
    weighted_contrib = round((pct * (mark.weightage_percent / 100.0)), 2) if mark.weightage_percent else None

    return MarkOut(
        id=mark.id,
        subject_id=mark.subject_id,
        assessment_name=mark.assessment_name,
        assessment_type=mark.assessment_type,
        scored_marks=mark.scored_marks,
        total_marks=mark.total_marks,
        weightage_percent=mark.weightage_percent,
        notes=mark.notes,
        recorded_date=mark.recorded_date,
        percentage=pct,
        weighted_contribution=weighted_contrib,
        subject_name=mark.subject.name if mark.subject else None,
        subject_color=mark.subject.color if mark.subject else None,
    )


@router.delete("/marks/{mark_id}", status_code=status.HTTP_200_OK)
async def delete_mark(
    mark_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an assessment score record."""
    stmt = select(Mark).join(Subject).where((Mark.id == mark_id) & (Subject.user_id == current_user.id))
    result = await db.execute(stmt)
    mark = result.scalar_one_or_none()
    if not mark:
        raise HTTPException(status_code=404, detail="Mark entry not found")

    await db.delete(mark)
    await db.commit()
    return {"status": "success", "message": "Mark entry deleted successfully"}


@router.get("/marks/performance", response_model=List[SubjectPerformanceOut])
async def get_performance_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Comprehensive academic performance breakdown with weighted mastery, trends, and individual marks."""
    stmt = (
        select(Subject)
        .options(selectinload(Subject.marks))
        .where(Subject.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    subjects = result.scalars().all()

    output = []
    for s in subjects:
        stats = _compute_subject_stats(s)
        formatted_marks = [
            MarkOut(
                id=m.id,
                subject_id=m.subject_id,
                assessment_name=m.assessment_name,
                assessment_type=m.assessment_type or "CAT/internal",
                scored_marks=m.scored_marks,
                total_marks=m.total_marks,
                weightage_percent=m.weightage_percent,
                notes=m.notes,
                recorded_date=m.recorded_date,
                percentage=round((m.scored_marks / m.total_marks * 100.0), 2) if m.total_marks > 0 else 0.0,
                weighted_contribution=round(((m.scored_marks / m.total_marks * 100.0) * (m.weightage_percent / 100.0)), 2) if m.weightage_percent and m.total_marks > 0 else None,
                subject_name=s.name,
                subject_color=s.color,
            )
            for m in s.marks
        ]

        output.append(
            SubjectPerformanceOut(
                subject_id=s.id,
                subject_name=s.name,
                subject_code=s.code,
                semester=s.semester or "Semester 1",
                credits=s.credits or 3.0,
                target_score=s.target_score or 85.0,
                simple_average=stats["average_score"],
                weighted_average=stats["weighted_score"],
                total_weightage_used=stats["total_weightage"],
                performance_status=stats["status"],
                performance_trend=stats["trend"],
                marks_count=len(s.marks),
                marks=formatted_marks,
            )
        )
    return output


# ==========================================
# ASSIGNMENTS CRUD
# ==========================================

@router.get("/assignments", response_model=List[AssignmentOut])
async def list_assignments(
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List student assignments with automatic overdue detection and time remaining."""
    stmt = (
        select(Assignment)
        .join(Subject)
        .options(selectinload(Assignment.subject))
        .where(Subject.user_id == current_user.id)
        .order_by(Assignment.due_date.asc())
    )
    if subject_id:
        stmt = stmt.where(Assignment.subject_id == subject_id)
    if priority:
        stmt = stmt.where(Assignment.priority == priority)

    result = await db.execute(stmt)
    assignments = result.scalars().all()
    now = datetime.now(timezone.utc)

    output = []
    for a in assignments:
        due = a.due_date.replace(tzinfo=timezone.utc) if a.due_date.tzinfo is None else a.due_date
        hrs_left = (due - now).total_seconds() / 3600.0
        is_over = hrs_left < 0 and a.status != "Completed"
        current_status = "Overdue" if is_over else a.status

        if status_filter and status_filter.lower() != "all":
            if status_filter.lower() == "overdue" and not is_over:
                continue
            elif status_filter.lower() == "pending" and a.status == "Completed":
                continue
            elif status_filter.lower() == "completed" and a.status != "Completed":
                continue

        output.append(
            AssignmentOut(
                id=a.id,
                subject_id=a.subject_id,
                title=a.title,
                description=a.description,
                due_date=a.due_date,
                priority=a.priority or "Medium",
                status=current_status,
                progress_percent=a.progress_percent or 0,
                estimated_effort_hours=a.estimated_effort_hours or 2.0,
                notes=a.notes,
                created_at=a.created_at,
                subject_name=a.subject.name if a.subject else None,
                subject_color=a.subject.color if a.subject else None,
                is_overdue=is_over,
                hours_remaining=round(hrs_left, 1),
            )
        )
    return output


@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new academic assignment with priority, due date, and estimated effort."""
    res = await db.execute(select(Subject).where((Subject.id == payload.subject_id) & (Subject.user_id == current_user.id)))
    subject = res.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    assignment = Assignment(
        subject_id=payload.subject_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        due_date=payload.due_date,
        priority=payload.priority or "Medium",
        status=payload.status or "Not Started",
        progress_percent=payload.progress_percent or 0,
        estimated_effort_hours=payload.estimated_effort_hours or 2.0,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    now = datetime.now(timezone.utc)
    due = assignment.due_date.replace(tzinfo=timezone.utc) if assignment.due_date.tzinfo is None else assignment.due_date
    hrs_left = (due - now).total_seconds() / 3600.0
    is_over = hrs_left < 0 and assignment.status != "Completed"

    return AssignmentOut(
        id=assignment.id,
        subject_id=assignment.subject_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        priority=assignment.priority,
        status="Overdue" if is_over else assignment.status,
        progress_percent=assignment.progress_percent,
        estimated_effort_hours=assignment.estimated_effort_hours,
        notes=assignment.notes,
        created_at=assignment.created_at,
        subject_name=subject.name,
        subject_color=subject.color,
        is_overdue=is_over,
        hours_remaining=round(hrs_left, 1),
    )


@router.put("/assignments/{assignment_id}", response_model=AssignmentOut)
@router.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit assignment details, progress percentage, or completion status."""
    stmt = (
        select(Assignment)
        .join(Subject)
        .options(selectinload(Assignment.subject))
        .where((Assignment.id == assignment_id) & (Subject.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            if field == "progress_percent" and val == 100:
                assignment.status = "Completed"
            elif field == "status" and val == "Completed" and "progress_percent" not in update_data:
                assignment.progress_percent = 100
            setattr(assignment, field, val.strip() if isinstance(val, str) else val)

    await db.commit()
    await db.refresh(assignment)

    now = datetime.now(timezone.utc)
    due = assignment.due_date.replace(tzinfo=timezone.utc) if assignment.due_date.tzinfo is None else assignment.due_date
    hrs_left = (due - now).total_seconds() / 3600.0
    is_over = hrs_left < 0 and assignment.status != "Completed"

    return AssignmentOut(
        id=assignment.id,
        subject_id=assignment.subject_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        priority=assignment.priority,
        status="Overdue" if is_over else assignment.status,
        progress_percent=assignment.progress_percent,
        estimated_effort_hours=assignment.estimated_effort_hours,
        notes=assignment.notes,
        created_at=assignment.created_at,
        subject_name=assignment.subject.name if assignment.subject else None,
        subject_color=assignment.subject.color if assignment.subject else None,
        is_overdue=is_over,
        hours_remaining=round(hrs_left, 1),
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_200_OK)
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an assignment task."""
    stmt = select(Assignment).join(Subject).where((Assignment.id == assignment_id) & (Subject.user_id == current_user.id))
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()
    return {"status": "success", "message": f"Assignment '{assignment.title}' deleted successfully"}


# ==========================================
# AI PRIORITIZATION & ACADEMIC DASHBOARD SUMMARY
# ==========================================

@router.get("/assignments/prioritized", response_model=List[AIPrioritizedAssignmentOut])
async def get_prioritized_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-Assisted Deadline Prioritization using a transparent multi-factor scoring model:
      Urgency (35%) + Priority (25%) + Academic Importance (20%) + Effort (10%) + Workload (10%)
    """
    stmt = (
        select(Assignment)
        .join(Subject)
        .options(selectinload(Assignment.subject).selectinload(Subject.marks))
        .where((Subject.user_id == current_user.id) & (Assignment.status != "Completed"))
    )
    result = await db.execute(stmt)
    active_assignments = result.scalars().all()
    now = datetime.now(timezone.utc)

    prioritized_list = []
    for a in active_assignments:
        subject = a.subject
        stats = _compute_subject_stats(subject) if subject else {}
        subject_avg = stats.get("weighted_score") or stats.get("average_score")
        
        prioritized_data = DeadlinePrioritizer.prioritize_assignment(
            assignment=a,
            subject=subject,
            all_active_assignments=active_assignments,
            subject_avg_score=subject_avg,
            now=now,
        )
        prioritized_list.append(prioritized_data)

    # Sort descending by composite priority score
    prioritized_list.sort(key=lambda x: x["priority_score"], reverse=True)
    return prioritized_list


@router.get("/summary", response_model=AcademicSummaryOut)
async def get_academic_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Consolidated academic summary for dashboard: upcoming deadlines, overdue tasks,
    completion rate, overall GPA/average, and top AI-prioritized tasks.
    """
    # Load subjects with marks and assignments
    stmt_subj = (
        select(Subject)
        .options(selectinload(Subject.marks), selectinload(Subject.assignments))
        .where(Subject.user_id == current_user.id)
    )
    res_subj = await db.execute(stmt_subj)
    subjects = res_subj.scalars().all()

    now = datetime.now(timezone.utc)

    all_assignments = []
    subject_performances = []
    all_subject_averages = []
    total_credits = 0.0
    weighted_gpa_sum = 0.0

    for s in subjects:
        stats = _compute_subject_stats(s)
        eff_score = stats["weighted_score"] if stats["weighted_score"] is not None else stats["average_score"]
        if eff_score is not None:
            all_subject_averages.append(eff_score)
            credits = s.credits or 3.0
            weighted_gpa_sum += eff_score * credits
            total_credits += credits

        formatted_marks = [
            MarkOut(
                id=m.id,
                subject_id=m.subject_id,
                assessment_name=m.assessment_name,
                assessment_type=m.assessment_type or "CAT/internal",
                scored_marks=m.scored_marks,
                total_marks=m.total_marks,
                weightage_percent=m.weightage_percent,
                notes=m.notes,
                recorded_date=m.recorded_date,
                percentage=round((m.scored_marks / m.total_marks * 100.0), 2) if m.total_marks > 0 else 0.0,
                weighted_contribution=round(((m.scored_marks / m.total_marks * 100.0) * (m.weightage_percent / 100.0)), 2) if m.weightage_percent and m.total_marks > 0 else None,
                subject_name=s.name,
                subject_color=s.color,
            )
            for m in s.marks
        ]

        subject_performances.append(
            SubjectPerformanceOut(
                subject_id=s.id,
                subject_name=s.name,
                subject_code=s.code,
                semester=s.semester or "Semester 1",
                credits=s.credits or 3.0,
                target_score=s.target_score or 85.0,
                simple_average=stats["average_score"],
                weighted_average=stats["weighted_score"],
                total_weightage_used=stats["total_weightage"],
                performance_status=stats["status"],
                performance_trend=stats["trend"],
                marks_count=len(s.marks),
                marks=formatted_marks,
            )
        )

        for a in s.assignments:
            due = a.due_date.replace(tzinfo=timezone.utc) if a.due_date.tzinfo is None else a.due_date
            hrs_left = (due - now).total_seconds() / 3600.0
            is_over = hrs_left < 0 and a.status != "Completed"
            all_assignments.append(
                AssignmentOut(
                    id=a.id,
                    subject_id=a.subject_id,
                    title=a.title,
                    description=a.description,
                    due_date=a.due_date,
                    priority=a.priority,
                    status="Overdue" if is_over else a.status,
                    progress_percent=a.progress_percent,
                    estimated_effort_hours=a.estimated_effort_hours,
                    notes=a.notes,
                    created_at=a.created_at,
                    subject_name=s.name,
                    subject_color=s.color,
                    is_overdue=is_over,
                    hours_remaining=round(hrs_left, 1),
                )
            )

    # Sort assignments by due date
    all_assignments.sort(key=lambda a: a.due_date)

    pending = [a for a in all_assignments if a.status != "Completed"]
    completed = [a for a in all_assignments if a.status == "Completed"]
    overdue = [a for a in all_assignments if a.is_overdue]
    upcoming = [a for a in pending if not a.is_overdue]

    completion_rate = round((len(completed) / len(all_assignments) * 100.0), 1) if all_assignments else 0.0
    overall_avg = round(sum(all_subject_averages) / len(all_subject_averages), 1) if all_subject_averages else None
    overall_gpa = round(weighted_gpa_sum / total_credits, 1) if total_credits > 0 else overall_avg

    # AI Prioritized top assignments
    active_assignments_raw = [a for s in subjects for a in s.assignments if a.status != "Completed"]
    top_prioritized = []
    for a in active_assignments_raw:
        s = a.subject
        stats = _compute_subject_stats(s) if s else {}
        subj_avg = stats.get("weighted_score") or stats.get("average_score")
        p_data = DeadlinePrioritizer.prioritize_assignment(
            assignment=a,
            subject=s,
            all_active_assignments=active_assignments_raw,
            subject_avg_score=subj_avg,
            now=now,
        )
        top_prioritized.append(p_data)

    top_prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

    return AcademicSummaryOut(
        total_subjects=len(subjects),
        total_assignments=len(all_assignments),
        pending_assignments_count=len(pending),
        overdue_assignments_count=len(overdue),
        completed_assignments_count=len(completed),
        completion_rate_percent=completion_rate,
        overall_academic_average=overall_avg,
        overall_weighted_gpa_score=overall_gpa,
        upcoming_deadlines=upcoming[:5],
        overdue_tasks=overdue,
        subject_performances=subject_performances,
        top_priority_assignments=top_prioritized[:5],
    )
