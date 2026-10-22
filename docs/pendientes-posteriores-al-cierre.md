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

### 2. Reproducir Ollama en el equipo de Cris — prioridad media

Jean ya verificó desde un clon limpio el backend Docker comunicándose con Ollama y una generación real con `qwen2.5:3b`. Esa evidencia ya está integrada; en el equipo de Cris, Ollama y el modelo continúan ausentes. Repetirla localmente aporta evidencia propia, pero ya no bloquea el cierre técnico compartido.

Pasos:

1. Instalar o abrir Ollama en Windows.
2. Descargar y comprobar el modelo configurado:

   ```powershell
   ollama --version
   ollama pull qwen2.5:3b
   ollama list
   Invoke-RestMethod http://localhost:11434/api/tags
   ```

3. Confirmar en el `.env` local, sin mostrarlo ni versionarlo, estos valores ya documentados en `.env.example`:
   - `OLLAMA_BASE_URL=http://host.docker.internal:11434` para el backend en Docker.
   - `OLLAMA_MODEL=qwen2.5:3b`.
   - `OLLAMA_TIMEOUT_SECONDS=120`, ajustándolo localmente solo si una medición real lo justifica.
4. Reconstruir o recrear el backend para que reciba la configuración vigente.
5. Comprobar la comunicación desde el contenedor con el procedimiento de [arranque y comprobaciones](infraestructura-jean.md#arranque-y-comprobaciones).
6. Ejecutar una sola prueba real y aislada:

   ```powershell
   uv run python tests/integration/run_snapshot.py --ref HEAD --real-ollama
   ```

Criterio para marcarla como terminada:

- Ollama responde en `localhost:11434` y el modelo exacto aparece disponible.
- El backend puede comunicarse con Ollama.
- La prueba real aprueba generación, validación Pydantic, guardado JSONB, propiedad, lectura y logout.
- El runner confirma que no dejó bases temporales.
- El resultado y la duración se agregan a la validación final sin guardar prompts privados ni credenciales.

### 3. Integrar `Cris-develop` en `main` — prioridad alta

La simulación del módulo 6 terminó sin conflictos. El merge real continúa pendiente y debe ejecutarse después de la revisión final del equipo y, si Cris exige evidencia propia de IA, después de la prueba anterior.

Criterio para marcarla como terminada:

- `main` contiene el cierre publicado de `Cris-develop`.
- El push a `origin/main` termina correctamente.
- El árbol queda limpio y el commit remoto coincide con el local.

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
| Adoptar migraciones para cambios futuros del esquema. | Equipo | Herramienta y procedimiento que sustituyan `create_all()` para evoluciones de base de datos. |
| Decidir si se reescribe el historial que contenía una credencial antigua. | Equipo | Decisión coordinada; la credencial local ya fue rotada y dejó de ser válida. |

## Orden recomendado para continuar

1. Restablecer la ejecución local de Python 3.12 con `uv`.
2. Cerrar con Alejandra y Jean los contratos pedagógicos, de catálogos y de seguridad que requieren decisión humana.
3. Revisar el diff final e integrar `Cris-develop` en `main` cuando el equipo lo apruebe.
4. Instalar Ollama y repetir la inferencia en el equipo de Cris solo si se requiere evidencia local adicional.
5. Planificar catálogo real, cuentas, migraciones y cualquier trabajo posterior al MVP.

## Completado después del cierre inicial

- Cris cerró para el MVP `TeachingPlanDraft` versión 1 como contenido persistido, la edición validada, los catálogos con sesión y la aceptación temporal de logout sin revocación en servidor. Alejandra no estaba disponible y no se le atribuyó la aprobación.
- Alejandra implementó y validó `PATCH /plans/{plan_id}`; Cris integró su prueba PostgreSQL en el runner.
- Jean verificó un clon limpio, build Docker sin caché, PostgreSQL aislado, comunicación con Ollama y una generación HTTP real.
- Cris integró ambas entregas y la suite final aprobó 226 pruebas sobre Python 3.12 y PostgreSQL real, sin bases temporales residuales.
- Cris preparó la carga validada y repetible del catálogo, reforzó las contraseñas iniciales y documentó el procedimiento privado.
- Cris aprobó y cargó localmente un catálogo interno del MVP y tres cuentas técnicas; la repetición creó cero registros y conservó los hashes existentes.

## Reglas para estas tareas

- Mantener `.env`, contraseñas, claves de sesión y datos docentes fuera de Git.
- Usar bases desechables para pruebas integradas y conservar intacta la base de desarrollo.
- Registrar resultados exactos; una prueba simulada y una prueba real deben seguir identificadas por separado.
- Coordinar antes de cambiar archivos de otro responsable, modelos compartidos, contratos, `pyproject.toml` o `uv.lock`.

Este documento es la lista de continuación. La [validación final](validacion-final-2026-10-16.md) conserva la evidencia de lo ya ejecutado y [decisiones pendientes](decisiones-pendientes.md) mantiene los acuerdos que todavía requieren al equipo.
