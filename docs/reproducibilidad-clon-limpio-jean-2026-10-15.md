# Reproducibilidad desde clon limpio — adelanto del viernes

Ejecutado el jueves 15 de octubre de 2026 por Jean. No se cambia la fecha de trabajo por la fecha del documento de cierre de Cris.
Este informe complementa la [guía de infraestructura](infraestructura-jean.md) y la [prueba ASGI previa](verificacion-flujo-integrado-jean-2026-10-14.md).

## Línea base y revisión del equipo

- Rama habitual: `feature/ai-infra-jean`, inicialmente limpia en `1c187bd`, coincidente con su remoto.
- Integración probada: `Cris-develop`, commit **`3c739de738bf1eec6ddb7c8d57853e4efdc04270`**.
- `origin/main`: `2e164c58485bab39e4de7b6312cba98ff5d1671a`; tiene el mismo código productivo, pero no los cuatro documentos/actualizaciones posteriores de Cris.
- `origin/Alejandra-develop`: `63e2480`, con `PATCH /plans/{plan_id}` y pruebas de edición, todavía **no integrado** en Cris.
  El cierre anterior de Cris que decía que esa edición no estaba publicada quedó desactualizado por este avance.
- Los PR #1 y #2 están fusionados y cerrados, sin comentarios ni solicitudes de cambios registrados al consultarlos.
- No se fusionaron ramas ni se modificó el checkout habitual para probar el código integrado.
  Los cambios productivos de Cris siguen siendo los mismos que en `31a569a`; sus avances posteriores corresponden a documentación/evidencia.

## Aislamiento y clon real

Se ejecutó un **git clone por HTTPS** del repositorio remoto, seleccionando `Cris-develop`, en una carpeta nueva fuera del repositorio habitual.
No fue un snapshot de archivos ni una copia del checkout de Jean. Se comprobó que no existían `.env` ni `.venv` antes de preparar el entorno.

Se creó una `.venv` nueva con `uv sync --locked` y una caché uv temporal vacía; se descargaron/instalaron 39 paquetes de host.
Python de Windows: **3.12.2**. Docker Engine: **29.8.2**; Compose: **5.5.1**.
No se copiaron dependencias, archivos temporales ni configuración privada del repositorio habitual.

La `.env` nueva se preparó desde `.env.example`, con contraseña PostgreSQL y clave de sesión generadas para esta prueba y sin mostrarlas.
Se cambió el nombre de la base y del usuario de la instancia temporal; no se reutilizaron credenciales de desarrollo.

Proyecto Compose exclusivo: `alfa-clean-6fd98aaf4939`, con imagen propia, red y volumen nuevos.
Un override temporal reemplazó los puertos por mapeos libres de loopback; la aplicación conservó `alfa-db:5432` internamente y Ollama en `host.docker.internal:11434`.
No se alteró `compose.yaml` versionado ni se arrancaron los servicios habituales `proyectoia`.
El volumen preexistente `proyectoia_alfa-db-data` quedó fuera de todas las operaciones de preparación y prueba.

## Instalación, build y arranque

- `uv sync --locked`: correcto, respetando `pyproject.toml` y `uv.lock` del clon.
- Compose config con proyecto/override explícitos: correcto.
- `docker compose ... build --no-cache backend`: correcto; dependencias de producción instaladas desde lock, sin reutilizar esa capa de build.
- Python dentro de la imagen: **3.12.15**, con 30 paquetes de producción y las dependencias de plataforma correspondientes.
- `docker compose ... up -d --wait`: correcto; PostgreSQL healthy y backend running.
- `python -m app.db.init_db` dentro del backend: correcto; cinco tablas nuevas, sin copiar datos.
- `GET /health` por HTTP real: **200**, `{"status":"ok"}`.
- `SELECT 1` desde el backend a su PostgreSQL temporal: **1**.
- Comunicación backend → Ollama Windows: **HTTP 200** en `/api/tags`, con `qwen2.5:3b` disponible.
- OpenAPI del servidor Docker: autenticación, catálogos, generación y planes registrados. La edición no pertenece a esta integración.

Los docentes se cargaron usando `create_user_if_missing`, la función existente de Cris, con contraseñas aleatorias de prueba.
Se comprobó su idempotencia. No se fingió una ejecución interactiva de su CLI.
Grado, asignatura y contenido fueron fixtures ficticias insertadas únicamente en la instancia temporal, no un catálogo oficial.

## Resultados diferenciados

### Suite automatizada desde el clon

Se ejecutó `python -m pytest -q` con el intérprete de la `.venv` nueva, PostgreSQL habilitado y la URL administrativa de la instancia temporal sobre `postgres`.
Se activaron `COLEGIO_ALFA_TEST_POSTGRES=1` y `COLEGIO_ALFA_TEST_AI_FLOW=1`; `COLEGIO_ALFA_TEST_REAL_OLLAMA=0`.

Resultado: **167 passed, 1 skipped, 1 warning**, en **24.42 segundos**. Ninguna prueba falló.
La omisión es la generación ASGI real opcional: se reservó la única inferencia adicional para el backend Docker.
La advertencia sigue siendo Starlette/httpx.

Esta suite usa aplicación ASGI, servicios y PostgreSQL real, con transporte Ollama simulado.
No se presenta como evidencia de tráfico HTTP hacia el contenedor.

### HTTP real hacia backend Docker

