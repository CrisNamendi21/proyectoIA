# Decisiones pendientes

Este registro se cerrará con acuerdos explícitos del equipo. Las propuestas técnicas no equivalen a requisitos oficiales. Prioridad **alta**: resolver el sábado 10 antes de que los módulos dependientes avancen.

| Prioridad | Decisión por confirmar | Quién debe coordinarla | Motivo |
| --- | --- | --- | --- |
| Alta | Nombres de variables, URL de PostgreSQL dentro/fuera de Compose, credenciales de ejemplo y forma de crear tablas/datos. | Cris y Jean | Bloquea conexión reproducible y modelos. |
| Alta | Campos, claves y relaciones mínimas de las cinco entidades; asociación real entre grado, asignatura y contenido. | Cris con Alejandra y referente del colegio | Evita cambiar modelos al iniciar catálogos. |
| Alta | Identificador de acceso y mecanismo de autenticación para cuentas precreadas; comportamiento de logout. | Cris y equipo | Define `User` y dependencia común de rutas. |
| Alta | Rutas, métodos, nombres de esquemas y representación del usuario autenticado. | Los tres | Permite desarrollar módulos compatibles. |
| Alta | Cuerpo JSONB de `Planning`, validación, vínculos curriculares y forma de editarlo. | Cris y Alejandra, con Jean para IA | Une persistencia y generación. |
| Alta | Contrato de solicitud/respuesta de Ollama y errores previstos. | Jean con Cris y Alejandra | Permite mocks y guardado sin Ollama real. |
| Media | Si “sección” tendrá catálogo, columna, campo flexible o quedará fuera del MVP. | Equipo y colegio | Grado y sección son conceptos distintos. |
| Media | Ficha oficial, campos pedagógicos obligatorios y reglas de revisión docente. | Colegio y equipo | Las fotos son ejemplos, no especificación final. |
| Media | Estrategia de pruebas con PostgreSQL en contenedor y datos de prueba. | Equipo | Evita pruebas que dependan de datos locales o Ollama real. |

## Diferencia de redacción detectada

El plan ofrece como contingencia que “FastAPI + PostgreSQL funcionen localmente” si Docker consume tiempo. La instrucción expresa de esta sesión exige que **PostgreSQL se ejecute en Docker** y que no se instale directamente en el sistema operativo. Para el trabajo actual se interpreta “localmente” como FastAPI local conectado a PostgreSQL en contenedor; conviene confirmar esta interpretación con Jean antes de documentar comandos.

## Fuentes aún no disponibles

No se han proporcionado el documento de requerimientos funcionales, las entrevistas ni la ficha oficial validada. No se tomarán decisiones académicas definitivas a partir de las fotografías.
