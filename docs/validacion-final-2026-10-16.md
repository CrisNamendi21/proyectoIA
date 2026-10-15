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
