from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


def _status_code_to_code(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
    }.get(status_code, f"HTTP_{status_code}")


def _request_id(request: Request) -> str | None:
    value = request.headers.get("X-Request-ID") or request.headers.get("X-Request-Id")
    return value if value else None


def _to_error_response(
    *,
    request: Request,
    status_code: int,
    message: str,
    details: Any | None = None,
    code: str | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        code=code or _status_code_to_code(status_code),
        message=message,
        details=details,
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI, *, debug: bool) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            message = str(detail.get("message") or detail.get("detail") or "Error")
            code = detail.get("code")
            return _to_error_response(
                request=request, status_code=exc.status_code, message=message, details=detail, code=code
            )
        return _to_error_response(
            request=request,
            status_code=exc.status_code,
            message=str(detail),
            details=None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return _to_error_response(
            request=request,
            status_code=422,
            message="Validation error",
            details={"errors": exc.errors()},
            code="VALIDATION_ERROR",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        details = {"type": type(exc).__name__} if debug else None
        return _to_error_response(
            request=request,
            status_code=500,
            message="Internal Server Error",
            details=details,
            code="INTERNAL_ERROR",
        )

