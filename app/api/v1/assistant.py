import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.patient import PatientMember
from app.models.chat import AssistantConversation, AssistantMessage
from app.schemas.chat import (
    AskAssistantRequest,
    AssistantMessageResponse,
    AssistantConversationResponse,
    AssistantSource
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(prefix="/patients/{patient_id}/assistant", tags=["Asistente IA"])


@router.post("/ask", response_model=AssistantMessageResponse)
async def ask_assistant(
    patient_id: str,
    data: AskAssistantRequest,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve or create conversation
    conv = None
    if data.conversation_id:
        stmt = select(AssistantConversation).where(
            AssistantConversation.id == data.conversation_id,
            AssistantConversation.patient_id == patient_id
        )
        res = await db.execute(stmt)
        conv = res.scalar_one_or_none()

    if not conv:
        conv = AssistantConversation(
            patient_id=patient_id,
            user_id=membership.user_id,
            title=f"Consulta: {data.question[:30]}..."
        )
        db.add(conv)
        await db.flush()

    # 1. User message
    user_msg = AssistantMessage(
        conversation_id=conv.id,
        sender="user",
        text=data.question
    )
    db.add(user_msg)

    # 2. Simulated AI response based on medical record
    ai_text = f"Analizando la historia clínica del paciente: Respecto a tu pregunta '{data.question}', el paciente ha registrado sus signos vitales de manera estable en los últimos 7 días. Su adherencia a medicamentos es del 95% y no registra alergias agudas."
    sources = [
        {"title": "Plan de Medicamentos", "category": "Receta", "date": "2026-09-15"},
        {"title": "Registro de Presión Arterial", "category": "Vitals", "date": "2026-09-28"}
    ]

    ai_msg = AssistantMessage(
        conversation_id=conv.id,
        sender="assistant",
        text=ai_text,
        sources=sources
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return AssistantMessageResponse.model_validate(ai_msg)


@router.get("/conversations", response_model=List[AssistantConversationResponse])
async def list_assistant_conversations(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AssistantConversation).where(
        AssistantConversation.patient_id == patient_id,
        AssistantConversation.user_id == membership.user_id
    ).order_by(desc(AssistantConversation.created_at))

    res = await db.execute(stmt)
    convs = res.scalars().all()
    return [AssistantConversationResponse.model_validate(c) for c in convs]
