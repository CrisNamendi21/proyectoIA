# Auditoría y preparación de integración de Jean

Fecha: 13 de octubre de 2026 (America/Managua). Repositorio real: `C:\Users\DELL\Desktop\proyectoIA`.
Este informe registra hechos comprobados y propuestas pendientes; no modifica los contratos compartidos.

## A. Git y ramas al inicio de la auditoría

Se ejecutó `git fetch origin` correctamente. El remoto es `https://github.com/CrisNamendi21/proyectoIA.git`.
La rama activa sigue siendo `feature/ai-infra-jean`. Antes de trabajar, el árbol estaba limpio: ningún cambio local ni archivo sin seguimiento.

| Referencia | Commit comprobado | Observación |
| --- | --- | --- |
| `HEAD` y `origin/feature/ai-infra-jean` | `ea32cee` | Local y remoto coinciden; no hay commits propios sin publicar. |
| `origin/Cris-develop` | `91e5ba1` | Ya integró los tres commits de Jean mediante merge. |
| `origin/Alejandra-develop` | `38ac062` | Tiene filtros y pruebas de catálogos posteriores a lo integrado por Cris. |
| `origin/main` | `3250eec` | No contiene todavía los tres commits de Jean. |
| `main` local | `1762ea2` | Está 11 commits detrás de `origin/main`; no se actualizó ni cambió de rama. |

`git merge-base HEAD origin/Cris-develop` devuelve `ea32cee` completo.
`git rev-list --left-right --count HEAD...origin/Cris-develop` devuelve `0 4`:
la rama de Jean es antecesora de la integración y quedó cuatro commits detrás.
`git diff origin/Cris-develop...HEAD` estaba vacío antes de las modificaciones de esta sesión.
Por tanto, un PR de la rama tal como estaba al inicio no aportaría código nuevo.

Commits alcanzables desde Cris que faltan en HEAD:

- `3250eec`: merge anterior hacia main incorporado en la historia.
- `b8508c8`: esquemas y router de catálogos de Alejandra.
- `1bf29e9`: merge de esos catálogos por Cris.
- `91e5ba1`: merge de la infraestructura y servicio IA de Jean.

El contenido diferente entre HEAD y Cris se limita a `app/api/catalogs.py` y `app/schemas/catalogs.py`, ausentes en la rama local.
No hubo cambios nuevos de Cris en autenticación, dependencias, configuración ni `main.py` respecto a la base local.
El router de catálogos integrado tampoco está registrado en `main.py` de Cris.
El commit `38ac062` de Alejandra aún no es alcanzable desde Cris: agrega filtros y `tests/test_catalogs.py`.
Su rama no contiene el núcleo actualizado de autenticación ni IA; no debe usarse como base para generación.

### Aportaciones históricas de Jean

| Commit | Archivos y contenido | Publicación |
| --- | --- | --- |
| `9b13085` | `.dockerignore`, `.env.example`, `Dockerfile`, `compose.yaml` | En la rama remota de Jean y en Cris. |
| `7b41d71` | Los seis módulos de `app/services/ai/` y `tests/test_ai_service.py`, `tests/test_ollama_client.py` | En la rama remota de Jean y en Cris. |
| `ea32cee` | Timeout predeterminado del servicio, variable de ejemplo y prueba del valor predeterminado | En la rama remota de Jean y en Cris. |

Estos commits tienen autor Jean y no modificaron archivos del núcleo de Cris ni módulos de Alejandra.
El mensaje de `ea32cee` menciona verificación de generación, pero su diff no agrega una prueba automatizada de inferencia real ni un registro de sus 64.13 segundos históricos.
La prueba real de esta sesión se informa por separado.

No hay conflictos actuales: no hay una operación de merge/rebase pendiente y HEAD es antecesor de Cris.
Los archivos nuevos/modificados aquí no se superponen con los cambios que faltan desde Cris; se espera integración sin conflicto textual con ese snapshot.
No se ejecutó una fusión para comprobarlo. Antes de integrar debe repetirse fetch y revisar cambios posteriores.
Una comparación directa de árboles puede mostrar los catálogos como ausentes; eso no es el diff de tres puntos de un PR.

### Secretos

