# Pendientes posteriores al cierre del viernes

Responsable de seguimiento: Cris. Estado registrado sobre `Cris-develop` después de la validación técnica del viernes 16 de octubre de 2026.

## Qué significa “terminado”

El alcance planificado para el viernes está terminado: el backend integrado arranca, usa PostgreSQL real, protege las rutas privadas, conserva la propiedad de las planificaciones y superó la regresión con Ollama simulado. `Cris-develop` también puede integrarse con `main` sin conflictos según la simulación realizada.

Esto no significa que el producto completo esté cerrado. Las tareas siguientes quedaron fuera de la validación final o dependen de acuerdos y entregas posteriores.

## Tareas que Cris hará después

### 1. Activar Ollama y validar una generación real en su equipo — prioridad alta

Jean ya registró una prueba real en su entorno. En el equipo de Cris, Ollama y el modelo continúan ausentes, por lo que esa evidencia todavía no se ha reproducido localmente.

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

### 2. Integrar `Cris-develop` en `main` — prioridad alta

La simulación del módulo 6 terminó sin conflictos. El merge real continúa pendiente y debe ejecutarse después de la revisión final del equipo y, si Cris exige evidencia propia de IA, después de la prueba anterior.

Criterio para marcarla como terminada:

- `main` contiene el cierre publicado de `Cris-develop`.
- El push a `origin/main` termina correctamente.
- El árbol queda limpio y el commit remoto coincide con el local.

### 3. Reproducir el arranque desde un clon limpio — prioridad media

Cris y Jean deben comprobar juntos un clon nuevo con `.env` privado, Docker Desktop, PostgreSQL y Ollama activos. La revisión del viernes conservó el volumen existente y no sustituye esta comprobación.

Criterio para marcarla como terminada:

- `uv sync --locked`, build de Compose, creación explícita de tablas, `/health`, `SELECT 1` y comunicación con Ollama funcionan desde el clon nuevo.
- No se reutilizan ni publican secretos del entorno anterior.
- Los pasos que difieran de README se corrigen en la documentación.

## Trabajo que requiere al equipo

| Pendiente | Responsable de coordinar | Resultado esperado |
| --- | --- | --- |
| Aprobar el JSON completo de `TeachingPlanDraft` como `Planning.content`, su versión y sus reglas de edición. | Alejandra con Cris y Jean | Contrato compartido actualizado y pruebas acordadas. |
| Revisar y aprobar el contrato de la edición ya integrada. | Alejandra con Cris y Jean | Confirmación del formato pedagógico, versión, reglas semánticas y pruebas acordadas. |
| Confirmar si los catálogos seguirán públicos o exigirán sesión. | Alejandra con Cris | Política HTTP explícita en contratos y pruebas. |
| Decidir revocación de sesión en servidor y protección adicional para peticiones con cookie. | Cris con el equipo | Decisión documentada; implementación y pruebas si se exige. |
| Proporcionar el catálogo curricular y las cuentas docentes reales por canales apropiados. | Equipo y colegio | Datos aprobados, estrategia de carga y ausencia de datos personales en Git. |
| Adoptar migraciones para cambios futuros del esquema. | Equipo | Herramienta y procedimiento que sustituyan `create_all()` para evoluciones de base de datos. |
| Decidir si se reescribe el historial que contenía una credencial antigua. | Equipo | Decisión coordinada; la credencial local ya fue rotada y dejó de ser válida. |

## Orden recomendado para continuar

1. Preparar Ollama en el equipo de Cris y ejecutar la prueba real una vez.
2. Registrar el resultado y revisar el diff final.
3. Integrar `Cris-develop` en `main` cuando el equipo lo apruebe.
4. Cerrar con Alejandra y Jean los contratos de la edición integrada antes de ampliarla o cambiar seguridad compartida.
5. Planificar catálogo real, migraciones y cualquier trabajo posterior al MVP.

## Reglas para estas tareas

- Mantener `.env`, contraseñas, claves de sesión y datos docentes fuera de Git.
- Usar bases desechables para pruebas integradas y conservar intacta la base de desarrollo.
- Registrar resultados exactos; una prueba simulada y una prueba real deben seguir identificadas por separado.
- Coordinar antes de cambiar archivos de otro responsable, modelos compartidos, contratos, `pyproject.toml` o `uv.lock`.

Este documento es la lista de continuación. La [validación final](validacion-final-2026-10-16.md) conserva la evidencia de lo ya ejecutado y [decisiones pendientes](decisiones-pendientes.md) mantiene los acuerdos que todavía requieren al equipo.
