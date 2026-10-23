# Arquitectura del backend

## Estado y criterios

La base técnica implementada el 10 de octubre de 2026 usa Python 3.12, FastAPI, SQLAlchemy 2 síncrono, Psycopg 3 y PostgreSQL en Docker. `pyproject.toml` declara las dependencias y `uv.lock` fija el entorno reproducible.

La arquitectura separa transporte HTTP, validación, lógica de negocio, configuración y persistencia. Las piezas futuras deben respetar esta separación sin añadir capas que no ayuden al MVP.

## Organización

```text
app/
  main.py                 aplicación y registro de routers — implementado, Cris
  api/
    health.py             comprobación de salud — implementado, Cris
    auth.py               login, logout y consulta de identidad — implementado, Cris
    deps.py               recuperación de usuario autenticado — implementado, Cris
    catalogs.py           consulta y filtros de catálogos — implementado, Alejandra
    plans.py              guardar, listar y consultar planes — integrado con auth
    generation.py         generación protegida — implementado, Jean
  core/
    config.py             configuración de entorno y sesión — implementado, Cris
  db/
    base.py               DeclarativeBase — implementado, Cris
    session.py            engine, SessionLocal y dependencia — implementado, Cris
    init_db.py            actualización a la cabeza de Alembic — implementado, Cris
    migrations/           historial versionado del esquema PostgreSQL — implementado, Cris
  models/                 cinco entidades compartidas — implementado, Cris
  schemas/                autenticación, catálogos, planes y salida de IA
  services/
    auth.py               búsqueda y verificación de cuentas — implementado, Cris
    ai/                   integración con Ollama — implementado, Jean
    plans.py              guardado y consulta por propietario — implementado, Alejandra
tests/                    pruebas de módulos y flujos integrados
```

Los routers traducen HTTP, validan mediante esquemas y llaman a servicios. Los servicios concentran la lógica de negocio y las integraciones. Los modelos representan persistencia y no ejecutan consultas ni commits por cuenta propia. Cris registra en `main.py` los routers que cada responsable exporte.

## Persistencia implementada

PostgreSQL conserva usuarios, catálogos y relaciones mediante columnas relacionales. `Planning.content` usa JSONB para el contenido pedagógico flexible; este campo no sustituye las claves foráneas ni la validación Pydantic que deberá aplicarse en los endpoints.

La aplicación crea un solo `engine` y un solo `sessionmaker`. `get_db_session()` entrega una sesión independiente por petición y la cierra al finalizar. Las operaciones futuras que escriban datos deben controlar `commit` y `rollback` de forma explícita.

`init_db()` aplica `alembic upgrade head`. Alembic conserva el historial del esquema, obtiene la URL desde la configuración de la aplicación y compara sus revisiones con `Base.metadata`. `create_all()` queda limitado a fixtures desechables de pruebas.

## Configuración e infraestructura

`app/core/config.py` obtiene `DATABASE_URL`, `SESSION_SECRET_KEY` y `SESSION_COOKIE_SECURE` del entorno o de un archivo local `.env`. La clave de sesión es obligatoria y debe permanecer fuera de Git. Desde Windows el host de PostgreSQL es `localhost`; si FastAPI se incorpora a Compose, será `alfa-db`.

Jean es responsable de versionar `compose.yaml`, `.env.example` y `Dockerfile`. Hasta que esos archivos se integren, la aplicación puede reproducir su entorno Python con `uv`, pero el repositorio no puede crear por sí solo el contenedor PostgreSQL en otra computadora.

## Generación y pruebas

Jean encapsuló Ollama en `app/services/ai/`. La salida se valida con Pydantic y el endpoint controla timeout, JSON inválido y servicio no disponible. Las pruebas usan mocks para no depender de Ollama.

Alejandra implementó la consulta de catálogos y el guardado, listado y detalle de planificaciones sin duplicar modelos. La edición de planes aún debe comprobar propiedad antes de incorporarse.

`create_app()` registra todos los routers actuales. Generación, planificaciones y catálogos dependen de `get_current_user`. Los errores no controlados de SQLAlchemy se traducen en una respuesta genérica `503` sin detalles de conexión.

Los contratos aún abiertos están en [decisiones pendientes](decisiones-pendientes.md), y los pasos de continuación están en [instrucciones para el equipo](instrucciones-equipo.md).
