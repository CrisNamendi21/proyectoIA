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
| Endpoints | Integrados; rutas del núcleo confirmadas por Cris para el MVP | Salud; `POST /auth/login`; `POST /auth/logout`; `GET /auth/me`; catálogos públicos de solo lectura; `POST /generation`; y creación, listado y detalle bajo `/plans`. | Falta edición de planificaciones, conformidad de Alejandra sobre el acceso público a catálogos y una prueba integral con PostgreSQL y Ollama disponibles. |
| Usuario autenticado | Implementación integrada, probada y confirmada por Cris para el MVP | `get_current_user` recupera al usuario por el ID de la cookie firmada y exige `is_active`. La cookie contiene solo el ID, es `HttpOnly`, `SameSite=Lax` y dura 8 horas. Generación y planes la utilizan. | Definir si el MVP necesita revocación en servidor y protección adicional frente a solicitudes entre sitios. |
| `Planning` | Guardado y lectura implementados | Pertenece al usuario autenticado; las referencias curriculares son opcionales, se comprueba su coherencia y `content` acepta un objeto JSON validado. | Edición con control de propietario y forma pedagógica definitiva. |
| Intercambio con IA | Ruta y autenticación confirmadas por Cris; adaptación de contenido provisional | `POST /generation` es la ruta del MVP, exige sesión, valida entrada y salida con Pydantic y traduce timeout, indisponibilidad y respuesta inválida a errores controlados. El borrador completo puede almacenarse técnicamente dentro de `Planning.content`, con los IDs curriculares separados. | Alejandra debe confirmar el formato persistido y las reglas de edición; falta probar el flujo integrado. |

La clave de desarrollo se define solo en el entorno local, no se versiona y no debe reutilizarse en producción.

## Revisión de integración de Cris — 14 de octubre de 2026

Esta revisión responde a la propuesta de Jean para preparar el trabajo del jueves. Distingue las decisiones que Cris puede cerrar como responsable del núcleo de las que afectan el módulo de Alejandra. La compatibilidad técnica comprobada no sustituye la aprobación compartida del formato pedagógico.

| Decisión | Estado | Alcance acordado o pendiente |
| --- | --- | --- |
| Ruta de generación | **Confirmada por Cris** | `POST /generation` es la ruta definitiva del MVP. No se creará una ruta de generación paralela. |
| Identidad y sesión | **Confirmada por Cris para el MVP** | Se conserva la cookie firmada de 8 horas, que contiene solo `User.id`; `get_current_user` exige una cuenta activa y protege generación y planes. `POST /auth/logout` borra la sesión del cliente. |
| Revocación de sesión | **Pendiente del equipo** | Una copia previa de la cookie continúa válida hasta expirar. La necesidad de revocación inmediata en servidor y de protección adicional frente a solicitudes entre sitios se evaluará por separado; no cambia el contrato integrado actual. |
| Catálogos | **Confirmados por Cris para integración; revisión pendiente de Alejandra** | Durante el MVP continúan como endpoints públicos de solo lectura porque exponen referencias curriculares y no datos personales. Alejandra debe confirmar esta decisión como responsable del módulo. |
| Forma de `Planning.content` | **Propuesta compatible; pendiente de Alejandra** | Guardar el objeto completo validado como `TeachingPlanDraft` dentro de `content`; enviar `grade_id`, `subject_id` y `curriculum_content_id` por separado. La generación no crea ni guarda el plan. |
| Revisión docente antes de guardar | **Propuesta compatible; pendiente de Alejandra** | El docente puede revisar y editar el borrador antes de `POST /plans`. Antes de persistirlo debe volver a validarse como `TeachingPlanDraft`, preservando todos sus campos y estructura. |
| Versión, metadatos y coherencia semántica | **Pendiente del equipo** | Falta decidir versionado del contenido, metadatos adicionales y la validación entre los nombres del borrador y los IDs curriculares seleccionados. |

No hacen falta cambios en `Planning`, JSONB ni un servicio adaptador para probar la propuesta. La adaptación mínima consiste en validar el borrador revisado, serializarlo como JSON dentro de `content` y conservar las referencias curriculares como campos separados de `PlanningCreate`.

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
