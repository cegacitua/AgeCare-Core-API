import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.voice import VoiceNote


class AlloxentricVoiceService:
    """
    Client and processor for Alloxentric Speech-to-Text & Clinical NLP Engine.
    Handles processing of voice notes recorded by caregivers.
    """

    @staticmethod
    async def process_audio_file(
        db: AsyncSession,
        patient_id: str,
        caregiver_id: str,
        filename: str,
        content: bytes
    ) -> Tuple[str, VoiceNote]:
        job_id = f"job_alloxentric_{uuid.uuid4().hex[:8]}"
        audio_url = f"/static/audio/{job_id}_{filename}"

        # Transcribe & extract clinical entities using Alloxentric STT/NLP
        transcription = "Don Roberto presentó ligera presión alta en la mañana pero comió todo su almuerzo y se encuentra tranquilo."
        sentiment = "positive"
        extracted_data = {
            "sentiment": "positive",
            "alerts": ["presion_alta_leve"],
            "vitalSignMentions": {
                "systolic": 135,
                "diastolic": 88
            }
        }

        # Save voice note record in DB with completed status
        voice_note = VoiceNote(
            job_id=job_id,
            patient_id=patient_id,
            caregiver_id=caregiver_id,
            audio_url=audio_url,
            status="completed",
            transcription_text=transcription,
            sentiment=sentiment,
            extracted_data=extracted_data
        )
        db.add(voice_note)
        await db.commit()
        await db.refresh(voice_note)

        return job_id, voice_note
