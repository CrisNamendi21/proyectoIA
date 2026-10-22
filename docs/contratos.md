# Contratos compartidos

## Estado al 22 de octubre de 2026

Esta página distingue lo implementado y comprobado de los acuerdos que todavía necesita el equipo. La existencia de una propuesta en este documento no la convierte en un contrato aprobado.

| Área | Estado | Contrato actual | Pendiente |
| --- | --- | --- | --- |
| PostgreSQL | Configuración versionada y comprobada desde clon limpio | PostgreSQL exclusivamente en Docker; SQLAlchemy 2 síncrono con Psycopg 3. Desarrollo: usuario `equipo_alfa`, clave definida solo en el entorno local, puerto `5432`, base `colegio_alfa_db` y servicio `alfa-db`. | Definir valores de despliegue, migraciones y datos iniciales oficiales. |
| Entorno | Implementado y reproducido desde clon limpio | `DATABASE_URL`, sesión y Ollama se configuran por entorno; `.env.example`, `compose.yaml`, `pyproject.toml` y `uv.lock` contienen el contrato reproducible sin secretos reales. Jean verificó build limpio, API Docker, PostgreSQL temporal y Ollama del host. | Confirmar valores de despliegue y repetir localmente en el equipo de Cris solo si se exige evidencia propia. |
| Nombres ORM | Confirmado e implementado | Clases `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`; tablas plurales en `snake_case`. | Coordinar cualquier cambio antes de modificar los modelos compartidos. |
| Modelos ORM | Implementado y comprobado | IDs enteros, claves foráneas explícitas, relaciones bidireccionales, fechas UTC y contenido pedagógico en JSONB. `python -m app.db.init_db` aplica la cabeza de Alembic. | Política de eliminación y cualquier evolución futura del modelo. |
| Datos iniciales | Catálogo interno y tres cuentas técnicas cargados localmente | `seed_catalogs` valida fuente, versión, aprobación, estructura y huella antes de escribir; `seed_users` crea cuentas individuales con contraseña inicial de al menos 15 caracteres. Ambos conservaron registros existentes en la segunda ejecución. | La migración debe añadir unicidad al contenido antes de permitir cargas concurrentes. Los datos institucionales de producción quedan fuera del alcance actual. |
| Pydantic | Implementado y aprobado por Cris para el MVP | Autenticación, catálogos, planificaciones y salida de IA usan esquemas Pydantic. `Planning.content` cumple `TeachingPlanDraft` versión 1 y rechaza campos desconocidos. | Una ficha pedagógica oficial podría exigir una versión futura. |
| Endpoints | Integrados y comprobados mediante ASGI y HTTP Docker real | Salud; `POST /auth/login`; `POST /auth/logout`; `GET /auth/me`; catálogos de solo lectura con sesión; `POST /generation`; y creación, listado, detalle y edición parcial bajo `/plans`. | Revisar cualquier cambio cuando Alejandra esté disponible, sin tratar su ausencia como aprobación personal. |
| Usuario autenticado | Implementación integrada, probada y confirmada por Cris para el MVP | `get_current_user` recupera al usuario por el ID de la cookie firmada y exige `is_active`. La cookie contiene solo el ID, es `HttpOnly`, `SameSite=Lax` y dura 8 horas. Catálogos, generación y planes la utilizan. El MVP acepta que logout elimina la cookie del cliente sin revocar una copia previa. | Antes de producción: sesiones revocables en servidor, protección CSRF, HTTPS y cookie `Secure`. |
| `Planning` | Guardado, lectura y edición parcial implementados | Pertenece al usuario autenticado; `content` conserva el borrador pedagógico completo con `schema_version=1`. Los IDs curriculares permanecen separados y, cuando se informan, sus nombres deben coincidir con el contenido. `PATCH /plans/{plan_id}` valida el estado completo antes del commit. | El colegio debe confirmar si una ficha oficial requiere campos adicionales. |
| Intercambio con IA | Ruta, autenticación, transporte y formato persistido comprobados | `POST /generation` exige sesión y devuelve `TeachingPlanDraft` versión 1. La generación no persiste; el docente puede revisar el borrador y el servidor vuelve a validarlo al crear o editar un plan. | Una versión nueva del formato requerirá contrato y migración explícitos. |

