import json
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ai.vision.face_auth import face_auth_engine
from backend.app.api.deps import get_current_user, get_db
from backend.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.app.models.user import AuthAuditLog, FaceTemplate, StudentProfile, User
from backend.app.schemas.auth import (
    CredentialVerificationResponse,
    FaceEnrollRequest,
    FaceLoginRequest,
    FaceValidationRequest,
    FaceValidationResponse,
    FallbackLoginRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    VerifyCredentialsRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def record_audit_log(
    db: AsyncSession,
    username: str,
    auth_method: str,
    status: str,
    details: str = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
):
    """Helper to log authentication attempts for security auditing and rate inspection."""
    ip = request.client.host if request and request.client else "127.0.0.1"
    audit = AuthAuditLog(
        user_id=user_id,
        username=username,
        auth_method=auth_method,
        status=status,
        details=details,
        ip_address=ip,
    )
    db.add(audit)
    await db.commit()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Registers a new student account using:
    Full name, User ID, Email, Password, Institution, Course, Year, Semester, and optional initial Face template.
    """
    # 1. Check for existing User ID
    res_user = await db.execute(select(User).where(User.username == payload.username))
    if res_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User ID '{payload.username}' is already taken. Please choose another User ID.",
        )

    # 2. Check for existing Email
    res_email = await db.execute(select(User).where(User.email == payload.email))
    if res_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{payload.email}' is already registered.",
        )

    # 3. Create User with salted bcrypt password
    new_user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    # 4. Create Student Profile
    profile = StudentProfile(
        user_id=new_user.id,
        institution=payload.institution,
        course=payload.course,
        year=payload.year,
        semester=payload.semester,
    )
    db.add(profile)

    # 5. Process Face Registration if image base64 or embedding vector is provided
    face_enrolled = False
    if payload.face_image_base64:
        success, embedding, msg = face_auth_engine.extract_embedding_from_image(payload.face_image_base64)
        if not success or not embedding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face registration failed: {msg}",
            )
        ft = FaceTemplate(
            user_id=new_user.id,
            embedding_vector=json.dumps(embedding),
            is_enrolled=True,
        )
        db.add(ft)
        face_enrolled = True
    elif payload.face_embedding:
        ft = FaceTemplate(
            user_id=new_user.id,
            embedding_vector=json.dumps(payload.face_embedding),
            is_enrolled=True,
        )
        db.add(ft)
        face_enrolled = True

    await db.commit()

    await record_audit_log(
        db=db,
        username=new_user.username,
        auth_method="registration",
        status="SUCCESS",
        details=f"User registered (Face template enrolled: {face_enrolled})",
        user_id=new_user.id,
        request=request,
    )

    token = create_access_token(subject=new_user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        username=new_user.username,
        full_name=new_user.full_name,
        auth_method="registration",
    )


@router.post("/face/validate", response_model=FaceValidationResponse)
async def validate_face_frame(payload: FaceValidationRequest):
    """
    Validates a camera frame for single face presence, lighting quality,
    and returns immediate feedback during registration or pre-login verification.
    """
    success, embedding, msg = face_auth_engine.extract_embedding_from_image(payload.face_image_base64)
    return FaceValidationResponse(
        valid=success,
        message=msg,
        has_embedding=bool(embedding),
    )


@router.post("/verify-credentials", response_model=CredentialVerificationResponse)
async def verify_credentials(
    payload: VerifyCredentialsRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1 & 2 of the mandatory authentication flow:
    1. User enters User ID
    2. User enters Password
    3. Backend verifies credentials and issues a short-lived challenge for Face Recognition step.
    """
    query = await db.execute(
        select(User)
        .options(selectinload(User.face_template))
        .where(User.username == payload.username.strip().lower())
    )
    user = query.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        await record_audit_log(
            db=db,
            username=payload.username,
            auth_method="password_verify",
            status="FAILED",
            details="Invalid User ID or password",
            user_id=user.id if user else None,
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User ID or password.",
        )

    has_face = bool(user.face_template and user.face_template.is_enrolled)
    challenge_token = create_access_token(subject=f"face_challenge:{user.id}")

    await record_audit_log(
        db=db,
        username=user.username,
        auth_method="password_verify",
        status="SUCCESS",
        details=f"Password verified. Face enrolled: {has_face}",
        user_id=user.id,
        request=request,
    )

    return CredentialVerificationResponse(
        status="verified",
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        has_face_enrolled=has_face,
        requires_face_step=True,
        session_challenge=challenge_token,
    )


@router.post("/face/login", response_model=TokenResponse)
async def face_login(
    payload: FaceLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 3 of the mandatory authentication flow:
    - Camera opens, face is detected, embedding generated, compared with registered template.
    - Match allows login and issues primary session JWT.
    """
    query = await db.execute(
        select(User)
        .options(selectinload(User.face_template))
        .where(User.username == payload.username.strip().lower())
    )
    user = query.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User ID not found")

    if not user.face_template or not user.face_template.is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face template enrolled for this user. Please use password fallback or enroll face first.",
        )

    # 1. Determine incoming feature vector
    incoming_vector = payload.face_embedding
    if not incoming_vector and payload.face_image_base64:
        success, embedding, msg = face_auth_engine.extract_embedding_from_image(payload.face_image_base64)
        if not success or not embedding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face recognition error: {msg}",
            )
        incoming_vector = embedding

    if not incoming_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face image frame or embedding provided for biometric verification.",
        )

    # 2. Compare against stored face template
    try:
        stored_vector = json.loads(user.face_template.embedding_vector)
        is_match, similarity_score = face_auth_engine.verify(incoming_vector, stored_vector, threshold=0.70)
    except Exception as e:
        logger.error("Error comparing face vectors: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing face embedding comparison",
        )

    if not is_match:
        await record_audit_log(
            db=db,
            username=user.username,
            auth_method="face_login",
            status="FAILED",
            details=f"Face mismatch. Similarity: {similarity_score:.3f} < 0.70",
            user_id=user.id,
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Face verification failed. Similarity match score: {similarity_score:.2f} (Threshold: 0.70).",
        )

    # 3. Successful match -> issue primary session token
    await record_audit_log(
        db=db,
        username=user.username,
        auth_method="face_login",
        status="SUCCESS",
        details=f"Face verified with match score: {similarity_score:.3f}",
        user_id=user.id,
        request=request,
    )

    token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        auth_method="user_id_password_face",
    )


@router.post("/fallback-login", response_model=TokenResponse)
async def fallback_login(
    payload: FallbackLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Secure fallback login if face authentication is temporarily unavailable (e.g. low lighting or no webcam).
    Requires full password re-verification.
    """
    query = await db.execute(
        select(User).where(User.username == payload.username.strip().lower())
    )
    user = query.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        await record_audit_log(
            db=db,
            username=payload.username,
            auth_method="fallback_login",
            status="FAILED",
            details="Invalid credentials during fallback login",
            user_id=user.id if user else None,
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User ID or password.",
        )

    await record_audit_log(
        db=db,
        username=user.username,
        auth_method="fallback_login",
        status="SUCCESS",
        details=f"Fallback login executed. Reason: {payload.reason}",
        user_id=user.id,
        request=request,
    )

    token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        auth_method="password_fallback",
    )


@router.post("/face/enroll")
async def enroll_face(
    payload: FaceEnrollRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enrolls or re-calibrates the student's face embedding template.
    Accepts webcam frame (base64) or extracted 128-d vector.
    """
    embedding_vector = payload.face_embedding

    if not embedding_vector and payload.face_image_base64:
        success, embedding, msg = face_auth_engine.extract_embedding_from_image(payload.face_image_base64)
        if not success or not embedding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face registration failed: {msg}",
            )
        embedding_vector = embedding

    if not embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid camera frame or feature vector.",
        )

    query = await db.execute(select(FaceTemplate).where(FaceTemplate.user_id == current_user.id))
    existing_template = query.scalar_one_or_none()

    embedding_json = json.dumps(embedding_vector)
    if existing_template:
        existing_template.embedding_vector = embedding_json
        existing_template.is_enrolled = True
        existing_template.created_at = datetime.now(timezone.utc)
    else:
        new_template = FaceTemplate(
            user_id=current_user.id,
            embedding_vector=embedding_json,
            is_enrolled=True,
        )
        db.add(new_template)

    await db.commit()

    await record_audit_log(
        db=db,
        username=current_user.username,
        auth_method="face_enroll",
        status="SUCCESS",
        details="Face embedding template enrolled",
        user_id=current_user.id,
        request=request,
    )

    return {
        "status": "enrolled",
        "message": "Face biometric template successfully registered.",
        "user_id": current_user.id,
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs student logout event and invalidates client session state."""
    await record_audit_log(
        db=db,
        username=current_user.username,
        auth_method="logout",
        status="SUCCESS",
        details="Student logged out",
        user_id=current_user.id,
        request=request,
    )
    return {"status": "logged_out", "message": "Successfully signed out."}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    current_user: User = Depends(get_current_user),
):
    """Refreshes the access token and returns a new 30-day JWT."""
    new_token = create_access_token(subject=current_user.id)
    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        auth_method="token_refresh",
    )


# Direct login compatibility route
@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Direct login route (User ID + password)."""
    query = await db.execute(select(User).where(User.username == payload.username.strip().lower()))
    user = query.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid User ID or password")

    token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        auth_method="user_id_password",
    )
