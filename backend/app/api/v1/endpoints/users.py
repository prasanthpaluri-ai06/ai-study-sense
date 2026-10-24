from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import StudentProfile, User
from backend.app.schemas.user import StudentProfileBase, StudentProfileOut, UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve currently authenticated student details and academic profile."""
    query = await db.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.face_template))
        .where(User.id == current_user.id)
    )
    user = query.scalar_one()

    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        profile=StudentProfileOut.model_validate(user.profile) if user.profile else None,
        has_face_enrolled=bool(user.face_template and user.face_template.is_enrolled),
    )


@router.put("/me/profile", response_model=StudentProfileOut)
async def update_my_profile(
    payload: StudentProfileBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update student academic profile details (institution, course, year, target hours)."""
    query = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = query.scalar_one_or_none()

    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return StudentProfileOut.model_validate(profile)
