from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import PatientMember
from app.models.elder import Photo, PhotoReaction, ContentItem
from app.schemas.elder import (
    SharePhotoRequest,
    PhotoResponse,
    ReactionRequest,
    PhotoReactionResponse,
    ContentItemResponse,
    TTSRequest,
    TTSResponse,
    STTRequest,
    STTResponse
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(tags=["Vista del Adulto Mayor: Fotos, Entretenimiento y Voz"])


@router.post("/patients/{patient_id}/photos", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def share_photo(
    patient_id: str,
    data: SharePhotoRequest,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    photo = Photo(
        patient_id=patient_id,
        upload_id=data.upload_id,
        shared_by=membership.user_id,
        caption=data.caption
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    res = PhotoResponse.model_validate(photo)
    res.shared_by_name = membership.user.full_name if membership.user else "Familiar"
    res.url = f"https://agecarestorage.blob.core.windows.net/agecare-documents/photos/{photo.upload_id}.jpg"
    return res


@router.get("/patients/{patient_id}/photos", response_model=List[PhotoResponse])
async def list_gallery_photos(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Photo, User).join(User, Photo.shared_by == User.id).where(
        Photo.patient_id == patient_id
    ).order_by(desc(Photo.created_at))

    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for photo, user in rows:
        # Fetch reactions
        stmt_r = select(PhotoReaction, User).join(User, PhotoReaction.user_id == User.id).where(PhotoReaction.photo_id == photo.id)
        res_r = await db.execute(stmt_r)
        r_rows = res_r.all()
        reactions = []
        for react, r_user in r_rows:
            r_dto = PhotoReactionResponse.model_validate(react)
            r_dto.user_name = r_user.full_name
            reactions.append(r_dto)

        p_res = PhotoResponse.model_validate(photo)
        p_res.shared_by_name = user.full_name
        p_res.url = f"https://agecarestorage.blob.core.windows.net/agecare-documents/photos/{photo.upload_id}.jpg"
        p_res.reactions = reactions
        out.append(p_res)
    return out


@router.post("/photos/{photo_id}/reactions", response_model=PhotoReactionResponse)
async def react_to_photo(
    photo_id: str,
    data: ReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Photo).where(Photo.id == photo_id)
    res = await db.execute(stmt)
    photo = res.scalar_one_or_none()
    if not photo:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="La foto no existe.")

    reaction = PhotoReaction(
        photo_id=photo_id,
        user_id=current_user.id,
        kind=data.kind,
        voice_blob_path=data.voice_blob_path
    )
    db.add(reaction)
    await db.commit()
    await db.refresh(reaction)

    res_dto = PhotoReactionResponse.model_validate(reaction)
    res_dto.user_name = current_user.full_name
    return res_dto


@router.get("/content/jokes-news", response_model=List[ContentItemResponse])
async def list_jokes_and_news(
    kind: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(ContentItem).where(ContentItem.is_active == True)
    if kind:
        query = query.where(ContentItem.kind == kind)
    query = query.order_by(desc(ContentItem.published_at)).limit(20)

    res = await db.execute(query)
    items = res.scalars().all()
    if not items:
        # Fallback sample content
        sample = ContentItem(
            kind="joke",
            title="El abuelo y la tecnología",
            body="— Abuelo, ¿cuál es tu red social favorita? — El banco de la plaza a las 11 de la mañana.",
            published_at=datetime.now(timezone.utc)
        )
        return [ContentItemResponse.model_validate(sample)]

    return [ContentItemResponse.model_validate(i) for i in items]


@router.post("/speech/tts", response_model=TTSResponse)
async def text_to_speech(data: TTSRequest):
    return TTSResponse(
        audio_url="https://agecarestorage.blob.core.windows.net/agecare-documents/audio/tts_sample.mp3",
        duration_sec=3.5
    )


@router.post("/speech/stt", response_model=STTResponse)
async def speech_to_text(data: STTRequest):
    return STTResponse(
        text="Hola familia, me siento muy bien hoy y ya almorcé.",
        confidence=0.98
    )
