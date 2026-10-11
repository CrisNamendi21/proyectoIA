# Contratos compartidos

## Estado al 11 de octubre de 2026

Esta página distingue lo implementado y comprobado de los acuerdos que todavía necesita el equipo. La existencia de una propuesta en este documento no la convierte en un contrato aprobado.

| Área | Estado | Contrato actual | Pendiente |
| --- | --- | --- | --- |
| PostgreSQL | Implementado y comprobado localmente | PostgreSQL exclusivamente en Docker; SQLAlchemy 2 síncrono con Psycopg 3. Desarrollo: usuario `equipo_alfa`, clave definida solo en el entorno local, puerto `5432`, base `colegio_alfa_db` y servicio `alfa-db`. | Jean debe versionar Compose y definir la disponibilidad del servicio. |
| Entorno | Implementado en la aplicación | `DATABASE_URL` y `SESSION_SECRET_KEY` se leen con `pydantic-settings`; esta última debe tener al menos 32 caracteres y permanecer fuera de Git. `SESSION_COOKIE_SECURE` activa la marca `Secure` bajo HTTPS. En Windows PostgreSQL usa `localhost`; dentro de Compose usará `alfa-db`. `pyproject.toml` y `uv.lock` son las fuentes oficiales de dependencias. | Jean debe añadir `.env.example` y `compose.yaml` con nombres y ejemplos no sensibles; faltan variables de Ollama. |
| Nombres ORM | Confirmado e implementado | Clases `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`; tablas plurales en `snake_case`. | Coordinar cualquier cambio antes de modificar los modelos compartidos. |
| Modelos ORM | Implementado y comprobado | IDs enteros, claves foráneas explícitas, relaciones bidireccionales, fechas UTC y contenido pedagógico en JSONB. `init_db()` crea las tablas. | Migraciones, política de eliminación y datos iniciales. |
| Pydantic | Criterio acordado | Las solicitudes, respuestas y salidas de IA se validarán con esquemas Pydantic. | Nombres, campos y reglas de los esquemas de cada dominio. |
| Endpoints | Salud confirmada; acceso provisional implementado y probado | `GET /health` responde `200` con `{"status":"ok"}`. `POST /auth/login` recibe `username` y `password`, responde `200` con `id` y `username` y establece cookie de sesión; credenciales erróneas o cuenta inactiva reciben `401` genérico y cuerpo inválido `422`. | El equipo debe revisar el contrato HTTP provisional. Catálogos, generación y planificaciones siguen pendientes. |
| Usuario autenticado | Implementación provisional probada | `get_current_user` recupera al usuario por el ID de la cookie firmada en cada petición y exige `is_active`. La cookie contiene solo el ID, es `HttpOnly`, `SameSite=Lax` y dura 8 horas. | El equipo debe aprobar el mecanismo y el formato que usarán otros routers; logout queda pendiente. |
| `Planning` | Base ORM implementada | Pertenece a un usuario; sus referencias curriculares son opcionales y `content` es JSONB obligatorio. | Esquema Pydantic del contenido, reglas de edición y validaciones de propiedad. |
| Intercambio con IA | Pendiente | Ollama propondrá una planificación y su respuesta deberá validarse antes de guardarla. | Solicitud, respuesta, versión, campos mínimos y errores controlados. |

La clave de desarrollo se define solo en el entorno local, no se versiona y no debe reutilizarse en producción.

## Sesión de base de datos

- La aplicación crea un solo `engine` y un solo `SessionLocal`.
- Cada petición que necesite persistencia recibe una nueva `Session` mediante `get_db_session()`.
- La dependencia cierra la sesión al finalizar la petición.
- Los servicios que escriban datos deben controlar `commit` y `rollback` explícitamente.
- Los modelos no abren conexiones ni crean tablas al importarse.
- La creación de tablas ocurre únicamente cuando se invoca `init_db()`.

## Integración entre módulos

1. Jean refleja el contrato de PostgreSQL en `.env.example` y `compose.yaml`.
2. Cris conserva los modelos compartidos y registra en `app/main.py` los routers exportados por el equipo.
3. Alejandra reutiliza las entidades existentes para catálogos y planificaciones.
4. Los tres acuerdan identidad de usuario, contratos HTTP y estructura validada de `Planning.content` antes de integrar esos módulos.
5. Los cambios posteriores de contratos se registran aquí y se coordinan con los responsables afectados.

Las tareas concretas para continuar están en [instrucciones para el equipo](instrucciones-equipo.md).
