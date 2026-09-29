from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientMember
from app.models.chat import ChatMessage, ChatReadPointer
from app.schemas.chat import (
    SendChatMessageRequest,
    ChatMessageResponse,
    MarkReadPointerRequest
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(prefix="/patients/{patient_id}/messages", tags=["Mensajes y Chat de Coordinación"])


@router.get("", response_model=List[ChatMessageResponse])
async def list_chat_messages(
    patient_id: str,
    limit: int = Query(50, le=100),
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatMessage, User).outerjoin(User, ChatMessage.sender_id == User.id).where(
        ChatMessage.patient_id == patient_id
    ).order_by(desc(ChatMessage.created_at)).limit(limit)

    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for msg, user in reversed(rows):
        r = ChatMessageResponse.model_validate(msg)
        r.sender_name = user.full_name if user else "Sistema"
        out.append(r)
    return out


@router.post("", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    patient_id: str,
    data: SendChatMessageRequest,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    msg = ChatMessage(
        patient_id=patient_id,
        sender_id=membership.user_id,
        kind=data.kind,
        text=data.text,
        media_blob_path=data.media_blob_path,
        duration_sec=data.duration_sec
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    res = ChatMessageResponse.model_validate(msg)
    res.sender_name = membership.user.full_name if membership.user else "Usuario"
    return res


@router.post("/read-pointer")
async def update_read_pointer(
    patient_id: str,
    data: MarkReadPointerRequest,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatReadPointer).where(
        ChatReadPointer.patient_id == patient_id,
        ChatReadPointer.user_id == membership.user_id
    )
    res = await db.execute(stmt)
    rp = res.scalar_one_or_none()

    if not rp:
        rp = ChatReadPointer(
            patient_id=patient_id,
            user_id=membership.user_id,
            last_read_message_id=data.last_read_message_id
        )
        db.add(rp)
    else:
        rp.last_read_message_id = data.last_read_message_id

    await db.commit()
    return {"message": "Puntero de lectura actualizado."}
