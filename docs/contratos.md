# Contratos compartidos

## Estado al 14 de octubre de 2026

Esta página distingue lo implementado y comprobado de los acuerdos que todavía necesita el equipo. La existencia de una propuesta en este documento no la convierte en un contrato aprobado.

| Área | Estado | Contrato actual | Pendiente |
| --- | --- | --- | --- |
| PostgreSQL | Configuración versionada y comprobada previamente | PostgreSQL exclusivamente en Docker; SQLAlchemy 2 síncrono con Psycopg 3. Desarrollo: usuario `equipo_alfa`, clave definida solo en el entorno local, puerto `5432`, base `colegio_alfa_db` y servicio `alfa-db`. | Repetir la prueba desde clon limpio con Docker activo. |
| Entorno | Implementado en aplicación y Compose | `DATABASE_URL`, sesión y Ollama se configuran por entorno; `.env.example`, `compose.yaml`, `pyproject.toml` y `uv.lock` contienen el contrato reproducible sin secretos reales. | Confirmar valores de despliegue y documentar la descarga del modelo de Ollama. |
| Nombres ORM | Confirmado e implementado | Clases `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`; tablas plurales en `snake_case`. | Coordinar cualquier cambio antes de modificar los modelos compartidos. |
| Modelos ORM | Implementado y comprobado | IDs enteros, claves foráneas explícitas, relaciones bidireccionales, fechas UTC y contenido pedagógico en JSONB. `python -m app.db.init_db` crea las tablas explícitamente. | Migraciones, política de eliminación y datos curriculares iniciales. |
| Pydantic | Implementado en los módulos actuales | Autenticación, catálogos, planificaciones y salida de IA usan esquemas Pydantic. | Confirmar la forma pedagógica definitiva de `Planning.content`. |
| Endpoints | Integrados y probados de forma aislada | Salud; `POST /auth/login`; `POST /auth/logout`; `GET /auth/me`; catálogos; `POST /generation`; y creación, listado y detalle bajo `/plans`. | Falta edición de planificaciones y una prueba integral con PostgreSQL y Ollama disponibles. |
| Usuario autenticado | Implementación integrada y probada | `get_current_user` recupera al usuario por el ID de la cookie firmada y exige `is_active`. La cookie contiene solo el ID, es `HttpOnly`, `SameSite=Lax` y dura 8 horas. Generación y planes la utilizan. | El equipo debe cerrar la aprobación del mecanismo y definir si necesita revocación de servidor. |
| `Planning` | Guardado y lectura implementados | Pertenece al usuario autenticado; las referencias curriculares son opcionales, se comprueba su coherencia y `content` acepta un objeto JSON validado. | Edición con control de propietario y forma pedagógica definitiva. |
| Intercambio con IA | Implementado y validado en aislamiento | `POST /generation` exige sesión, valida entrada y salida con Pydantic y traduce timeout, indisponibilidad y respuesta inválida a errores controlados. | Probar el flujo con Ollama real y acordar la conversión final al contenido persistido. |

La clave de desarrollo se define solo en el entorno local, no se versiona y no debe reutilizarse en producción.

## Sesión de base de datos

- La aplicación crea un solo `engine` y un solo `SessionLocal`.
- Cada petición que necesite persistencia recibe una nueva `Session` mediante `get_db_session()`.
- La dependencia cierra la sesión al finalizar la petición.
- Los servicios que escriban datos deben controlar `commit` y `rollback` explícitamente.
- Los modelos no abren conexiones ni crean tablas al importarse.
- La creación de tablas ocurre únicamente cuando se invoca `init_db()`.

## Integración entre módulos

1. Jean reflejó el contrato de PostgreSQL en `.env.example` y `compose.yaml`.
2. Cris conserva los modelos compartidos y registra en `app/main.py` los routers exportados por el equipo.
3. Alejandra reutilizó las entidades existentes para catálogos y planificaciones.
4. Los tres acuerdan identidad de usuario, contratos HTTP y estructura validada de `Planning.content` antes de integrar esos módulos.
5. Los cambios posteriores de contratos se registran aquí y se coordinan con los responsables afectados.

Las tareas concretas para continuar están en [instrucciones para el equipo](instrucciones-equipo.md).
