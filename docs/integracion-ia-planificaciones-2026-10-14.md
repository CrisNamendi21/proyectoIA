# Miércoles 14: coordinación de IA y planificaciones

Responsable: Jean. **Propuesta provisional para revisión de Cris y Alejandra; no es un contrato aprobado.**
Complementa la [guía de infraestructura](infraestructura-jean.md) y conserva la [auditoría del martes](auditoria-integracion-jean-2026-10-13.md) como evidencia histórica.

## Estado real del equipo

Fetch con prune completado. Jean permanece en `feature/ai-infra-jean` con HEAD `9e540ec`, inicialmente limpio y publicado.
`origin/Cris-develop` avanzó a `31a569a`; `origin/Alejandra-develop`, a `b9f7a46`; `origin/main`, a `4394042`.
Antes del commit documental del miércoles, Jean quedó seis commits detrás de Cris y sin commits locales sin publicar.
No se realizó merge, rebase ni checkout de otras ramas.

El [PR #1](https://github.com/CrisNamendi21/proyectoIA/pull/1) está cerrado y fusionado; GitHub conserva su indicador draft.
No tiene comentarios, revisiones ni solicitudes de cambios registradas. Se integró mediante `688b2e2`.
Los documentos de hoy no deben añadirse como si ese PR siguiera abierto: después de revisión/autorización, requieren una entrega documental nueva.

Cambios publicados de Cris:

- `688b2e2`: integra el trabajo de Jean.
- `c607ad1`: integra catálogos y planificaciones, incluido `b9f7a46` de Alejandra y sus filtros previos `38ac062`.
- `62a6bd2`: conecta `get_current_user` a planes, registra generación en `/generation`, catálogos y planes, agrega `/auth/me` y logout, errores SQL controlados y validaciones del núcleo.
- `31a569a`: actualiza README y documentos de estado; `main` recibió esa integración en `4394042`.

Los módulos IA, el router de generación, dependencias y modelos ORM no cambiaron frente a la rama de Jean.
No se detectó incompatibilidad de firmas. La ruta `/generation` ya está **implementada por Cris**; sigue pendiente aprobación final del contrato del equipo.
En Alejandra, `get_planning_user()` aún devuelve 503 si no se sustituye; en Cris es alias de `get_current_user` y devuelve 401 sin sesión.
No confundir ese placeholder de su rama aislada con un bloqueo pendiente del núcleo integrado.

## Comparación de formatos y responsabilidades

| Dato | IA: `PlanningGenerationRequest` / `TeachingPlanDraft` | Planes: `PlanningCreate` / `PlanningRead` |
| --- | --- | --- |
| Contexto curricular | `context.grade`, `context.subject`, `context.curriculum_content`, como texto | `grade_id`, `subject_id`, `curriculum_content_id`, enteros positivos estrictos u opcionales |
| Objetivo y actividades | `learning_objective`, `activities` con `stage`, `description`, `minutes`, `resources` | Se preservan dentro de `content`; no tienen columnas nuevas |
| Evaluación y materiales | `assessment`, `materials`, `teacher_notes` | Se preservan dentro de `content` |
| Título y nombres curriculares | `title`, `grade`, `subject`, `curriculum_content` en la salida | Se preservan dentro de `content`; no sustituyen las referencias por ID |
| Duración/necesidades/meta de la solicitud | `duration_minutes`, `student_needs`, `learning_goal`, recursos, modelo | No se devuelven íntegramente en el borrador; acordar si conservar metadatos antes de añadirlos |
| Autor | La solicitud IA no incluye autor | `create_planning(db, data, owner_id)` usa el ID del usuario autenticado; `PlanningCreate` rechaza `user_id` extra |
| Identidad y fechas persistidas | No existen en el borrador | `PlanningRead` agrega `id`, `user_id`, `created_at`, `updated_at` del servidor |

`PlanningCreate.content` acepta cualquier objeto JSON con valores JSON válidos, incluso `{}`.
Rechaza valores Python no JSON, NaN/infinito e IDs inválidos; prohíbe campos extra fuera de `content`.
No define todavía obligatoriedad pedagógica ni versión. Los ejemplos españoles de sus tests no imponen un esquema distinto al borrador inglés de IA.

`create_planning(db: Session, data: PlanningCreate, owner_id: int) -> Planning` verifica existencia y coherencia de las referencias,
hace add → flush → commit y rollback en errores. El listado y detalle filtran por `Planning.user_id`; un plan ajeno devuelve 404.
Si solo se envía `curriculum_content_id`, no completa automáticamente `grade_id` ni `subject_id`: los campos omitidos permanecen null.
El servicio no verifica la igualdad semántica entre los nombres de `content` y los catálogos ni la calidad de la propuesta.

## Ejemplos concretos

Datos sintéticos para validación, no catálogo oficial. Los IDs del ejemplo deben reemplazarse por los obtenidos en catálogos reales antes de guardar.

### Entrada IA: `PlanningGenerationRequest`, `POST /generation` en Cris

```json
{
  "context": {
    "grade": "Quinto grado",
    "subject": "Matemática",
    "curriculum_content": "Fracciones equivalentes",
    "duration_minutes": 45,
    "learning_goal": "Reconocer fracciones equivalentes.",
    "student_needs": "Apoyo con representaciones visuales.",
    "resources": ["pizarra", "tarjetas"]
  },
  "model": "qwen2.5:3b"
}
```

El consumidor debe construir el texto desde la selección curricular verificada; la ruta actual no recibe IDs ni los consulta.
`model` puede omitirse para usar `OLLAMA_MODEL`. El equipo debe decidir si permite selección de modelos por petición.

### Salida IA: `TeachingPlanDraft`, HTTP 200

```json
{
  "title": "Fracciones equivalentes",
  "grade": "Quinto grado",
  "subject": "Matemática",
  "curriculum_content": "Fracciones equivalentes",
  "learning_objective": "Reconocer fracciones equivalentes mediante representaciones visuales.",
  "activities": [
    {"stage": "inicio", "description": "Comparar dibujos de fracciones.", "minutes": 10, "resources": ["pizarra"]},
    {"stage": "desarrollo", "description": "Relacionar tarjetas equivalentes en equipos.", "minutes": 25, "resources": ["tarjetas"]},
    {"stage": "cierre", "description": "Explicar una equivalencia y resolver dudas.", "minutes": 10, "resources": ["pizarra"]}
  ],
  "assessment": {"criteria": ["Identifica equivalencias", "Explica una representación"], "evidence": "Tarjetas clasificadas y explicación oral."},
  "materials": ["pizarra", "tarjetas"],
  "teacher_notes": ["Revisar la propuesta antes de guardarla."]
}
```

### Creación: `PlanningCreate`, `POST /plans`, éxito HTTP 201

```json
{
  "grade_id": 1,
  "subject_id": 1,
  "curriculum_content_id": 1,
  "content": {
    "title": "Fracciones equivalentes",
    "grade": "Quinto grado",
    "subject": "Matemática",
    "curriculum_content": "Fracciones equivalentes",
    "learning_objective": "Reconocer fracciones equivalentes mediante representaciones visuales.",
    "activities": [
      {"stage": "inicio", "description": "Comparar dibujos de fracciones.", "minutes": 10, "resources": ["pizarra"]},
      {"stage": "desarrollo", "description": "Relacionar tarjetas equivalentes en equipos.", "minutes": 25, "resources": ["tarjetas"]},
      {"stage": "cierre", "description": "Explicar una equivalencia y resolver dudas.", "minutes": 10, "resources": ["pizarra"]}
    ],
    "assessment": {"criteria": ["Identifica equivalencias", "Explica una representación"], "evidence": "Tarjetas clasificadas y explicación oral."},
    "materials": ["pizarra", "tarjetas"],
    "teacher_notes": ["Revisar la propuesta antes de guardarla."]
  }
}
```

Adaptación mínima propuesta después de revisión docente:

```python
draft = TeachingPlanDraft.model_validate(reviewed_payload)
data = PlanningCreate(
    grade_id=selected_grade_id,
    subject_id=selected_subject_id,
    curriculum_content_id=selected_content_id,
    content=draft.model_dump(mode="json"),
)
```

No hace falta un servicio adaptador nuevo ni cambiar `Planning` o JSONB: solo envolver el borrador revisado bajo `content`
y enviar por separado los IDs seleccionados. El endpoint `/plans` se encarga de llamar a `create_planning` con el usuario de sesión.
No llamar al servicio de persistencia desde `/generation` ni copiar campos del borrador al nivel superior de `PlanningCreate`.

## Validaciones y decisiones para el jueves

La compatibilidad estructural ya existe; la aprobación pedagógica sigue pendiente.

- **Jean y Alejandra:** decidir si el objeto completo `TeachingPlanDraft` dentro de `content` será el formato mínimo común, con sus nombres de campos actuales.
- **Equipo:** decidir versión y metadatos, reglas de edición y qué campos conservar si el docente cambia el borrador.
- **Alejandra:** validar guardado y edición según el acuerdo; comprobar propiedad, persistencia real y rechazo de referencias incoherentes.
- **Jean:** preparar mocks y ejemplos compatibles, coordinar validación del borrador; no crear otra implementación de generación.
- **Cris:** confirmar la ruta ya implementada, cookie/logout y protección de solicitudes; revisar el flujo registrado y los errores compartidos.
- **Antes de guardar:** sesión activa, JSON válido, IDs existentes y coherentes, correspondencia entre texto y selección curricular, revisión docente.
  Acordar si se exigen las tres etapas y la suma de minutos: el schema actual exige al menos tres actividades, pero no esas dos reglas de conjunto.

Hoy funcionan en aislamiento generación, consulta curricular, validación, transacción y filtros de propiedad.
El núcleo publicado conecta autenticación y rutas; eso no demuestra el recorrido persistido completo.
No hay endpoint de edición publicado en el snapshot revisado.
Las 50 pruebas de planes simulan SQLAlchemy y no prueban rollback/persistencia en una base real ni aislamiento de dos docentes reales.

Prueba integrada pendiente del jueves, con datos y base desechables acordados:
login → catálogo → generación con mock → revisión → POST /plans → GET /plans y detalle → segundo docente rechazado → logout.
Después, una única comprobación con Ollama real si la integración con mocks es satisfactoria. No declarar flujo extremo a extremo completo antes de ejecutarlo.

## Verificación del miércoles

- `docker compose config --quiet`, `uv lock --check` y `uv sync --locked` finalizaron correctamente; Python local es 3.12.2.
- Docker Engine 29.8.2 está disponible, pero ambos contenedores están detenidos; el volumen existe.
  No se arrancaron/reconstruyeron servicios ni se ejecutaron cambios SQL hoy. Health y SELECT 1 reales conservan la evidencia del martes, no una verificación nueva.
- `ollama list` contiene `qwen2.5:3b` y `GET http://localhost:11434/api/tags` devuelve HTTP 200.
  Se comprobó la ayuda de `ollama pull`; no se repitió inferencia ni descarga del modelo.
- Snapshot Git de Alejandra `b9f7a46`, sin checkout ni merge: **70 passed, 1 warning** (20 catálogos y 50 planes), con sesiones mock.
- Snapshot Git de Cris `31a569a`, sin checkout ni merge: **137 passed, 3 skipped, 1 warning**.
  Las tres integraciones PostgreSQL se deshabilitaron deliberadamente con `COLEGIO_ALFA_TEST_POSTGRES=0`; no se conectó a la base de desarrollo.
- Los snapshots se extrajeron fuera del repositorio y se ejecutaron con el Python/dependencias bloqueadas de Jean, idénticas a las de Cris.
  Se usó una URL ficticia no conectable y clave de sesión aleatoria; ninguna credencial de desarrollo se copió a los snapshots.
- La advertencia sigue siendo Starlette/httpx. No se modificaron dependencias ni pruebas de otros integrantes.

- Los tres JSON se validaron con `PlanningGenerationRequest`, `TeachingPlanDraft` y `PlanningCreate` real de Cris.
  Se comprobó que `content` preserva el borrador sin pérdida y que el ejemplo suma 45 minutos, sin convertirlo en una regla implementada.
- Se revisó la sintaxis de cinco bloques Python de los documentos. La generación de `.env` se simuló en una carpeta temporal,
  comprobando correspondencia entre contraseña y URL, clave de sesión y settings IA, sin tocar `.env` del repositorio ni conectar a una base.
- No se publican rutas de usuario, credenciales ni snapshots. Solo se agregan los dos documentos de Jean;
  README, contratos y código de Cris/Alejandra permanecen intactos.

La instalación y arranque desde clon limpio siguen reservados para el viernes 16; no se presentan los snapshots como esa prueba.

## Mensaje preparado para Cris y Alejandra

> Revisé las ramas publicadas: Cris ya conectó autenticación y registró generación, catálogos y planes. Las 70 pruebas aisladas de Alejandra pasan; el snapshot de Cris pasa 137 pruebas y omite las tres PostgreSQL opcionales. El borrador IA cabe sin renombrar campos dentro de PlanningCreate.content; los IDs curriculares van separados y el propietario sale de la sesión. Propongo acordar únicamente: (1) si conservamos completo TeachingPlanDraft como contenido mínimo; (2) reglas de edición, versión/metadatos y coherencia curricular; (3) confirmación de /generation y cookies. El jueves falta comprobar guardado/consulta y propiedad con PostgreSQL desechable antes de una inferencia real. Preparé guía Docker/Ollama y ejemplos validados; el PR #1 ya está fusionado, por lo que esta documentación tendrá revisión nueva. ¿Confirmamos esos tres puntos para probar el flujo?

Mensaje preparado, no enviado.
