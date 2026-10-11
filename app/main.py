from fastapi import FastAPI


app = FastAPI(
    title="Colegio Alfa API",
    description="Backend para la gestión de planificaciones didácticas.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