Se ejecutó el nuevo helper propio `tests/integration/run_docker_http.py` con el Python del clon.
Reutiliza la entrada curricular de las pruebas existentes, verifica la identidad del proyecto Docker y envía solicitudes de red con cookies.
No sustituye autenticación, servicios, persistencia ni el transporte de Ollama y no usa TestClient para esas peticiones.
Resultado: **smoke HTTP aprobado, 28 solicitudes, ninguna comprobación fallida**.
La única generación válida con `qwen2.5:3b` tardó **81.75 segundos**; el flujo del helper, **82.77 segundos**.
Hubo tráfico HTTP real hacia el backend Docker, tráfico real de ese backend hacia Ollama y persistencia PostgreSQL real.
No se repitió inferencia ASGI ni se reintentó generación.

El flujo comprueba login, identidad, catálogos, una generación, validación Pydantic, revisión simulada, guardado y lectura JSONB desde otra conexión,
listado/detalle, aislamiento bidireccional de dos docentes, rechazo de propietario enviado por cliente y acceso después de logout.
También comprueba 401 sin sesión/credenciales incorrectas, 422 de solicitud inválida y 404 de referencias/planes ajenos.
La revisión de la propuesta es una edición de JSON en la prueba; no equivale a evaluación pedagógica humana.

## Reproducibilidad de la documentación

Otro integrante puede preparar el backend a partir del clon y de las herramientas/requisitos declarados.
Se siguen necesitando Docker Desktop y Ollama instalados en el host; no se afirma una instalación del sistema operativo ni de esas herramientas desde cero.
Se reutilizó la instalación de Ollama/modelo como requisito, no una base o configuración privada del proyecto anterior.

La guía propia se actualizó para documentar la prueba de segundo clon: proyecto/nombres/puertos exclusivos, override sin tocar Compose principal,
inicialización explícita, diferencia entre fixture curricular y carga oficial, y helper HTTP con manifiesto temporal.
El README compartido no se modificó. Propuesta para Cris: enlazar este informe y la guía, actualizar los pendientes de clon limpio/inferencia según esta evidencia
y distinguir la edición ya publicada por Alejandra de la edición integrada.

La falta de seed curricular oficial no impide arrancar ni probar con fixtures; sí debe resolverse para una demostración con datos del colegio.

## Acuerdos y límites del cierre

Los contratos remotos contienen confirmación expresa de Cris de `/generation` y de la cookie firmada de 8 horas para el MVP.
La lectura pública de catálogos está aceptada por Cris para integración, pendiente de conformidad de Alejandra.
El JSON completo `TeachingPlanDraft` dentro de `Planning.content`, con IDs separados, continúa provisional hasta su aprobación compartida.
No se encontró aprobación de Alejandra en los documentos revisados; que `PlanningUpdate` acepte JSON no establece un contrato pedagógico definitivo.

Pendientes:

- Integrar y verificar la edición `63e2480` bajo responsabilidad de Cris/Alejandra; no se fusionó ni modificó aquí.
- Acordar versión/metadatos y coherencia entre nombres curriculares e IDs. La validación actual comprueba referencias, no equivalencia semántica del texto.
- Decidir si se requiere revocación de servidor o protección adicional para peticiones con cookies; borrar la cookie no invalida copias previas.
- Revisar credenciales por entorno, HTTPS/`SESSION_COOKIE_SECURE`, exposición de puertos, firewall y acceso a Ollama para un despliegue posterior.
- Acordar catálogo/cuentas reales, procedimiento de carga y validación pedagógica.

## Limpieza y entrega

La identidad de todos los recursos temporales se verifica mediante etiquetas Compose y comparación con el inventario previo antes de eliminarlos.
No se usa `down -v` en el proyecto habitual ni se eliminan sus contenedores o volúmenes.

- Una consulta independiente al catálogo de la instancia nueva confirmó **0 bases temporales de tests** antes de retirarla.
- Se ejecutó `stop` en el proyecto temporal y se comprobó que su volumen seguía existiendo: parada segura validada.
- Después se ejecutó `down` sin `-v` exclusivamente sobre ese proyecto y se eliminó únicamente su volumen identificado por nombre/etiquetas,
  que no figuraba en el inventario previo. También se retiró la etiqueta de imagen exclusiva de la prueba.
- Resultado final: **0 recursos Compose de ese proyecto**; contenedores y volumen de desarrollo preexistentes conservados, sin iniciarlos ni recrearlos.
- Se eliminaron la `.env` privada nueva y el override generado dentro del clon, comprobando antes que sus rutas estaban bajo la carpeta temporal propia.
- El clon real se conserva para inspección con Git limpio, sin credenciales; su `.venv` y caché de instalación son artefactos temporales esperados fuera del repositorio habitual.

Solo se conserva en la rama habitual el helper de prueba, esta evidencia y la actualización de la guía propia.
No se cambian código de Cris/Alejandra, modelos, contratos, dependencias ni README; no se hace push, merge, rebase ni PR.

## Cierre técnico de Jean y del MVP

La infraestructura, integración Ollama, generación y comprobaciones propias de Jean quedan técnicamente verificadas,
incluido el arranque desde un clon sin archivos privados previos y el flujo real del contenedor.
La demostración del recorrido disponible con datos ficticios es reproducible; falta la aceptación funcional del equipo/colegio.
No se declara terminado el MVP completo: edición publicada pero no integrada, contrato pedagógico y datos oficiales pendientes.

Para cerrar la entrega, revisar/publicar el commit propio de esta evidencia mediante una nueva entrega cuando el usuario lo autorice;
los dos PR anteriores están fusionados. Cris debe actualizar sus referencias de clon limpio/inferencia con esta evidencia y reproducir Ollama en su equipo si requiere comprobación propia.
Antes de integrar el cierre en `main`, revisar la edición de Alejandra en Cris, aprobar contratos/políticas pendientes y repetir las pruebas afectadas sobre el conjunto final.
