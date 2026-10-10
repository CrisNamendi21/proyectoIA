# Modelo de datos compartido

## Estado del diseño

El plan confirma la existencia mínima de cinco entidades: `User`, `Grade`, `Subject`, `CurriculumContent` y `Planning`. No define todavía columnas, cardinalidades ni restricciones exactas. La tabla siguiente separa la responsabilidad confirmada de atributos y relaciones **propuestos** para discutir el sábado 10; nada de lo propuesto es un esquema aprobado o implementado.

| Entidad | Responsabilidad confirmada | Atributos propuestos, pendientes de acuerdo | Relaciones propuestas, pendientes de acuerdo |
| --- | --- | --- | --- |
| `User` | Representar cuentas docentes precreadas y propiedad del historial. | `id`, identificador de acceso, hash de contraseña, estado de cuenta. | Un usuario posee muchas `Planning`. |
| `Grade` | Permitir seleccionar y consultar grados. | `id`, nombre o código. | Un grado puede agrupar contenidos curriculares y planificaciones. |
| `Subject` | Permitir seleccionar y consultar asignaturas. | `id`, nombre o código. | Una asignatura puede agrupar contenidos y planificaciones. |
| `CurriculumContent` | Representar el contenido curricular que selecciona el docente. | `id`, descripción y referencias a grado/asignatura si el catálogo real lo exige. | Podría pertenecer a un grado y una asignatura; una planificación podría referenciarlo. |
| `Planning` | Guardar una planificación editable y recuperable en el historial de su docente. | `id`, `user_id`, referencias curriculares, cuerpo JSONB, fechas de creación/actualización. | Pertenece a un usuario; podría vincularse a grado, asignatura y contenido. |

Los identificadores, claves foráneas, índices, unicidad, borrado y nulabilidad se decidirán al cerrar contratos. El mecanismo de autenticación determinará qué identificador de `User` y qué campos de credenciales son adecuados. El formato JSONB y el tratamiento de versiones o cambios de ficha siguen pendientes.

## Grado y sección

`Grade` representa el **grado académico** (por ejemplo, quinto o sexto). Una **sección** distingue grupos dentro de un grado. Las fotos muestran “sección” en una ficha, pero el plan no exige aún modelarla como entidad ni como columna. El equipo debe confirmar si existe catálogo de secciones, si la sección es texto libre o si queda dentro del cuerpo de planificación. No se debe usar `Grade` para guardar ambos conceptos.

## Información aún necesaria

Se requieren el catálogo curricular real, las reglas de asociación grado–asignatura–contenido, una ficha oficial de planificación y las decisiones de autenticación. Las fotos son ejemplos y no justifican declarar obligatorios campos académicos como indicador, contenido, evaluación o fechas. Se documentarán cuando el colegio valide el formato.
