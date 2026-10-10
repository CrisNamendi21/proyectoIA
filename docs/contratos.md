# Contratos compartidos por acordar

## Estado

El plan pide congelar contratos base el sábado 10 de octubre para permitir el trabajo paralelo. Esta página es un inventario para esa conversación. **No hay endpoints, esquemas ni variables implementados o aprobados aquí.** Los nombres concretos se incorporarán después del acuerdo y de comprobar el código.

| Área | Confirmado por el plan o la instrucción del equipo | Acuerdo necesario antes de implementar |
| --- | --- | --- |
| PostgreSQL | Base relacional en contenedor Docker; SQLAlchemy 2 como ORM. | Nombre de servicio, puerto, credenciales de desarrollo, URL dentro/fuera de Compose, creación inicial de tablas y datos. |
| Entorno | Jean prepara `.env.example` y `requirements.txt`; Cris consume la configuración. | Nombres exactos de variables para BD, secreto de auth y URL de Ollama; valores de ejemplo no sensibles. |
| Nombres | Cinco entidades compartidas con nombres `User`, `Grade`, `Subject`, `CurriculumContent`, `Planning`. | Convención de tablas, columnas, módulos y nombres públicos de esquemas. |
| Modelos ORM | Cris publica los modelos mínimos antes del inicio del módulo de Alejandra. | Atributos, tipos, claves, relaciones, restricciones, nulabilidad y estrategia de inicialización. |
| Pydantic | Se validarán solicitudes, respuestas y salida de IA. | Nombres y campos de esquemas de catálogo, autenticación, generación y planificación; reglas de serialización. |
| Endpoints | Login y protección; consulta de catálogos; generación; guardar, consultar, editar e historial. | Rutas, métodos, parámetros, filtros, respuestas y códigos de error. Ninguna ruta concreta está aprobada. |
| Usuario autenticado | Cuentas precreadas y acceso personal a planificaciones. | Mecanismo de sesión o token, identificador que entregará la dependencia común y manejo de logout. |
| `Planning` | Debe permitir guardar, editar y consultar; se recomienda JSONB para el contenido flexible. | Forma del cuerpo, referencias curriculares, propiedad, validación, fechas y política de cambios. |
| Intercambio con IA | Ollama propone una planificación; la salida debe validarse y poder guardarse. | Esquema de entrada/salida, versión, campos mínimos, tratamiento de respuesta incompleta o inválida y errores. |

## Secuencia de acuerdo propuesta

1. Cris y Jean acuerdan la configuración de PostgreSQL y variables de entorno; Jean la plasma en `.env.example` y Compose.
2. Los tres revisan [modelo de datos](modelo-datos.md) y cierran las entidades mínimas; Cris publica modelos compartidos.
3. Cris, Jean y Alejandra acuerdan identidad de usuario, contratos HTTP y estructura de `Planning` compatible con IA.
4. Se registra cada decisión confirmada aquí o en [decisiones pendientes](decisiones-pendientes.md), con fecha y responsables. Un cambio posterior se coordina antes de editar modelos compartidos.

Los JSON de ejemplo y mocks serán útiles para pruebas independientes una vez acordado su formato; no se inventa uno en esta fase.
