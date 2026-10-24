from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.config import settings
from backend.app.core.security import decode_access_token
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        if settings.DEBUG:
            user_res = await db.execute(select(User).order_by(User.id.asc()))
            first_user = user_res.scalars().first()
            if first_user:
                return first_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        if settings.DEBUG:
            user_res = await db.execute(select(User).order_by(User.id.asc()))
            first_user = user_res.scalars().first()
            if first_user:
                return first_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        if settings.DEBUG:
            user_res = await db.execute(select(User).order_by(User.id.asc()))
            first_user = user_res.scalars().first()
            if first_user:
                return first_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    try:
        clean_sub = str(user_id).replace("face_challenge:", "")
        uid = int(clean_sub)
    except Exception:
        uid = None

    user = None
    if uid is not None:
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()

    if not user and settings.DEBUG:
        result = await db.execute(select(User).order_by(User.id.asc()))
        user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional user dependency for non-critical vision and posture endpoints."""
    try:
        return await get_current_user(credentials, db)
    except Exception:
        if settings.DEBUG:
            user_res = await db.execute(select(User).order_by(User.id.asc()))
            return user_res.scalars().first()
        return None
