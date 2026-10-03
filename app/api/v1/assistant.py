import uuid
from datetime import datetime, timezone
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

    # 2. Dynamic response based on real data
    from app.models.vital import VitalReading
    from app.models.medication import Medication
    
    # Get last vitals
    stmt_v = select(VitalReading).where(VitalReading.patient_id == patient_id).order_by(VitalReading.measured_at.desc()).limit(3)
    res_v = await db.execute(stmt_v)
    vitals = res_v.scalars().all()
    vitals_summary = ", ".join([f"{v.type}: {v.value}" for v in vitals]) if vitals else "Sin registros"

    # Get medications
    stmt_m = select(Medication).where(Medication.patient_id == patient_id, Medication.discontinued_at.is_(None))
    res_m = await db.execute(stmt_m)
    meds = res_m.scalars().all()
    meds_summary = ", ".join([m.name for m in meds]) if meds else "Sin medicamentos"

    ai_text = (
        f"He analizado la historia clínica respecto a tu consulta: '{data.question}'.\n\n"
        f"🩺 **Signos vitales recientes**: {vitals_summary}\n"
        f"💊 **Medicamentos activos**: {meds_summary}\n\n"
        f"(Nota: Esta es una respuesta dinámica basada en los datos reales del paciente en la BD)."
    )

    sources = [
        {"title": "Plan de Medicamentos", "category": "Receta", "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
        {"title": "Registro de Signos Vitales", "category": "Vitals", "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
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
