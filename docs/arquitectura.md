# Arquitectura propuesta del backend

## Estado y criterios

Este documento describe una organización para implementar el MVP; todavía no hay módulos de aplicación. El plan semanal confirma Python 3.12, FastAPI/Uvicorn, Pydantic, SQLAlchemy 2, PostgreSQL, Docker Compose, Git/GitHub, Ollama local y pytest. Se busca un proceso sencillo que pueda probarse sin requerir una respuesta real de IA en cada ejecución.

## Organización propuesta

```text
app/
  main.py                 creación de la aplicación y registro de routers — Cris
  core/                   configuración y utilidades transversales — Cris
  db/                     engine, sesiones e inicialización acordada — Cris
  models/                 entidades SQLAlchemy compartidas — Cris
  schemas/                contratos Pydantic por dominio — cada responsable
  api/                    routers HTTP por dominio — cada responsable
  services/
    ai/                   cliente y generación con Ollama — Jean
    plans.py              operaciones de planificación — Alejandra
tests/                    pruebas por módulo — cada responsable
```

El router traduce HTTP y usa dependencias comunes; el servicio aplica la lógica; el modelo representa persistencia; el esquema valida entradas y salidas. `main.py` lo integra Cris. Los nombres concretos de módulos podrán ajustarse al acordar los contratos, sin crear una capa extra por anticipado.

## Persistencia

PostgreSQL es la base principal confirmada porque usuarios, catálogos y propiedad de las planificaciones tienen relaciones que conviene expresar con claves y restricciones. La propuesta es guardar los vínculos estables como columnas relacionales y el cuerpo pedagógico editable de `Planning` en JSONB. Así se puede revisar la ficha oficial sin rediseñar inmediatamente todas las tablas. JSONB no sustituye las claves foráneas ni la validación Pydantic. Aún deben decidirse sus campos, versión y reglas de actualización.

PostgreSQL se ejecutará como contenedor Docker. Jean es responsable principal de `compose.yaml`, `Dockerfile` y `.env.example`; Cris coordina con él la URL de conexión y las variables necesarias. El equipo confirmó que `pyproject.toml` y `uv.lock`, administrados con `uv`, son la fuente oficial de dependencias y que cualquier cambio se coordina entre Cris y Jean. El arranque de FastAPI y la conexión real con PostgreSQL mediante `SELECT 1` ya fueron verificados.

Para el MVP se usará SQLAlchemy 2 en modo síncrono con Psycopg 3. La aplicación leerá `DATABASE_URL` mediante `pydantic-settings` y creará una sesión independiente por petición. La dependencia de FastAPI cerrará la sesión al finalizar; las operaciones que escriban datos controlarán de forma explícita `commit` y `rollback`. El formato acordado para la conexión es `postgresql+psycopg://usuario:contraseña@host:puerto/base_de_datos`.

## Generación y pruebas

Jean encapsulará la llamada a Ollama en un servicio, con salida estructurada validada y errores controlados cuando haya timeout, JSON inválido o servicio no disponible. El contrato de salida debe ser compatible con el guardado de Alejandra. Los tests de generación usarán mocks; las pruebas de persistencia y autorización comprobarán acceso al propietario y entradas inválidas. El plan asigna integración completa al jueves 15 y estabilización al viernes 16.

## Riesgos de integración

Los modelos compartidos deben estar disponibles antes de que Alejandra comience el domingo 11. También se necesitan acuerdos tempranos sobre identidad del usuario, URL de PostgreSQL, estructura de `Planning`, esquema de salida de IA y nombres de rutas/esquemas. El inventario está en [contratos](contratos.md) y las preguntas abiertas en [decisiones pendientes](decisiones-pendientes.md).
