# Validación técnica final — viernes 16 de octubre de 2026

Responsable: Cris. Rama de trabajo: `Cris-develop`.

## Objetivo

Comprobar que el backend integrado puede instalarse, arrancar y ejecutar el flujo disponible de forma estable. El viernes se reserva para pruebas integrales, corrección de defectos críticos y revisión técnica. No se añadirán módulos funcionales nuevos.

## Línea base revisada

La revisión inicial se realizó con `Cris-develop` limpio y sincronizado en `972744e`.

| Rama remota | Último commit revisado | Estado respecto de `Cris-develop` |
| --- | --- | --- |
| `main` | `2e164c5` | Contiene el cierre del jueves de Cris mediante merge. No tiene código funcional adicional pendiente de traer a Cris. |
| `feature/ai-infra-jean` | `1c187bd` | Completamente integrada mediante `3810afe`. No tiene commits remotos pendientes. |
| `Alejandra-develop` | `b9f7a46` | Todo lo publicado está integrado mediante `c607ad1`. No hay un avance remoto posterior. |

La evidencia previa más reciente corresponde al flujo integrado sobre `3810afe`: **167 pruebas aprobadas, 1 omitida y 1 advertencia conocida**, con PostgreSQL real desechable y Ollama simulado. El commit `972744e` posterior modifica únicamente documentación.

## Alcance cerrado del viernes

1. Comprobar el entorno reproducible: Python 3.12, uv, lockfile, Compose, PostgreSQL, API y configuración de Ollama.
2. Ejecutar la regresión normal y la suite integrada con PostgreSQL desechable.
3. Ejecutar una prueba real de extremo a extremo si Ollama y el modelo están disponibles.
4. Corregir exclusivamente defectos críticos demostrados por las verificaciones.
5. Repetir las comprobaciones afectadas y cerrar la revisión técnica.
6. Auditar el estado final, comprobar la integración con `main` y preparar la entrega al equipo.

Cada bloque termina con una verificación, un commit descriptivo y un push a `origin/Cris-develop`. El merge posterior hacia `main` requiere una instrucción expresa.

## Criterios de aprobación

- `uv lock --check` y la instalación bloqueada terminan correctamente con Python 3.12.
- La configuración versionada de Compose es válida y PostgreSQL alcanza estado saludable sin borrar el volumen.
- La API arranca y `/health` responde correctamente.
- Autenticación, identidad, catálogos, generación y planificaciones conservan sus contratos actuales.
- Las rutas protegidas rechazan una sesión ausente, inválida o perteneciente a una cuenta inactiva.
- Un docente no puede consultar ni atribuirse la planificación de otro.
- El borrador IA validado puede conservarse completo en JSONB con los IDs curriculares separados.
- Los fallos de PostgreSQL y Ollama producen respuestas controladas y no dejan escrituras parciales.
- Las pruebas no usan ni eliminan la base de desarrollo y no dejan bases temporales.
- `.env`, credenciales, archivos de base, salidas privadas y artefactos temporales permanecen fuera de Git.
- El estado final de Git queda limpio y sincronizado con `origin/Cris-develop`.

## Pendientes conocidos al iniciar

- El `.env` local de Cris no coincide con la contraseña conservada en el volumen PostgreSQL y no incluye todas las variables de `.env.example`. Debe sincronizarse sin publicar valores ni borrar datos.
- Ollama no estaba instalado ni activo en el entorno de Cris durante la última comprobación. No se declarará una inferencia real nueva si continúa ausente.
- Alejandra todavía no ha publicado la edición de planificaciones ni su aprobación del formato completo de `Planning.content` y del acceso público a catálogos.
- La versión y los metadatos de `Planning.content`, la coherencia semántica entre textos e IDs y la posible revocación de sesión en servidor siguen siendo decisiones del equipo.
- La credencial local de PostgreSQL mencionada en el historial debe rotarse y sincronizarse; no se registrará su valor en documentación, comandos compartidos ni commits.

Estos pendientes se documentan y se prueban hasta donde permita el código publicado. No justifican implementar durante el viernes responsabilidades funcionales aún no entregadas por Alejandra.

## Evidencia requerida por bloque

Cada comprobación debe registrar el comando o procedimiento reproducible, el commit probado, el resultado exacto, las omisiones y cualquier limitación. Una prueba omitida, una dependencia ausente o un flujo simulado se describen como tales; no se presentan como verificaciones reales.

## Resultado del módulo 2 — entorno reproducible

Línea base: `5f69d1b` en `Cris-develop`.