`.env` está ignorado y no está seguido; `git log --all -- .env` no devolvió commits.
`.dockerignore` excluye `.env` y `.env.*`, permitiendo solo el ejemplo.
No se imprimieron credenciales locales ni se copiaron al informe.
Se detectaron candidatos a credenciales en URLs PostgreSQL de documentación histórica, incluidos `b148817:docs/contratos.md:10` y `3250eec:README.md:41`.
Esto coincide con el pendiente ya registrado por Cris. No procede reescribir historia automáticamente.
Una comparación privada no encontró la contraseña actual de `POSTGRES_PASSWORD` del `.env` en el documento de `b148817`; no demuestra la rotación de todas las credenciales ni la seguridad de otras instalaciones.
Cris y Jean deben confirmar rotación y no reutilización de los valores históricos.
`.gitignore` solo cubre el nombre exacto `.env`: hay que evitar añadir manualmente copias de credenciales con otros nombres.

## B. Qué está implementado

Infraestructura: imagen Python 3.12 con uv, instalación desde lock sin dependencias dev, Uvicorn, PostgreSQL 16 en Compose,
volumen persistente y dependencia del backend sobre el healthcheck de PostgreSQL.
Las variables y nombres corresponden al contrato conocido; las tablas se crean con el comando explícito de Cris, no al arrancar Compose.
Las imágenes de Python y PostgreSQL usan etiquetas actualizables, sin digest: el lock fija Python packages, pero no garantiza una imagen binaria idéntica en el futuro.

IA: cliente urllib para `POST /api/generate`, `stream=false`, `format=json`, modelo configurable y validación de los dos objetos JSON.
El prompt incorpora el contexto, pide español y una propuesta editable sin datos personales.
`AIPlanningService` coordina prompt, cliente y validación Pydantic de `TeachingPlanDraft`.
No escribe en PostgreSQL. Los esquemas internos siguen siendo provisionales.

No existían `app/api/generation.py`, un registro de generación en `main.py`, operaciones de planes ni un contrato aprobado de `Planning.content`.
No existe logout ni `/me` en el código local o en el snapshot de Cris inspeccionado.
README, arquitectura, instrucciones y contratos siguen describiendo infraestructura/IA como pendientes pese a estar integradas; corresponde coordinar su actualización.

## C. Hallazgos y correcciones mínimas

1. **Configuración nativa incorrecta:** `from_env()` solo usaba `os.getenv`. Se comprobó que las tres variables Ollama estaban en `.env` y no en el proceso.
   Pydantic Settings del núcleo ignora esas claves, por lo que no las exporta. Ahora una configuración propia del módulo IA carga `.env` y respeta la prioridad del entorno.
2. **Timeout inválido:** antes se aceptaban cero, negativos, NaN e infinito; el parseo inválido se ocultaba usando 120.
   Ahora se exige un valor positivo y finito tanto en configuración como en el cliente/override. La configuración inválida responde 503 en el router sin revelar valores.
   El default del cliente directo era 30 mientras el servicio usaba 120: ambos quedan en 120 segundos.
3. **Fallos HTTP sin traducir:** se agregaron traducciones de desconexión, lectura HTTP incompleta y UTF-8 inválido.
   Se conserva la clasificación existente de HTTPError como indisponibilidad. Las respuestas del router contienen mensajes genéricos.
4. **Endpoint pendiente:** se agregó una fábrica de router autenticado y síncrono. La ruta es un argumento obligatorio porque no está acordada.
   FastAPI ejecuta la inferencia en su pool de hilos. La prueba comprobó que el hilo de inferencia difiere del event loop.

No se añadió una segunda implementación del servicio ni una autenticación alternativa.
No se modificaron modelos, sesiones, contratos aprobados, `main.py`, dependencias o archivos de Alejandra.

Límites pendientes del contrato pedagógico: Pydantic valida estructura, rangos y campos obligatorios, pero no garantiza cobertura de las tres etapas,
suma de minutos ni igualdad del grado/asignatura/contenido con la entrada. El prompt lo solicita; no equivale a una validación de dominio.
Las listas de recursos/materiales/criterios no limitan la longitud individual de cada cadena. Debe acordarse qué reglas son obligatorias antes de endurecer el contrato.
Los textos curriculares enviados por el cliente no se cotejan con IDs de catálogo, y el cliente puede solicitar otro modelo.
Si se conserva `model` en el contrato HTTP, el equipo debe decidir qué modelos permite.
La cookie y la protección frente a solicitudes entre sitios siguen pendientes en la documentación de Cris; generación consume recursos aunque no persista planes.
El timeout de urllib controla operaciones de socket; no es una garantía estricta de duración total de toda la petición.

