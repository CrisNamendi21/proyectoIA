from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth import router as auth_router
from app.api.catalogs import router as catalogs_router
from app.api.generation import create_generation_router
from app.api.health import router as health_router
from app.api.plans import router as plans_router
from app.api.profile import router as profile_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> FastAPI:
    settings = get_settings()
    secret = settings.session_secret_key
    if secret is None or len(secret.get_secret_value()) < 32:
        raise RuntimeError("SESSION_SECRET_KEY debe tener al menos 32 caracteres.")

    app = FastAPI(
        title="Colegio Alfa API",
        description="Backend para la gestión de planificaciones didácticas.",
        version="0.1.0",
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret.get_secret_value(),
        session_cookie="colegio_alfa_session",
        max_age=8 * 60 * 60,
        same_site="lax",
        https_only=settings.session_cookie_secure,
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(catalogs_router)
    app.include_router(profile_router)
    app.include_router(create_generation_router("/generation", include_chat=True))
    app.include_router(plans_router)
    if FRONTEND_DIR.is_dir():
        @app.get("/", include_in_schema=False)
        def frontend_index() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

        app.mount(
            "/frontend",
            StaticFiles(directory=FRONTEND_DIR),
            name="frontend",
        )
    return app


app = create_app()
