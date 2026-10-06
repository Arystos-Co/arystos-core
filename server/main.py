"""FastAPI application for ARYSTOS Core."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from server.admin.router import router as admin_router
from server.routers.admin_users import router as admin_users_router
from server.routers.auth import router as auth_router
from server.routers.client import router as client_router
from server.routers.delivery import router as delivery_router
from server.routers.schemas import ErrorResponse
from server.routers.updates import router as updates_router

logger = logging.getLogger(__name__)

app = FastAPI(title="ARYSTOS Core")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(client_router)
app.include_router(delivery_router)
app.include_router(updates_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_users_router)

_dashboard_static_dir = Path(__file__).resolve().parent / "dashboard" / "static"
if _dashboard_static_dir.exists():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(_dashboard_static_dir), html=True),
        name="dashboard",
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Return the server health without authentication or a database check."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def handle_unhandled_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Log an unhandled exception with its traceback and return a safe error."""
    logger.error(
        "Unhandled server exception",
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    error_response = ErrorResponse(error="server_error")
    return JSONResponse(status_code=500, content=error_response.model_dump(exclude_none=True))


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request,
    exception: RequestValidationError,
) -> Response:
    """Return canonical input errors for administrator request validation.

    Args:
        request: Incoming request whose body failed validation.
        exception: FastAPI validation details.

    Returns:
        The administrator error payload or FastAPI's normal validation response.
    """
    if not request.url.path.startswith("/api/v1/admin/"):
        return await request_validation_exception_handler(request, exception)

    errors = exception.errors()
    detail = errors[0]["msg"] if errors else "Invalid request input."
    if errors:
        location = errors[0]["loc"]
        field = location[-1] if location else None
        if field == "status":
            detail = "status must be one of: active, suspended, offboarded"
        elif field == "payment_status":
            detail = "payment_status must be one of: paid, pending, overdue"

    return JSONResponse(
        status_code=422,
        content={"error": "invalid_input", "detail": detail},
    )
