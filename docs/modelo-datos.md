# Modelo de datos compartido

## Estado del diseño

El 10 de octubre de 2026 se implementaron las cinco entidades mínimas con SQLAlchemy 2. La estructura conserva como JSONB el contenido pedagógico que todavía debe validar el colegio.

| Entidad | Responsabilidad | Atributos implementados | Relaciones implementadas |
| --- | --- | --- | --- |
| `User` | Representar cuentas docentes precreadas y propiedad del historial. | `id`, `username`, `password_hash`, `is_active`. | Un usuario posee muchas `Planning`. |
| `Grade` | Permitir seleccionar y consultar grados. | `id`, `name`. | Un grado agrupa contenidos curriculares y puede relacionarse con planificaciones. |
| `Subject` | Permitir seleccionar y consultar asignaturas. | `id`, `name`. | Una asignatura agrupa contenidos curriculares y puede relacionarse con planificaciones. |
| `CurriculumContent` | Representar el contenido curricular que selecciona el docente. | `id`, `grade_id`, `subject_id`, `description`. | Pertenece obligatoriamente a un grado y una asignatura; puede relacionarse con planificaciones. |
| `Planning` | Guardar una planificación editable y recuperable en el historial de su docente. | `id`, `user_id`, `grade_id`, `subject_id`, `curriculum_content_id`, `content`, `created_at`, `updated_at`. | Pertenece obligatoriamente a un usuario. Sus referencias curriculares son opcionales mientras se valida el formato definitivo. |

Las tablas usan nombres plurales en `snake_case` e IDs enteros autoincrementales. `username`, `Grade.name` y `Subject.name` son únicos. Las claves foráneas están declaradas e indexadas. `Planning.content` usa JSONB y sus fechas se generan en UTC. La etapa no incorpora Alembic; `init_db()` crea las tablas explícitamente.

## Grado y sección

`Grade` representa el **grado académico** (por ejemplo, quinto o sexto). Una **sección** distingue grupos dentro de un grado. Las fotos muestran “sección” en una ficha, pero todavía no se modela como entidad ni columna. Hasta confirmar su diseño, podrá conservarse dentro de `Planning.content`. No se debe usar `Grade` para guardar ambos conceptos.

## Información aún necesaria

Se requieren el catálogo curricular real, una ficha oficial de planificación y las decisiones de autenticación. También falta acordar la forma exacta del JSONB, la política de eliminación y la estrategia posterior de migraciones. Las fotos son ejemplos y no justifican declarar obligatorios campos académicos como indicador, evaluación o fechas de clase.
