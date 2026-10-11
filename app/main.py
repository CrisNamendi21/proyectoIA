from fastapi import FastAPI

from app.api.health import router as health_router


app = FastAPI(
    title="Colegio Alfa API",
    description="Backend para la gestión de planificaciones didácticas.",
    version="0.1.0",
)

app.include_router(health_router)
