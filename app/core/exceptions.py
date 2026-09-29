import uuid
from typing import Any, List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[Any]] = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AgeCareHTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Any]] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


async def agecare_exception_handler(request: Request, exc: AgeCareHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    payload = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id
        }
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    payload = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Hay datos inválidos en la solicitud. Revisa los campos marcados.",
            "details": exc.errors(),
            "request_id": request_id
        }
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    payload = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Algo salió mal de nuestro lado. Intenta más tarde.",
            "details": [str(exc)] if request.app.debug else None,
            "request_id": request_id
        }
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
