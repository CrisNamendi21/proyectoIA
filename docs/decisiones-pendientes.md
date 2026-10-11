# Decisiones pendientes

Este registro requiere acuerdos explícitos del equipo. Las propuestas técnicas no equivalen a requisitos oficiales.

## Pendientes activos

| Prioridad | Decisión por confirmar | Quién debe coordinarla | Motivo |
| --- | --- | --- | --- |
| Alta | Configuración reproducible de PostgreSQL mediante `compose.yaml` y `.env.example`. | Jean con Cris | Permite ejecutar la base en otra computadora y cerrar el criterio de portabilidad. |
| Alta | Identificador de acceso, mecanismo de autenticación para cuentas precreadas y comportamiento de logout. | Cris y equipo | Define la dependencia de usuario autenticado y la protección de rutas. |
| Alta | Rutas, métodos, esquemas Pydantic, respuestas y errores de los módulos funcionales. | Los tres | Evita implementar módulos incompatibles. |
| Alta | Forma validada de `Planning.content`, vínculos curriculares y reglas de edición. | Cris y Alejandra, con Jean para IA | Une generación, persistencia y consulta. |
| Alta | Contrato de solicitud y respuesta de Ollama, incluidos sus errores. | Jean con Cris y Alejandra | Permite crear mocks compatibles con el guardado. |
| Media | Catálogo curricular real y reglas de grado, asignatura y contenido. | Alejandra con el equipo y el colegio | Define datos iniciales y validaciones del dominio. |
| Media | Estrategia para cargar cuentas y catálogos iniciales. | Equipo | `init_db()` crea tablas, pero no carga datos. |
| Media | Si “sección” será catálogo, columna, campo flexible o quedará fuera del MVP. | Equipo y colegio | Grado y sección son conceptos distintos. |
| Media | Ficha oficial y campos pedagógicos obligatorios. | Colegio y equipo | Las fotografías son referencias, no la especificación final. |
| Media | Estrategia de migraciones y política de eliminación entre entidades. | Equipo | `create_all()` sirve para la base inicial, pero no gestiona cambios de esquema. |
| Media | Estrategia de pruebas con PostgreSQL y datos aislados. | Equipo | Evita depender de información local compartida entre pruebas. |

## Propuesta provisional de autenticación — 11 de octubre de 2026

**Responsable de la propuesta:** Cris. **Estado de las decisiones de esta sección:** propuestas provisionales, pendientes de revisión por Jean y Alejandra; implementarlas parcialmente no las convierte en contratos aprobados. Como hoy no están disponibles, Cris avanza en `Cris-develop` con estas hipótesis y deja los puntos compartidos identificados para su revisión posterior.

| Decisión | Propuesta para el trabajo de Cris | Revisión pendiente |
| --- | --- | --- |
| Identificador de acceso | Usar `User.username`, ya único y limitado a 50 caracteres. Quitar espacios al inicio y al final, exigir un valor no vacío y tratar las mayúsculas y minúsculas como distintas. | Equipo: confirmar la regla antes de cargar cuentas. |
| Hash de contraseñas | Usar Argon2id mediante `pwdlib[argon2]`. Guardar solo el resultado en `User.password_hash`; nunca una contraseña ni un hash fijo de ejemplo en Git. | Cris incorporó la dependencia el 11 de octubre por la ausencia de Jean; Jean debe revisar `pyproject.toml` y `uv.lock` después. |
| Cuentas precreadas | Cris implementó `uv run python -m app.db.seed_users <username>`: una cuenta por ejecución, contraseña solicitada y confirmada sin mostrarse. El nombre se recorta y debe tener entre 1 y 50 caracteres; conserva mayúsculas y minúsculas. El comando omite usuarios existentes y guarda solo el hash de los nuevos, sin ejecutarse al importar modelos ni al iniciar la API. La doble ejecución se comprobó en PostgreSQL con cuentas ficticias y una base desechable: no cambió el número de cuentas ni los valores previos. | Equipo: revisar el formato provisional, decidir quién entregará las cuentas reales por un canal privado y confirmar si se cargarán cuentas inactivas. La prueba de una cuenta inactiva fue solo técnica; no representa una decisión de cargarlas. |
| Sesión e identidad | Usar `SessionMiddleware` de Starlette con cookie firmada, `HttpOnly`, `SameSite=Lax` y vigencia propuesta de 8 horas. Guardar solo `User.id` en la sesión. Proponer `SESSION_SECRET_KEY` para la clave obligatoria, fuera de Git, y `SESSION_COOKIE_SECURE` para activar `Secure` bajo HTTPS. | Equipo: aprobar duración, uso de cookie y requisitos de despliegue. Jean: revisar los nombres de variables y sus ejemplos en `.env.example`. |
| Usuario autenticado | Proponer `get_current_user` en `app/api/deps.py`, dependiente de `get_db_session()`. En cada petición obtiene el `User` por el ID de sesión y exige `is_active`; entrega el objeto `User` a los routers. | Alejandra: confirmar la ruta de importación y el tipo que consumirán sus routers y pruebas. |
| Acceso HTTP del domingo | Proponer `POST /auth/login` con JSON validado por `LoginRequest` (`username`, `password`) y respuesta `LoginResponse` (`id`, `username`), además de la cookie. Credenciales erróneas o cuenta inactiva: `401` con mensaje genérico; cuerpo inválido: `422`. No devolver el hash ni indicar si existe el usuario. | Equipo: confirmar ruta, esquemas y errores antes de tratarlos como contrato compartido. |
| Dependencias nuevas | `pwdlib[argon2]` para hashing ya se añadió con `uv add`; `itsdangerous` para `SessionMiddleware` queda pendiente hasta trabajar en sesiones. `pyproject.toml` y `uv.lock` siguen siendo las únicas fuentes de dependencias. | Jean: revisar la incorporación de `pwdlib[argon2]` y coordinar cualquier dependencia posterior. |

La cookie firmada permite leer su contenido, aunque no modificarlo sin la clave; por eso solo contendría el ID. Borrar la cookie durante el logout previsto para el lunes no invalida una copia obtenida antes: si el equipo requiere revocación inmediata en el servidor, habrá que elegir otro mecanismo antes de integrar. Los endpoints que escriban datos también requerirán revisar la protección frente a solicitudes entre sitios al usar cookies.

**Alcance del domingo:** implementar el acceso mínimo y comprobar que una segunda petición resuelve la misma identidad mediante la dependencia, sin publicar `/me` solo para esa comprobación. **Reservado para el lunes 12:** completar logout, `/me`, aplicar la dependencia a rutas protegidas y `tests/test_auth.py`. Mientras falte revisión del equipo, estos nombres y comportamientos siguen siendo propuestas.

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

## Diferencia de redacción resuelta

El plan menciona como contingencia que “FastAPI + PostgreSQL funcionen localmente”. Para este proyecto significa FastAPI ejecutado en el equipo de desarrollo y PostgreSQL dentro de Docker; PostgreSQL no se instala directamente en Windows. Si FastAPI se incorpora a Compose, `DATABASE_URL` usará `alfa-db` como host.

## Fuentes aún no disponibles

No se han proporcionado el documento de requerimientos funcionales, las entrevistas ni una ficha oficial validada. No se tomarán decisiones académicas definitivas a partir de las fotografías.
