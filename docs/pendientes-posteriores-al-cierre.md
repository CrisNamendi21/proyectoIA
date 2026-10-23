# Pendientes posteriores al cierre del viernes

Responsable de seguimiento: Cris. Estado registrado sobre `Cris-develop` después de la validación técnica del viernes 16 de octubre de 2026.

## Qué significa “terminado”

El alcance planificado para el viernes está terminado: el backend integrado arranca, usa PostgreSQL real, protege las rutas privadas, conserva la propiedad de las planificaciones y superó la regresión con Ollama simulado. `Cris-develop` también puede integrarse con `main` sin conflictos según la simulación realizada.

Esto no significa que el producto completo esté cerrado. Las tareas siguientes quedaron fuera de la validación final o dependen de acuerdos y entregas posteriores.

## Tareas que Cris hará después

### 1. Restablecer Python 3.12 local — completado el 19 de octubre de 2026

El bloqueo de Control de aplicaciones afectaba únicamente al ejecutable antiguo de `.venv\Scripts\python.exe`. El intérprete base CPython 3.12.14 administrado por `uv` funcionaba correctamente, por lo que se reconstruyó el entorno virtual desde `uv.lock` sin desactivar la protección de Windows ni modificar las dependencias declaradas.

Comandos aplicados:

```powershell
uv venv --clear --python 3.12 .venv
uv sync --locked
uv run python --version
```

Resultado verificado:

- `uv run python --version`: Python 3.12.14.
- `uv run pytest -q`: 195 aprobadas, 5 omitidas y 1 advertencia.
- `uv run python tests/integration/run_snapshot.py --ref HEAD`: 226 aprobadas, 1 omitida y 1 advertencia sobre PostgreSQL real.
- El runner integrado confirmó código de salida 0, catálogo temporal intacto y 0 bases residuales nuevas.

### 2. Reproducir Ollama en el equipo de Cris — completado el 23 de octubre de 2026

Cris instaló Ollama 0.40.9 y descargó `qwen2.5:3b`. La API local respondió, el backend Docker encontró el modelo mediante `host.docker.internal` y la única prueba real aprobó generación, validación Pydantic, guardado JSONB, propiedad, consulta y logout.

La medición del flujo fue de **62.56 segundos**. El runner terminó con 1 prueba aprobada, las migraciones correctas, el catálogo temporal sin cambios y 0 bases residuales nuevas. La evidencia completa está en [verificación de Ollama en el equipo de Cris](verificacion-ollama-cris-2026-10-23.md).

### 3. Integrar `Cris-develop` en `main` — completado el 23 de octubre de 2026

La revisión final aprobó la suite aislada, el runner con PostgreSQL, las migraciones, el flujo real de Ollama y el control de secretos. Cris autorizó la integración explícita mediante `merge --no-ff`; `main` recibió el estado completo de `Cris-develop` y ambas ramas fueron publicadas.

### 4. Reproducir el arranque en el equipo de Cris — prioridad baja

Jean ya comprobó un clon nuevo con `.env` privado, Docker Desktop, PostgreSQL y Ollama activos. Cris solo necesita repetirlo si el equipo exige una segunda evidencia local independiente.

Criterio para marcarla como terminada:

- `uv sync --locked`, build de Compose, creación explícita de tablas, `/health`, `SELECT 1` y comunicación con Ollama funcionan desde el clon nuevo.
- No se reutilizan ni publican secretos del entorno anterior.
- Los pasos que difieran de README se corrigen en la documentación.

## Trabajo que requiere al equipo

| Pendiente | Responsable de coordinar | Resultado esperado |
| --- | --- | --- |
| Sustituir los datos internos si el proyecto llega a producción institucional. | Equipo y colegio | Catálogo institucional aprobado y cuentas reales tratadas fuera de Git; fuera del alcance del MVP actual. |

## Orden aplicado

1. Se restableció la ejecución local de Python 3.12 con `uv`.
2. Se cerraron los contratos funcionales necesarios para el MVP.
3. Se instaló Ollama y se reprodujo la inferencia real en el equipo de Cris.
4. Se revisó el diff final y se integró `Cris-develop` en `main` con autorización de Cris.
5. Los datos institucionales reales y cualquier ampliación posterior permanecen fuera del alcance del MVP.

## Completado después del cierre inicial

- Cris cerró para el MVP `TeachingPlanDraft` versión 1 como contenido persistido, la edición validada, los catálogos con sesión y la aceptación temporal de logout sin revocación en servidor. Alejandra no estaba disponible y no se le atribuyó la aprobación.
- Alejandra implementó y validó `PATCH /plans/{plan_id}`; Cris integró su prueba PostgreSQL en el runner.
- Jean verificó un clon limpio, build Docker sin caché, PostgreSQL aislado, comunicación con Ollama y una generación HTTP real.
- Cris integró ambas entregas y la suite final aprobó 226 pruebas sobre Python 3.12 y PostgreSQL real, sin bases temporales residuales.
- Cris preparó la carga validada y repetible del catálogo, reforzó las contraseñas iniciales y documentó el procedimiento privado.
- Cris aprobó y cargó localmente un catálogo interno del MVP y tres cuentas técnicas; la repetición creó cero registros y conservó los hashes existentes.
- Cris adoptó Alembic, creó la revisión inicial, agregó unicidad curricular y automatizó upgrade, downgrade y detección de cambios sin migración.
- Cris confirmó nuevamente la revocación de la credencial antigua, auditó todas las referencias, creó un respaldo privado y decidió conservar el historial sin forzar ramas ni clones.
- Cris instaló Ollama 0.40.9, descargó `qwen2.5:3b` y reprodujo localmente una generación real completa en 62.56 segundos, sin bases temporales residuales.

## Reglas para estas tareas

- Mantener `.env`, contraseñas, claves de sesión y datos docentes fuera de Git.
- Usar bases desechables para pruebas integradas y conservar intacta la base de desarrollo.
- Registrar resultados exactos; una prueba simulada y una prueba real deben seguir identificadas por separado.
- Coordinar antes de cambiar archivos de otro responsable, modelos compartidos, contratos, `pyproject.toml` o `uv.lock`.

Este documento es la lista de continuación. La [validación final](validacion-final-2026-10-16.md) conserva la evidencia de lo ya ejecutado y [decisiones pendientes](decisiones-pendientes.md) mantiene los acuerdos que todavía requieren al equipo.
