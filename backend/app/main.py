from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.api import router
from backend.app.config import Settings
from backend.app.errors import AppError


def _error_payload(
    *,
    request_id: str,
    code: str,
    message: str,
    retryable: bool,
    field_errors: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "field_errors": field_errors or [],
            "request_id": request_id,
            "retryable": retryable,
        }
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_env()
    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                request_id=request.state.request_id,
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
                field_errors=exc.field_errors,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        field_errors = [
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                request_id=request.state.request_id,
                code="VALIDATION_ERROR",
                message="입력 내용을 확인해 주세요.",
                retryable=False,
                field_errors=field_errors,
            ),
        )

    app.include_router(router)
    return app


app = create_app()
