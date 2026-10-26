const app = document.querySelector("#app");
const toastRegion = document.querySelector("#toast-region");

const state = {
  user: null,
  view: "create",
  grades: [],
  subjects: [],
  contents: [],
  plans: [],
  draft: null,
  editingPlan: null,
  selectedGradeId: "",
  selectedSubjectId: "",
  selectedContentId: "",
  apiOnline: false,
  sidebarOpen: false,
};

const icons = {
  sparkles: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.4 4.2L17 9l-3.6 1.8L12 15l-1.4-4.2L7 9l3.6-1.8L12 3Z"/><path d="m5 14 .8 2.2L8 17l-2.2.8L5 20l-.8-2.2L2 17l2.2-.8L5 14Zm14-1 .8 2.2 2.2.8-2.2.8L19 19l-.8-2.2L16 16l2.2-.8L19 13Z"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`,
  library: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20M8 7h8"/></svg>`,
  logout: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 17l5-5-5-5M15 12H3M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/></svg>`,
  menu: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>`,
  close: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>`,
  arrow: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>`,
  back: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>`,
  save: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h12l2 2v16H5V3Z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/></svg>`,
  edit: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 20 4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10L4 20Z"/><path d="m14 7 3 3"/></svg>`,
  clock: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`,
  user: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>`,
  check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>`,
  warning: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5M12 18h.01"/></svg>`,
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function describeError(payload, fallback) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg).filter(Boolean).join(" · ") || fallback;
  }
  return fallback;
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") {
      state.user = null;
      renderLogin("Tu sesión terminó. Ingresa nuevamente para continuar.");
    }
    const error = new Error(describeError(payload, "No se pudo completar la solicitud."));
    error.status = response.status;
    throw error;
  }
  return payload;
}

function toast(message, type = "success") {
  const item = document.createElement("div");
  item.className = `toast toast--${type}`;
  item.innerHTML = `${type === "success" ? icons.check : icons.warning}<span>${escapeHtml(message)}</span>`;
  toastRegion.append(item);
  setTimeout(() => item.remove(), 4800);
}

function setButtonLoading(button, loading, label) {
  if (!button) return;
  button.disabled = loading;
  if (!button.dataset.original) button.dataset.original = button.innerHTML;
  button.innerHTML = loading
    ? `<span class="spinner" aria-hidden="true"></span>${escapeHtml(label)}`
    : button.dataset.original;
}

function renderLogin(message = "") {
  state.view = "create";
  state.sidebarOpen = false;
  app.innerHTML = `
    <main class="login-page">
      <section class="login-story" aria-label="Presentación de Colegio Alfa">
        <div class="login-story__content">
          <a class="brand brand--light" href="#" aria-label="Colegio Alfa">
            <span class="brand-mark">A</span>
            <span><strong>Colegio Alfa</strong><small>Planificador docente</small></span>
          </a>
          <div class="story-orb" aria-hidden="true"><span></span></div>
          <p class="eyebrow">IA local · Privacidad primero</p>
          <h1>Convierte tu contexto de clase en un borrador que puedes hacer tuyo.</h1>
          <p class="story-copy">Organiza objetivos, actividades y evaluación con apoyo de IA, manteniendo siempre la revisión docente.</p>
          <div class="story-points">
            <span>${icons.check} Borradores editables</span>
            <span>${icons.check} Historial personal</span>
            <span>${icons.check} Datos en tu entorno</span>
          </div>
        </div>
      </section>
      <section class="login-panel">
        <form id="login-form" class="login-form">
          <div class="mobile-brand">
            <span class="brand-mark">A</span>
            <strong>Colegio Alfa</strong>
          </div>
          <p class="eyebrow">Bienvenido de nuevo</p>
          <h2>Accede a tu espacio docente</h2>
          <p class="muted">Usa la cuenta precreada que recibiste del equipo.</p>
          ${message ? `<div class="form-alert">${icons.warning}<span>${escapeHtml(message)}</span></div>` : ""}
          <label class="field">
            <span>Usuario</span>
            <input name="username" type="text" autocomplete="username" maxlength="50" required placeholder="Tu nombre de usuario" />
          </label>
          <label class="field">
            <span>Contraseña</span>
            <div class="password-wrap">
              <input name="password" type="password" autocomplete="current-password" required placeholder="Tu contraseña" />
              <button class="text-button" id="toggle-password" type="button">Mostrar</button>
            </div>
          </label>
          <button class="button button--primary button--wide" type="submit">Entrar a mi espacio ${icons.arrow}</button>
          <p class="login-help">¿No puedes acceder? Solicita apoyo al responsable técnico del colegio.</p>
        </form>
      </section>
    </main>`;

  const form = document.querySelector("#login-form");
  document.querySelector("#toggle-password").addEventListener("click", (event) => {
    const input = form.elements.password;
    input.type = input.type === "password" ? "text" : "password";
    event.currentTarget.textContent = input.type === "password" ? "Mostrar" : "Ocultar";
  });
  form.addEventListener("submit", handleLogin);
}

