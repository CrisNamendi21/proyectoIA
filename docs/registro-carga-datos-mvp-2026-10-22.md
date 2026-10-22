# Registro de carga de datos del MVP — 22 de octubre de 2026

## Alcance aprobado

Cris decidió cerrar la etapa 3 sin depender de otra intervención humana. Para el entorno local del MVP se aprobó una selección interna basada en la **Guía para Maestros - Matemática 5° grado** publicada por el MINED. Esta aprobación pertenece al proyecto y no se presenta como una aprobación institucional del Colegio Alfa ni como una reproducción completa del currículo nacional.

El archivo de entrada y las credenciales iniciales permanecen en `data/private/`, fuera de Git. El repositorio conserva únicamente esta evidencia sin contraseñas, hashes ni identificadores de cuenta.

## Catálogo cargado

| Dato | Resultado |
| --- | --- |
| Versión del esquema | 1 |
| Grados | 1 |
| Asignaturas | 1 |
| Contenidos | 13 |
| SHA-256 del archivo aprobado | `e2e8c54e80ac8549016e0f605b8e048acf7842612bc101eeaf019018d2a7ac49` |
| Primera ejecución | 1 grado, 1 asignatura y 13 contenidos creados |
| Segunda ejecución | 0 registros creados; 15 registros reconocidos como existentes |

Fuente curricular: [Guía para Maestros - Matemática 5° grado del MINED](https://www.mined.gob.ni/biblioteca/wp-content/uploads/2024/09/Guia-5to-MATEMATICA-BAJA-1.pdf).

## Cuentas cargadas

Se crearon tres identificadores técnicos de docente. Las contraseñas iniciales se generaron aleatoriamente, cumplen el mínimo de 15 caracteres y están disponibles solo en el archivo privado local. Una segunda ejecución creó cero cuentas, conservó los tres hashes y comprobó que cada contraseña corresponde a su hash Argon2id sin aparecer en texto plano dentro de la base de datos.

## Estado

La etapa 3 queda operativamente completada en la base PostgreSQL local. Si el volumen local se elimina, la reposición se realiza con los archivos privados del equipo y el procedimiento de [carga controlada](carga-datos-oficiales.md).
