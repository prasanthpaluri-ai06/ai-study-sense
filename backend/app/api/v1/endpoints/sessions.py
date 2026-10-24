from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.websocket_manager import ws_manager
from backend.app.models.academic import Subject
from backend.app.models.session import (
    FocusRecord,
    PostureRecord,
    SessionMetric,
    SpacedRepetitionCard,
    StudySession,
)
from backend.app.models.user import User
from backend.app.schemas.session import (
    FocusUpdate,
    PostureUpdate,
    SM2CalculateRequest,
    SM2CalculateResponse,
    SessionMetricOut,
    SpacedRepetitionCardCreate,
    SpacedRepetitionCardOut,
    SpacedRepetitionCardReview,
    StudySessionCreate,
    StudySessionEnd,
    StudySessionOut,
    StudySessionStatusUpdate,
)
from ai.academic.spaced_repetition import SM2Scheduler

router = APIRouter()


# ==========================================
# STUDY SESSION LIFECYCLE
# ==========================================

@router.post("/start", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: StudySessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new active study session for any of the 5 study methods and sync with ESP32."""
    # Verify subject if provided
    subject = None
    if payload.subject_id:
        res = await db.execute(
            select(Subject).where((Subject.id == payload.subject_id) & (Subject.user_id == current_user.id))
        )
        subject = res.scalar_one_or_none()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

    session = StudySession(
        user_id=current_user.id,
        subject_id=payload.subject_id,
        topic_name=payload.topic_name.strip() if payload.topic_name else "General Study",
        study_method=payload.study_method,
        status="active",
        start_time=datetime.now(timezone.utc),
        method_metadata=payload.method_metadata,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(session)
    await db.flush()

    # Create initial session metric record
    metric = SessionMetric(
        session_id=session.id,
        focus_score=100.0,
        posture_score=100.0,
        productivity_score=85.0,
        good_posture_seconds=0,
        buffer_posture_seconds=0,
        bad_posture_seconds=0,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(session)

    # Sync ESP32 hardware & Dashboard via WebSocket
    oled_msg = "FOCUS"
    if payload.study_method == "52/17":
        oled_msg = "DEEP WORK"
    elif payload.study_method == "Active Recall":
        oled_msg = "RECALL"
    elif payload.study_method == "Feynman Technique":
        oled_msg = "TEACH IT"
    elif payload.study_method == "Spaced Repetition":
        oled_msg = "SM-2 REVIEW"

    await ws_manager.update_study_state(
        posture="good",
        focus="focused",
        session="active",
        oled_animation="good_posture",
        led_state="GREEN",
        message=oled_msg,
        session_id=session.id,
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=subject.name if subject else None,
        subject_color=subject.color if subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(metric),
    )


@router.post("/{session_id}/pause", response_model=StudySessionOut)
async def pause_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause an ongoing study session."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "paused"
    await db.commit()
    await db.refresh(session)

    await ws_manager.update_study_state(
        session="paused",
        message="PAUSED",
        led_state="YELLOW",
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


@router.post("/{session_id}/resume", response_model=StudySessionOut)
async def resume_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused study session."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "active"
    await db.commit()
    await db.refresh(session)

    await ws_manager.update_study_state(
        session="active",
        message="RESUMED",
        led_state="GREEN",
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


@router.post("/{session_id}/break", response_model=StudySessionOut)
async def trigger_session_break(
    session_id: int,
    break_duration_mins: Optional[int] = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger restorative break during active study session, updating ESP32 to green break animation."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await ws_manager.update_study_state(
        session="break",
        posture="good",
        focus="calm",
        oled_animation="break_time",
        led_state="GREEN",
        message="BREAK TIME",
        timer_seconds=(break_duration_mins or 5) * 60,
        session_id=session.id,
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


@router.post("/{session_id}/break-end", response_model=StudySessionOut)
async def resume_session_from_break(
    session_id: int,
    work_duration_mins: Optional[int] = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transition from break back to active study focus sprint."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await ws_manager.update_study_state(
        session="active",
        posture="good",
        focus="focused",
        oled_animation="good_posture",
        led_state="GREEN",
        message="FLOW STATE",
        timer_seconds=(work_duration_mins or 25) * 60,
        session_id=session.id,
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


@router.post("/{session_id}/end", response_model=StudySessionOut)
async def end_session(
    session_id: int,
    payload: StudySessionEnd = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete a study session, compute duration, record method outcomes, and generate AI feedback."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(timezone.utc)
    session.end_time = now
    
    if payload and payload.duration_minutes is not None and payload.duration_minutes > 0:
        session.duration_minutes = round(payload.duration_minutes, 2)
    else:
        start = session.start_time.replace(tzinfo=timezone.utc) if session.start_time.tzinfo is None else session.start_time
        duration = (now - start).total_seconds() / 60.0
        session.duration_minutes = round(max(0.1, duration), 2)

    session.status = "completed"

    if payload:
        if payload.method_metadata:
            session.method_metadata = payload.method_metadata
        if payload.notes:
            session.notes = payload.notes.strip()

    if session.metric:
        total_posture_secs = (
            session.metric.good_posture_seconds
            + session.metric.buffer_posture_seconds
            + session.metric.bad_posture_seconds
        )
        if total_posture_secs > 0:
            session.metric.posture_score = round(
                (session.metric.good_posture_seconds / total_posture_secs) * 100, 1
            )
        session.metric.ai_feedback_summary = (
            f"{session.study_method} session completed ({session.duration_minutes:.1f} mins). "
            f"Focus score: {session.metric.focus_score}%, Posture quality: {session.metric.posture_score}%."
        )

    await db.commit()
    await db.refresh(session)

    # Inform ESP32 hardware
    await ws_manager.update_study_state(
        posture="good",
        focus="focused",
        session="completed",
        oled_animation="session_complete",
        led_state="GREEN",
        message="DONE! ^_^",
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


@router.post("/{session_id}/cancel", response_model=StudySessionOut)
async def cancel_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel/discard an in-progress study session."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.end_time = datetime.now(timezone.utc)
    session.status = "cancelled"
    await db.commit()
    await db.refresh(session)

    await ws_manager.update_study_state(
        posture="good",
        focus="focused",
        session="idle",
        oled_animation="idle",
        led_state="OFF",
        message="STUDYSENSE READY",
    )

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


@router.get("/recent", response_model=List[StudySessionOut])
async def list_recent_sessions(
    limit: int = Query(15, ge=1, le=100),
    method: Optional[str] = Query(None, description="Filter by study method"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List session history for the authenticated user with metrics and subject info."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where(StudySession.user_id == current_user.id)
        .order_by(StudySession.start_time.desc())
    )
    if method:
        stmt = stmt.where(StudySession.study_method == method)

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    return [
        StudySessionOut(
            id=s.id,
            user_id=s.user_id,
            subject_id=s.subject_id,
            subject_name=s.subject.name if s.subject else None,
            subject_color=s.subject.color if s.subject else None,
            topic_name=s.topic_name,
            study_method=s.study_method,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_minutes=s.duration_minutes,
            status=s.status,
            method_metadata=s.method_metadata,
            notes=s.notes,
            metric=SessionMetricOut.model_validate(s.metric) if s.metric else None,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=StudySessionOut)
async def get_session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed report of a specific study session."""
    stmt = (
        select(StudySession)
        .options(selectinload(StudySession.subject), selectinload(StudySession.metric))
        .where((StudySession.id == session_id) & (StudySession.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return StudySessionOut(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        subject_name=session.subject.name if session.subject else None,
        subject_color=session.subject.color if session.subject else None,
        topic_name=session.topic_name,
        study_method=session.study_method,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        method_metadata=session.method_metadata,
        notes=session.notes,
        metric=SessionMetricOut.model_validate(session.metric) if session.metric else None,
    )


# ==========================================
# POSTURE & VISION TELEMETRY
# ==========================================

@router.post("/{session_id}/posture-telemetry")
async def record_posture_telemetry(
    session_id: int,
    payload: PostureUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log real-time posture telemetry from laptop vision engine and sync with ESP32."""
    record = PostureRecord(
        session_id=session_id,
        state=payload.state,
        angle_degrees=payload.angle_degrees,
        led_color=payload.led_color or ("GREEN" if payload.state == "good" else "YELLOW" if payload.state == "buffer" else "RED"),
    )
    db.add(record)

    # Update session metrics counters
    res = await db.execute(select(SessionMetric).where(SessionMetric.session_id == session_id))
    metric = res.scalar_one_or_none()
    if metric:
        if payload.state == "good":
            metric.good_posture_seconds += 1
        elif payload.state == "buffer":
            metric.buffer_posture_seconds += 1
        elif payload.state == "bad":
            metric.bad_posture_seconds += 1
            metric.posture_alerts_count += 1

    await db.commit()

    # Synchronize ESP32 traffic light and OLED animation
    await ws_manager.update_study_state(
        posture=payload.state,
        led_state=payload.led_color or ("GREEN" if payload.state == "good" else "YELLOW" if payload.state == "buffer" else "RED"),
    )

    return {"status": "ok", "state": payload.state}


# ==========================================
# SPACED REPETITION (SM-2) ENGINE
# ==========================================

@router.post("/spaced-repetition/calculate", response_model=SM2CalculateResponse)
async def calculate_sm2_schedule(payload: SM2CalculateRequest):
    """Compute next SuperMemo-2 spaced repetition review date and ease factor."""
    result = SM2Scheduler.calculate_next_review(
        quality_rating=payload.quality_rating,
        repetition_number=payload.repetition_number or 0,
        ease_factor=payload.ease_factor or 2.5,
        interval_days=payload.interval_days or 0,
    )
    return result


@router.get("/spaced-repetition/cards", response_model=List[SpacedRepetitionCardOut])
async def list_spaced_repetition_cards(
    subject_id: Optional[int] = Query(None),
    only_due: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List student spaced repetition review cards."""
    stmt = (
        select(SpacedRepetitionCard)
        .options(selectinload(SpacedRepetitionCard.subject))
        .where(SpacedRepetitionCard.user_id == current_user.id)
        .order_by(SpacedRepetitionCard.next_review_date.asc())
    )
    if subject_id:
        stmt = stmt.where(SpacedRepetitionCard.subject_id == subject_id)

    result = await db.execute(stmt)
    cards = result.scalars().all()
    now = datetime.now(timezone.utc)

    output = []
    for c in cards:
        next_dt = c.next_review_date.replace(tzinfo=timezone.utc) if c.next_review_date.tzinfo is None else c.next_review_date
        is_due = next_dt <= now
        if only_due and not is_due:
            continue
        output.append(
            SpacedRepetitionCardOut(
                id=c.id,
                user_id=c.user_id,
                subject_id=c.subject_id,
                subject_name=c.subject.name if c.subject else None,
                front_prompt=c.front_prompt,
                back_answer=c.back_answer,
                ease_factor=c.ease_factor,
                interval_days=c.interval_days,
                repetitions_count=c.repetitions_count,
                last_quality_rating=c.last_quality_rating,
                last_reviewed_at=c.last_reviewed_at,
                next_review_date=c.next_review_date,
                is_due=is_due,
            )
        )
    return output


@router.post("/spaced-repetition/cards", response_model=SpacedRepetitionCardOut, status_code=status.HTTP_201_CREATED)
async def create_spaced_repetition_card(
    payload: SpacedRepetitionCardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new concept/card for SM-2 spaced repetition tracking."""
    # Verify subject
    res = await db.execute(
        select(Subject).where((Subject.id == payload.subject_id) & (Subject.user_id == current_user.id))
    )
    subject = res.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    card = SpacedRepetitionCard(
        user_id=current_user.id,
        subject_id=payload.subject_id,
        front_prompt=payload.front_prompt.strip(),
        back_answer=payload.back_answer.strip(),
        ease_factor=2.5,
        interval_days=0,
        repetitions_count=0,
        next_review_date=datetime.now(timezone.utc),
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)

    return SpacedRepetitionCardOut(
        id=card.id,
        user_id=card.user_id,
        subject_id=card.subject_id,
        subject_name=subject.name,
        front_prompt=card.front_prompt,
        back_answer=card.back_answer,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions_count=card.repetitions_count,
        last_quality_rating=card.last_quality_rating,
        last_reviewed_at=card.last_reviewed_at,
        next_review_date=card.next_review_date,
        is_due=True,
    )


@router.post("/spaced-repetition/cards/{card_id}/review", response_model=SpacedRepetitionCardOut)
async def review_spaced_repetition_card(
    card_id: int,
    payload: SpacedRepetitionCardReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an SM-2 recall rating (0-5) and update the card's interval and ease factor."""
    stmt = (
        select(SpacedRepetitionCard)
        .options(selectinload(SpacedRepetitionCard.subject))
        .where((SpacedRepetitionCard.id == card_id) & (SpacedRepetitionCard.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Spaced repetition card not found")

    now = datetime.now(timezone.utc)
    sm2_res = SM2Scheduler.calculate_next_review(
        quality_rating=payload.quality_rating,
        repetition_number=card.repetitions_count,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        now=now,
    )

    card.repetitions_count = sm2_res["repetition_number"]
    card.ease_factor = sm2_res["ease_factor"]
    card.interval_days = sm2_res["interval_days"]
    card.next_review_date = sm2_res["next_review_date"]
    card.last_quality_rating = payload.quality_rating
    card.last_reviewed_at = now

    await db.commit()
    await db.refresh(card)

    return SpacedRepetitionCardOut(
        id=card.id,
        user_id=card.user_id,
        subject_id=card.subject_id,
        subject_name=card.subject.name if card.subject else None,
        front_prompt=card.front_prompt,
        back_answer=card.back_answer,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions_count=card.repetitions_count,
        last_quality_rating=card.last_quality_rating,
        last_reviewed_at=card.last_reviewed_at,
        next_review_date=card.next_review_date,
        is_due=False,
    )