Para Windows nativo usar `OLLAMA_BASE_URL=http://localhost:11434`; para el backend en Docker, `http://host.docker.internal:11434`.
Análogamente, `DATABASE_URL` necesita `localhost` desde Windows y `alfa-db` desde Compose.
El ejemplo actual es para Compose; copiarlo sin ajustar hosts no reproduce la ejecución nativa.
PostgreSQL y API publican puertos en las interfaces del host; su exposición fuera del equipo requiere revisar credenciales y configuración de red.

## D. Trabajo y verificación de la primera pasada

Archivos modificados:

- `app/services/ai/ai_service.py`
- `app/services/ai/ollama_client.py`
- `tests/test_ai_service.py`
- `tests/test_ollama_client.py`

Archivos creados:

- `app/api/generation.py`
- `tests/test_generation.py`
- Este informe de Jean, sin alterar los documentos de contratos compartidos.

No se crearon commits, no se hizo push, no se abrió PR ni se ejecutó merge/rebase/reset/cambio de rama.
Los cambios nuevos quedan locales y sin staging para revisión.

| Comando/comprobación | Resultado observado |
| --- | --- |
| `uv run python --version` | Python 3.12.2 |
| `uv run pytest -q` antes de editar | 21 passed, 3 skipped, 1 warning |
| `uv run pytest -q tests/test_ollama_client.py tests/test_ai_service.py tests/test_generation.py` | 46 passed, 1 warning |
| `uv run pytest -q` después de implementar | 57 passed, 3 skipped, 1 warning |
| `uv lock --check` | Correcto |
| `uv sync --locked` | Correcto; no cambios de dependencias |
| `docker compose config --quiet` | Exit code 0 |
| `git diff --check` | Sin errores de whitespace; avisos de conversión LF/CRLF de Git |
| Docker en ejecución | No verificable: falta el pipe del motor Docker Desktop Linux |
| `GET http://localhost:11434/api/tags` | Disponible; listado con `qwen2.5:3b` |
| Una generación real con `AIPlanningService.generate_plan()` y `qwen2.5:3b` | JSON validado en 105.70 segundos; tres actividades, etapas inicio/desarrollo/cierre y suma de 45 minutos |

La prueba real usó contexto ficticio de Ciencias Naturales de octavo grado sobre fotosíntesis y flujo de energía.
Se sustituyó el host del cliente en memoria por `localhost:11434` para ejecutar desde Windows; no se modificó `.env`.
No fue una llamada al endpoint HTTP ni una inferencia desde Docker. Se hizo una sola generación.
El tiempo observado fue mayor que los 64.13 segundos históricos y quedó dentro del timeout de 120; no garantiza ese tiempo en otras ejecuciones.

