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
    auth.py               acceso mínimo con sesión — implementado y registrado, Cris
    deps.py               recuperación de usuario autenticado — implementado, Cris
    catalogs.py           catálogos — pendiente, Alejandra
    plans.py              planificaciones — pendiente, Alejandra
    generation.py         generación — pendiente, Jean
  core/
    config.py             configuración de entorno y sesión — implementado, Cris
  db/
    base.py               DeclarativeBase — implementado, Cris
    session.py            engine, SessionLocal y dependencia — implementado, Cris
    init_db.py            creación explícita de tablas — implementado, Cris
  models/                 cinco entidades compartidas — implementado, Cris
  schemas/                autenticación implementada; otros dominios pendientes
  services/
    auth.py               búsqueda y verificación de cuentas — implementado, Cris
    ai/                   integración con Ollama — pendiente, Jean
    plans.py              lógica de planificaciones — pendiente, Alejandra
tests/                    pruebas de hashing, carga, acceso y sesión implementadas; otras pendientes
```

Los routers traducen HTTP, validan mediante esquemas y llaman a servicios. Los servicios concentran la lógica de negocio y las integraciones. Los modelos representan persistencia y no ejecutan consultas ni commits por cuenta propia. Cris registra en `main.py` los routers que cada responsable exporte.

## Persistencia implementada

PostgreSQL conserva usuarios, catálogos y relaciones mediante columnas relacionales. `Planning.content` usa JSONB para el contenido pedagógico flexible; este campo no sustituye las claves foráneas ni la validación Pydantic que deberá aplicarse en los endpoints.

La aplicación crea un solo `engine` y un solo `sessionmaker`. `get_db_session()` entrega una sesión independiente por petición y la cierra al finalizar. Las operaciones futuras que escriban datos deben controlar `commit` y `rollback` de forma explícita.

`init_db()` importa los modelos y ejecuta `Base.metadata.create_all()`. El 10 de octubre se verificaron la conexión mediante `SELECT 1`, las cinco tablas y sus seis claves foráneas en PostgreSQL. Alembic no forma parte de esta etapa.

## Configuración e infraestructura

`app/core/config.py` obtiene `DATABASE_URL`, `SESSION_SECRET_KEY` y `SESSION_COOKIE_SECURE` del entorno o de un archivo local `.env`. La clave de sesión es obligatoria y debe permanecer fuera de Git. Desde Windows el host de PostgreSQL es `localhost`; si FastAPI se incorpora a Compose, será `alfa-db`.

Jean es responsable de versionar `compose.yaml`, `.env.example` y `Dockerfile`. Hasta que esos archivos se integren, la aplicación puede reproducir su entorno Python con `uv`, pero el repositorio no puede crear por sí solo el contenedor PostgreSQL en otra computadora.

## Generación y pruebas

Jean encapsulará Ollama en `app/services/ai/`. Toda respuesta de IA debe validarse con Pydantic antes de utilizarse o persistirse y debe manejar timeout, JSON inválido y servicio no disponible. Las pruebas del servicio usarán mocks.

Alejandra implementará catálogos y planificaciones sin duplicar los modelos compartidos. Las pruebas de persistencia y autorización deberán comprobar propiedad, datos inválidos y errores reales del dominio.

Los contratos aún abiertos están en [decisiones pendientes](decisiones-pendientes.md), y los pasos de continuación están en [instrucciones para el equipo](instrucciones-equipo.md).
