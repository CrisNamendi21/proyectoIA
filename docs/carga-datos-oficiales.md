# Carga controlada de datos oficiales

Estado al 22 de octubre de 2026. Cris aprobó y cargó un catálogo interno y tres cuentas técnicas para el entorno local del MVP. Los archivos fuente y las credenciales permanecen en `data/private/`, fuera de Git. La evidencia reproducible está en el [registro de carga](registro-carga-datos-mvp-2026-10-22.md).

## Decisión de alcance

El MINED publica documentos curriculares y describe varias modalidades de primaria. Cris eligió para el MVP una selección interna de Matemática de quinto grado basada en una guía pública del MINED. La selección permite operar y probar el proyecto, pero no se atribuye al Colegio Alfa ni se presenta como un catálogo nacional completo. No se copiaron datos desde fotografías ni datos personales reales.

Fuentes de referencia:

- [Educación Primaria del MINED](https://www.mined.gob.ni/educacion-primaria/).
- [Documentos curriculares del MINED](https://www.mined.gob.ni/biblioteca/product-category/documentos-curriculares/?per_page=64).

## Preparar y validar el catálogo

1. Copiar `data/templates/catalog.template.json` a `data/private/catalog.json`.
2. Completar los metadatos de la fuente aprobada, la persona o instancia que la aprobó y la fecha.
3. Transcribir únicamente los grados, asignaturas y contenidos aprobados. `data/private/` está ignorado por Git.
4. Validar el archivo sin escribir en PostgreSQL:

   ```powershell
   uv run python -m app.db.seed_catalogs data/private/catalog.json
   ```

5. Revisar los totales y guardar la huella SHA-256 en el registro interno de la carga. Esa huella permite comprobar qué archivo se usó sin publicar su contenido.
6. Aplicar el archivo aprobado:

   ```powershell
   uv run python -m app.db.seed_catalogs data/private/catalog.json --apply
   ```

7. Repetir la orden con `--apply`. El resultado esperado es cero registros creados y todas las entradas informadas como existentes.

La ejecución nativa necesita una `DATABASE_URL` cuyo host sea `localhost`, siguiendo el procedimiento privado ya descrito en la guía de infraestructura. No se debe imprimir ni incorporar esa URL al historial. El archivo rechaza versiones desconocidas, campos adicionales, textos vacíos y duplicados dentro de la entrada.

El cargador preserva filas existentes y solo agrega las ausentes. Hasta que la etapa de migraciones añada una restricción única para `(grade_id, subject_id, description)`, una sola persona debe realizar la carga y no deben ejecutarse dos importaciones concurrentes. PostgreSQL ofrece resolución de conflictos mediante `ON CONFLICT`, pero esta garantía necesita primero una restricción única compatible: [documentación de `INSERT`](https://www.postgresql.org/docs/current/sql-insert.html).

## Crear las cuentas docentes

La institución debe entregar los identificadores aprobados por un canal privado. Por cada cuenta se ejecuta:

```powershell
docker compose exec backend python -m app.db.seed_users <nombre_de_usuario>
```

El comando solicita la contraseña dos veces sin mostrarla, exige al menos 15 caracteres, guarda únicamente el hash Argon2id y no modifica una cuenta que ya existe. No se versionarán nombres personales, listas de docentes, contraseñas ni hashes. La contraseña debe ser única para la cuenta y entregarse al docente por un canal distinto del usado para enviar el identificador.

El mínimo de 15 caracteres sigue la recomendación vigente para contraseñas usadas como único factor; el sistema permite contraseñas largas y no exige reglas artificiales de composición. Referencias: [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/) y [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).

## Criterio de cierre operativo

La etapa 3 quedó cerrada para el MVP cuando un único operador validó y aplicó el catálogo, conservó su huella, repitió la carga sin crear duplicados y comprobó las tres cuentas técnicas. Una eventual sustitución por datos institucionales de producción queda fuera del alcance actual.
