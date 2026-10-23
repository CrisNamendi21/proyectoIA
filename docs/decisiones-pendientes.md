# Decisiones pendientes

Este registro requiere acuerdos explícitos del equipo. Las propuestas técnicas no equivalen a requisitos oficiales.

## Pendientes activos

| Prioridad | Decisión por confirmar | Quién debe coordinarla | Motivo |
| --- | --- | --- | --- |
| Media | Si “sección” será catálogo, columna, campo flexible o quedará fuera del MVP. | Equipo y colegio | Grado y sección son conceptos distintos. |
| Media | Ficha oficial y campos pedagógicos obligatorios. | Colegio y equipo | Las fotografías son referencias, no la especificación final. |
| Media | Política de eliminación entre entidades. | Equipo | Alembic ya gestiona la evolución del esquema; todavía debe decidirse el comportamiento de borrado y cascadas. |

## Decisiones cerradas por Cris para el MVP — 19 de octubre de 2026

Alejandra no estaba disponible durante este cierre. Estas decisiones permiten continuar con un contrato comprobable del MVP, pero no se atribuyen a Alejandra ni sustituyen la futura revisión del equipo o una ficha oficial del colegio.

- `Planning.content` conserva el objeto completo `TeachingPlanDraft` con `schema_version=1`; los IDs curriculares se almacenan en las columnas relacionales existentes.
- La creación y la edición rechazan contenido incompleto, versiones desconocidas, campos adicionales y referencias cuyos nombres no coincidan con el borrador.
- El docente puede editar el borrador antes de guardarlo y mediante `PATCH`; el servidor valida el estado completo antes del commit.
- Los catálogos son de solo lectura, pero requieren una sesión válida y una cuenta activa.
- `POST /generation` mantiene el contrato de errores implementado y no persiste automáticamente su respuesta.
- El MVP conserva la cookie firmada de ocho horas sin revocación individual en servidor. La revocación, la protección CSRF, HTTPS y la cookie `Secure` son requisitos antes de una puesta en producción real.
- El catálogo aprobado se valida desde un JSON privado versionado por esquema, registra una huella SHA-256 y solo se aplica con `--apply`. Las cuentas se crean una a una y su contraseña inicial exige 15 caracteres. Ninguno de estos mecanismos implica que los datos reales ya hayan sido entregados.
- Cris aprobó y cargó para el MVP una selección interna de Matemática de quinto grado y tres cuentas técnicas. Los archivos privados no se versionan y una sustitución institucional futura queda fuera del alcance actual.

## Propuesta provisional de autenticación — 11 de octubre de 2026

**Responsable de la propuesta:** Cris. **Estado de las decisiones de esta sección:** propuestas provisionales, pendientes de revisión por Jean y Alejandra; implementarlas parcialmente no las convierte en contratos aprobados. Como hoy no están disponibles, Cris avanza en `Cris-develop` con estas hipótesis y deja los puntos compartidos identificados para su revisión posterior.

| Decisión | Propuesta para el trabajo de Cris | Revisión pendiente |
| --- | --- | --- |
| Identificador de acceso | Usar `User.username`, ya único y limitado a 50 caracteres. Quitar espacios al inicio y al final, exigir un valor no vacío y tratar las mayúsculas y minúsculas como distintas. | Equipo: confirmar la regla antes de cargar cuentas. |
| Hash de contraseñas | Usar Argon2id mediante `pwdlib[argon2]`. Guardar solo el resultado en `User.password_hash`; nunca una contraseña ni un hash fijo de ejemplo en Git. | Cris incorporó la dependencia el 11 de octubre por la ausencia de Jean; Jean debe revisar `pyproject.toml` y `uv.lock` después. |
| Cuentas precreadas | Cris implementó `uv run python -m app.db.seed_users <username>`: una cuenta por ejecución, contraseña solicitada y confirmada sin mostrarse. El nombre se recorta y debe tener entre 1 y 50 caracteres; conserva mayúsculas y minúsculas. El comando omite usuarios existentes y guarda solo el hash de los nuevos, sin ejecutarse al importar modelos ni al iniciar la API. La doble ejecución se comprobó en PostgreSQL con cuentas ficticias y una base desechable: no cambió el número de cuentas ni los valores previos. | Equipo: revisar el formato provisional, decidir quién entregará las cuentas reales por un canal privado y confirmar si se cargarán cuentas inactivas. La prueba de una cuenta inactiva fue solo técnica; no representa una decisión de cargarlas. |
| Sesión e identidad | Se implementó `SessionMiddleware` de Starlette con cookie firmada `HttpOnly`, `SameSite=Lax` y vigencia de 8 horas. La sesión guarda solo `User.id`. `SESSION_SECRET_KEY` es obligatoria, de al menos 32 caracteres y queda fuera de Git; `SESSION_COOKIE_SECURE=true` activa `Secure` bajo HTTPS. | Equipo: aprobar duración, uso de cookie y requisitos de despliegue. Jean: revisar los nombres de variables y sus ejemplos en `.env.example`. |
| Usuario autenticado | `get_current_user` en `app/api/deps.py` depende de `get_db_session()`. En cada petición obtiene el `User` por el ID de sesión y exige `is_active`; generación y planificaciones rechazan sesión ausente, inválida o cuenta desactivada con `401`. | Equipo: confirmar definitivamente este contrato para los módulos integrados. |
| Acceso HTTP del domingo | `POST /auth/login` está registrado en `main.py` con JSON validado por `LoginRequest` (`username`, `password`) y respuesta `LoginResponse` (`id`, `username`). Busca `User.username`, verifica el hash, guarda solo el ID en la sesión y responde `401` genérico si las credenciales fallan o la cuenta está inactiva; un cuerpo inválido recibe `422`. No devuelve el hash ni revela si existe el usuario. La cookie y la recuperación de identidad en la siguiente petición se comprobaron con datos ficticios y PostgreSQL aislado. | Equipo: confirmar ruta, esquemas, errores y formato de identidad antes de tratarlos como contrato compartido. |
| Dependencias nuevas | `pwdlib[argon2]` para hashing e `itsdangerous` para `SessionMiddleware` ya se añadieron con `uv add`; `pyproject.toml` y `uv.lock` siguen siendo las únicas fuentes de dependencias. | Jean: revisar ambas incorporaciones y coordinar cualquier dependencia posterior. |

