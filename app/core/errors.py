from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


async def database_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    del request, exc
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Base de datos no disponible."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
