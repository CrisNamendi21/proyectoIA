# Verificación de Ollama en el equipo de Cris — 23 de octubre de 2026

## Objetivo

Reproducir localmente el flujo real ya validado por Jean: comunicación con Ollama, generación de un borrador, validación Pydantic, guardado en PostgreSQL y consulta posterior, usando una sola inferencia real.

## Entorno comprobado

- Ollama para Windows instalado mediante `winget`: versión `0.40.9`.
- API local disponible en `http://127.0.0.1:11434`.
- Modelo disponible: `qwen2.5:3b`, tamaño informado de `1,929,912,432` bytes.
- Imagen `colegio-alfa-backend:dev` reconstruida desde el código vigente.
- El contenedor del backend consultó `http://host.docker.internal:11434/api/tags` y encontró el modelo configurado.
- PostgreSQL se ejecutó únicamente en Docker Compose.

## Prueba real ejecutada

Comando:

```powershell
uv run python tests/integration/run_snapshot.py --ref HEAD --real-ollama
```

El snapshot correspondió al commit `71726fc85f8396edb7b9afaafd5a3d96416fdfd4`. El runner seleccionó exclusivamente `test_real_ollama_persisted_flow`, por lo que se hizo una sola llamada válida a `POST /generation`.

Resultados:

- flujo real de Ollama: aprobado;
- duración medida dentro del flujo: **62.56 segundos**;
- resultado de pytest: **1 prueba aprobada**, 1 advertencia de deprecación, en 64.60 segundos;
- el JSON devuelto fue validado como `TeachingPlanDraft`;
- el borrador fue revisado por el flujo de prueba, guardado como JSONB y consultado bajo la identidad del docente;
- se comprobaron propiedad, segunda sesión, logout y rechazo posterior sin sesión;
- las migraciones aprobaron `upgrade head`, ausencia de cambios pendientes, `downgrade base` y segundo `upgrade head`.

## Limpieza

El runner comparó el catálogo de PostgreSQL antes y después de la ejecución:

- `temporary_database_catalog_unchanged`: `true`;
- `new_leftover_databases`: `0`.

Una consulta directa posterior confirmó **0** bases con los patrones temporales del proyecto. El contenedor efímero usado para probar la comunicación backend → Ollama se eliminó correctamente.

## Conclusión

El flujo real de generación, validación, guardado y consulta funciona también en el equipo de Cris. Ollama y el modelo permanecen como recursos locales y no forman parte del repositorio.