La advertencia real es `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
Se inspeccionó el código instalado de Starlette: primero intenta importar `httpx2`, después permite `httpx` y emite la advertencia.
Las pruebas pasan con las dependencias fijadas. Cualquier migración del grupo dev debe coordinarse con Cris; no se agregó una dependencia de producción.

Las tres omisiones son `test_auth_flow.py`, `test_auth_session.py` y `test_seed_users.py`, sujetas a `COLEGIO_ALFA_TEST_POSTGRES=1`.
Sus fixtures crean bases con nombres únicos y las eliminan al terminar; no se habilitaron en la primera pasada porque Docker no estaba disponible.
En esa primera pasada no se comprobó construcción de imagen, health real del backend, SQL SELECT 1 ni conectividad Docker→Ollama.
Los resultados históricos de esas pruebas no se presentan como verificación actual.

Las pruebas nuevas cubren lectura de dotenv/prioridad del entorno, timeout inválido, URL HTTP válida,
payload del cliente y overrides, errores de transporte, JSON no objeto, autenticación mediante el login y cookie reales de Cris con BD simulada,
usuarios inactivos/eliminados, validación de solicitud/salida, respuestas 502/503/504 y OpenAPI.
No se midió cobertura porcentual; una cuenta de pruebas no acredita exhaustividad.

### Continuación: verificación real después de iniciar Docker Desktop

Se continuó desde los cambios existentes sin repetir la implementación ni la inferencia real de Ollama.
La rama permanece en `feature/ai-infra-jean`; los cambios locales anteriores se conservaron.
En esta continuación solo se editó este informe. No se modificaron archivos de Cris/Alejandra, `.env`, Compose, código ni dependencias.

Antes de arrancar se inspeccionaron contenedores, volúmenes y montaje de PostgreSQL:
existían `proyectoia-alfa-db-1` y `proyectoia-backend-1`, ambos detenidos con salida 0,
y el volumen `proyectoia_alfa-db-data`, montado en `/var/lib/postgresql/data`.
Se ejecutó `docker compose up -d --build`: reconstruyó la imagen del backend, recreó ese contenedor y arrancó PostgreSQL
usando el volumen existente. La capa de instalación de dependencias se reutilizó desde la caché de build.
El nombre y la fecha de creación del volumen coinciden antes/después. No se eliminaron contenedores manualmente, volúmenes ni datos persistentes;
no se ejecutó `docker compose down -v` ni inicialización/seed sobre la base de desarrollo.

| Comprobación de la continuación | Resultado real |
| --- | --- |
| `docker info --format '{{.ServerVersion}}'` | Engine disponible, versión 29.8.2 |
| `docker compose config --quiet` | Correcto, sin errores |
| `docker compose up -d --build` | Exit code 0; imagen construida y servicios iniciados |
| Estado final de `alfa-db` | Running / healthy |
| Estado final del backend | Running; Uvicorn completó el startup |
| `GET http://127.0.0.1:8000/health` | HTTP 200, `{"status":"ok"}` |
| `SELECT 1` mediante SQLAlchemy desde `backend` | Devuelve 1; conexión real backend→PostgreSQL |
| `GET /api/tags` desde `backend` usando la configuración IA | HTTP 200 vía `host.docker.internal`; modelo configurado `qwen2.5:3b` disponible |
| Tres pruebas PostgreSQL antes omitidas, habilitadas | 3 passed, 1 warning, en 3.45 segundos |
| Suite completa con PostgreSQL habilitado | 60 passed, 0 skipped, 1 warning, en 7.60 segundos |
| Catálogo de bases temporales antes/después | 0 antes y 0 después; ningún residuo nuevo |

La consulta `SELECT 1` fue la comprobación de lectura solicitada hacia la base configurada del backend.
Las pruebas no usaron esa base: se construyó una URL administrativa en memoria con las credenciales locales,
host `127.0.0.1`, puerto publicado `5432` y **base `postgres`**, y se verificó `SELECT current_database()`.
Esa URL se pasó exclusivamente al entorno de los subprocesos pytest como `DATABASE_URL`, junto a `COLEGIO_ALFA_TEST_POSTGRES=1`.
No se escribió la URL con credenciales al informe ni se modificó `.env` o el entorno permanente de Windows.

Los tests ejecutados expresamente fueron:

- `tests/test_auth_flow.py::test_seed_login_rejection_and_later_identity`
- `tests/test_auth_session.py::test_login_and_next_request_with_postgresql`
- `tests/test_seed_users.py::test_seed_twice_preserves_active_and_inactive_accounts`

Se revisaron sus implementaciones antes de habilitarlos. Cada uno crea una base
`colegio_alfa_{flow|auth|seed}_test_<uuid>`, usa allí sus tablas/cuentas ficticias y elimina únicamente esa base en `finally`.
Después se ejecutó la suite completa con el mismo entorno administrativo aislado.
Ambas ejecuciones devolvieron exit code 0; una consulta al catálogo `pg_database` desde `postgres` confirmó la limpieza.
No se ejecutaron inserts, updates, seeds ni cambios de esquema en `colegio_alfa_db` para estas pruebas.

Comandos pytest ejecutados (con el entorno de prueba descrito):

```powershell
uv run pytest -q tests/test_auth_flow.py::test_seed_login_rejection_and_later_identity tests/test_auth_session.py::test_login_and_next_request_with_postgresql tests/test_seed_users.py::test_seed_twice_preserves_active_and_inactive_accounts
uv run pytest -q
```

