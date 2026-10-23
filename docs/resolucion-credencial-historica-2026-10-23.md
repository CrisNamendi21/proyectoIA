# Resolución de la credencial histórica — 23 de octubre de 2026

## Decisión

Se **conserva el historial Git** y no se ejecutará `filter-repo`, rebase masivo ni `push --force`.

La credencial antigua ya está revocada, la credencial vigente es distinta y ninguna punta de rama contiene el valor anterior. Reescribir el historial no revocaría copias ya clonadas y obligaría a reemplazar referencias válidas en todas las ramas y clones. En este caso aumentaría el riesgo operativo sin mejorar la protección conseguida mediante la rotación.

Esta decisión cambiaría únicamente si apareciera una credencial todavía activa, un requisito legal o una política externa que exigiera eliminar el dato histórico. Ante ese escenario se partiría del respaldo privado documentado abajo, se volverían a rotar las credenciales antes de modificar Git y se prepararía una ventana coordinada para reemplazar todas las referencias.

## Confirmación de la rotación

La prueba se realizó contra el mismo PostgreSQL local y el mismo puerto:

- la credencial histórica es diferente de la actual;
- una conexión nueva con la credencial histórica fue rechazada;
- la credencial actual ejecutó `SELECT 1` correctamente;
- no se imprimió ni almacenó en este documento ninguno de los dos valores.

## Commits históricos afectados

La credencial apareció por primera vez en `b14881766d9a`. Se detectó en cuatro blobs pertenecientes únicamente a `README.md` y `docs/contratos.md`, presentes en estos nueve snapshots:

- `b14881766d9a`
- `cc788a33b232`
- `a1c601e98301`
- `3250eec55500`
- `dc67d912bef4`
- `d06ab4340989`
- `b8508c877ede`
- `38ac0628a16c`
- `b9f7a46fbe96`

Las distintas líneas de desarrollo retiraron el valor en `7ecf0dbe7326`, `1bf29e9d2103`, `c607ad13615b` y `43940428ac02`. Estos identificadores permiten auditar el incidente sin publicar la credencial.

## Respaldo previo

Antes de decidir se creó y verificó un bundle completo con las ramas locales y remotas conocidas:

- ubicación local ignorada: `data/private/backups/proyectoIA-before-history-decision-2026-10-23.bundle`;
- SHA-256: `06a036871e22ca9dee434e7dd1d3899903dd03da7f4b48ffc183f134c6b0158f`;
- validación: `git bundle verify` confirmó un historial completo;
- acceso: herencia de permisos retirada y acceso concedido al usuario local actual.

El bundle conserva el historial afectado y no debe publicarse, adjuntarse ni copiarse a una ubicación compartida.

## Revisión de secretos

Se revisaron las 70 revisiones alcanzables por las referencias locales y remotas. La comprobación exacta buscó, sin mostrarlos, estos seis valores vigentes: `DATABASE_URL`, `POSTGRES_PASSWORD`, `SESSION_SECRET_KEY` y las tres contraseñas iniciales de docentes. Ninguno apareció en un blob Git.

También se ejecutó Gitleaks dentro de Docker con `--redact=100` sobre el historial. Revisó 52 commits con cambios de contenido y aproximadamente 783 KB. Informó dos coincidencias `generic-api-key` en `tests/test_catalogs.py` y `tests/test_plans.py`; ambas son claves ficticias de middleware utilizadas exclusivamente en pruebas. El informe redactado permanece en `data/private/security-scan/` y no se versiona.

Todas las puntas revisadas están libres de la credencial histórica:

- `main` y `origin/main`;
- `Cris-develop` y `origin/Cris-develop`;
- `Problems_Cris`;
- `origin/Alejandra-develop`;
- `origin/Jean-develop`;
- `origin/feature/ai-infra-jean`.

El único nombre sensible versionado es `.env.example`, que contiene marcadores públicos y no credenciales activas. No se encontraron `.env`, claves privadas, certificados ni archivos de credenciales versionados.

## Coordinación de ramas y clones

Como no hay reescritura, ningún colaborador debe borrar ramas, volver a clonar ni ejecutar `reset --hard` o `push --force`. La actualización normal es:

```powershell
git fetch --all --prune
git switch Cris-develop
git pull --ff-only origin Cris-develop
```

Una rama de trabajo vigente puede incorporar después `Cris-develop` mediante el flujo normal del proyecto. Los archivos `.env` y `data/private/` permanecen locales y no deben copiarse al sincronizar un clon.

## Estado de cierre

El incidente queda resuelto: la credencial expuesta continúa inválida, la activa no aparece en el historial, no hay secretos activos en las referencias revisadas y la decisión evita alterar hashes compartidos. El respaldo queda disponible solo como contingencia privada.
