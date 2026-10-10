# Colegio Alfa

Backend de un MVP universitario que ayudará a docentes a generar, revisar, editar, guardar y consultar planificaciones didácticas. El objetivo de la semana del **10 al 16 de octubre de 2026** es dejar funcional el flujo de cuenta precreada → selección curricular → propuesta con Ollama → edición → guardado → historial.

## Estado

**Preparación documental.** Aún no hay aplicación, endpoints, modelos, configuración de Docker ni instrucciones de arranque verificadas. El trabajo de código comenzará después de acordar los contratos compartidos. Este repositorio no está listo para ejecutarse.

## Stack acordado

Python 3.12, FastAPI, Uvicorn, Pydantic, SQLAlchemy 2, PostgreSQL en Docker, Docker Compose, Ollama local, pytest y Git/GitHub. El uso previsto de JSONB permite conservar el contenido pedagógico flexible de una planificación en PostgreSQL. No se ha acordado añadir otras bases de datos o componentes de IA.

## Equipo

| Integrante | Responsabilidad principal |
| --- | --- |
| Cris | Core de FastAPI, conexión y modelos de base de datos, autenticación, integración técnica. |
| Jean | Infraestructura, dependencias, Docker Compose, servicio de IA con Ollama. |
| Alejandra | Catálogos académicos, planificaciones, validaciones de propiedad y pruebas de esos módulos. |

Los contratos y archivos compartidos se coordinan entre los tres; la responsabilidad principal no impide revisión conjunta.

## Organización prevista

La estructura `app/` y `tests/` descrita abajo es **propuesta**, no existe todavía. La estructura actual contiene esta documentación y `.gitignore`.

```text
app/                 API, core, acceso a datos, modelos, esquemas y servicios (pendiente)
tests/               Pruebas automatizadas (pendiente)
docs/                Contexto y acuerdos de integración
AGENTS.md            Instrucciones de trabajo para asistentes
README.md            Entrada al proyecto
```

## Documentación

- [Contexto y alcance](docs/contexto.md)
- [Arquitectura propuesta](docs/arquitectura.md)
- [Modelo de datos](docs/modelo-datos.md)
- [Contratos por acordar](docs/contratos.md)
- [Flujo de trabajo](docs/flujo-trabajo.md)
- [Decisiones pendientes](docs/decisiones-pendientes.md)

Los comandos de instalación, pruebas y arranque se añadirán cuando la implementación permita verificarlos. Jean coordinará la configuración de Docker y las instrucciones técnicas de ejecución con el equipo.
