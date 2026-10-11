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