async function handleLogin(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type='submit']");
  setButtonLoading(button, true, "Verificando…");
  try {
    const data = new FormData(event.currentTarget);
    state.user = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: data.get("username"), password: data.get("password") }),
    });
    await loadWorkspace();
    toast(`Bienvenido, ${state.user.username}.`);
  } catch (error) {
    renderLogin(error.message);
  } finally {
    setButtonLoading(button, false, "");
  }
}

async function loadWorkspace() {
  const [grades, subjects, plans] = await Promise.all([
    request("/catalogs/grades"),
    request("/catalogs/subjects"),
    request("/plans"),
  ]);
  state.grades = grades;
  state.subjects = subjects;
  state.plans = plans;
  renderShell();
}

function renderShell() {
  const current = state.view === "edit" ? "plans" : state.view;
  app.innerHTML = `
    <div class="app-shell ${state.sidebarOpen ? "app-shell--menu-open" : ""}">
      <button class="sidebar-backdrop" id="sidebar-backdrop" aria-label="Cerrar menú"></button>
      <aside class="sidebar" aria-label="Navegación principal">
        <div class="sidebar__top">
          <a class="brand" href="#" id="brand-home">
            <span class="brand-mark">A</span>
            <span><strong>Colegio Alfa</strong><small>Planificador docente</small></span>
          </a>
          <button class="icon-button sidebar-close" id="sidebar-close" aria-label="Cerrar menú">${icons.close}</button>
        </div>
        <nav class="side-nav">
          <p class="side-label">Tu espacio</p>
          <button class="side-link ${current === "create" ? "is-active" : ""}" data-view="create">${icons.plus}<span>Nueva planificación</span></button>
          <button class="side-link ${current === "plans" ? "is-active" : ""}" data-view="plans">${icons.library}<span>Mis planificaciones</span><b>${state.plans.length}</b></button>
        </nav>
        <div class="sidebar-note">
          <span class="mini-orb" aria-hidden="true"></span>
          <strong>IA local activa</strong>
          <p>Tus propuestas se generan con Ollama en el entorno del colegio.</p>
        </div>
        <div class="user-card">
          <span class="avatar">${escapeHtml(state.user.username.slice(0, 1).toUpperCase())}</span>
          <span><strong>${escapeHtml(state.user.username)}</strong><small>Docente</small></span>
          <button class="icon-button" id="logout" title="Cerrar sesión" aria-label="Cerrar sesión">${icons.logout}</button>
        </div>
      </aside>
      <section class="workspace">
        <header class="topbar">
          <button class="icon-button menu-button" id="menu-button" aria-label="Abrir menú">${icons.menu}</button>
          <div>
            <p class="topbar__context">Colegio Alfa</p>
            <h2>${state.view === "plans" ? "Mis planificaciones" : state.view === "edit" ? "Editar planificación" : "Nueva planificación"}</h2>
          </div>
          <div class="service-status ${state.apiOnline ? "is-online" : ""}"><span></span>${state.apiOnline ? "Sistema disponible" : "Comprobando sistema"}</div>
        </header>
        <main class="workspace__content" id="workspace-content"></main>
      </section>
    </div>`;

  bindShellEvents();
  if (state.view === "plans") renderPlans();
  else if (state.view === "edit") renderEditPlan();
  else renderCreate();
}

function bindShellEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      state.sidebarOpen = false;
      state.editingPlan = null;
      renderShell();
    });
  });
  document.querySelector("#brand-home").addEventListener("click", (event) => {
    event.preventDefault();
    state.view = "create";
    renderShell();
  });
  document.querySelector("#menu-button").addEventListener("click", () => toggleSidebar(true));
  document.querySelector("#sidebar-close").addEventListener("click", () => toggleSidebar(false));
  document.querySelector("#sidebar-backdrop").addEventListener("click", () => toggleSidebar(false));
  document.querySelector("#logout").addEventListener("click", handleLogout);
}

function toggleSidebar(open) {
  state.sidebarOpen = open;
  document.querySelector(".app-shell")?.classList.toggle("app-shell--menu-open", open);
}

async function handleLogout() {
  try {
    await request("/auth/logout", { method: "POST" });
  } finally {
    state.user = null;
    state.draft = null;
    renderLogin();
  }
}

function selectOptions(items, selected, placeholder) {
  return `<option value="">${escapeHtml(placeholder)}</option>${items
    .map((item) => `<option value="${item.id}" ${String(item.id) === String(selected) ? "selected" : ""}>${escapeHtml(item.name)}</option>`)
    .join("")}`;
}

function contentOptions() {
  return `<option value="">Selecciona un contenido</option>${state.contents
    .map((item) => `<option value="${item.id}" ${String(item.id) === String(state.selectedContentId) ? "selected" : ""}>${escapeHtml(item.description)}</option>`)
    .join("")}`;
}

function renderCreate() {
  const container = document.querySelector("#workspace-content");
  container.innerHTML = `
    <section class="create-hero">
      <div class="ai-orb" aria-hidden="true"><span></span></div>
      <p class="eyebrow">Asistente pedagógico local</p>
      <h1>¿Qué quieres planificar hoy?</h1>
      <p>Define el contexto de tu clase. La IA preparará un borrador para que lo revises antes de guardarlo.</p>
    </section>
    <section class="planner-layout">
      <form id="generation-form" class="planning-form">
        <div class="section-heading">
          <span class="step-number">1</span>
          <div><h3>Contexto curricular</h3><p>Selecciona los datos oficiales que guiarán la propuesta.</p></div>
        </div>
        <div class="form-grid form-grid--3">
          <label class="field"><span>Grado</span><select id="grade" required>${selectOptions(state.grades, state.selectedGradeId, "Selecciona un grado")}</select></label>
          <label class="field"><span>Asignatura</span><select id="subject" required>${selectOptions(state.subjects, state.selectedSubjectId, "Selecciona una asignatura")}</select></label>
          <label class="field"><span>Duración</span><select id="duration"><option value="45">45 minutos</option><option value="60">60 minutos</option><option value="90">90 minutos</option><option value="120">120 minutos</option></select></label>
        </div>
        <label class="field"><span>Contenido curricular</span><select id="curriculum-content" required ${state.contents.length ? "" : "disabled"}>${contentOptions()}</select><small>${state.contents.length ? "Contenido asociado al grado y asignatura." : "Selecciona primero el grado y la asignatura."}</small></label>
        <div class="section-divider"></div>
        <div class="section-heading">
          <span class="step-number">2</span>
          <div><h3>Intención de la clase</h3><p>Añade orientaciones para obtener un borrador más útil.</p></div>
        </div>
        <label class="field"><span>Meta de aprendizaje <em>Opcional</em></span><textarea id="learning-goal" maxlength="1000" rows="3" placeholder="Ej. Que el estudiante reconozca y represente fracciones equivalentes…"></textarea></label>
        <div class="form-grid">
          <label class="field"><span>Necesidades del grupo <em>Opcional</em></span><textarea id="student-needs" maxlength="1000" rows="3" placeholder="Ej. Incluir apoyos visuales y trabajo en parejas…"></textarea></label>
          <label class="field"><span>Recursos disponibles <em>Opcional</em></span><textarea id="resources" rows="3" placeholder="Uno por línea: pizarra, tarjetas, cuaderno…"></textarea></label>
        </div>
        <div class="generation-action">
          <div>${icons.sparkles}<span><strong>La IA creará un borrador editable</strong><small>No se guardará hasta que tú lo confirmes.</small></span></div>
          <button class="button button--primary" id="generate-button" type="submit">Crear borrador con IA ${icons.arrow}</button>
        </div>
      </form>
      <aside class="tips-panel">
        <span class="tips-icon">${icons.sparkles}</span>
        <h3>Para un mejor resultado</h3>
        <ul><li>Selecciona el contenido exacto.</li><li>Describe las necesidades particulares del grupo.</li><li>Indica solamente recursos que realmente tienes.</li></ul>
        <p>La propuesta es un punto de partida. Tu criterio docente sigue siendo la decisión final.</p>
      </aside>
    </section>
    <section id="draft-region"></section>`;

  const form = document.querySelector("#generation-form");
  document.querySelector("#grade").addEventListener("change", handleCatalogChange);
  document.querySelector("#subject").addEventListener("change", handleCatalogChange);
  document.querySelector("#curriculum-content").addEventListener("change", (event) => {
    state.selectedContentId = event.target.value;
  });
  form.addEventListener("submit", handleGenerate);
  if (state.draft) renderDraftEditor("create");
}

