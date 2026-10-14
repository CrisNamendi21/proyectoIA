# Adelanto del jueves: flujo integrado con PostgreSQL

Fecha: miércoles 14 de octubre de 2026. Responsable: Jean.
Esta evidencia complementa la [propuesta de integración](integracion-ia-planificaciones-2026-10-14.md).
Usar el JSON completo de `TeachingPlanDraft` dentro de `PlanningCreate.content` sigue siendo una **propuesta provisional**.

## Código y entorno probados

- Snapshot inmutable de `origin/Cris-develop`: `31a569a9ef306274e54bcf4e4bc49984d2d8019c`.
- Alejandra permanece en `b9f7a46`; no hubo nuevos commits remotos desde la revisión anterior.
- Jean permanece en `feature/ai-infra-jean`; no se realizó merge, rebase ni checkout de otra rama.
- Se arrancó únicamente el contenedor existente `alfa-db` y se esperó a healthy. El backend de desarrollo permaneció detenido.
- Se conservó el volumen PostgreSQL existente. La conexión administrativa apuntó a `postgres`, no a la base de desarrollo.
- Se extrajo el código con `git archive` fuera del repositorio; se copiaron únicamente las pruebas propias a ese entorno.
  No se copió `.env`. Se exigió igualdad del lockfile con el entorno instalado de Jean.
- Peticiones mediante `TestClient` a la aplicación ASGI de Cris, con sus routers y autenticación registrados.
  La dependencia de sesión se sustituyó por sesiones independientes de PostgreSQL **real**, únicamente sobre la base desechable de cada caso.
  No se sustituyeron usuarios, autenticación, catálogos, validadores ni servicios de persistencia por mocks.

## Pruebas propias y reproducción

Archivos separados bajo `tests/integration/`:

- `run_snapshot.py`: extracción del commit remoto, entorno privado de prueba, ejecución de suite y comprobación de residuos.
- `conftest.py`: crea y elimina una base nueva `colegio_alfa_ai_flow_test_<uuid>` por caso, con datos docentes/curriculares ficticios.
- `test_ai_planning_flow.py`: flujo completo, propiedad, errores y observaciones de acceso/sesión.

Desde la raíz, con uv sincronizado, PostgreSQL healthy y las credenciales locales válidas:

```powershell
uv run python tests/integration/run_snapshot.py
```

Ejecuta la suite de Cris y las pruebas nuevas. Habilita las tres pruebas PostgreSQL preexistentes.
Simula exclusivamente `urllib.request.urlopen` de Ollama; conserva el cliente, prompt, servicio y validación reales de IA.
Las claves/URLs privadas solo pasan al entorno del proceso. El runner redacta valores privados en la salida y no los guarda en el repositorio.

Una ejecución adicional, exclusivamente del flujo con Ollama real:

```powershell
uv run python tests/integration/run_snapshot.py --real-ollama
```

Hace una sola llamada `/generation` con `qwen2.5:3b` en `http://localhost:11434`; no ejecuta de nuevo los casos con mocks.
No usar una URL de base de desarrollo al ejecutar los tests directamente. El módulo requiere activación explícita y está pensado para este runner.
Las guardas exigen PostgreSQL/Psycopg, host local y administración sobre `postgres`; los nombres a eliminar se generan internamente con UUID.
El runner consulta el catálogo antes/después y no elimina bases existentes que no hayan sido creadas por sus fixtures.

## Flujo comprobado

1. Login del docente A y lectura de su identidad desde la cookie firmada.
2. Consulta de grados/asignaturas y filtro conjunto de contenidos curriculares.
3. `POST /generation`, validación de `TeachingPlanDraft` y comprobación de que generación no guarda planes.
4. Revisión simulada previa al guardado: cambia una actividad y añade observaciones; vuelve a validar el JSON.
5. `POST /plans` con el borrador completo bajo `content` e IDs curriculares separados; respuesta 201.
6. Cierre del pool y lectura desde una conexión nueva: contenido íntegro, autor correcto, fechas y tipo PostgreSQL `jsonb`.
7. Listado y detalle del docente A coinciden con la planificación guardada.
8. El docente B no ve el plan en su historial y recibe 404 al solicitar su ID.
   B puede crear su propio plan; A tampoco puede acceder a él. Un `user_id` enviado en el cuerpo recibe 422.
