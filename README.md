# Colegio Alfa

Backend universitario para apoyar a docentes en la creación, revisión, guardado y consulta de planificaciones didácticas. El MVP se desarrollará del **10 al 16 de octubre de 2026**.

## Estado al 22 de octubre de 2026

La base técnica y los módulos principales están integrados en `Cris-develop`:

- aplicación FastAPI con salud, autenticación, catálogos, generación y planificaciones;
- configuración mediante `DATABASE_URL`;
- SQLAlchemy 2 síncrono con Psycopg 3;
- una sesión de base de datos por petición;
- modelos `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`;
- esquema versionado y actualizado con Alembic mediante `init_db()` o `alembic upgrade head`;
- dependencias administradas con `uv`, `pyproject.toml` y `uv.lock`;
- sesión por cookie firmada, consulta de identidad y cierre de sesión;
- rutas de generación y planificaciones protegidas con `get_current_user`;
- edición parcial de planificaciones con control de propietario y validación de referencias;
- respuestas controladas para fallos de PostgreSQL y Ollama.
- flujo autenticación → catálogos → generación → revisión simulada → guardado → historial comprobado con PostgreSQL desechable.
- arranque desde clon limpio y flujo HTTP real del backend Docker hacia Ollama verificados por Jean.

Cris confirmó para el MVP la ruta `/generation`, la sesión actual, `TeachingPlanDraft` versión 1 y catálogos protegidos por sesión. Las planificaciones se pueden guardar, listar, consultar y editar mediante `PATCH /plans/{plan_id}`. El entorno local ya contiene un catálogo interno aprobado por Cris y tres cuentas técnicas; sus archivos y credenciales permanecen fuera de Git.

El alcance técnico del viernes está cerrado. Jean ya comprobó una inferencia real con `qwen2.5:3b` desde un clon limpio y Cris integró esa evidencia; reproducirla en el equipo de Cris continúa como verificación local. El merge final hacia `main` y los acuerdos pendientes del equipo están enumerados en [pendientes posteriores al cierre](docs/pendientes-posteriores-al-cierre.md).

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

Crea un archivo local `.env` en la raíz a partir de `.env.example`. Este archivo está ignorado por Git. Conserva todos los nombres de variables y reemplaza únicamente los marcadores de contraseña PostgreSQL y clave de sesión por valores privados:

```powershell
if (Test-Path .env) { throw ".env ya existe; revísalo sin sobrescribirlo." }
Copy-Item .env.example .env
```

En la configuración de Compose, `DATABASE_URL` usa `alfa-db` como host. `SESSION_SECRET_KEY` es obligatoria y debe tener al menos 32 caracteres; `SESSION_COOKIE_SECURE` debe ser `true` al servir la API mediante HTTPS. No versiones `.env` ni compartas su contenido.

La ejecución nativa de FastAPI en Windows necesita cambiar el host de PostgreSQL a `localhost` únicamente para ese proceso. La [guía de infraestructura](docs/infraestructura-jean.md#variables-reales) contiene el procedimiento que reutiliza la contraseña en memoria sin imprimirla ni guardarla en el historial de la terminal.

## Actualizar el esquema

Con los servicios de Compose disponibles, ejecuta:

```powershell
docker compose exec -T backend python -m app.db.init_db
```

El comando aplica todas las revisiones Alembic pendientes hasta `head`. Una base nueva se crea desde la revisión inicial; una base existente conserva sus datos. El procedimiento de creación y revisión está en [migraciones](docs/migraciones.md).

Para crear una cuenta docente sin guardar la contraseña en archivos o en el historial de la terminal:

```powershell
docker compose exec backend python -m app.db.seed_users <nombre_de_usuario>
```

El comando solicita y confirma la contraseña de forma interactiva. Si la cuenta ya existe, no modifica sus datos.
La contraseña inicial debe tener al menos 15 caracteres. El procedimiento completo para cuentas y catálogos aprobados está en [carga controlada de datos oficiales](docs/carga-datos-oficiales.md).

## Iniciar la API

```powershell
docker compose up -d --build
```

Comprueba la ruta de salud:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

La respuesta esperada es `{"status":"ok"}`. `POST /auth/login` establece la sesión, `GET /auth/me` devuelve la identidad pública y `POST /auth/logout` elimina la cookie. Las rutas `/generation` y `/plans` requieren una sesión válida; `PATCH /plans/{plan_id}` permite editar parcialmente solo una planificación del docente autenticado. El contrato HTTP disponible puede consultarse en `http://127.0.0.1:8000/docs`.

## Comprobar PostgreSQL

```powershell
docker compose exec -T backend python -c "from sqlalchemy import text; from app.db.session import engine; connection = engine.connect(); print(connection.execute(text('SELECT 1')).scalar_one()); connection.close(); engine.dispose()"
```

La salida esperada es `1`. La construcción de la imagen, el arranque de ambos servicios, la conexión y la existencia de las cinco tablas se comprobaron nuevamente durante la validación final.

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

La carga interna del catálogo y las cuentas técnicas del MVP está registrada sin publicar credenciales. Una sustitución posterior por datos institucionales deberá conservar el mismo procedimiento controlado.

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
- [Reproducibilidad desde clon limpio y flujo Docker real](docs/reproducibilidad-clon-limpio-jean-2026-10-15.md)
- [Alcance de la validación técnica final del viernes](docs/validacion-final-2026-10-16.md)
- [Pendientes posteriores al cierre del viernes](docs/pendientes-posteriores-al-cierre.md)
- [Carga controlada de datos oficiales](docs/carga-datos-oficiales.md)
- [Registro de carga de datos del MVP](docs/registro-carga-datos-mvp-2026-10-22.md)
- [Migraciones y revisión de cambios de esquema](docs/migraciones.md)
