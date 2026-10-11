# Flujo de trabajo del equipo

## Ramas y entregas

`main` conserva versiones estables y `Cris-develop` es la rama de integración publicada para esta etapa. El equipo trabajará en ramas individuales como `feature/core-auth-cris`, `feature/ai-infra-jean` y `feature/plans-catalogs-alejandra`, creadas desde `Cris-develop` y con PR hacia esa misma rama. Antes de iniciar trabajo paralelo, cada integrante debe actualizar la rama de integración y crear su rama de trabajo. No se harán push ni merges automáticos sin revisión.

Los commits futuros deben ser pequeños y descriptivos. Cada PR debe explicar el cambio, las pruebas ejecutadas y cómo reproducirlas; Cris revisa contratos e incompatibilidades y el autor corrige su módulo antes de integrar. Nadie modifica archivos de otro módulo sin avisar y coordinar. `main.py` queda bajo Cris; Jean y Alejandra exportan routers. `compose.yaml` queda bajo Jean; `pyproject.toml` y `uv.lock` son la fuente oficial de dependencias y sus cambios se coordinan entre Cris y Jean. Los modelos compartidos quedan bajo Cris durante la semana.

## Hitos del 10 al 16 de octubre

| Fecha | Coordinación esperada |
| --- | --- |
| Sábado 10 | Cris y Jean acuerdan configuración, modelos y contratos. Cris entrega modelos base; Jean prepara infraestructura y Ollama. |
| Domingo 11 | Alejandra comienza catálogos sobre contratos publicados; Cris trabaja cuentas precreadas; Jean el cliente de IA. |
| Lunes 12 | Se revisan autenticación, catálogos y servicio de IA aislados; se acuerda el esquema de salida de IA. |
| Martes 13 y miércoles 14 | Se completan generación, guardado, edición, historial y pruebas de módulos. |
| Jueves 15 | Primera integración completa en `Cris-develop` y prueba del flujo principal. |
| Viernes 16 | Regresión, corrección de fallos críticos y documentación de arranque verificada. |

El plan estima unas cinco horas diarias por persona, con sincronización al inicio y registro de bloqueos al final. Si un contrato no está listo, se puede avanzar con mocks o datos de ejemplo acordados, sin presentar el módulo como integrado.

## Uso responsable de Codex

Antes de pedir cambios, indicar rama, módulo, responsable y criterio de aceptación. El asistente debe revisar el estado de Git, leer [AGENTS.md](../AGENTS.md), distinguir contratos confirmados de propuestas y mantener el cambio dentro del alcance del día. Debe mostrar diferencias y pruebas reales, explicar los pendientes y pedir coordinación antes de tocar archivos de otro responsable. No debe hacer push o merge por iniciativa propia ni copiar datos personales de las fotos docentes.
