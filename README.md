# Colegio Alfa

Backend universitario para apoyar a docentes en la creación, revisión, guardado y consulta de planificaciones didácticas. El MVP se desarrollará del **10 al 16 de octubre de 2026**.

## Estado al 14 de octubre de 2026

La base técnica y los módulos principales están integrados en `Cris-develop`:

- aplicación FastAPI con salud, autenticación, catálogos, generación y planificaciones;
- configuración mediante `DATABASE_URL`;
- SQLAlchemy 2 síncrono con Psycopg 3;
- una sesión de base de datos por petición;
- modelos `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`;
- creación explícita de tablas con `init_db()`;
- dependencias administradas con `uv`, `pyproject.toml` y `uv.lock`;
- sesión por cookie firmada, consulta de identidad y cierre de sesión;
- rutas de generación y planificaciones protegidas con `get_current_user`;
- respuestas controladas para fallos de PostgreSQL y Ollama.
- flujo autenticación → catálogos → generación → revisión simulada → guardado → historial comprobado con PostgreSQL desechable.

Cris confirmó para el MVP la ruta `/generation` y la sesión actual; la revocación en servidor sigue pendiente del equipo. Las planificaciones se pueden guardar, listar y consultar; la edición y la aprobación del formato pedagógico corresponden al siguiente avance de Alejandra. El catálogo curricular real y sus datos iniciales aún deben ser proporcionados y acordados.

## Requisitos

- `uv` instalado.
- Docker Desktop activo.
- PostgreSQL ejecutándose en un contenedor con el contrato descrito en [contratos](docs/contratos.md).

El repositorio fija Python 3.12 mediante `.python-version`. No se usa `requirements.txt`.

## Preparar el entorno

Instala exactamente las dependencias del lockfile:

```powershell
uv sync --locked
uv run python --version
```

La segunda orden debe mostrar Python 3.12.x.

Crea un archivo local `.env` en la raíz. Este archivo está ignorado por Git. Mientras FastAPI se ejecute directamente en Windows, usa la contraseña configurada en el contenedor PostgreSQL:

```dotenv
DATABASE_URL=postgresql+psycopg://equipo_alfa:<CONTRASENA_LOCAL>@localhost:5432/colegio_alfa_db
SESSION_SECRET_KEY=<CLAVE_ALEATORIA_DE_32_O_MAS_CARACTERES>
SESSION_COOKIE_SECURE=false
```

Sustituye los marcadores por valores locales. `SESSION_SECRET_KEY` es obligatoria; `SESSION_COOKIE_SECURE` debe ser `true` al servir la API mediante HTTPS. No versiones `.env` ni compartas su contenido. `.env.example` documenta el conjunto completo de variables usadas por Compose y Ollama.

## Crear las tablas

Con PostgreSQL disponible, ejecuta:

```powershell
uv run python -m app.db.init_db
```

La inicialización usa `create_all()` y no reemplaza una estrategia posterior de migraciones.

Para crear una cuenta docente sin guardar la contraseña en archivos o en el historial de la terminal:

```powershell
uv run python -m app.db.seed_users <nombre_de_usuario>
```

El comando solicita y confirma la contraseña de forma interactiva. Si la cuenta ya existe, no modifica sus datos.

## Iniciar la API

```powershell
uv run uvicorn app.main:app --reload
```

Comprueba la ruta de salud:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

La respuesta esperada es `{"status":"ok"}`. `POST /auth/login` establece la sesión, `GET /auth/me` devuelve la identidad pública y `POST /auth/logout` elimina la cookie. Las rutas `/generation` y `/plans` requieren una sesión válida. El contrato HTTP disponible puede consultarse en `http://127.0.0.1:8000/docs`.

## Comprobar PostgreSQL

```powershell
uv run python -c "from sqlalchemy import text; from app.db.session import engine; connection = engine.connect(); print(connection.execute(text('SELECT 1')).scalar_one()); connection.close(); engine.dispose()"
```

La salida esperada es `1`. Este comando, la creación de tablas y el arranque de Uvicorn fueron comprobados el 10 de octubre de 2026.

## Estructura

```text
app/
  main.py               aplicación y registro de routers
  api/                   salud, autenticación, catálogos, generación y planes
  core/                  configuración, hashing, validaciones y errores
  db/                   base declarativa, engine, sesiones e inicialización
  models/               cinco entidades SQLAlchemy compartidas
  schemas/               contratos Pydantic de autenticación y planes
  services/              autenticación, Ollama y persistencia de planes
docs/                   arquitectura, contratos y coordinación
tests/                  pruebas aisladas y pruebas opcionales con PostgreSQL
```

La edición de planificaciones y la carga del catálogo curricular acordado siguen pendientes. No se deben inventar datos académicos para cerrar esas tareas.

## Continuación del equipo

Los cambios en modelos, contratos compartidos, `pyproject.toml` o `uv.lock` se coordinan antes de implementarlos.

## Documentación

- [Contexto y alcance](docs/contexto.md)
- [Arquitectura](docs/arquitectura.md)
- [Modelo de datos](docs/modelo-datos.md)
- [Contratos compartidos](docs/contratos.md)
- [Instrucciones para el equipo](docs/instrucciones-equipo.md)
- [Flujo de trabajo](docs/flujo-trabajo.md)
- [Decisiones pendientes](docs/decisiones-pendientes.md)
- [Verificación de la etapa 5 del domingo](docs/verificacion-etapa-5-2026-10-11.md)
- [Infraestructura Docker y Ollama](docs/infraestructura-jean.md)
- [Propuesta de integración entre IA y planificaciones](docs/integracion-ia-planificaciones-2026-10-14.md)
- [Verificación del flujo integrado preparada por Jean](docs/verificacion-flujo-integrado-jean-2026-10-14.md)
- [Alcance de la validación técnica final del viernes](docs/validacion-final-2026-10-16.md)