9. Logout responde 204, elimina la cookie del cliente y las siguientes peticiones a identidad, planes y generación reciben 401.

Se verificaron también: credenciales incorrectas/inactivas, desactivación consultada nuevamente en PostgreSQL,
IDs inexistentes (404), referencias incoherentes y solicitudes inválidas (422), fallos Ollama (502/503/504),
y error SQL controlado (503, simulado en la dependencia para comprobar saneamiento HTTP).
Los casos fallidos no persistieron planes.

El rollback de guardado se comprobó causando una violación CHECK **real en la tabla temporal de la prueba**:
`POST /plans` devolvió 500 genérico, no quedó ninguna fila y la petición válida posterior guardó correctamente.
No se alteraron modelos compartidos ni tablas de desarrollo para provocar ese fallo.

## Resultados

- Suite de Cris más casos nuevos: **167 passed, 1 skipped, 1 warning**, 23.06 segundos.
  Son 140 casos preexistentes de Cris y 27 casos propios; la única omisión es la inferencia real opcional, ejecutada por separado.
- La advertencia sigue siendo `StarletteDeprecationWarning` por el uso de httpx en TestClient.
- El catálogo de bases temporales quedó igual antes/después de esa ejecución: ningún residuo nuevo.
- Flujo adicional con Ollama real: **1 passed, 1 warning**; 65.01 segundos dentro del flujo y 66.17 segundos de pytest.
  Se hizo una sola generación con `qwen2.5:3b`, validación Pydantic, revisión simulada, guardado/lectura JSONB,
  comprobación de propietarios y logout. No se sustituyó el cliente Ollama ni su transporte en esta ejecución.
- Tras esa segunda ejecución el catálogo temporal también quedó igual antes/después: ningún residuo nuevo.

## Límites observados y coordinación

No se encontraron fallos inesperados en el flujo con mocks. Se reprodujeron dos decisiones pendientes ya visibles en la implementación:

- **Logout:** una cookie copiada antes del cierre puede reutilizarse y obtener identidad con 200.
  El cliente que cerró sesión correctamente recibe 401. La cookie firmada no tiene revocación de servidor.
  Cris y el equipo deben decidir si el MVP requiere revocación inmediata; si la requiere, coordinar un mecanismo de invalidación de servidor,
  porque borrar la cookie del navegador no basta. No se implementó ningún cambio de autenticación.
- **Catálogos:** permiten lectura anónima. Confirmar con Cris si se conserva esa política o si deben exigir sesión.
  No se cambió su router ni se trata este comportamiento como un contrato aprobado.

Con Alejandra y Cris faltan aprobación del formato pedagógico mínimo, versión/metadatos, reglas de coherencia textual y edición.
Las referencias se validan por ID; el servicio no garantiza que los nombres escritos dentro del borrador coincidan con la selección.
La revisión del docente se simuló editando el JSON antes del POST, no fue una evaluación de calidad pedagógica humana.
No existe todavía endpoint de edición de planes en el snapshot probado.

Quedó adelantada la comprobación de autenticación → catálogo → generación → revisión → guardado → historial/detalle,
con PostgreSQL real y aislamiento de propietarios, primero con Ollama simulado y después con Ollama real.
No equivale a una instalación completa ni a una prueba de despliegue Docker del backend:
se usó la aplicación ASGI de Cris directamente en Python.

Para el viernes 16: reproducir instalación y arranque desde clon limpio, comprobar el backend Docker con las rutas actuales,
incorporar acuerdos/edición cuando estén implementados y repetir regresión sobre la integración final.
Los datos curriculares oficiales y la aprobación pedagógica deben coordinarse, no inventarse para cerrar la demostración.

## Alcance Git

Solo se agregan estas tres pruebas/helpers propios y este documento. No se modifican archivos de Cris o Alejandra,
contratos, dependencias, README, `.env` ni código de producción. El commit local se crea después de revisar resultados y secretos.
No se publica, no se fusionan ramas ni se abre otro PR.