async function handleCatalogChange() {
  state.selectedGradeId = document.querySelector("#grade").value;
  state.selectedSubjectId = document.querySelector("#subject").value;
  state.selectedContentId = "";
  state.contents = [];
  if (state.selectedGradeId && state.selectedSubjectId) {
    try {
      state.contents = await request(`/catalogs/contents?grade_id=${state.selectedGradeId}&subject_id=${state.selectedSubjectId}`);
    } catch (error) {
      if (error.status !== 401) toast(error.message, "error");
    }
  }
  const select = document.querySelector("#curriculum-content");
  select.innerHTML = contentOptions();
  select.disabled = !state.contents.length;
  select.nextElementSibling.textContent = state.contents.length
    ? "Contenido asociado al grado y asignatura."
    : "No hay contenidos disponibles para esta combinación.";
}

function splitLines(value) {
  return value.split(/\n|,/).map((item) => item.trim()).filter(Boolean).slice(0, 12);
}

async function handleGenerate(event) {
  event.preventDefault();
  const grade = state.grades.find((item) => String(item.id) === String(state.selectedGradeId));
  const subject = state.subjects.find((item) => String(item.id) === String(state.selectedSubjectId));
  const content = state.contents.find((item) => String(item.id) === String(state.selectedContentId));
  if (!grade || !subject || !content) {
    toast("Selecciona grado, asignatura y contenido curricular.", "error");
    return;
  }

  const button = document.querySelector("#generate-button");
  setButtonLoading(button, true, "Creando borrador…");
  document.querySelector("#draft-region").innerHTML = `
    <div class="generation-progress" aria-busy="true">
      <div class="ai-orb ai-orb--small" aria-hidden="true"><span></span></div>
      <div><strong>Ollama está preparando tu propuesta</strong><p>Está organizando objetivo, actividades y evaluación. Esto puede tardar cerca de un minuto.</p></div>
      <span class="loading-line"></span>
    </div>`;
  try {
    state.draft = await request("/generation", {
      method: "POST",
      body: JSON.stringify({
        context: {
          grade: grade.name,
          subject: subject.name,
          curriculum_content: content.description,
          duration_minutes: Number(document.querySelector("#duration").value),
          learning_goal: document.querySelector("#learning-goal").value.trim() || null,
          student_needs: document.querySelector("#student-needs").value.trim() || null,
          resources: splitLines(document.querySelector("#resources").value),
        },
      }),
    });
    renderDraftEditor("create");
    document.querySelector("#draft-region").scrollIntoView({ behavior: "smooth", block: "start" });
    toast("Borrador generado. Revísalo antes de guardarlo.");
  } catch (error) {
    if (error.status !== 401) {
      document.querySelector("#draft-region").innerHTML = `<div class="inline-error">${icons.warning}<div><strong>No pudimos crear el borrador</strong><p>${escapeHtml(error.message)} Tu formulario se conserva para que puedas intentarlo de nuevo.</p></div></div>`;
      toast(error.message, "error");
    }
  } finally {
    setButtonLoading(button, false, "");
  }
}

