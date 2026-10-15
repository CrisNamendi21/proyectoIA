# Decisiones pendientes

Este registro requiere acuerdos explícitos del equipo. Las propuestas técnicas no equivalen a requisitos oficiales.

## Pendientes activos

| Prioridad | Decisión por confirmar | Quién debe coordinarla | Motivo |
| --- | --- | --- | --- |
| Alta | Verificación del entorno desde un clon limpio con Docker y Ollama activos. | Jean con Cris | `compose.yaml` y `.env.example` ya existen; falta demostrar el arranque completo en otra instalación. |
| Alta | Necesidad de revocación de sesión en servidor y protección adicional frente a solicitudes entre sitios. | Equipo | Cris confirmó para el MVP la cookie firmada y el logout local; una copia previa de la cookie sigue válida hasta expirar. |
| Alta | Contratos todavía no cerrados de los módulos funcionales. | Los tres | Cris confirmó `/generation`, la sesión y las rutas actuales; falta la edición de planes y la conformidad de Alejandra sobre catálogos públicos. |
| Alta | Aprobación compartida de `TeachingPlanDraft` como forma de `Planning.content`, vínculos curriculares y reglas de edición. | Alejandra con Cris y Jean | Cris confirmó su compatibilidad técnica; Alejandra debe aprobar el contrato del módulo de planes. |
| Alta | Contrato de solicitud y respuesta de Ollama, incluidos sus errores. | Jean con Cris y Alejandra | Permite crear mocks compatibles con el guardado. |
| Media | Catálogo curricular real y reglas de grado, asignatura y contenido. | Alejandra con el equipo y el colegio | Define datos iniciales y validaciones del dominio. |
| Media | Datos curriculares y estrategia para cargarlos. | Equipo | Las cuentas tienen carga idempotente; todavía no existe un catálogo oficial que pueda versionarse o cargarse. |
| Media | Si “sección” será catálogo, columna, campo flexible o quedará fuera del MVP. | Equipo y colegio | Grado y sección son conceptos distintos. |
| Media | Ficha oficial y campos pedagógicos obligatorios. | Colegio y equipo | Las fotografías son referencias, no la especificación final. |
| Media | Estrategia de migraciones y política de eliminación entre entidades. | Equipo | `create_all()` sirve para la base inicial, pero no gestiona cambios de esquema. |

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

**Avance al miércoles 14:** `POST /auth/logout` y `GET /auth/me` están implementados; generación y planificaciones usan `get_current_user`, y sus routers están registrados en `main.py`. La suite comprueba el cierre de sesión, la identidad posterior, las rutas protegidas y la sanitización de errores de base de datos. Cris confirmó la cookie y su duración actual para el MVP; la política de revocación y los controles adicionales siguen pendientes del equipo.

**Revisión de integración de Cris — 14 de octubre:** Cris confirmó `POST /generation` como ruta definitiva del MVP y aceptó el mecanismo de sesión actual para integrar generación y planes. También propuso mantener los catálogos como lectura pública durante el MVP; este punto necesita conformidad de Alejandra. La estructura completa de `TeachingPlanDraft` dentro de `Planning.content`, con los IDs curriculares separados, es técnicamente compatible y fue aceptada por Cris como base de integración, pero permanece provisional hasta la revisión de Alejandra. Las reglas detalladas y sus estados están en [contratos compartidos](contratos.md).

**Cierre de la etapa 5:** la [verificación reproducible](verificacion-etapa-5-2026-10-11.md) cubrió carga, acceso correcto y rechazado, identidad posterior y persistencia de hashes en PostgreSQL. La credencial local de PostgreSQL que apareció en el historial se rotó durante la validación final del viernes: la anterior fue rechazada y la nueva permanece únicamente en el `.env` ignorado. La posible limpieza del historial compartido y la coordinación del contrato con Jean y Alejandra siguen pendientes. No se registra aquí ningún valor privado.

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

## Diferencia de redacción resuelta

El plan menciona como contingencia que “FastAPI + PostgreSQL funcionen localmente”. Para este proyecto significa FastAPI ejecutado en el equipo de desarrollo y PostgreSQL dentro de Docker; PostgreSQL no se instala directamente en Windows. Si FastAPI se incorpora a Compose, `DATABASE_URL` usará `alfa-db` como host.

## Fuentes aún no disponibles

No se han proporcionado el documento de requerimientos funcionales, las entrevistas ni una ficha oficial validada. No se tomarán decisiones académicas definitivas a partir de las fotografías.
