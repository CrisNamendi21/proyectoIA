# Migraciones de base de datos

## Herramienta elegida

Colegio Alfa usa **Alembic** como herramienta oficial de migraciones. Es la herramienta del proyecto SQLAlchemy, trabaja con PostgreSQL y puede comparar `Base.metadata` con el esquema existente para producir revisiones candidatas. `pyproject.toml` y `uv.lock` fijan su versión; no se instalará ni mantendrá otra herramienta de migración en paralelo.

La documentación oficial advierte que `--autogenerate` produce candidatos que siempre deben revisarse manualmente. También ofrece `alembic check` para detectar cambios de modelos que todavía no tienen revisión:

- [Autogenerate y sus límites](https://alembic.sqlalchemy.org/en/latest/autogenerate.html).
- [`alembic check`](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#running-alembic-check-to-test-for-new-upgrade-operations).
- [Alembic como herramienta de migraciones de SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/metadata.html#altering-database-objects-through-migrations).

## Uso normal

Actualizar una base existente o crear una nueva:

```powershell
uv run alembic upgrade head
```

El comando histórico sigue disponible y ejecuta la misma actualización:

```powershell
uv run python -m app.db.init_db
```

Consultar el estado:

```powershell
uv run alembic current
uv run alembic heads
uv run alembic history
```

Alembic obtiene la conexión desde `DATABASE_URL`; `alembic.ini` no contiene credenciales.

## Crear una migración futura

1. Partir de `Cris-develop` actualizado y comprobar que existe una sola cabeza con `uv run alembic heads`.
2. Modificar los modelos SQLAlchemy.
3. Generar el candidato:

   ```powershell
   uv run alembic revision --autogenerate -m "descripción breve"
   ```

4. Revisar línea por línea `upgrade()` y `downgrade()`. La revisión debe confirmar:
   - que no aparecen tablas, columnas, índices ni restricciones ajenas al cambio;
   - que los renombres no se expresan como una eliminación y creación accidental;
   - que tipos, nulabilidad, valores por defecto y nombres de restricciones son correctos;
   - que cualquier transformación de datos ocurre antes de imponer una regla incompatible;
   - que el downgrade es explícito y solo afecta una base desechable durante la prueba;
   - que no hay SQL construido con datos externos, credenciales o valores privados.
5. Ejecutar la verificación automatizada:

   ```powershell
   uv run python tests/integration/check_migrations.py
   uv run pytest -q
   ```

6. Confirmar que modelos y cabeza coinciden:

   ```powershell
   uv run alembic check
   ```

7. Revisar el diff de la migración junto con el cambio de modelo. Un cambio de esquema no se integra si falta la revisión, el downgrade razonable o la evidencia sobre PostgreSQL desechable.

## Qué comprueba el ejecutor

`tests/integration/check_migrations.py` crea una base PostgreSQL con nombre aleatorio y ejecuta:

1. `upgrade head` desde una base vacía;
2. `alembic check` sin diferencias pendientes;
3. comprobación de tablas y de la restricción curricular;
4. `downgrade base` únicamente en esa base desechable;
5. un segundo `upgrade head` y otro `alembic check`;
6. eliminación forzada de la base temporal, incluso si hay un error.

El runner integrado ejecuta esta comprobación automáticamente y vigila que no queden bases temporales.

## Reglas de historial

- Cada revisión publicada es inmutable. Una corrección se agrega como otra revisión.
- La línea debe conservar una sola cabeza; ramas Alembic solo se unen mediante una revisión de merge explícita.
- Las restricciones e índices nuevos reciben nombres estables.
- Las operaciones destructivas necesitan estrategia de respaldo y recuperación documentada antes de aplicarse fuera de una base desechable.
- `Base.metadata.create_all()` puede seguir usándose dentro de fixtures aisladas, pero no inicializa ni actualiza entornos de la aplicación.

## Adopción de una base creada antes de Alembic

La revisión `c040b61622ed` representa el esquema histórico. Antes de marcar una base existente con esa revisión se compara su estructura y se revisan datos incompatibles. Solo entonces se ejecuta:

```powershell
uv run alembic stamp c040b61622ed
uv run alembic upgrade head
uv run alembic check
```

`stamp` no modifica tablas: únicamente registra el punto de partida comprobado. No debe usarse para ocultar diferencias de esquema.