function activityCard(activity, index) {
  return `
    <article class="activity-card" data-activity="${index}">
      <div class="activity-card__header">
        <label class="field field--compact"><span>Etapa</span><select data-field="stage"><option value="inicio" ${activity.stage === "inicio" ? "selected" : ""}>Inicio</option><option value="desarrollo" ${activity.stage === "desarrollo" ? "selected" : ""}>Desarrollo</option><option value="cierre" ${activity.stage === "cierre" ? "selected" : ""}>Cierre</option></select></label>
        <label class="field field--compact"><span>Minutos</span><input data-field="minutes" type="number" min="1" max="240" value="${activity.minutes}" /></label>
        <button class="icon-button remove-activity" type="button" title="Quitar actividad" aria-label="Quitar actividad" ${state.draft.activities.length <= 3 ? "disabled" : ""}>${icons.close}</button>
      </div>
      <label class="field"><span>Descripción</span><textarea data-field="description" rows="3" maxlength="1200">${escapeHtml(activity.description)}</textarea></label>
      <label class="field"><span>Recursos de esta actividad</span><input data-field="resources" value="${escapeHtml(activity.resources.join(", "))}" placeholder="Separados por comas" /></label>
    </article>`;
}

function renderDraftEditor(mode) {
  const region = mode === "edit" ? document.querySelector("#edit-region") : document.querySelector("#draft-region");
  if (!region || !state.draft) return;
  region.innerHTML = `
    <section class="draft-editor">
      <div class="draft-editor__title">
        <div><p class="eyebrow">${mode === "edit" ? "Planificación guardada" : "Borrador generado"}</p><h2>${mode === "edit" ? "Actualiza tu planificación" : "Revísalo y hazlo tuyo"}</h2><p>Todos los cambios serán validados antes de guardarse.</p></div>
        <span class="version-badge">Versión ${state.draft.schema_version}</span>
      </div>
      <div class="editor-section">
        <div class="section-heading"><span class="step-number">3</span><div><h3>Información general</h3><p>Ajusta el título y el propósito pedagógico.</p></div></div>
        <label class="field"><span>Título</span><input id="draft-title" maxlength="180" value="${escapeHtml(state.draft.title)}" /></label>
        <label class="field"><span>Objetivo de aprendizaje</span><textarea id="draft-objective" rows="3" maxlength="1000">${escapeHtml(state.draft.learning_objective)}</textarea></label>
      </div>
      <div class="editor-section">
        <div class="editor-section__header"><div class="section-heading"><span class="step-number">4</span><div><h3>Secuencia de actividades</h3><p>Debe incluir inicio, desarrollo y cierre.</p></div></div><button class="button button--secondary" id="add-activity" type="button">${icons.plus} Añadir actividad</button></div>
        <div id="activities-list" class="activities-list">${state.draft.activities.map(activityCard).join("")}</div>
      </div>
      <div class="editor-section">
        <div class="section-heading"><span class="step-number">5</span><div><h3>Evaluación y apoyos</h3><p>Define qué observarás y qué necesitarás.</p></div></div>
        <div class="form-grid">
          <label class="field"><span>Criterios de evaluación</span><textarea id="draft-criteria" rows="4" placeholder="Uno por línea">${escapeHtml(state.draft.assessment.criteria.join("\n"))}</textarea></label>
          <label class="field"><span>Evidencia esperada</span><textarea id="draft-evidence" rows="4" maxlength="800">${escapeHtml(state.draft.assessment.evidence)}</textarea></label>
          <label class="field"><span>Materiales</span><textarea id="draft-materials" rows="4" placeholder="Uno por línea">${escapeHtml(state.draft.materials.join("\n"))}</textarea></label>
          <label class="field"><span>Notas docentes</span><textarea id="draft-notes" rows="4" placeholder="Una por línea">${escapeHtml(state.draft.teacher_notes.join("\n"))}</textarea></label>
        </div>
      </div>
      <div class="editor-footer">
        <div>${icons.check}<span><strong>Tu revisión es la decisión final</strong><small>${mode === "edit" ? "Se actualizará la planificación existente." : "La propuesta aún no está guardada."}</small></span></div>
        <button class="button button--primary" id="save-plan" type="button">${icons.save} ${mode === "edit" ? "Guardar cambios" : "Guardar planificación"}</button>
      </div>
    </section>`;

  region.querySelector("#add-activity").addEventListener("click", () => {
    syncDraftFromEditor();
    if (state.draft.activities.length >= 8) return toast("Puedes incluir hasta ocho actividades.", "error");
    state.draft.activities.push({ stage: "desarrollo", description: "Nueva actividad", minutes: 10, resources: [] });
    renderDraftEditor(mode);
  });
  region.querySelectorAll(".remove-activity").forEach((button, index) => {
    button.addEventListener("click", () => {
      syncDraftFromEditor();
      state.draft.activities.splice(index, 1);
      renderDraftEditor(mode);
    });
  });
  region.querySelector("#save-plan").addEventListener("click", () => savePlan(mode));
}