Para repetir sin cambiar `.env`, preparar el entorno solo del subproceso:

```powershell
@'
import os, subprocess
from sqlalchemy.engine import make_url
from app.core.config import get_settings
url = make_url(get_settings().database_url).set(
    host="127.0.0.1", port=5432, database="postgres"
)
env = os.environ.copy()
env["DATABASE_URL"] = url.render_as_string(hide_password=False)
env["COLEGIO_ALFA_TEST_POSTGRES"] = "1"
raise SystemExit(subprocess.run(["uv", "run", "pytest", "-q"], env=env).returncode)
'@ | uv run python -
```

La advertencia de Starlette/httpx sigue siendo la misma de la primera pasada y no impide la suite.
La comunicación Docker→Ollama ya está comprobada por HTTP; no se repitió generación real desde el contenedor.
El endpoint de generación aún no está registrado en la aplicación servida: el health exitoso no significa que esa ruta pública ya exista.

## E. Preparación del PR y acuerdos

**Destino correcto: `Cris-develop`.** Lo confirman `docs/flujo-trabajo.md`, AGENTS.md y los merges reales `1bf29e9`/`91e5ba1`.
`main` es el destino posterior de una integración revisada del equipo.

El módulo queda listo para revisión de código con mocks, PostgreSQL real e infraestructura comprobada.
El bloqueo anterior de Docker queda resuelto. No está aprobado como flujo integrado ni como endpoint público definitivo.
La rama necesita sincronizarse con la integración según el flujo del equipo; no se realizó esa operación sin consulta.
El PR histórico ya no tiene aportaciones pendientes: los tres commits están integrados. Un próximo PR aportaría los siete archivos de esta sesión,
mediante el commit local preparado tras la revisión final descrita al cierre de este informe.
No debería volver a incluir commits de Cris o Alejandra como aportaciones de Jean.

### Cris

Debe confirmar el contrato HTTP y la identidad existente, elegir la ruta y registrar el router dentro de `create_app()`.
Ejemplo de registro **solo si el equipo aprueba `/generation`**:

```python
from app.api.generation import create_generation_router

# Dentro de create_app(), junto al registro de los otros routers:
app.include_router(create_generation_router("/generation"))
```

La fábrica devuelve `APIRouter`; no se exporta una instancia con ruta definitiva mientras ese acuerdo falte.
Se reutilizan `PlanningGenerationRequest` y `TeachingPlanDraft` existentes, sin crear nuevos formatos.
Las respuestas propuestas/probadas son 200, 401, 422, 502 (salida inválida), 503 (indisponibilidad/configuración) y 504 (timeout).
Cris no necesita cambiar ORM o dependencias para este registro.
También debe registrar catálogos, revisar los avances posteriores de Alejandra y completar los pendientes de autenticación que el equipo apruebe.

### Alejandra con Jean y Cris

Acuerdos necesarios: forma/versionado de `Planning.content`, obligatoriedad de campos pedagógicos,
si generación recibe texto o IDs curriculares, validación de correspondencia y formato de guardado/edición.
Propuesta mínima de adaptación, todavía no aprobada:

- Usar `draft.model_dump(mode="json")` como candidato a contenido después de validación y revisión docente.
- Enviar los IDs curriculares por separado y validarlos contra los catálogos; los nombres generados no son IDs.
- Obtener `user_id` exclusivamente del usuario autenticado al guardar, nunca del cuerpo enviado por el cliente.
- La generación no crea `Planning`; guardado, propiedad, edición e historial corresponden al servicio de planes.

Los esquemas IA son internos bajo `app/services/ai/`; cuando se apruebe un esquema HTTP compartido, coordinar su ubicación en `app/schemas/` sin duplicar modelos.

## F. Próximos pasos en orden

1. **Jean y Cris:** revisar estos siete archivos y acordar la actualización de la rama desde `origin/Cris-develop`; no usar reset ni forzar publicación.
2. **Equipo:** confirmar ruta HTTP, contrato provisional y adaptación a `Planning.content`.
3. **Cris:** registrar generación y catálogos; revisar autenticación/cookies y los avances `38ac062` de Alejandra.
4. **Jean — completado en la continuación:** build, arranque conservando el volumen, health, SELECT 1, comunicación Docker→Ollama,
   tres pruebas PostgreSQL con bases desechables y suite completa: 60 passed, ninguna omitida. Repetir solo si cambios posteriores afectan estas comprobaciones.