- uv `0.12.10`, Python local `3.12.14`, `uv lock --check` y `uv sync --locked`: correctos.
- Docker Engine `29.8.0` y Docker Compose `5.5.1`: disponibles después de iniciar Docker Desktop.
- El `.env` local se completó con las once variables de `.env.example` y se sincronizó con la configuración del contenedor existente. Se conservó la clave de sesión, no se mostró ningún valor y el archivo continúa ignorado por Git.
- `docker compose config --quiet` y `docker compose up -d --build`: correctos. La imagen usa Python `3.12.15` y las versiones bloqueadas por `uv.lock`.
- PostgreSQL inició en estado saludable conservando el volumen. `SELECT 1` devolvió `1` sobre `colegio_alfa_db`.
- La base de desarrollo no tenía tablas. Se ejecutó explícitamente `python -m app.db.init_db` dentro del backend y quedaron disponibles `users`, `grades`, `subjects`, `curriculum_contents` y `plannings`. No se borraron datos ni volúmenes.
- El backend respondió `{"status":"ok"}` en `/health`.
- La API de Ollama no está disponible y no hay una instalación local registrada. La inferencia real del módulo 4 continúa bloqueada hasta disponer de Ollama y `qwen2.5:3b`.

El entorno queda con `backend` y `alfa-db` en ejecución para la regresión del módulo 3. La credencial se sincronizó para el entorno actual, pero su rotación por haber aparecido históricamente continúa pendiente; ningún valor privado se incorporó al repositorio.

## Resultado del módulo 3 — regresión automatizada

Commit probado: `5c759dd94b6f5bb0708f6c727ce9ca5d8bae38bf`.

### Suite normal

Comando: `uv run pytest -q`.

- **137 pruebas aprobadas**.
- **4 pruebas omitidas** porque requieren activación explícita de PostgreSQL o del flujo integrado.
- **1 advertencia conocida** de Starlette sobre el uso de httpx en `TestClient`.
- Duración: **9.55 segundos**.

### Suite integrada

Comando: `uv run python tests/integration/run_snapshot.py --ref HEAD`.

- **167 pruebas aprobadas**.
- **1 prueba omitida**: la inferencia con Ollama real.
- **1 advertencia conocida** de Starlette/httpx.
- Duración de pytest: **33.18 segundos**.
- Código ejecutado desde un snapshot inmutable del commit indicado.
- PostgreSQL real con una base desechable nueva por caso.
- Ollama simulado únicamente en el transporte HTTP; FastAPI, autenticación, servicios, validación y persistencia permanecieron reales.

La regresión integrada cubrió login, identidad, cuentas inactivas, catálogos, generación, errores de Ollama, revisión simulada del borrador, guardado JSONB, referencias inválidas, aislamiento de dos docentes, rollback de escritura, saneamiento de errores, historial, detalle y logout.

El catálogo de bases temporales se comprobó de forma independiente antes y después: comenzó y terminó con **0 bases de prueba**. El runner también informó `temporary_database_catalog_unchanged: true` y `new_leftover_databases: 0`. La API continuó respondiendo correctamente en `/health`.

No se detectaron regresiones ni defectos críticos y no fue necesario modificar código productivo en este módulo. `backend` y `alfa-db` permanecen en ejecución para el módulo 4.

## Resultado del módulo 4 — smoke test HTTP real

Línea base: `a328149` en `Cris-develop`. Desde el módulo anterior no hubo cambios en `app/`; la imagen utilizada contiene el mismo código productivo.

Se creó una base PostgreSQL temporal `colegio_alfa_e2e_test_<uuid>` y se levantó un segundo contenedor del backend en la red de Compose y en un puerto dinámico local. La base recibió exclusivamente dos docentes y referencias curriculares ficticias. Las credenciales del entorno y la clave de sesión pasaron mediante un archivo temporal eliminado inmediatamente después de iniciar el contenedor.

Comprobaciones realizadas mediante HTTP real:

- `/health`, login, `/auth/me` y catálogos: correctos.
- `POST /generation`: **503 controlado**, porque no existe un servicio Ollama en el entorno.
- El fallo de generación no se trató como una propuesta válida ni como una inferencia comprobada.
- Para continuar verificando la parte independiente de IA se envió a `POST /plans` un borrador ficticio preparado manualmente y compatible con la forma de `TeachingPlanDraft`.
- Guardado, listado, detalle y persistencia de `Planning.content`: correctos; quedó una fila únicamente dentro de la base temporal.
- Un segundo docente obtuvo un historial vacío y respuesta 404 al solicitar el plan del primer docente.
- Logout: 204; la consulta posterior de identidad devolvió 401.

Al finalizar se detuvieron y eliminaron el contenedor temporal y su archivo de entorno, y se eliminó la base temporal. Una comprobación posterior encontró **0 contenedores E2E** y **0 bases E2E** residuales. El backend principal continuó respondiendo correctamente en `/health`.

### Límite del resultado

La inferencia real continúa **bloqueada**: Ollama no está instalado, su API no responde y `qwen2.5:3b` no puede verificarse en este equipo. El smoke test demuestra el transporte HTTP, PostgreSQL y el flujo posterior con un borrador manual; no demuestra una generación real. No se modificó código productivo para ocultar o evitar esta limitación.

## Resultado del módulo 5 — revisión crítica y cierre técnico

Línea base revisada: `d6a85af` en `Cris-develop`.

Se inspeccionaron el arranque de FastAPI, la configuración, las dependencias de sesión y usuario autenticado, los routers de autenticación, generación y planificaciones, la validación de esquemas, la persistencia y el aislamiento por propietario. No se encontraron defectos críticos nuevos en el código productivo:

