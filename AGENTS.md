# Instrucciones para trabajar en Colegio Alfa

## Propósito y alcance

Construir un backend universitario comprensible para cuentas docentes precreadas, consulta curricular, generación de propuestas con Ollama, edición, persistencia e historial personal. El horizonte del MVP es del 10 al 16 de octubre de 2026. Evita ampliar esta semana a frontend completo, PDF, recuperación de contraseña, panel administrativo o fine-tuning. Lee [contexto](docs/contexto.md) y [decisiones pendientes](docs/decisiones-pendientes.md) antes de asumir detalles del dominio.

## Estado y estructura

La base del sábado ya incluye la aplicación FastAPI, configuración, persistencia y cinco modelos compartidos; los módulos funcionales y sus pruebas siguen pendientes. Comprueba el estado real antes de actuar. La separación vigente está en [arquitectura](docs/arquitectura.md). No describas una ruta o una prueba como funcional sin comprobarla.

## Stack y separación

- Usa Python 3.12, FastAPI/Uvicorn, Pydantic, SQLAlchemy 2, PostgreSQL mediante Docker Compose, Ollama local y pytest.
- Mantén routers HTTP en `app/api/`, validación y serialización en `app/schemas/`, lógica de negocio e integración externa en `app/services/`, configuración en `app/core/`, sesión y persistencia en `app/db/` y entidades ORM en `app/models/`.
- En FastAPI, declara dependencias para sesión de BD y usuario autenticado; mantén los routers delgados y documenta las respuestas de error que realmente implemente cada endpoint.
- Usa SQLAlchemy 2 en modo síncrono con Psycopg 3. Aplica los patrones `Mapped` y `mapped_column`, una sesión independiente por petición y relaciones explícitas. Evita consultas y commits escondidos en modelos o esquemas.
- Valida datos de entrada y la salida de IA con Pydantic. No confíes en JSON producido por Ollama sin validarlo.
- PostgreSQL es la única base de datos del MVP. Ejecuta PostgreSQL en un contenedor, no lo instales directamente en el sistema operativo. Considera JSONB para contenido pedagógico flexible, manteniendo relaciones, usuarios y catálogos como datos relacionales.
- Usa `uv` para gestionar Python y las dependencias. `pyproject.toml` declara las dependencias y `uv.lock` fija las versiones reproducibles; ambos son la fuente oficial acordada con Jean. No mantengas un `requirements.txt` paralelo.
- Mantén secretos y credenciales fuera de Git. Documenta solo nombres y valores de ejemplo no sensibles en `.env.example` cuando Jean lo prepare; no copies archivos `.env` con valores reales.

## Propiedad y contratos

| Responsable principal | Archivos previstos |
| --- | --- |
| Cris | `app/main.py`, `app/core/`, `app/db/`, `app/models/`, `app/api/auth.py`, `tests/test_auth.py` |
| Jean | `Dockerfile`, `compose.yaml`, `.env.example`, `app/services/ai/`, `app/api/generation.py`, `tests/test_ai.py`; coordina con Cris los cambios de dependencias en `pyproject.toml` y `uv.lock` |
| Alejandra | `app/api/catalogs.py`, `app/api/plans.py`, `app/schemas/catalogs.py`, `app/schemas/plans.py`, `app/services/plans.py`, `tests/test_catalogs.py`, `tests/test_plans.py` |

Antes de editar archivos de otro responsable o cambiar entidades/contratos compartidos, explica la necesidad y coordina el cambio con el equipo. Cris registra los routers en `main.py`; Jean y Alejandra exportan sus routers. Los acuerdos propuestos y su estado constan en [contratos](docs/contratos.md) y [modelo de datos](docs/modelo-datos.md). No conviertas propuestas en contratos aprobados por mera implementación.

## Git y revisión

`main` es estable y `Cris-develop` integra el trabajo de esta etapa. El trabajo paralelo usará ramas de feature desde `Cris-develop` y PR hacia `Cris-develop`, según [flujo de trabajo](docs/flujo-trabajo.md). Antes de editar, revisa rama, estado y archivos existentes. No sobrescribas cambios ajenos. No hagas push ni merge sin la revisión solicitada; cada PR debe decir qué se probó y cómo repetirlo.

## Calidad y conducta de agentes

- Haz cambios pequeños y legibles, con nombres consistentes y tipado útil; evita capas y dependencias sin beneficio claro para el MVP.
- Añade pruebas cuando verifiquen comportamiento relevante: autenticación, propiedad de planes, validación, persistencia y fallos de Ollama. Usa mocks para IA y fixtures aisladas para BD cuando se implementen.
- Ejecuta solo pruebas disponibles y reporta exactamente cuáles pasaron o qué quedó sin verificar. No declares el backend terminado por haber escrito documentación.
- Distingue hechos del plan, decisiones expresas del equipo, propuestas y pendientes. Si las fuentes chocan, deja constancia antes de resolverlo.
- Las fotos docentes son referencias pedagógicas; no copies nombres, firmas ni otros datos personales al repositorio.
