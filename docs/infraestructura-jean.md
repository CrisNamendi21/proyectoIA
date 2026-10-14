# Infraestructura de Jean: Windows, Docker, PostgreSQL y Ollama

Guía del 14 de octubre de 2026. Responsable: Jean. No cambia contratos compartidos.
Describe los archivos existentes; la prueba definitiva desde un clon limpio se reserva para el viernes 16.
Los resultados actuales y el estado de integración están en [coordinación IA y planificaciones](integracion-ia-planificaciones-2026-10-14.md).

## Requisitos

- Windows 11 con PowerShell y Git.
- uv: seguir su [instalación oficial](https://docs.astral.sh/uv/getting-started/installation/).
- Python 3.12, administrado por uv según `.python-version`.
- Docker Desktop con el motor de contenedores Linux iniciado; PostgreSQL vive en Docker, no se instala en Windows.
- Ollama instalado y abierto en Windows; no se incluye en Compose.
- Conexión a Internet durante la primera descarga de Python, dependencias, imágenes y modelo; puertos locales 8000, 5432 y 11434 disponibles.

Comprobaciones sin iniciar inferencia:

```powershell
git --version
uv --version
docker info --format '{{.ServerVersion}}'
docker compose version
ollama --version
```

## Preparación inicial de un clon nuevo

```powershell
git clone https://github.com/CrisNamendi21/proyectoIA.git
cd proyectoIA
git switch --track origin/Cris-develop
uv python install 3.12
uv sync --locked
uv run python --version
```

Se elige `Cris-develop` para reproducir la integración actual. Una rama de Jean anterior puede tener los mismos servicios IA/Docker,
pero carecer del registro HTTP, logout y planes que Cris añadió después. No cambiar una rama existente con cambios locales para seguir esta guía.
`pyproject.toml` y `uv.lock` son las fuentes oficiales; no usar `requirements.txt` ni actualizar dependencias para arrancar.

### Crear `.env` sin sobrescribir uno existente

Este ejemplo toma `.env.example` y sustituye sus dos marcadores de credenciales por valores aleatorios locales.
La contraseña hexadecimal también evita caracteres que requieran codificación en la URL PostgreSQL.
No ejecutar sobre un entorno que ya tiene `.env` o datos inicializados con otras credenciales.

```powershell
@'
from pathlib import Path
import secrets
target = Path(".env")
if target.exists():
    raise SystemExit(".env ya existe; revisar su configuración sin sobrescribirlo.")
example = Path(".env.example").read_text(encoding="utf-8")
password = secrets.token_hex(24)
session_key = secrets.token_urlsafe(48)
example = example.replace("change-me-local-password", password)
example = example.replace("change-me-please-use-at-least-32-characters", session_key)
target.write_text(example, encoding="utf-8")
print(".env creado; valores privados no mostrados.")
'@ | uv run python -
```

Los valores de `.env.example` son públicos y deben reemplazarse. `.env` está ignorado; no añadir copias de credenciales con otros nombres a Git.
La clave de sesión debe tener al menos 32 caracteres. En un volumen PostgreSQL existente, cambiar `POSTGRES_PASSWORD` en `.env`
no cambia la contraseña ya guardada: coordinar su rotación, conservando datos, antes de cambiar la URL de conexión.

### Variables reales

| Variable | Uso |
| --- | --- |
| `POSTGRES_DB` | Base de desarrollo: `colegio_alfa_db`; la inicialización de la imagen la usa en el primer arranque del volumen. |
| `POSTGRES_USER` | Usuario de desarrollo `equipo_alfa`. |
| `POSTGRES_PASSWORD` | Contraseña privada local; debe coincidir con la URL y con el volumen existente. |
| `POSTGRES_PORT` | Puerto publicado en Windows, por defecto 5432. El puerto interno sigue siendo 5432. |
| `POSTGRES_HOST` | Ejemplo informativo `alfa-db`; el código no lo usa para construir `DATABASE_URL`. |
| `DATABASE_URL` | URL SQLAlchemy con driver `postgresql+psycopg`; host y puerto dependen de dónde corre Python. |
| `SESSION_SECRET_KEY` | Clave privada de firma de cookies. |
| `SESSION_COOKIE_SECURE` | `false` para HTTP local; `true` cuando la API usa HTTPS. |
| `OLLAMA_BASE_URL` | URL del servidor Ollama en Windows. |
| `OLLAMA_MODEL` | `qwen2.5:3b`; puede omitirse `model` en la petición para usarlo. |
| `OLLAMA_TIMEOUT_SECONDS` | 120 por defecto; valor positivo y finito. No garantiza un límite total estricto de la petición. |

FastAPI escucha en `0.0.0.0:8000` dentro de Docker por el comando de `Dockerfile`; no existe una variable `FASTAPI_PORT` en este proyecto.
Compose inyecta `.env` en los contenedores. La ejecución nativa carga `.env` con Pydantic Settings.

| Lugar de ejecución de Python | PostgreSQL en `DATABASE_URL` | Ollama en `OLLAMA_BASE_URL` |
| --- | --- | --- |
| Contenedor backend | `alfa-db:5432` | `http://host.docker.internal:11434` |
| Windows nativo | `localhost:5432` o el puerto publicado configurado | `http://localhost:11434` |

Dentro del backend, `localhost` identifica ese contenedor. Desde Windows, `alfa-db` no es el host de conexión.
Para cambiar a ejecución nativa sin editar `.env`, preparar variables **solo para el proceso**:

```powershell
@'
import os, subprocess
from app.core.config import get_settings
from sqlalchemy.engine import make_url
from dotenv import dotenv_values
values = dotenv_values(".env")
url = make_url(get_settings().database_url).set(
    host="127.0.0.1", port=int(values.get("POSTGRES_PORT") or "5432")
)
env = os.environ.copy()
env["DATABASE_URL"] = url.render_as_string(hide_password=False)
env["OLLAMA_BASE_URL"] = "http://localhost:11434"
raise SystemExit(subprocess.run(
    ["uv", "run", "uvicorn", "app.main:app", "--reload", "--port", "8000"], env=env
).returncode)
'@ | uv run python -
```

Usar un solo backend en el puerto 8000. Si se elige ejecución nativa, levantar solo `docker compose up -d alfa-db`.

### Modelo local

```powershell
ollama pull qwen2.5:3b
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```

La descarga es inicial; repetir `list` o `/api/tags` para comprobar disponibilidad sin generar una propuesta.
No iniciar otro `ollama serve` si la aplicación de Windows ya sirve ese puerto.

## Arranque y comprobaciones

Desde la raíz, con Docker Desktop y Ollama abiertos:

```powershell
docker compose config --quiet
docker compose ps -a
docker volume ls
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
```

Esperado: `alfa-db` healthy, backend running y `{"status":"ok"}`.
La imagen se instala con `uv sync --frozen --no-dev --no-install-project`; las pruebas se ejecutan con uv en Windows, no dentro de esa imagen.
`/health` confirma la aplicación; no comprueba la base ni el modelo por sí solo.

Solo durante la preparación inicial, crear tablas explícitamente con el comando compatible con ambas revisiones del núcleo:

```powershell
docker compose exec -T backend python -c "from app.db.init_db import init_db; init_db()"
```

`create_all()` no borra datos ni migra cambios de esquema. No ejecutarlo como rutina diaria ni usarlo para resolver incompatibilidades de columnas.
Las cuentas se cargan explícitamente, sin contraseñas en la línea de comandos:

```powershell
docker compose exec backend python -m app.db.seed_users nombre_docente
```

Es interactivo: no añadir `-T` al comando de cuenta. No crear cuentas reales de otro integrante durante las comprobaciones.
El catálogo oficial sigue pendiente; no hay un comando de carga curricular acordado.

Conexión real del backend a PostgreSQL, sin escritura:

```powershell
docker compose exec -T backend python -c "from sqlalchemy import text; from app.db.session import engine; connection = engine.connect(); print(connection.execute(text('SELECT 1')).scalar_one()); connection.close(); engine.dispose()"
```

Debe devolver `1`. Comunicación con Ollama usando la configuración del servicio, sin inferencia:

```powershell
@'
import json, urllib.request
from app.services.ai.ai_service import AIPlanningService
service = AIPlanningService.from_env()
with urllib.request.urlopen(service.client.base_url.rstrip("/") + "/api/tags", timeout=10) as response:
    names = [item["name"] for item in json.load(response)["models"]]
    print({"status": response.status, "configured_model_available": service.client.model in names})
'@ | docker compose exec -T backend python -
```

Esperado: status 200 y `configured_model_available=True`.
Consultar `/docs` o `/openapi.json` para ver las rutas de la revisión que realmente se esté ejecutando.
En `Cris-develop` del 14 están registrados `/generation`, `/plans`, catálogos y autenticación; no inferirlo de una imagen anterior.

## Pruebas

Pruebas habituales con mocks, sin habilitar las integraciones PostgreSQL:

```powershell
uv run pytest -q
```

Mantener `COLEGIO_ALFA_TEST_POSTGRES` sin definir o en `0` en esa ejecución. Tres pruebas se omiten intencionalmente cuando no se habilita PostgreSQL.
El número total depende de la revisión: los resultados de Jean y de Cris no son intercambiables.
La advertencia Starlette/httpx es conocida; cualquier cambio de dependencias se coordina con Cris.

### PostgreSQL opcional y desechable

Requiere `alfa-db` running/healthy, credenciales válidas y permiso para crear/eliminar bases temporales.
Los tres tests actuales usan `CREATE DATABASE` con UUID y eliminan **solo sus bases creadas** al finalizar.
No apuntar las pruebas a `colegio_alfa_db`, no usar fixtures que borren tablas de desarrollo y no desactivar sus guardas.
Este comando deja `.env` intacto y conecta la administración a `postgres`:

```powershell
@'
import os, subprocess
from dotenv import dotenv_values
from app.core.config import get_settings
from sqlalchemy.engine import make_url
values = dotenv_values(".env")
url = make_url(get_settings().database_url).set(
    host="127.0.0.1", port=int(values.get("POSTGRES_PORT") or "5432"), database="postgres"
)
env = os.environ.copy()
env["DATABASE_URL"] = url.render_as_string(hide_password=False)
env["COLEGIO_ALFA_TEST_POSTGRES"] = "1"
raise SystemExit(subprocess.run(["uv", "run", "pytest", "-q"], env=env).returncode)
'@ | uv run python -
```

La contraseña pasa en memoria al subproceso, no se muestra ni se incluye en el historial como un valor literal.
Estos tests cubren autenticación/cuentas con PostgreSQL; los de planes de Alejandra usan mocks y todavía no demuestran persistencia real.

## Rutina diaria y parada

Diariamente: abrir Docker Desktop y Ollama, revisar rama/estado, comprobar Compose, ejecutar `docker compose up -d`, comprobar `/health` y `/api/tags`.
Usar `--build` cuando cambie el código o la imagen; la imagen contiene una copia del código y no monta el repositorio en vivo.
No repetir descarga de modelo, creación de `.env`, inicialización de tablas ni carga de cuentas cada día.

```powershell
docker compose stop
```

Detiene servicios conservando contenedores y volumen; posteriormente `docker compose up -d` los arranca.
No borrar volúmenes ni usar `docker compose down -v` para solucionar problemas.

## Fallos frecuentes

| Síntoma | Comprobación y solución mínima |
| --- | --- |
| No existe el pipe de Docker Engine | Abrir Docker Desktop, esperar a que el motor esté listo y repetir `docker info`. |
| Motor activo, pero `/health` no responde | Revisar `docker compose ps -a`; servicios detenidos necesitan `up -d`. Si falla startup, consultar logs localmente sin publicar credenciales. |
| Puerto 8000 o 5432 ocupado | Evitar un segundo backend/contenedor; revisar qué proceso ocupa el puerto antes de cambiar mapeos. |
| PostgreSQL healthy pero error de login SQL | `pg_isready` no valida la contraseña de la aplicación. Revisar que URL y volumen usan la misma credencial; no reinicializar el volumen. |
| Host de PostgreSQL incorrecto | En backend Docker usar `alfa-db:5432`; en Windows usar el puerto publicado de `localhost`. |
| Ollama no disponible | Abrir Ollama, comprobar `/api/tags` en Windows y después desde el backend; revisar el host configurado. |
| Windows alcanza Ollama y el contenedor no | Revisar firewall y dirección de escucha; cambios de `OLLAMA_HOST` en Windows requieren reiniciar Ollama según la [FAQ oficial](https://docs.ollama.com/faq#setting-environment-variables-on-windows). No publicar el puerto a Internet. |
| Modelo no encontrado | Verificar `ollama list`; descargar el nombre exacto `qwen2.5:3b` si falta. |
| Generación tarda o devuelve 504 | Revisar carga del equipo y timeout. Se midieron 105.70 s el martes; no garantiza tiempos futuros. Cambiar timeout local y recrear solo backend si procede, sin repetir inferencias innecesarias. |
| 503 de configuración IA | Revisar URL HTTP/HTTPS y timeout positivo/finito; no instalar otra dependencia para arreglar valores inválidos. |
| 401 en generación/planes | Iniciar sesión y conservar la cookie; no enviar `user_id` para sustituir autenticación. |
| Código o rutas antiguos dentro de Docker | Revisar la rama y reconstruir la imagen correcta; no suponer que fetch actualiza el contenedor. |

No imprimir `docker compose config` sin `--quiet` ni un `docker inspect` completo al compartir diagnósticos: pueden mostrar el entorno privado.

## Bloque propuesto para el README de Cris

README es documentación compartida mantenida por Cris según su historial; no se modificó. Propuesta para añadir a su lista de documentación:

```markdown
- [Infraestructura Docker y Ollama: configuración y pruebas](docs/infraestructura-jean.md)
- [Propuesta de integración IA y planificaciones](docs/integracion-ia-planificaciones-2026-10-14.md)
```

Cris debe comprobar esas referencias después de integrar estos documentos. Los docs antiguos de instrucciones siguen describiendo la base del sábado;
el README remoto ya refleja la integración del miércoles. Esta guía no sustituye `docs/contratos.md`.
