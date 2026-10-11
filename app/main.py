from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.core.config import get_settings


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
    app.include_router(health_router)
    app.include_router(auth_router)
    return app


app = create_app()