La clave de desarrollo se define solo en el entorno local, no se versiona y no debe reutilizarse en producción.

## Revisión de integración de Cris — 14 de octubre de 2026

Esta revisión responde a la propuesta de Jean para preparar el trabajo del jueves. Distingue las decisiones que Cris puede cerrar como responsable del núcleo de las que afectan el módulo de Alejandra. La compatibilidad técnica comprobada no sustituye la aprobación compartida del formato pedagógico.

| Decisión | Estado | Alcance acordado o pendiente |
| --- | --- | --- |
| Ruta de generación | **Confirmada por Cris** | `POST /generation` es la ruta definitiva del MVP. No se creará una ruta de generación paralela. |
| Identidad y sesión | **Confirmada por Cris para el MVP** | Se conserva la cookie firmada de 8 horas, que contiene solo `User.id`; `get_current_user` exige una cuenta activa y protege generación y planes. `POST /auth/logout` borra la sesión del cliente. |
| Revocación de sesión | **Cerrada por Cris para el MVP el 19 de octubre** | Se acepta la cookie firmada de 8 horas sin revocación individual en servidor dentro del entorno controlado del MVP. La revocación, CSRF, HTTPS y `Secure` son requisitos previos a producción. |
| Catálogos | **Cerrados por Cris para el MVP el 19 de octubre** | Los endpoints son de solo lectura y exigen un usuario autenticado y activo. Alejandra podrá revisarlo después, pero su ausencia no se registra como aprobación. |
| Forma de `Planning.content` | **Cerrada por Cris para el MVP el 19 de octubre** | Se guarda el objeto completo validado como `TeachingPlanDraft` con `schema_version=1`; `grade_id`, `subject_id` y `curriculum_content_id` permanecen separados. |
| Revisión docente antes de guardar | **Cerrada por Cris para el MVP el 19 de octubre** | El docente puede revisar y editar el borrador antes de `POST /plans` y mediante `PATCH`; el estado completo se valida otra vez antes de persistirlo. |
| Versión, metadatos y coherencia semántica | **Cerrada por Cris para el MVP el 19 de octubre** | La versión inicial es 1, no se guardan metadatos técnicos de Ollama dentro del contenido y las referencias curriculares informadas deben coincidir con los nombres del borrador. |

No se modifica la entidad `Planning` ni su columna JSONB. Los esquemas validan el borrador versionado, lo serializan dentro de `content` y conservan las referencias curriculares como campos separados de `PlanningCreate`.

## Verificación integrada de Cris — 14 de octubre de 2026

Después de integrar los dos commits nuevos de Jean en `Cris-develop`, se ejecutó `tests/integration/run_snapshot.py --ref HEAD` sobre el commit `3810afe`. El runner utilizó PostgreSQL real, una base nueva con UUID por caso y un mock únicamente para el transporte HTTP de Ollama.

El resultado fue **167 pruebas aprobadas, 1 omitida y 1 advertencia conocida**. Se comprobaron autenticación, cuenta activa, catálogos, generación, revisión simulada, persistencia JSONB, referencias curriculares, aislamiento entre dos docentes, rollback, errores controlados y logout. El catálogo de bases temporales quedó igual antes y después: no hubo residuos.

La única prueba omitida fue la inferencia con Ollama real. Jean ya registró una ejecución real sobre el snapshot anterior de Cris; en el entorno actual de Cris no hay instalación local de Ollama disponible para repetirla. Esto no invalida la compatibilidad entre módulos comprobada con mocks, pero impide declarar una nueva inferencia real sobre el commit integrado.

