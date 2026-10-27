# Prototipo conversacional del frontend

Este prototipo explora una interfaz oscura con navegación lateral y acentos violetas, inspirada en la referencia visual del equipo. La composición se adaptó al flujo real de Colegio Alfa: formulario curricular, generación con IA, revisión docente, guardado e historial.

## Decisiones del prototipo

- HTML, CSS y JavaScript modular sin proceso de compilación ni dependencias nuevas.
- Archivos servidos por FastAPI en el mismo origen para reutilizar la cookie `HttpOnly` y evitar una configuración CORS provisional.
- Pantalla de acceso, restauración de sesión y cierre de sesión reales.
- Catálogos conectados al backend y contenidos filtrados por grado y asignatura.
- Una sola solicitud de generación con estado de espera visible y protección contra envíos duplicados.
- Editor para título, objetivo, actividades, evaluación, materiales y notas.
- Guardado mediante `POST /plans`, listado personal, detalle y actualización mediante `PATCH`.
- Diseño adaptable para escritorio, tablet y móvil, con foco visible y movimiento reducido cuando el sistema lo solicita.

No se añadieron registro, recuperación de contraseña, eliminación, exportación, panel administrativo ni comunicación directa del navegador con Ollama.

## Ejecutar

El frontend forma parte de la misma aplicación. Su segunda iteración reemplaza el
formulario rígido por un asistente conversacional:

- el primer acceso solicita una sola vez los años y asignaturas del docente;
- cada conversación nueva fija año, asignatura y duración una sola vez;
- los mensajes posteriores se escriben con lenguaje natural;
- el backend profesionaliza la petición mediante un prompt controlado;
- el JSON de Ollama pasa por validación estructural, comprobación de año,
  asignatura y duración antes de llegar al navegador;
- el docente puede revisar, editar, guardar y volver a abrir el borrador.

El perfil usa las relaciones `user_grades` y `user_subjects` y registra
`users.profile_completed_at`. `GET /profile` consulta la configuración y
`PUT /profile` la crea o actualiza. `POST /chat/generate` solo acepta años y
asignaturas pertenecientes al docente autenticado. La conversación envía como
máximo ocho mensajes resumidos y no se persiste como historial de chat.

Después de preparar `.env`, PostgreSQL, las migraciones y las cuentas locales:

```powershell
docker compose up -d --build
docker compose exec -T backend python -m app.db.init_db
```

Para evaluar el onboarding con varios años y asignaturas puede cargarse el
conjunto demostrativo. No contiene contenidos curriculares oficiales y nunca se
ejecuta automáticamente:

```powershell
docker compose exec -T backend python -m app.db.seed_prototype_options --apply
```

Abrir `http://127.0.0.1:8000/`. La documentación OpenAPI continúa disponible en `http://127.0.0.1:8000/docs`.

Para ejecución nativa también se puede usar Uvicorn, conservando la configuración local de PostgreSQL descrita en la guía de infraestructura.

## Límite de esta entrega

Es una prueba funcional de diseño y flujo. Las conversaciones viven únicamente
en la sesión del navegador; los borradores guardados sí persisten en PostgreSQL.
Las opciones demostrativas no sustituyen el catálogo que apruebe el colegio. Su
evaluación servirá para decidir la tecnología y el sistema visual del frontend
definitivo; no convierte esta implementación en la interfaz final del producto.
