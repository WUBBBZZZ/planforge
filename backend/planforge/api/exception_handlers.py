"""Map domain exceptions to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from planforge.core.exceptions import (
    PlanforgeError,
    TaskNotEditableError,
    TaskNotFoundError,
    TaskStateError,
    ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers for application-layer errors."""

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_handler(
        _request: Request,
        exc: TaskNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(TaskNotEditableError)
    async def task_not_editable_handler(
        _request: Request,
        exc: TaskNotEditableError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(TaskStateError)
    async def task_state_error_handler(
        _request: Request,
        exc: TaskStateError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(PlanforgeError)
    async def planforge_error_handler(
        _request: Request,
        exc: PlanforgeError,
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