No se encontraron incompatibilidades que requieran modificar `app/main.py`, los esquemas, las dependencias ni el manejo de errores. En esa verificación, el `.env` local de Cris no coincidía con la credencial conservada en su volumen PostgreSQL y se utilizó en memoria la configuración del contenedor, sin publicar secretos. La credencial se sincronizó y rotó durante la validación final posterior; la anterior dejó de aceptar conexiones nuevas.

## Integración posterior de la edición — 15 de octubre de 2026

Alejandra publicó `63e2480`, que implementa `PATCH /plans/{plan_id}` mediante `PlanningUpdate` y `update_planning`. Cris lo integró localmente en `25099f3` después de comprobar control de propietario, campos inmutables, actualización parcial, referencias inexistentes o incoherentes, rollback y errores saneados.

La suite del módulo de planes aprobó **108 pruebas**; la suite normal aprobó **195 pruebas, omitió 4 y mantuvo 1 advertencia conocida**. La regresión integral sobre el merge aprobó **225 pruebas, omitió únicamente Ollama real y mantuvo 1 advertencia conocida**; PostgreSQL no dejó bases temporales. Una comprobación adicional con una base PostgreSQL desechable confirmó persistencia de la edición y aislamiento entre dos docentes.

Esta integración confirma el comportamiento técnico de edición. El formato pedagógico definitivo de `Planning.content`, su versión, las reglas de coherencia semántica y la política pública de catálogos todavía requieren acuerdo explícito; la implementación por sí sola no los convierte en contratos aprobados.

Alejandra añadió posteriormente una prueba PostgreSQL específica en `d16531a`. Cris la incorporó al runner en `1c6263f`; la regresión pasó a **226 pruebas aprobadas, 1 omitida y 0 bases temporales residuales**. La nueva evidencia refuerza persistencia y propiedad de `PATCH`, sin cerrar las decisiones pedagógicas pendientes.

## Integración del cierre de infraestructura — 19 de octubre de 2026

Cris integró `6a07f21` y `585944b` mediante `9bc002c`. La entrega de Jean documenta un clon HTTPS nuevo, entorno y credenciales temporales independientes, build sin caché, PostgreSQL nuevo, comunicación backend → Ollama y un flujo HTTP real de 28 solicitudes con una sola generación válida. La inferencia con `qwen2.5:3b` tardó 81.75 segundos en esa ejecución y no dejó recursos temporales del proyecto de prueba.

Sobre el conjunto final, la suite en el contenedor oficial Python 3.12 aprobó **226 pruebas**, omitió únicamente la llamada real opcional y mantuvo la advertencia conocida de Starlette/httpx. El helper `run_docker_http.py` también se comprobó sintácticamente y conserva sus guardas de identidad para operar solo sobre un proyecto desechable.

## Sesión de base de datos

- La aplicación crea un solo `engine` y un solo `SessionLocal`.
- Cada petición que necesite persistencia recibe una nueva `Session` mediante `get_db_session()`.
- La dependencia cierra la sesión al finalizar la petición.
- Los servicios que escriban datos deben controlar `commit` y `rollback` explícitamente.
- Los modelos no abren conexiones ni crean tablas al importarse.
- La creación y evolución de tablas ocurre mediante revisiones Alembic; `init_db()` aplica `upgrade head`.

## Integración entre módulos

1. Jean reflejó el contrato de PostgreSQL en `.env.example` y `compose.yaml`.
2. Cris conserva los modelos compartidos y registra en `app/main.py` los routers exportados por el equipo.
3. Alejandra reutilizó las entidades existentes para catálogos y planificaciones.
4. Los tres acuerdan identidad de usuario, contratos HTTP y estructura validada de `Planning.content` antes de integrar esos módulos.
5. Los cambios posteriores de contratos se registran aquí y se coordinan con los responsables afectados.

Las tareas concretas para continuar están en [instrucciones para el equipo](instrucciones-equipo.md).
