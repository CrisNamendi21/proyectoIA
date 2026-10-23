# Instrucciones de integración para Jean y Alejandra

Estas instrucciones parten de la base técnica disponible al finalizar el sábado 10 de octubre de 2026.

## Aviso de sincronización — 23 de octubre de 2026

La [credencial histórica](resolucion-credencial-historica-2026-10-23.md) está revocada y el equipo decidió conservar el historial. No se debe ejecutar ningún `push --force`, rebase masivo o reclonado por este incidente. Basta con actualizar `Cris-develop` mediante `git fetch --all --prune` y `git pull --ff-only origin Cris-develop`. Los archivos privados siguen fuera de Git.

## Preparación común

1. Actualizar la rama de integración y crear la rama de trabajo correspondiente:

   ```powershell
   git switch Cris-develop
   git pull origin Cris-develop
   git switch -c nombre-de-la-rama
   ```

2. Reproducir el entorno y comprobar Python:

   ```powershell
   uv sync --locked
   uv run python --version
   ```

3. Leer [arquitectura](arquitectura.md), [modelo de datos](modelo-datos.md), [contratos](contratos.md) y [decisiones pendientes](decisiones-pendientes.md).
4. No modificar los cinco modelos ni inventar contratos compartidos sin coordinarlo con Cris y el responsable afectado.
5. Mantener credenciales reales fuera de Git. El archivo local `.env` ya está ignorado.

## Jean — infraestructura e IA

- Crear `compose.yaml`, `.env.example` y `Dockerfile` según su responsabilidad.
- Usar para PostgreSQL el servicio `alfa-db`, puerto `5432`, base `colegio_alfa_db` y valores locales de ejemplo acordados en [contratos](contratos.md).
- Configurar un volumen persistente y un mecanismo de disponibilidad para que la aplicación no dependa de tiempos arbitrarios de espera.
- Comprobar `docker compose up -d`, `docker compose ps` y la conexión desde la aplicación mediante `SELECT 1`.
- Implementar Ollama dentro de `app/services/ai/` y exportar el router desde `app/api/generation.py`; Cris lo registrará en `app/main.py`.
- Validar con Pydantic la salida de Ollama y cubrir timeout, servicio no disponible y JSON inválido con pruebas que usen mocks.
- Coordinar antes de cambiar `pyproject.toml` o `uv.lock`. Después de un cambio acordado, ejecutar `uv lock --check` y `uv sync --locked`.

## Alejandra — catálogos y planificaciones

- Reutilizar `Grade`, `Subject`, `CurriculumContent` y `Planning`; no crear entidades duplicadas.
- Implementar esquemas en `app/schemas/`, routers delgados en `app/api/` y lógica de negocio en `app/services/plans.py`.
- Obtener la sesión mediante `get_db_session()` y controlar de forma explícita `commit` y `rollback` en operaciones de escritura.
- No asumir que “sección” es una columna. Para el MVP, respetar `TeachingPlanDraft` con `schema_version=1` dentro de `Planning.content` y proponer una versión nueva si la ficha oficial exige otros campos.
- Exportar los routers de catálogos y planificaciones para que Cris los registre en `app/main.py`.
- Probar validación, persistencia, ausencia de registros y propiedad de las planificaciones con fixtures aisladas.

## Acuerdos que deben cerrarse antes de integrar

- mecanismo de autenticación e identidad que recibirán los routers;
- rutas, esquemas Pydantic y respuestas de error;
- cualquier evolución posterior de la versión 1 de `Planning.content`;
- cambios posteriores del contrato entre generación de IA y guardado de planificaciones;
- estrategia de datos iniciales y pruebas con PostgreSQL.

## Entrega de cada módulo

Antes de abrir un PR hacia `Cris-develop`:

1. Sincronizar la rama con la integración actual.
2. Ejecutar las pruebas del módulo y anotar el comando y el resultado real.
3. Confirmar que `uv sync --locked` funciona si se cambiaron dependencias.
4. Explicar rutas implementadas, respuestas de error y decisiones pendientes.
5. Solicitar revisión del responsable de cualquier contrato o archivo compartido modificado.
