from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.academic import Subject
from backend.app.models.syllabus import Module, Syllabus, Topic, TopicProgress
from backend.app.models.user import User
from backend.app.schemas.syllabus import (
    ModuleRoadmapOut,
    SyllabusExtractPreviewOut,
    SyllabusPreviewModule,
    SyllabusPreviewTopic,
    SyllabusRoadmapOut,
    SyllabusSummaryItem,
    SyllabusUploadTextRequest,
    TopicOut,
    TopicProgressUpdate,
)
from ai.academic.syllabus_parser import SyllabusDocumentExtractor, SyllabusParser

router = APIRouter()


async def _get_existing_topic_progress_map(db: AsyncSession, subject_id: int, user_id: int) -> Dict[str, Any]:
    """Retrieve existing progress by normalized topic title so syllabus replacement preserves progress."""
    stmt = (
        select(Syllabus)
        .options(
            selectinload(Syllabus.modules).selectinload(Module.topics).selectinload(Topic.progress)
        )
        .where((Syllabus.subject_id == subject_id) & (Syllabus.user_id == user_id))
    )
    res = await db.execute(stmt)
    old_syllabi = res.scalars().all()
    prog_map = {}
    for old_syl in old_syllabi:
        for m in old_syl.modules:
            for t in m.topics:
                norm_title = t.title.strip().lower()
                user_p = next((p for p in t.progress if p.user_id == user_id), None)
                if user_p and user_p.status != "Not Started":
                    prog_map[norm_title] = {
                        "status": user_p.status,
                        "is_completed": user_p.is_completed,
                        "notes": user_p.notes,
                        "confidence_level": user_p.confidence_level,
                        "last_studied_at": user_p.last_studied_at,
                    }
    return prog_map


def _build_syllabus_roadmap_out(syl: Syllabus, current_user_id: int) -> SyllabusRoadmapOut:
    modules_out: List[ModuleRoadmapOut] = []
    total_topics = 0
    completed_topics = 0
    in_progress_topics = 0
    needs_revision_topics = 0
    not_started_topics = 0

    sorted_modules = sorted(syl.modules, key=lambda m: m.order_index)

    for mod in sorted_modules:
        topics_out: List[TopicOut] = []
        mod_completed = 0
        mod_topics = sorted(mod.topics, key=lambda t: t.order_index)

        for top in mod_topics:
            total_topics += 1
            user_prog = next((p for p in top.progress if p.user_id == current_user_id), None)
            cur_status = user_prog.status if user_prog else "Not Started"
            is_comp = user_prog.is_completed if user_prog else False

            if cur_status == "Completed" or is_comp:
                completed_topics += 1
                mod_completed += 1
            elif cur_status == "In Progress":
                in_progress_topics += 1
            elif cur_status == "Needs Revision":
                needs_revision_topics += 1
            else:
                not_started_topics += 1

            topics_out.append(
                TopicOut(
                    id=top.id,
                    module_id=top.module_id,
                    title=top.title,
                    subtopics=top.subtopics or [],
                    is_core=top.is_core or False,
                    difficulty_level=top.difficulty_level or "Medium",
                    recommended_study_method=top.recommended_study_method or "Active Recall",
                    conceptual_dependencies=top.conceptual_dependencies or [],
                    status=cur_status,
                    is_completed=is_comp,
                    notes=user_prog.notes if user_prog else None,
                    order_index=top.order_index,
                )
            )

        mod_total = len(mod_topics)
        mod_prog = round((mod_completed / mod_total * 100.0), 1) if mod_total > 0 else 0.0

        # Construct module conceptual chain
        chain = [t.title for t in mod_topics]

        modules_out.append(
            ModuleRoadmapOut(
                id=mod.id,
                syllabus_id=mod.syllabus_id,
                name=mod.name,
                module_number=mod.module_number or 1,
                description=mod.description,
                order_index=mod.order_index,
                topics=topics_out,
                completed_count=mod_completed,
                total_count=mod_total,
                progress_percent=mod_prog,
                conceptual_chain=chain,
            )
        )

    overall_pct = round((completed_topics / total_topics * 100.0), 1) if total_topics > 0 else 0.0

    return SyllabusRoadmapOut(
        id=syl.id,
        user_id=syl.user_id,
        subject_id=syl.subject_id,
        subject_name=syl.subject.name if syl.subject else None,
        subject_color=syl.subject.color if syl.subject else "#5A6E52",
        title=syl.title,
        file_name=syl.file_name,
        created_at=syl.created_at,
        modules=modules_out,
        total_topics=total_topics,
        completed_topics=completed_topics,
        in_progress_topics=in_progress_topics,
        needs_revision_topics=needs_revision_topics,
        not_started_topics=not_started_topics,
        overall_progress_percent=overall_pct,
    )


