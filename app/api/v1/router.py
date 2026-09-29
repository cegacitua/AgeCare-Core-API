from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.patients import router as patients_router
from app.api.v1.vitals import router as vitals_router
from app.api.v1.medications import router as medications_router
from app.api.v1.observations import router as observations_router
from app.api.v1.files import router as files_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.messages import router as messages_router
from app.api.v1.elder import router as elder_router
from app.api.v1.caregiver import router as caregiver_router
from app.api.v1.marketplace import router as marketplace_router
from app.api.v1.voice import router as voice_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(patients_router)
api_v1_router.include_router(vitals_router)
api_v1_router.include_router(medications_router)
api_v1_router.include_router(observations_router)
api_v1_router.include_router(files_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(assistant_router)
api_v1_router.include_router(messages_router)
api_v1_router.include_router(elder_router)
api_v1_router.include_router(caregiver_router)
api_v1_router.include_router(marketplace_router)
api_v1_router.include_router(voice_router)