function syncDraftFromEditor() {
  const region = document.querySelector(".draft-editor");
  if (!region || !state.draft) return;
  state.draft.title = region.querySelector("#draft-title").value.trim();
  state.draft.learning_objective = region.querySelector("#draft-objective").value.trim();
  state.draft.activities = [...region.querySelectorAll("[data-activity]")].map((card) => ({
    stage: card.querySelector("[data-field='stage']").value,
    description: card.querySelector("[data-field='description']").value.trim(),
    minutes: Number(card.querySelector("[data-field='minutes']").value),
    resources: splitLines(card.querySelector("[data-field='resources']").value),
  }));
  state.draft.assessment = {
    criteria: splitLines(region.querySelector("#draft-criteria").value).slice(0, 8),
    evidence: region.querySelector("#draft-evidence").value.trim(),
  };
  state.draft.materials = splitLines(region.querySelector("#draft-materials").value);
  state.draft.teacher_notes = splitLines(region.querySelector("#draft-notes").value).slice(0, 8);
}

function validateDraftClient() {
  syncDraftFromEditor();
  if (!state.draft.title || !state.draft.learning_objective) return "Completa el título y el objetivo.";
  if (state.draft.activities.some((item) => !item.description || item.minutes < 1)) return "Revisa la descripción y duración de todas las actividades.";
  const stages = new Set(state.draft.activities.map((item) => item.stage));
  if (!["inicio", "desarrollo", "cierre"].every((stage) => stages.has(stage))) return "Incluye al menos una actividad de inicio, desarrollo y cierre.";
  if (!state.draft.assessment.criteria.length || !state.draft.assessment.evidence) return "Completa los criterios y la evidencia de evaluación.";
  return "";
}

