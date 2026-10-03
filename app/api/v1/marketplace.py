from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.caregiver import CaregiverProfile
from app.models.marketplace import MarketplaceProduct, CaregiverReview, ContactRequest
from app.schemas.caregiver import CaregiverProfileResponse
from app.schemas.marketplace import (
    MarketplaceProductResponse,
    CaregiverReviewCreate,
    CaregiverReviewResponse,
    ContactCaregiverRequest,
    ContactRequestResponse
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/marketplace", tags=["Marketplace Vitrina"])


@router.get("/caregivers")
async def search_caregivers(
    zone: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(CaregiverProfile, User).join(User, CaregiverProfile.user_id == User.id).where(
        CaregiverProfile.is_listed == True
    ).order_by(desc(CaregiverProfile.rating_avg))

    res = await db.execute(query)
    rows = res.all()

    out = []
    for prof, user in rows:
        p_res = CaregiverProfileResponse.model_validate(prof)
        p_res.profile_id = prof.id
        p_res.name = user.full_name
        p_res.photo_url = user.photo_url
        p_res.rating = prof.rating_avg
        out.append(p_res)
    return {"items": out}


@router.get("/caregivers/{profile_id}", response_model=CaregiverProfileResponse)
async def get_caregiver_public_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverProfile, User).join(User, CaregiverProfile.user_id == User.id).where(
        CaregiverProfile.id == profile_id
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="Perfil no encontrado.")

    prof, user = row
    p_res = CaregiverProfileResponse.model_validate(prof)
    p_res.profile_id = prof.id
    p_res.name = user.full_name
    p_res.photo_url = user.photo_url
    p_res.rating = prof.rating_avg
    return p_res


@router.post("/caregivers/{profile_id}/contact", response_model=ContactRequestResponse, status_code=status.HTTP_201_CREATED)
async def contact_caregiver(
    profile_id: str,
    data: ContactCaregiverRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverProfile).where(CaregiverProfile.id == profile_id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()
    if not prof:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="Perfil no encontrado.")

    req = ContactRequest(
        profile_id=profile_id,
        family_user_id=current_user.id,
        message=data.message
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return ContactRequestResponse.model_validate(req)


@router.post("/caregivers/{profile_id}/reviews", response_model=CaregiverReviewResponse, status_code=status.HTTP_201_CREATED)
async def rate_caregiver(
    profile_id: str,
    data: CaregiverReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverProfile).where(CaregiverProfile.id == profile_id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()
    if not prof:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="Perfil no encontrado.")

    review = CaregiverReview(
        profile_id=profile_id,
        author_id=current_user.id,
        rating=data.rating,
        comment=data.comment
    )
    db.add(review)

    # Recalculate rating average
    prof.reviews_count += 1
    prof.rating_avg = round(((prof.rating_avg * (prof.reviews_count - 1)) + data.rating) / prof.reviews_count, 1)

    await db.commit()
    await db.refresh(review)

    res_dto = CaregiverReviewResponse.model_validate(review)
    res_dto.author_name = current_user.full_name
    return res_dto


@router.get("/products")
async def list_products(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(MarketplaceProduct).where(MarketplaceProduct.is_active == True)
    if category:
        query = query.where(MarketplaceProduct.category == category)

    res = await db.execute(query)
    prods = res.scalars().all()
    if not prods:
        import uuid
        sample = MarketplaceProduct(
            id=str(uuid.uuid4()),
            name="Silla de Ruedas Ergonómica Plegable",
            category="mobility",
            description="Silla liviana de aluminio con apoyabrazos acolchados y frenos de seguridad.",
            image_url="https://agecarestorage.blob.core.windows.net/agecare-documents/products/silla.jpg",
            price=120000.0,
            contact_info="ventas@ortopedia.cl"
        )
        return {"items": [MarketplaceProductResponse.model_validate(sample)]}

    return {"items": [MarketplaceProductResponse.model_validate(p) for p in prods]}
