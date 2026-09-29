from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.voice import VoiceNote
from app.schemas.voice import VoiceUploadAcceptedResponse, VoiceTranscriptionResponse, ExtractedClinicalData
from app.services.alloxentric import AlloxentricVoiceService

router = APIRouter(prefix="/voice", tags=["Procesamiento de Voz & Alloxentric"])


@router.post("/upload", response_model=VoiceUploadAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_voice_note_for_alloxentric(
    file: UploadFile = File(...),
    patientId: str = Form(...),
    caregiverId: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Validate codec / format (.wav or .m4a)
    if not (file.filename.endswith(".wav") or file.filename.endswith(".m4a") or "audio" in (file.content_type or "")):
        raise AgeCareHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNPROCESSABLE_AUDIO_FORMAT",
            message="El archivo de audio debe estar en formato .wav o .m4a (PCM/AAC 16kHz)."
        )

    content = await file.read()
    job_id, voice_note = await AlloxentricVoiceService.process_audio_file(
        db=db,
        patient_id=patientId,
        caregiver_id=caregiverId,
        filename=file.filename,
        content=content
    )

    return VoiceUploadAcceptedResponse(
        jobId=job_id,
        status="processing",
        estimatedTimeSeconds=3
    )


@router.get("/transcriptions/{jobId}", response_model=VoiceTranscriptionResponse)
async def get_voice_transcription(
    jobId: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VoiceNote).where(VoiceNote.job_id == jobId)
    res = await db.execute(stmt)
    vn = res.scalar_one_or_none()

    if not vn:
        raise AgeCareHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"No se encontró el trabajo de transcripción con ID '{jobId}'."
        )

    extracted_dto = None
    if vn.extracted_data:
        extracted_dto = ExtractedClinicalData(
            sentiment=vn.extracted_data.get("sentiment", "neutral"),
            alerts=vn.extracted_data.get("alerts", []),
            vitalSignMentions=vn.extracted_data.get("vitalSignMentions", {})
        )

    return VoiceTranscriptionResponse(
        jobId=vn.job_id,
        status=vn.status,
        transcription=vn.transcription_text,
        extractedData=extracted_dto
    )