5. **Alejandra:** implementar guardado/edición/historial y pruebas de propiedad según el contrato que apruebe el equipo.
6. **Jean:** registrar en un commit local los siete archivos revisados con la suite ya aprobada, y comprobar el diff de tres puntos.
   Publicar ese commit a su rama y abrir PR hacia Cris únicamente después de autorización adicional del usuario.
7. **Equipo:** antes de pasar a main, probar login → catálogo → generación → revisión/edición → guardado → historial,
   acceso ajeno rechazado, fallos de Ollama, persistencia, entorno reproducible y regresión sobre la integración actual.

Descripción sugerida del próximo PR: endpoint de generación configurable y autenticado que reutiliza el servicio IA,
corrección de lectura de `.env` y errores de transporte/timeout, con pruebas de integración FastAPI mediante mocks.
Debe incluir el resultado final de 60 pruebas aprobadas, los comandos para repetirlas y los pendientes de contrato/registro/sincronización,
sin presentar Docker como bloqueo actual ni declarar completo el MVP.

## G. Revisión final y preparación del commit local

El usuario autorizó crear un commit local después de revisar estos siete archivos; no autorizó push, merge, rebase ni PR.
Se hizo otro `git fetch origin`: `origin/Cris-develop` continúa en `91e5ba1` y la rama de Jean sigue en `feature/ai-infra-jean`.
El índice estaba vacío y no aparecieron archivos de otro origen desde las verificaciones anteriores.

Se revisaron los diffs completos, el router, sus pruebas y el informe. Además se cotejaron los siete archivos con los secretos del `.env`
sin mostrar sus valores, y se buscaron URLs con credenciales, tokens habituales y claves privadas: no hubo coincidencias.
Las contraseñas ficticias de tests y las claves de sesión generadas en tiempo de prueba no son credenciales reales.
El informe no contiene passwords, hashes de cuentas reales, claves de sesión ni contenido privado de `.env`.

Alcance exacto del commit autorizado:

- Nuevo: `app/api/generation.py`.
- Modificados: `app/services/ai/ai_service.py`, `app/services/ai/ollama_client.py`.
- Modificados: `tests/test_ai_service.py`, `tests/test_ollama_client.py`.
- Nuevos: `tests/test_generation.py` y este informe.

No se encontraron errores evidentes que bloqueen la revisión de Cris. Las firmas del servicio y los esquemas existentes se conservan,
la autenticación reutiliza `get_current_user` de Cris y no hay persistencia desde generación.
Los cambios deliberados de configuración son la lectura de `.env`, la validación HTTP de la URL y el rechazo explícito de timeouts inválidos.
No se introdujeron dependencias ni se tocaron archivos compartidos. No se aprobó ningún contrato por implementación.
El código no cambió desde la suite final de 60 pruebas aprobadas; solo se actualizó la documentación, por lo que no se repitió la suite ni la inferencia.

Mensaje preparado: `feat(ai): prepare authenticated generation router for integration`.
El hash definitivo se comunica después de crear el commit; puede consultarse con `git log -1 --format=%H`.
El diff de tres puntos hacia Cris debe contener únicamente estos siete archivos; los catálogos ausentes en la rama local
no se eliminan mediante ese PR. Los tres commits históricos de Jean ya pertenecen a Cris.

Los cambios de Cris desde el ancestro común solo agregan catálogos y no se superponen con los archivos de este commit;
no se esperan conflictos textuales con el snapshot revisado. Hay que volver a comprobarlo si avanza el remoto.
Git permite publicar el commit y abrir un PR sin actualizar primero la rama, pero el flujo documentado del equipo
pide sincronizarla con la integración antes del PR. Esa operación queda pendiente de autorización y no debe confundirse con un bloqueo técnico del push.
Después de sincronizar, validar la combinación de módulos según los cambios recibidos.

Conclusión: listo para revisión de Cris; integración definitiva pendiente de sincronización acordada,
aprobación de ruta/contrato HTTP, registro del router por Cris y acuerdo con Alejandra sobre `Planning.content` y vínculos curriculares.
