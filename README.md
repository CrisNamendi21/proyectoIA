# Colegio Alfa

Backend universitario para apoyar a docentes en la creación, revisión, guardado y consulta de planificaciones didácticas. El MVP se desarrollará del **10 al 16 de octubre de 2026**.

## Estado al 11 de octubre de 2026

La base técnica y el acceso mínimo están implementados y verificados:

- aplicación FastAPI con `GET /health` y `POST /auth/login`;
- configuración mediante `DATABASE_URL`;
- SQLAlchemy 2 síncrono con Psycopg 3;
- una sesión de base de datos por petición;
- modelos `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`;
- creación explícita de tablas con `init_db()`;
- dependencias administradas con `uv`, `pyproject.toml` y `uv.lock`;
- sesión por cookie firmada y recuperación de usuario autenticado en una petición posterior.

El contrato de autenticación sigue siendo provisional hasta la revisión del equipo. Catálogos, generación con Ollama y operaciones de planificación todavía no tienen routers funcionales. La infraestructura versionada de Docker queda a cargo de Jean.

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

Sustituye los marcadores por valores locales. `SESSION_SECRET_KEY` es obligatoria; `SESSION_COOKIE_SECURE` debe ser `true` al servir la API mediante HTTPS. No versiones `.env` ni compartas su contenido. Jean debe publicar valores de ejemplo no sensibles en `.env.example` junto con `compose.yaml`.

## Crear las tablas

Con PostgreSQL disponible, ejecuta:

```powershell
uv run python -c "from app.db.init_db import init_db; init_db()"
```

La inicialización usa `create_all()` y no reemplaza una estrategia posterior de migraciones.

## Iniciar la API

```powershell
uv run uvicorn app.main:app --reload
```

Comprueba la ruta de salud:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

La respuesta esperada es `{"status":"ok"}`. `POST /auth/login` recibe JSON con `username` y `password`; si las credenciales son válidas responde con `id` y `username` y establece una cookie de sesión. Responde `401` para credenciales inválidas o cuentas inactivas y `422` para un cuerpo inválido. Puede consultarse el contrato provisional en `http://127.0.0.1:8000/docs`.

## Comprobar PostgreSQL

```powershell
uv run python -c "from sqlalchemy import text; from app.db.session import engine; connection = engine.connect(); print(connection.execute(text('SELECT 1')).scalar_one()); connection.close(); engine.dispose()"
```

La salida esperada es `1`. Este comando, la creación de tablas y el arranque de Uvicorn fueron comprobados el 10 de octubre de 2026.

## Estructura

```text
app/
  main.py               aplicación y registro de routers
  api/                   salud, acceso y dependencia de usuario autenticado
  core/                  configuración y hashing
  db/                   base declarativa, engine, sesiones e inicialización
  models/               cinco entidades SQLAlchemy compartidas
  schemas/auth.py        entrada y salida del acceso
  services/auth.py       búsqueda y verificación de cuentas
docs/                   arquitectura, contratos y coordinación
tests/                  pruebas de hashing, carga, acceso y sesión
```

Los módulos de catálogos, generación y planificaciones se incorporarán durante las siguientes etapas. La dependencia `get_current_user` está preparada, pero su uso por otros routers requiere revisar el contrato con el equipo.

## Continuación del equipo

Jean y Alejandra deben leer [instrucciones de integración](docs/instrucciones-equipo.md) antes de comenzar sus módulos. Cualquier cambio en modelos, contratos compartidos, `pyproject.toml` o `uv.lock` se coordina antes de implementarlo.

## Documentación

- [Contexto y alcance](docs/contexto.md)
- [Arquitectura](docs/arquitectura.md)
- [Modelo de datos](docs/modelo-datos.md)
- [Contratos compartidos](docs/contratos.md)
- [Instrucciones para el equipo](docs/instrucciones-equipo.md)
- [Flujo de trabajo](docs/flujo-trabajo.md)
- [Decisiones pendientes](docs/decisiones-pendientes.md)
- [Verificación de la etapa 5 del domingo](docs/verificacion-etapa-5-2026-10-11.md)
