import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import PatientMember
from app.models.file import Upload, Document
from app.schemas.file import (
    UploadUrlRequest,
    UploadUrlResponse,
    DocumentCreate,
    DocumentResponse
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(tags=["Archivos y Documentos Médicos"])


@router.post("/uploads/request-url", response_model=UploadUrlResponse, status_code=status.HTTP_201_CREATED)
async def request_upload_url(
    data: UploadUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    upload_id = str(uuid.uuid4())
    blob_path = f"{data.purpose}/{current_user.id}/{upload_id}_{data.filename}"

    upload = Upload(
        id=upload_id,
        user_id=current_user.id,
        purpose=data.purpose,
        blob_path=blob_path,
        content_type=data.content_type,
        size_bytes=data.size_bytes,
        status="uploaded"
    )
    db.add(upload)
    await db.commit()

    # Generate presigned upload URL (or mock URL in dev)
    mock_presigned_url = f"https://agecarestorage.blob.core.windows.net/agecare-documents/{blob_path}?sv=2026-08-14&se=2026-09-30T00%3A00%3A00Z&sr=b&sp=rw&sig=mockSignature123"

    return UploadUrlResponse(
        upload_id=upload_id,
        upload_url=mock_presigned_url,
        blob_path=blob_path,
        expires_in_sec=3600
    )


@router.post("/patients/{patient_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_document(
    patient_id: str,
    data: DocumentCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Upload).where(Upload.id == data.upload_id)
    res = await db.execute(stmt)
    upload = res.scalar_one_or_none()
    if not upload:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="El archivo subido no existe.")

    doc = Document(
        patient_id=patient_id,
        upload_id=data.upload_id,
        title=data.title,
        category=data.category,
        doc_date=data.doc_date,
        uploaded_by=membership.user_id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    res_doc = DocumentResponse.model_validate(doc)
    res_doc.blob_path = upload.blob_path
    res_doc.download_url = f"https://agecarestorage.blob.core.windows.net/agecare-documents/{upload.blob_path}"
    return res_doc


@router.get("/patients/{patient_id}/documents", response_model=List[DocumentResponse])
async def list_medical_documents(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document, Upload).join(Upload, Document.upload_id == Upload.id).where(
        Document.patient_id == patient_id
    ).order_by(desc(Document.created_at))

    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for doc, upload in rows:
        r = DocumentResponse.model_validate(doc)
        r.blob_path = upload.blob_path
        r.download_url = f"https://agecarestorage.blob.core.windows.net/agecare-documents/{upload.blob_path}"
        out.append(r)
    return out


@router.get("/documents/{document_id}/download")
async def download_medical_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document, Upload).join(Upload, Document.upload_id == Upload.id).where(Document.id == document_id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="El documento no existe.")

    doc, upload = row
    download_url = f"https://agecarestorage.blob.core.windows.net/agecare-documents/{upload.blob_path}?sp=r&sig=downloadToken123"
    return {"download_url": download_url, "expires_in_sec": 3600}
