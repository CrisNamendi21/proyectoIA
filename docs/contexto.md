# Contexto y alcance de Colegio Alfa

## Problema y propósito

El equipo quiere apoyar a docentes en la elaboración y consulta de planificaciones didácticas. El flujo de trabajo puede aprovechar una propuesta generada por IA, pero requiere revisión humana antes de guardarla. El proyecto de esta semana se centra en el backend que sostiene ese flujo; la eficacia pedagógica de las propuestas todavía deberá validarse con el colegio.

## Usuarios y flujo confirmado para el MVP

El usuario previsto es un docente con una cuenta precreada. El flujo acordado es: autenticarse, seleccionar grado/asignatura/contenido curricular, pedir una propuesta a Ollama, revisarla o editarla, guardarla en PostgreSQL y consultar después su historial personal. El plan semanal exige validación de endpoints y pruebas mínimas, además de manejo de fallos del servicio de IA.

## Límites de la semana

El objetivo entre el 10 y el 16 de octubre de 2026 es un backend funcional y defendible, no un sistema listo para producción. Frontend completo, React, exportación PDF, panel administrativo completo, recuperación de contraseña y fine-tuning con Unsloth quedan fuera del objetivo principal. No se incorporarán MongoDB, una base vectorial, pgvector, RAG ni microservicios sin necesidad comprobada y acuerdo del equipo.

## Referencias pedagógicas y cautela

Las fotografías facilitadas muestran ejemplos de planificación de Matemática de quinto y sexto grado. Se distinguen campos como indicador de logro o competencia, sección, contenidos, criterios y actividades de evaluación, instrumento y fechas. Una imagen adicional muestra trabajo de aula en un cuaderno. Estas fotos sirven para conversar sobre necesidades docentes; no establecen una plantilla obligatoria, una estructura final de `Planning` ni datos curriculares oficiales. No se trasladan nombres, firmas ni otros datos personales de esas imágenes al repositorio.

Faltan el documento de requerimientos funcionales, entrevistas y una ficha oficial validada para el sistema. La forma definitiva de una planificación, sus reglas de aprobación y sus campos académicos deberán confirmarse con el equipo y el colegio.
