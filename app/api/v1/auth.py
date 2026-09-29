from datetime import datetime, timezone, timedelta
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User, RefreshToken, PushDevice
from app.models.patient import Patient, PatientMember
from app.models.alert import NotificationSetting
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    PasswordRecoveryRequest,
    PasswordResetRequest,
    UserProfileUpdate,
    UserResponse,
    MembershipDTO,
    PushDeviceRegister
)
from app.schemas.alert import NotificationSettingResponse, NotificationSettingUpdate
from app.api.deps import get_current_user

router = APIRouter(tags=["Autenticación y Usuario"])


async def _build_user_response(user: User, db: AsyncSession) -> UserResponse:
    stmt_members = select(PatientMember, Patient).join(Patient, PatientMember.patient_id == Patient.id).where(
        PatientMember.user_id == user.id,
        Patient.deleted_at.is_(None)
    )
    res_m = await db.execute(stmt_members)
    rows = res_m.all()

    memberships = [
        MembershipDTO(
            patient_id=m.patient_id,
            patient_name=p.full_name,
            role=m.role
        )
        for m, p in rows
    ]

    return UserResponse(
        id=user.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        locale=user.locale or "es",
        created_at=user.created_at,
        memberships=memberships
    )


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == data.email.lower())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise AgeCareHTTPException(
            status_code=status.HTTP_409_CONFLICT,
            code="EMAIL_ALREADY_EXISTS",
            message="El correo electrónico ya está registrado."
        )

    user = User(
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        locale=data.locale or "es"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_resp = await _build_user_response(user, db)

    access_token = create_access_token(subject=user.id)
    raw_refresh_token = create_refresh_token(subject=user.id)

    db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=get_password_hash(raw_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh)
    await db.commit()

    return TokenResponse(
        user_id=user.id,
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=user_resp,
        roles={},
        memberships=user_resp.memberships
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == data.email.lower(), User.deleted_at.is_(None))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise AgeCareHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CREDENTIALS",
            message="Correo o contraseña incorrectos."
        )

    user_resp = await _build_user_response(user, db)
    roles_map = {m.patient_id: m.role for m in user_resp.memberships}

    access_token = create_access_token(subject=user.id, roles=roles_map)
    raw_refresh_token = create_refresh_token(subject=user.id)

    db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=get_password_hash(raw_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh)
    await db.commit()

    return TokenResponse(
        user_id=user.id,
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=user_resp,
        roles=roles_map,
        memberships=user_resp.memberships
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise AgeCareHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Refresh token inválido o expirado."
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise AgeCareHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="El usuario no existe."
        )

    user_resp = await _build_user_response(user, db)
    roles_map = {m.patient_id: m.role for m in user_resp.memberships}

    new_access_token = create_access_token(subject=user.id, roles=roles_map)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        user_id=user.id,
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=user_resp,
        roles=roles_map,
        memberships=user_resp.memberships
    )


@router.post("/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RefreshToken).where(RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None))
    res = await db.execute(stmt)
    tokens = res.scalars().all()
    for t in tokens:
        t.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Sesión cerrada exitosamente."}


@router.post("/auth/password/recovery")
async def request_password_recovery(data: PasswordRecoveryRequest):
    return {"message": "Si el correo existe en nuestro sistema, enviamos instrucciones para restablecer la contraseña."}


@router.post("/auth/password/reset")
async def reset_password(data: PasswordResetRequest):
    return {"message": "Contraseña restablecida exitosamente."}


# Endpoints for getting and updating current user profile (/auth/me and /users/me)
@router.get("/auth/me", response_model=UserResponse)
@router.get("/users/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await _build_user_response(current_user, db)


@router.put("/auth/me", response_model=UserResponse)
@router.patch("/users/me", response_model=UserResponse)
@router.put("/users/me", response_model=UserResponse)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    if data.locale is not None:
        current_user.locale = data.locale

    await db.commit()
    await db.refresh(current_user)
    return await _build_user_response(current_user, db)


@router.post("/auth/devices")
@router.post("/users/me/devices")
async def register_push_device(
    data: PushDeviceRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    device = PushDevice(
        user_id=current_user.id,
        push_token=data.push_token,
        platform=data.platform,
        is_active=True
    )
    db.add(device)
    await db.commit()
    return {"message": "Dispositivo registrado para notificaciones push."}


@router.get("/users/me/notification-settings", response_model=List[NotificationSettingResponse])
async def get_user_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    res = await db.execute(stmt)
    settings_list = res.scalars().all()
    return [NotificationSettingResponse.model_validate(s) for s in settings_list]


@router.put("/users/me/notification-settings", response_model=NotificationSettingResponse)
async def update_user_notification_settings(
    data: NotificationSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationSetting).where(
        NotificationSetting.user_id == current_user.id,
        NotificationSetting.alert_type == data.alert_type
    )
    res = await db.execute(stmt)
    setting = res.scalar_one_or_none()

    if not setting:
        setting = NotificationSetting(
            user_id=current_user.id,
            alert_type=data.alert_type,
            push_enabled=data.push_enabled
        )
        db.add(setting)
    else:
        setting.push_enabled = data.push_enabled

    await db.commit()
    await db.refresh(setting)
    return NotificationSettingResponse.model_validate(setting)
