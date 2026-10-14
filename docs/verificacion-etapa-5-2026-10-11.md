# Verificación de la etapa 5 — domingo 11 de octubre de 2026

## Alcance y resultado

Se verificó el flujo de cuentas y autenticación en `Cris-develop`, a partir del commit `968ab05`. Se usaron únicamente datos ficticios y una base PostgreSQL desechable. La prueba está en `tests/test_auth_flow.py`; crea la base, ejecuta la carga y el acceso, inspecciona los registros y elimina la base al finalizar. La ruta `/__test/identity` existe solo dentro de la prueba para comprobar la dependencia `get_current_user`; no forma parte de la API publicada.

| Comprobación | Resultado |
| --- | --- |
| Carga explícita de `docente_ficticio` dos veces | Ambas ejecuciones terminaron correctamente y quedó una sola cuenta. |
| Persistencia en PostgreSQL | En sesiones nuevas se encontró la cuenta; `password_hash` comienza con `$argon2id$`, verifica la contraseña ficticia y no contiene texto plano. |
| Acceso correcto | `POST /auth/login` respondió `200` solo con `id` y `username`. |
| Identidad posterior | Una petición posterior con la cookie resolvió el mismo usuario mediante `get_current_user`. Sin cookie respondió `401`. |
| Acceso rechazado | Contraseña incorrecta y usuario desconocido devolvieron el mismo `401` genérico. Tras el intento fallido no quedó identidad válida en el cliente. |
| Suite completa con PostgreSQL | `COLEGIO_ALFA_TEST_POSTGRES=1` y `uv run pytest -q`: **14 passed**. Hubo un aviso de deprecación de `httpx` en `starlette.testclient`; no hubo fallos de prueba. |
| Dependencias | `uv lock --check`: correcto. |
| Git | Rama `Cris-develop`; estado limpio al comenzar. `git diff --check`: correcto. Los cambios de la etapa son la prueba, este registro y los enlaces de documentación. `.env` permanece ignorado y no está versionado. |

Para repetir la suite en esta computadora, con el contenedor local `alfa-db` disponible y un `.env` local con `DATABASE_URL` y `SESSION_SECRET_KEY`:

```powershell
docker start alfa-db
$env:COLEGIO_ALFA_TEST_POSTGRES = '1'
uv run pytest -q
Remove-Item Env:COLEGIO_ALFA_TEST_POSTGRES
docker stop alfa-db
```

Las pruebas de integración crean bases con nombres aleatorios y las eliminan en `finally`; requieren que el usuario local de PostgreSQL pueda crear bases. No se crearon cuentas docentes reales.

## Revisión de secretos y archivos

Se revisaron 44 archivos actuales versionados o nuevos mediante una búsqueda de credenciales de PostgreSQL en URL, asignaciones directas de `SESSION_SECRET_KEY` y claves privadas PEM, sin imprimir valores: esos patrones no detectaron secretos en el contenido actual. La revisión del historial encontró referencias antiguas a una clave de PostgreSQL en `README.md` y `docs/contratos.md`. **Esa clave coincide con la del entorno local actual.** Un commit nuevo no elimina el dato del historial; hay que rotar la clave local y actualizar el entorno por un canal seguro cuanto antes. No se incluyó el valor en este registro.

`git status` no mostró modificaciones ajenas al alcance de esta etapa. La prueba y la documentación quedan sin commit para la revisión de Cris.

## Pendientes y siguiente paso pequeño

- **Prioridad alta, Cris y Jean:** rotar la clave local de PostgreSQL expuesta en el historial y revisar cómo distribuir las credenciales de desarrollo. La limpieza del historial, si el equipo la considera necesaria, requiere una decisión separada porque reescribe commits compartidos.
- **Cris, Jean y Alejandra:** confirmar el identificador de acceso, el contrato HTTP, la cookie de ocho horas y la forma de `User` que consumirán los routers. La implementación actual sigue siendo provisional.
- **Jean:** revisar `pwdlib[argon2]` e `itsdangerous` en `pyproject.toml` y `uv.lock`, y completar `compose.yaml` y `.env.example` con ejemplos no sensibles.
- **Alejandra:** confirmar la dependencia `get_current_user` antes de aplicarla a catálogos y planificaciones.
- **Lunes 12, Cris:** tras revisar el contrato con el equipo, implementar el logout como cambio pequeño y probar que borra la cookie; después abordar `/me` y la protección de rutas. Revisar también la protección contra solicitudes entre sitios al usar cookies.

No se verificaron cuentas docentes reales, despliegue HTTPS, disponibilidad de Ollama, routers de catálogos y planificaciones ni una ejecución reproducible de Docker Compose desde cero. Esas piezas no forman parte de la conclusión sobre autenticación local.
