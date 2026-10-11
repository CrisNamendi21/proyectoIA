# Contratos compartidos

## Estado

El plan pide congelar contratos base el sábado 10 de octubre para permitir el trabajo paralelo. Esta página distingue los acuerdos confirmados de lo que todavía debe coordinarse. Los contratos documentados no implican por sí solos que el código ya esté implementado.

| Área | Confirmado por el plan o la instrucción del equipo | Acuerdo necesario antes de implementar |
| --- | --- | --- |
| PostgreSQL | Base relacional exclusivamente en Docker; SQLAlchemy 2 síncrono con Psycopg 3. Para desarrollo: usuario `equipo_alfa`, contraseña `alfa2026`, puerto `5432`, base `colegio_alfa_db` y servicio de Compose `alfa-db`. | Creación inicial de tablas y datos. Las credenciales son solo para desarrollo local. |
| Entorno | La conexión se leerá desde `DATABASE_URL` con `pydantic-settings`. Desde Windows se usará `postgresql+psycopg://equipo_alfa:alfa2026@localhost:5432/colegio_alfa_db`; dentro de Compose el host será `alfa-db`. `pyproject.toml` y `uv.lock` son la fuente oficial de dependencias. | Jean debe reflejar el contrato en `.env.example` y `compose.yaml`. Faltan las variables de autenticación y Ollama. |
| Nombres | Cinco entidades compartidas con nombres `User`, `Grade`, `Subject`, `CurriculumContent`, `Planning`. | Convención de tablas, columnas, módulos y nombres públicos de esquemas. |
| Modelos ORM | Están implementados `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`, con claves foráneas y relaciones bidireccionales. Las tablas se crean mediante `init_db()`. | Estrategia posterior de migraciones, política de eliminación y datos iniciales. |
| Pydantic | Se validarán solicitudes, respuestas y salida de IA. | Nombres y campos de esquemas de catálogo, autenticación, generación y planificación; reglas de serialización. |
| Endpoints | Login y protección; consulta de catálogos; generación; guardar, consultar, editar e historial. | Rutas, métodos, parámetros, filtros, respuestas y códigos de error. Ninguna ruta concreta está aprobada. |
| Usuario autenticado | Cuentas precreadas y acceso personal a planificaciones. | Mecanismo de sesión o token, identificador que entregará la dependencia común y manejo de logout. |
| `Planning` | Debe permitir guardar, editar y consultar; se recomienda JSONB para el contenido flexible. | Forma del cuerpo, referencias curriculares, propiedad, validación, fechas y política de cambios. |
| Intercambio con IA | Ollama propone una planificación; la salida debe validarse y poder guardarse. | Esquema de entrada/salida, versión, campos mínimos, tratamiento de respuesta incompleta o inválida y errores. |

## Sesión de base de datos

- Se creará un solo `engine` y un solo `sessionmaker` para la aplicación.
- Cada petición que necesite persistencia recibirá una nueva `Session` mediante una dependencia de FastAPI con `yield`.
- La sesión se cerrará siempre al terminar la petición y no se compartirá entre peticiones.
- Los servicios u operaciones que escriban datos harán `commit` de forma explícita y ejecutarán `rollback` cuando corresponda.
- No se abrirán conexiones ni se crearán tablas al importar los modelos.

## Secuencia de acuerdo propuesta

1. Cris y Jean acuerdan la configuración de PostgreSQL y variables de entorno; Jean la plasma en `.env.example` y Compose.
2. Los tres revisan [modelo de datos](modelo-datos.md) y cierran las entidades mínimas; Cris publica modelos compartidos.
3. Cris, Jean y Alejandra acuerdan identidad de usuario, contratos HTTP y estructura de `Planning` compatible con IA.
4. Se registra cada decisión confirmada aquí o en [decisiones pendientes](decisiones-pendientes.md), con fecha y responsables. Un cambio posterior se coordina antes de editar modelos compartidos.

Los JSON de ejemplo y mocks serán útiles para pruebas independientes una vez acordado su formato; no se inventa uno en esta fase.
