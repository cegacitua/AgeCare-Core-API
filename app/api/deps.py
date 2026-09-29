from typing import Optional, List
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import Patient, PatientMember


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AgeCareHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Tu sesión expiró o no enviaste token. Vuelve a iniciar sesión."
        )
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AgeCareHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Token de acceso inválido o expirado. Vuelve a iniciar sesión."
        )
    
    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise AgeCareHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="El usuario asociado al token ya no existe."
        )
    
    return user


async def get_patient_membership(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PatientMember:
    stmt = select(PatientMember).where(
        PatientMember.patient_id == patient_id,
        PatientMember.user_id == current_user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise AgeCareHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="No tienes permisos para realizar esta acción sobre este paciente."
        )
    
    return membership


def require_patient_roles(allowed_roles: List[str]):
    async def role_checker(membership: PatientMember = Depends(get_patient_membership)) -> PatientMember:
        if membership.role not in allowed_roles:
            raise AgeCareHTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message=f"Tu rol '{membership.role}' no está autorizado para realizar esta operación."
            )
        return membership
    return role_checker