- Una sesión ausente, inválida o asociada a un usuario inactivo produce 401 y no conserva una identidad utilizable.
- La generación exige autenticación y convierte los fallos de Ollama en respuestas controladas.
- El propietario de una planificación se obtiene de la sesión; no puede ser atribuido mediante el cuerpo de la petición.
- El listado y el detalle filtran por propietario, y las escrituras aplican rollback ante errores de dominio o persistencia.
- `Planning.content` valida que el contenido sea JSON finito antes de almacenarlo.

### Corrección crítica aplicada al entorno local

Se rotó la credencial activa de PostgreSQL que había aparecido en antecedentes del proyecto. La operación conservó el volumen y los datos existentes, actualizó únicamente el `.env` local ignorado por Git y no mostró ni versionó valores privados. Una conexión nueva con la credencial anterior fue rechazada y otra con la nueva devolvió `SELECT 1 = 1`.

Después de recrear `alfa-db` y `backend`, PostgreSQL volvió a estado saludable, `/health` respondió `ok` y continuaron disponibles las cinco tablas: `users`, `grades`, `subjects`, `curriculum_contents` y `plannings`.

### Regresión posterior a la corrección

Comando: `uv run python tests/integration/run_snapshot.py --ref HEAD`.

- **167 pruebas aprobadas**.
- **1 prueba omitida**: inferencia con Ollama real.
- **1 advertencia conocida** de Starlette/httpx.
- Duración de pytest: **32.69 segundos**.
- El runner informó `temporary_database_catalog_unchanged: true` y `new_leftover_databases: 0`.

La revisión del árbol actualmente versionado no encontró claves privadas ni tokens reales. Las URLs con contraseña detectadas corresponden al valor demostrativo de `.env.example`, credenciales ficticias de pruebas y un texto de error usado para comprobar su saneamiento. `.env` continúa ignorado y no se versionaron archivos de base de datos, claves ni certificados.

### Límites y pendientes comunicados

- La credencial histórica puede permanecer en commits anteriores, aunque ya no permite acceder al PostgreSQL local revisado. Reescribir historia compartida requiere una decisión separada del equipo.
- Ollama y `qwen2.5:3b` siguen ausentes; la inferencia real permanece sin verificar.
- La edición de planificaciones y las decisiones contractuales pendientes de Alejandra no se implementaron durante esta revisión, porque constituirían funcionalidad nueva fuera del cierre técnico del viernes.

Con la corrección local y la regresión completadas, no quedan bloqueos críticos demostrados en el flujo actualmente publicado. La limitación de Ollama y los contratos aún no acordados permanecen visibles para el equipo.

## Resultado del módulo 6 — auditoría final y preparación de entrega

Línea base revisada: `bfa2b81` en `Cris-develop`.

Se actualizó la información remota antes de revisar el cierre. Los commits publicados en `origin/Alejandra-develop` y `origin/feature/ai-infra-jean` están contenidos en `Cris-develop`; no hay trabajo nuevo de esas dos ramas pendiente de integrar.

`origin/main` y `Cris-develop` tienen historiales divergentes por los merges previos hacia `main`: antes de este cierre existían dos commits exclusivos de `main` y cinco commits de validación exclusivos de `Cris-develop`. Una integración virtual mediante `git merge-tree --write-tree origin/main Cris-develop` terminó con código 0 y **sin conflictos**. No se modificó `main` ni se ejecutó el merge real.

### Comprobaciones finales

- `uv lock --check`: correcto; el lockfile resolvió 41 paquetes sin cambios.
- `docker compose config --quiet`: correcto.
- PostgreSQL: contenedor activo y saludable.
- Backend: contenedor activo y `/health` respondió `ok`.
- OpenAPI publicó las diez rutas previstas: salud, login, logout, identidad, tres catálogos, generación, listado/creación de planes y detalle de plan.
- `git diff --check origin/main...Cris-develop`: correcto.
- No existen cambios en `app/`, `tests/`, dependencias, Docker o Compose desde la suite integrada de 167 pruebas registrada en el módulo 5; los commits posteriores contienen únicamente esta evidencia documental.

### Estado de entrega

El alcance actualmente publicado queda listo para revisión e integración de `Cris-develop` hacia `main`. La entrega demostrada incluye arranque reproducible, autenticación por sesión, catálogos, generación con transporte simulado, guardado e historial con aislamiento por docente, manejo controlado de fallos y PostgreSQL real.

La afirmación anterior conserva estos límites:

- La inferencia real no se considera aprobada en este equipo mientras falten Ollama y `qwen2.5:3b`.
- La edición de planificaciones y los contratos que Alejandra aún debe confirmar continúan pendientes.
- La credencial local expuesta anteriormente fue rotada, pero sanear el historial compartido requiere una decisión del equipo.

La rama queda preparada para el merge; la integración efectiva en `main` se realizará únicamente cuando Cris la ordene y después de revisar este informe.
