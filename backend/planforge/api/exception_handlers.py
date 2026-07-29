"""Map domain exceptions to HTTP responses."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from planforge.core.exceptions import (
    AppointmentDeleteError,
    AppointmentNotEditableError,
    AppointmentNotFoundError,
    MaintenanceLinkError,
    MaintenanceNotEditableError,
    MaintenanceNotFoundError,
    NotFoundError,
    PlanforgeError,
    StateError,
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

    @app.exception_handler(NotFoundError)
    async def not_found_handler(
        _request: Request,
        exc: NotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_handler(
        _request: Request,
        exc: TaskNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(StateError)
    async def state_error_handler(
        _request: Request,
        exc: StateError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

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

    @app.exception_handler(AppointmentNotFoundError)
    async def appointment_not_found_handler(
        _request: Request,
        exc: AppointmentNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AppointmentNotEditableError)
    async def appointment_not_editable_handler(
        _request: Request,
        exc: AppointmentNotEditableError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(AppointmentDeleteError)
    async def appointment_delete_error_handler(
        _request: Request,
        exc: AppointmentDeleteError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaintenanceLinkError)
    async def maintenance_link_error_handler(
        _request: Request,
        exc: MaintenanceLinkError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaintenanceNotEditableError)
    async def maintenance_not_editable_handler(
        _request: Request,
        exc: MaintenanceNotEditableError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(MaintenanceNotFoundError)
    async def maintenance_not_found_handler(
        _request: Request,
        exc: MaintenanceNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PlanforgeError)
    async def planforge_error_handler(
        _request: Request,
        exc: PlanforgeError,
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def value_error_handler(
        _request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