La cookie firmada permite leer su contenido, aunque no modificarlo sin la clave; por eso solo contiene el ID. El logout implementado borra la cookie del cliente, pero no invalida una copia obtenida antes: si el equipo requiere revocación inmediata en el servidor, habrá que elegir otro mecanismo. Los endpoints que escriben datos también requieren revisar la protección frente a solicitudes entre sitios al usar cookies.

**Avance al miércoles 14:** `POST /auth/logout` y `GET /auth/me` están implementados; generación y planificaciones usan `get_current_user`, y sus routers están registrados en `main.py`. La suite comprueba el cierre de sesión, la identidad posterior, las rutas protegidas y la sanitización de errores de base de datos. El 19 de octubre Cris aceptó para el MVP la ausencia de revocación individual y fijó la revocación en servidor y los controles CSRF como requisitos previos a producción.

**Revisión de integración de Cris — 14 de octubre:** Cris confirmó `POST /generation` como ruta definitiva del MVP y aceptó el mecanismo de sesión actual para integrar generación y planes. La propuesta inicial de catálogos públicos y el formato pedagógico provisional fueron reemplazados por las decisiones de Cris del 19 de octubre. Las reglas vigentes y sus estados están en [contratos compartidos](contratos.md).

**Actualización de Alejandra — 15 de octubre:** `PATCH /plans/{plan_id}` ya está implementado e integrado con control de propietario, actualización parcial, validación del estado final y rollback. Sus pruebas confirmaron que el JSON completo de `TeachingPlanDraft` podía preservarse al editar. El 19 de octubre Cris fijó para el MVP la versión 1, las reglas de coherencia y la autenticación de catálogos; esta decisión no se atribuye a Alejandra.

**Cierre de la etapa 5:** la [verificación reproducible](verificacion-etapa-5-2026-10-11.md) cubrió carga, acceso correcto y rechazado, identidad posterior y persistencia de hashes en PostgreSQL. La credencial local de PostgreSQL que apareció en el historial fue rotada y continúa rechazada. El 23 de octubre se decidió [conservar el historial](resolucion-credencial-historica-2026-10-23.md) después de comprobar que ningún secreto activo está versionado; no se requiere `force-push` ni reinicializar clones.

Referencias técnicas para evaluar la propuesta: [hashing con Argon2 en FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) y [sesiones por cookie en Starlette](https://www.starlette.io/middleware/).

## Decisiones cerradas el 10 de octubre

- Python 3.12 fijado mediante `.python-version`.
- `uv`, `pyproject.toml` y `uv.lock` como fuentes oficiales del entorno.
- SQLAlchemy 2 síncrono con Psycopg 3.
- PostgreSQL ejecutado en Docker y configurado mediante `DATABASE_URL`.
- Una sesión independiente por petición.
- Cinco modelos compartidos con nombres de tabla plurales en `snake_case`.
- IDs enteros, relaciones explícitas, claves foráneas y fechas UTC.
- JSONB para el contenido pedagógico flexible de `Planning`.
- `init_db()` como inicialización explícita durante esta etapa, sin Alembic.

## Decisiones técnicas cerradas el 14 de octubre

- Las pruebas integradas usan PostgreSQL real y una base desechable con UUID por caso; nunca vacían ni reutilizan la base de desarrollo.
- El runner verifica el catálogo antes y después de la suite y falla si deja bases temporales nuevas.
- Ollama se simula en la regresión principal; una inferencia real se ejecuta por separado y de forma explícita cuando el entorno dispone del modelo.

## Verificaciones técnicas cerradas después del 14 de octubre

- Jean reprodujo el proyecto desde un clon HTTPS limpio con configuración temporal, build Docker sin caché, PostgreSQL aislado y Ollama real.
- El flujo HTTP real del backend Docker completó autenticación, catálogos, una generación con `qwen2.5:3b`, guardado JSONB, propiedad e identidad posterior.
- Cris integró la prueba PostgreSQL de edición de Alejandra y el cierre de infraestructura de Jean en `Cris-develop`.
- Cris reprodujo después el flujo en su propio equipo: Ollama 0.40.9 y `qwen2.5:3b` fueron accesibles desde el backend Docker; una generación real validada, guardada y consultada terminó en 62.56 segundos sin bases temporales residuales.

## Diferencia de redacción resuelta

El plan menciona como contingencia que “FastAPI + PostgreSQL funcionen localmente”. Para este proyecto significa FastAPI ejecutado en el equipo de desarrollo y PostgreSQL dentro de Docker; PostgreSQL no se instala directamente en Windows. Si FastAPI se incorpora a Compose, `DATABASE_URL` usará `alfa-db` como host.

## Fuentes aún no disponibles

No se han proporcionado el documento de requerimientos funcionales, las entrevistas ni una ficha oficial validada. No se tomarán decisiones académicas definitivas a partir de las fotografías.
