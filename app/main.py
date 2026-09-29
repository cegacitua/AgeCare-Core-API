from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.database import async_engine, Base
from app.core.exceptions import (
    AgeCareHTTPException,
    agecare_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from app.api.v1.router import api_v1_router
from app.websockets.chat_manager import ws_manager
from app.core.security import decode_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if dev / testing
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AgeCareHTTPException, agecare_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


# Request ID Middleware for Audit & Tracing
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include API v1 Router
app.include_router(api_v1_router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }


# Real-time Chat WebSocket Channel
@app.websocket("/ws/chat/{patient_id}")
async def websocket_chat(websocket: WebSocket, patient_id: str, token: str = None):
    if not token:
        await websocket.close(code=4001)
        return

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4002)
        return

    user_id = payload.get("sub")
    await ws_manager.connect(patient_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast message to all active participants in patient circle
            message_event = {
                "type": "chat_message",
                "patient_id": patient_id,
                "sender_id": user_id,
                "data": data
            }
            await ws_manager.broadcast_to_patient(patient_id, message_event)
    except WebSocketDisconnect:
        ws_manager.disconnect(patient_id, websocket)