# ==========================================
# SYLLABUS ROADMAP ENDPOINTS
# ==========================================

@router.get("/roadmaps", response_model=List[SyllabusRoadmapOut])
async def get_all_roadmaps(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns complete hierarchical checklist roadmaps (Modules -> Topics -> Subtopics)
    with conceptual dependencies and 4-state item progress tracking.
    """
    stmt = (
        select(Syllabus)
        .options(
            selectinload(Syllabus.modules).selectinload(Module.topics).selectinload(Topic.progress),
            selectinload(Syllabus.subject),
        )
        .where(Syllabus.user_id == current_user.id)
        .order_by(Syllabus.created_at.desc())
    )
    if subject_id:
        stmt = stmt.where(Syllabus.subject_id == subject_id)

    result = await db.execute(stmt)
    syllabi = result.scalars().all()

    return [_build_syllabus_roadmap_out(s, current_user.id) for s in syllabi]


@router.get("/{syllabus_id}", response_model=SyllabusRoadmapOut)
async def get_single_roadmap(
    syllabus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed checklist roadmap for a specific syllabus."""
    stmt = (
        select(Syllabus)
        .options(
            selectinload(Syllabus.modules).selectinload(Module.topics).selectinload(Topic.progress),
            selectinload(Syllabus.subject),
        )
        .where((Syllabus.id == syllabus_id) & (Syllabus.user_id == current_user.id))
    )
    result = await db.execute(stmt)
    syl = result.scalar_one_or_none()
    if not syl:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    return _build_syllabus_roadmap_out(syl, current_user.id)


@router.post("/extract-preview", response_model=SyllabusExtractPreviewOut)
async def extract_syllabus_preview(
    file: Optional[UploadFile] = File(None),
    content_text: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    Extracts text from an uploaded document (PDF, DOCX, TXT, image) or raw text
    and parses it into structured modules and topics for student review before saving.
    """
    extracted_text = ""
    filename = "Text Input"
    if file is not None and file.filename:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        filename = file.filename
        try:
            extracted_text = SyllabusDocumentExtractor.extract_text(
                file_bytes, filename, file.content_type or ""
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif content_text and content_text.strip():
        extracted_text = content_text.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide a syllabus document (PDF, DOCX, TXT, image) or paste syllabus text."
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract readable text from the syllabus."
        )

    parsed_modules = SyllabusParser.parse_syllabus(extracted_text)
    total_topics = sum(len(m.topics) for m in parsed_modules)
    if total_topics == 0:
        raise HTTPException(
            status_code=400,
            detail="No course topics could be identified in the syllabus document. Please ensure it contains topic listings or paste text directly."
        )

    preview_modules: List[SyllabusPreviewModule] = []
    total_subtopics = 0
    for m in parsed_modules:
        m_topics: List[SyllabusPreviewTopic] = []
        for t in m.topics:
            total_subtopics += len(t.subtopics)
            m_topics.append(
                SyllabusPreviewTopic(
                    title=t.title,
                    subtopics=t.subtopics,
                    is_core=t.is_core,
                    difficulty_level=t.difficulty_level,
                    recommended_study_method=t.recommended_study_method,
                    conceptual_dependencies=t.conceptual_dependencies,
                )
            )
        preview_modules.append(
            SyllabusPreviewModule(
                module_number=m.module_number,
                name=m.name,
                description=m.description or "",
                topics=m_topics,
            )
        )

    preview_snippet = extracted_text[:400] + ("..." if len(extracted_text) > 400 else "")

    return SyllabusExtractPreviewOut(
        raw_text_preview=preview_snippet,
        modules_count=len(preview_modules),
        topics_count=total_topics,
        subtopics_count=total_subtopics,
        modules=preview_modules,
    )


@router.post("/upload/text", response_model=SyllabusRoadmapOut, status_code=status.HTTP_201_CREATED)
@router.post("/upload", response_model=SyllabusRoadmapOut, status_code=status.HTTP_201_CREATED)
async def upload_syllabus_text(
    payload: SyllabusUploadTextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and parse raw syllabus text into structured modules, topics, and subtopics."""
    # Verify subject ownership
    res = await db.execute(
        select(Subject).where((Subject.id == payload.subject_id) & (Subject.user_id == current_user.id))
    )
    subject = res.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Map existing progress to preserve upon replacement
    existing_progress_map = await _get_existing_topic_progress_map(db, payload.subject_id, current_user.id)

    # Delete previous syllabi for this subject to cleanly replace
    old_syllabi_res = await db.execute(
        select(Syllabus).where((Syllabus.subject_id == payload.subject_id) & (Syllabus.user_id == current_user.id))
    )
    for old_syl in old_syllabi_res.scalars().all():
        await db.delete(old_syl)
    await db.flush()

    # Create Syllabus
    syllabus = Syllabus(
        user_id=current_user.id,
        subject_id=payload.subject_id,
        title=payload.title.strip(),
        raw_content=payload.content_text,
        file_name="Text Input",
    )
    db.add(syllabus)
    await db.flush()

    # Parse hierarchy & conceptual dependencies using AI Syllabus Parser
    parsed_modules = SyllabusParser.parse_syllabus(payload.content_text)
    if not parsed_modules or sum(len(m.topics) for m in parsed_modules) == 0:
        raise HTTPException(
            status_code=400,
            detail="Could not detect any topics in the text. Please provide valid syllabus content."
        )

    for mod_idx, m_item in enumerate(parsed_modules, 1):
        db_mod = Module(
            syllabus_id=syllabus.id,
            name=m_item.name,
            module_number=m_item.module_number,
            description=m_item.description,
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

            # Restore existing progress if matching topic title
            saved_prog = existing_progress_map.get(t_item.title.strip().lower())
            if saved_prog:
                db_prog = TopicProgress(
                    topic_id=db_top.id,
                    user_id=current_user.id,
                    status=saved_prog["status"],
                    is_completed=saved_prog["is_completed"],
                    notes=saved_prog.get("notes"),
                    confidence_level=saved_prog.get("confidence_level", 3),
                    last_studied_at=saved_prog.get("last_studied_at"),
                )
            else:
                db_prog = TopicProgress(
                    topic_id=db_top.id,
                    user_id=current_user.id,
                    status="Not Started",
                    is_completed=False,
                )
            db.add(db_prog)

    await db.commit()

    # Re-fetch populated syllabus
    stmt = (
        select(Syllabus)
        .options(
            selectinload(Syllabus.modules).selectinload(Module.topics).selectinload(Topic.progress),
            selectinload(Syllabus.subject),
        )
        .where(Syllabus.id == syllabus.id)
    )
    res_full = await db.execute(stmt)
    full_syl = res_full.scalar_one()

    return _build_syllabus_roadmap_out(full_syl, current_user.id)


@router.post("/upload/file", response_model=SyllabusRoadmapOut, status_code=status.HTTP_201_CREATED)
async def upload_syllabus_file(
    subject_id: int = Form(...),
    title: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and parse syllabus document (PDF, DOCX, TXT, image) into a hierarchical roadmap.
    Validates file format, extracts readable content, and builds dependencies.
    Preserves progress on matching topics if replacing an existing syllabus.
    """
    res = await db.execute(
        select(Subject).where((Subject.id == subject_id) & (Subject.user_id == current_user.id))
    )
    subject = res.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    filename = file.filename or "uploaded_syllabus.txt"
    content_type = file.content_type or ""

    try:
        extracted_text = SyllabusDocumentExtractor.extract_text(file_bytes, filename, content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Parse structure & dependencies
    parsed_modules = SyllabusParser.parse_syllabus(extracted_text)
    if not parsed_modules or sum(len(m.topics) for m in parsed_modules) == 0:
        raise HTTPException(
            status_code=400,
            detail="Could not detect any topics in the uploaded document. Please check the file formatting or paste text directly."
        )

    # Preserve progress for matching topics
    existing_progress_map = await _get_existing_topic_progress_map(db, subject_id, current_user.id)

    # Delete previous syllabi for this subject to cleanly replace
    old_syllabi_res = await db.execute(
        select(Syllabus).where((Syllabus.subject_id == subject_id) & (Syllabus.user_id == current_user.id))
    )
    for old_syl in old_syllabi_res.scalars().all():
        await db.delete(old_syl)
    await db.flush()

    doc_title = title.strip() if title else f"{subject.name} Syllabus ({filename})"

    syllabus = Syllabus(
        user_id=current_user.id,
        subject_id=subject_id,
        title=doc_title,
        raw_content=extracted_text,
        file_name=filename,
    )
    db.add(syllabus)
    await db.flush()

    for mod_idx, m_item in enumerate(parsed_modules, 1):
        db_mod = Module(
            syllabus_id=syllabus.id,
            name=m_item.name,
            module_number=m_item.module_number,
            description=m_item.description,
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

            saved_prog = existing_progress_map.get(t_item.title.strip().lower())
            if saved_prog:
                db_prog = TopicProgress(
                    topic_id=db_top.id,
                    user_id=current_user.id,
                    status=saved_prog["status"],
                    is_completed=saved_prog["is_completed"],
                    notes=saved_prog.get("notes"),
                    confidence_level=saved_prog.get("confidence_level", 3),
                    last_studied_at=saved_prog.get("last_studied_at"),
                )
            else:
                db_prog = TopicProgress(
                    topic_id=db_top.id,
                    user_id=current_user.id,
                    status="Not Started",
                    is_completed=False,
                )
            db.add(db_prog)

    await db.commit()

    stmt = (
        select(Syllabus)
        .options(
            selectinload(Syllabus.modules).selectinload(Module.topics).selectinload(Topic.progress),
            selectinload(Syllabus.subject),
        )
        .where(Syllabus.id == syllabus.id)
    )
    res_full = await db.execute(stmt)
    full_syl = res_full.scalar_one()

    return _build_syllabus_roadmap_out(full_syl, current_user.id)


@router.patch("/topics/{topic_id}/status", response_model=TopicOut)
async def update_topic_status(
    topic_id: int,
    payload: TopicProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually update a topic's status in the checklist roadmap.
    Supported statuses: Not Started, In Progress, Completed, Needs Revision.
    """
    valid_statuses = ["Not Started", "In Progress", "Completed", "Needs Revision"]
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(valid_statuses)}",
        )

    # Verify topic exists and belongs to user's syllabus
    stmt = (
        select(Topic)
        .join(Module)
        .join(Syllabus)
        .where((Topic.id == topic_id) & (Syllabus.user_id == current_user.id))
    )
    res = await db.execute(stmt)
    topic = res.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Find or create progress record
    res_prog = await db.execute(
        select(TopicProgress).where(
            (TopicProgress.topic_id == topic_id) & (TopicProgress.user_id == current_user.id)
        )
    )
    prog = res_prog.scalar_one_or_none()
    is_comp = payload.status == "Completed"

    if not prog:
        prog = TopicProgress(
            topic_id=topic_id,
            user_id=current_user.id,
            status=payload.status,
            is_completed=is_comp,
            notes=payload.notes,
            last_studied_at=datetime.now(timezone.utc) if is_comp else None,
        )
        db.add(prog)
    else:
        prog.status = payload.status
        prog.is_completed = is_comp
        if payload.notes is not None:
            prog.notes = payload.notes.strip()
        if payload.confidence_level is not None:
            prog.confidence_level = payload.confidence_level
        if is_comp:
            prog.last_studied_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(prog)

    return TopicOut(
        id=topic.id,
        module_id=topic.module_id,
        title=topic.title,
        subtopics=topic.subtopics or [],
        is_core=topic.is_core or False,
        difficulty_level=topic.difficulty_level or "Medium",
        recommended_study_method=topic.recommended_study_method or "Active Recall",
        conceptual_dependencies=topic.conceptual_dependencies or [],
        status=prog.status,
        is_completed=prog.is_completed,
        notes=prog.notes,
        order_index=topic.order_index,
    )


@router.delete("/{syllabus_id}", status_code=status.HTTP_200_OK)
async def delete_syllabus(
    syllabus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a syllabus and cascade delete all its modules, topics, and progress records."""
    stmt = select(Syllabus).where((Syllabus.id == syllabus_id) & (Syllabus.user_id == current_user.id))
    res = await db.execute(stmt)
    syl = res.scalar_one_or_none()
    if not syl:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    await db.delete(syl)
    await db.commit()
    return {"status": "success", "message": f"Syllabus '{syl.title}' deleted successfully"}