async function savePlan(mode) {
  const validation = validateDraftClient();
  if (validation) return toast(validation, "error");
  const button = document.querySelector("#save-plan");
  setButtonLoading(button, true, mode === "edit" ? "Actualizando…" : "Guardando…");
  const payload = {
    grade_id: Number(state.selectedGradeId) || null,
    subject_id: Number(state.selectedSubjectId) || null,
    curriculum_content_id: Number(state.selectedContentId) || null,
    content: state.draft,
  };
  try {
    const saved = await request(mode === "edit" ? `/plans/${state.editingPlan.id}` : "/plans", {
      method: mode === "edit" ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    const existing = state.plans.findIndex((plan) => plan.id === saved.id);
    if (existing >= 0) state.plans[existing] = saved;
    else state.plans.push(saved);
    state.draft = null;
    state.editingPlan = null;
    state.view = "plans";
    renderShell();
    toast(mode === "edit" ? "Cambios guardados correctamente." : "Planificación guardada correctamente.");
  } catch (error) {
    if (error.status !== 401) toast(error.message, "error");
  } finally {
    setButtonLoading(button, false, "");
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat("es-NI", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function renderPlans() {
  const container = document.querySelector("#workspace-content");
  container.innerHTML = `
    <section class="page-intro">
      <div><p class="eyebrow">Tu biblioteca</p><h1>Planificaciones guardadas</h1><p>Consulta y continúa mejorando tus propuestas docentes.</p></div>
      <button class="button button--primary" id="new-plan">${icons.plus} Nueva planificación</button>
    </section>
    ${state.plans.length ? `<div class="plans-grid">${[...state.plans].reverse().map((plan) => `
      <article class="plan-card">
        <div class="plan-card__top"><span class="subject-mark">${escapeHtml(plan.content.subject.slice(0, 1).toUpperCase())}</span><span>Actualizada ${escapeHtml(formatDate(plan.updated_at))}</span></div>
        <div><p class="plan-grade">${escapeHtml(plan.content.grade)}</p><h3>${escapeHtml(plan.content.title)}</h3><p class="plan-objective">${escapeHtml(plan.content.learning_objective)}</p></div>
        <div class="plan-meta"><span>${icons.clock} ${plan.content.activities.reduce((sum, item) => sum + item.minutes, 0)} min</span><span>${plan.content.activities.length} actividades</span></div>
        <button class="button button--secondary edit-plan" data-plan-id="${plan.id}">${icons.edit} Ver y editar</button>
      </article>`).join("")}</div>` : `
      <div class="empty-state"><div class="empty-illustration">${icons.library}</div><h3>Aún no tienes planificaciones</h3><p>Genera tu primer borrador y guárdalo para comenzar tu biblioteca.</p><button class="button button--primary" id="empty-new-plan">Crear mi primera planificación ${icons.arrow}</button></div>`}`;

  const openCreate = () => { state.view = "create"; renderShell(); };
  document.querySelector("#new-plan")?.addEventListener("click", openCreate);
  document.querySelector("#empty-new-plan")?.addEventListener("click", openCreate);
  document.querySelectorAll(".edit-plan").forEach((button) => button.addEventListener("click", () => openPlan(Number(button.dataset.planId))));
}

async function openPlan(planId) {
  try {
    const plan = await request(`/plans/${planId}`);
    state.editingPlan = plan;
    state.draft = structuredClone(plan.content);
    state.selectedGradeId = plan.grade_id ? String(plan.grade_id) : "";
    state.selectedSubjectId = plan.subject_id ? String(plan.subject_id) : "";
    state.selectedContentId = plan.curriculum_content_id ? String(plan.curriculum_content_id) : "";
    state.view = "edit";
    renderShell();
  } catch (error) {
    if (error.status !== 401) toast(error.message, "error");
  }
}

function renderEditPlan() {
  const container = document.querySelector("#workspace-content");
  container.innerHTML = `
    <button class="back-button" id="back-to-plans">${icons.back} Volver a mis planificaciones</button>
    <section class="edit-context"><div><span>Grado</span><strong>${escapeHtml(state.draft.grade)}</strong></div><div><span>Asignatura</span><strong>${escapeHtml(state.draft.subject)}</strong></div><div><span>Contenido</span><strong>${escapeHtml(state.draft.curriculum_content)}</strong></div></section>
    <section id="edit-region"></section>`;
  document.querySelector("#back-to-plans").addEventListener("click", () => {
    state.draft = null;
    state.editingPlan = null;
    state.view = "plans";
    renderShell();
  });
  renderDraftEditor("edit");
}

async function boot() {
  try {
    const health = await fetch("/health").then((response) => response.json());
    state.apiOnline = health.status === "ok";
  } catch {
    state.apiOnline = false;
  }
  try {
    state.user = await request("/auth/me");
    await loadWorkspace();
  } catch (error) {
    if (error.status !== 401) renderLogin("No pudimos conectar con el backend. Comprueba que el servicio esté activo.");
    else if (!state.user) renderLogin();
  }
}

boot();
