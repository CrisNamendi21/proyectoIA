# Modelo de datos compartido

## Estado del diseño

El 10 de octubre de 2026 se implementaron y comprobaron cinco entidades con el estilo tipado de SQLAlchemy 2: `Mapped`, `mapped_column` y `relationship`. Las tablas usan nombres plurales en `snake_case` e identificadores enteros autoincrementales.

## Campos implementados

### `User` — tabla `users`

| Campo | Tipo y reglas |
| --- | --- |
| `id` | entero, clave primaria |
| `username` | `VARCHAR(50)`, obligatorio, único e indexado |
| `password_hash` | `VARCHAR(255)`, obligatorio |
| `is_active` | booleano, obligatorio, valor inicial `true` |

Relación: un usuario posee muchas planificaciones mediante `plannings`.

### `Grade` — tabla `grades`

| Campo | Tipo y reglas |
| --- | --- |
| `id` | entero, clave primaria |
| `name` | `VARCHAR(50)`, obligatorio, único e indexado |

Relaciones: un grado tiene muchos contenidos curriculares y puede asociarse con muchas planificaciones.

### `Subject` — tabla `subjects`

| Campo | Tipo y reglas |
| --- | --- |
| `id` | entero, clave primaria |
| `name` | `VARCHAR(100)`, obligatorio, único e indexado |

Relaciones: una asignatura tiene muchos contenidos curriculares y puede asociarse con muchas planificaciones.

### `CurriculumContent` — tabla `curriculum_contents`

| Campo | Tipo y reglas |
| --- | --- |
| `id` | entero, clave primaria |
| `grade_id` | entero, obligatorio, indexado y clave foránea a `grades.id` |
| `subject_id` | entero, obligatorio, indexado y clave foránea a `subjects.id` |
| `description` | texto, obligatorio; único dentro de la combinación de grado y asignatura |

Relaciones: pertenece a un grado y una asignatura; puede asociarse con muchas planificaciones.

### `Planning` — tabla `plannings`

| Campo | Tipo y reglas |
| --- | --- |
| `id` | entero, clave primaria |
| `user_id` | entero, obligatorio, indexado y clave foránea a `users.id` |
| `grade_id` | entero opcional, indexado y clave foránea a `grades.id` |
| `subject_id` | entero opcional, indexado y clave foránea a `subjects.id` |
| `curriculum_content_id` | entero opcional, indexado y clave foránea a `curriculum_contents.id` |
| `content` | JSONB, obligatorio |
| `created_at` | fecha y hora con zona, creada en UTC |
| `updated_at` | fecha y hora con zona, creada y actualizada en UTC |

Relaciones: pertenece obligatoriamente a un usuario y puede vincularse con un grado, una asignatura y un contenido curricular.

## Comprobación de integridad

SQLAlchemy creó las cinco tablas en PostgreSQL y se comprobaron seis claves foráneas: dos en `curriculum_contents` y cuatro en `plannings`. Las relaciones son bidireccionales mediante `back_populates`.

Alembic versiona el esquema desde la revisión inicial. La política de eliminación en cascada continúa pendiente.

## Grado y sección

`Grade` representa el grado académico. Una sección distingue grupos dentro de un grado y todavía no se modela como entidad ni columna. Hasta confirmar su diseño, puede conservarse dentro de `Planning.content`. No debe utilizarse `Grade` para mezclar ambos conceptos.

La carga inicial de `Grade`, `Subject` y `CurriculumContent` usa un JSON aprobado y validado mediante `app.db.seed_catalogs`. La restricción `uq_curriculum_contents_grade_subject_description` impide que dos procesos conserven el mismo contenido para una combinación de grado y asignatura.

## Información aún necesaria

Se requieren una ficha oficial de planificación si el proyecto pasa a uso institucional. Cris fijó para el MVP `TeachingPlanDraft` con `schema_version=1` como esquema Pydantic del contenido JSONB; una ficha posterior deberá originar una nueva versión en lugar de cambiar silenciosamente la versión 1. Continúa pendiente la política de eliminación. Las fotografías son referencias y no convierten campos como indicador, evaluación o fechas de clase en requisitos definitivos.
