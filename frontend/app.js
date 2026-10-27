const app = document.querySelector("#app");
const toastRegion = document.querySelector("#toast-region");

const state = {
  user: null,
  profile: null,
  grades: [],
  subjects: [],
  plans: [],
  view: "chat",
  chat: null,
  sidebarOpen: false,
  editingMessage: null,
};

const icon = (name) => ({
  sparkles: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.5 4.4L18 9l-4.5 1.6L12 15l-1.5-4.4L6 9l4.5-1.6L12 3Z"/><path d="m5 15 .7 2.3L8 18l-2.3.7L5 21l-.7-2.3L2 18l2.3-.7L5 15Zm14-2 .7 2.3 2.3.7-2.3.7L19 19l-.7-2.3L16 16l2.3-.7L19 13Z"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`,
  library: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20M8 7h8"/></svg>`,
  send: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 17 8-17 8 3-8-3-8Z"/><path d="M7 12h14"/></svg>`,
  settings: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></svg>`,
  logout: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 17l5-5-5-5M15 12H3M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/></svg>`,
  menu: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>`,
  close: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>`,
  edit: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 20 4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10L4 20Z"/><path d="m14 7 3 3"/></svg>`,
  save: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h12l2 2v16H5V3Z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/></svg>`,
  check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>`,
  warning: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2 21h20L12 3Z"/><path d="M12 9v5M12 18h.01"/></svg>`,
  chevron: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>`,
}[name] || "");

function escapeHtml(value = "") {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function describeError(payload, fallback) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (Array.isArray(payload?.detail)) return payload.detail.map((item) => item.msg).filter(Boolean).join(" · ") || fallback;
  return fallback;
}

async function request(path, options = {}) {
  const response = await fetch(path, { credentials: "include", ...options, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers } });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") { state.user = null; renderLogin("Tu sesión terminó. Inicia sesión nuevamente."); }
    throw new Error(describeError(payload, "No se pudo completar la solicitud."));
  }
  return payload;
}

function toast(message, type = "success") {
  const node = document.createElement("div");
  node.className = `toast toast--${type}`;
  node.innerHTML = `${icon(type === "success" ? "check" : "warning")}<span>${escapeHtml(message)}</span>`;
  toastRegion.append(node);
  setTimeout(() => node.remove(), 4800);
}

function setLoading(button, loading, text = "Procesando…") {
  if (!button) return;
  if (!button.dataset.label) button.dataset.label = button.innerHTML;
  button.disabled = loading;
  button.innerHTML = loading ? `<span class="spinner"></span>${escapeHtml(text)}` : button.dataset.label;
}

function renderLogin(message = "") {
  state.chat = null;
  app.innerHTML = `
    <main class="login-page">
      <section class="login-story"><a class="brand brand--light" href="#"><span class="brand-mark">A</span><span><strong>Colegio Alfa</strong><small>Asistente docente local</small></span></a><div class="story-copy"><span class="story-orb">${icon("sparkles")}</span><p class="eyebrow">IA local · Privacidad primero</p><h1>Conversa. Crea. Ajusta a tu manera.</h1><p>Describe lo que necesitas para tu clase y recibe un borrador profesional, editable y listo para revisar.</p></div><p class="story-foot">La IA propone. La decisión pedagógica siempre es tuya.</p></section>
      <section class="login-panel"><form id="login-form" class="login-form"><div class="mobile-brand"><span class="brand-mark">A</span><strong>Colegio Alfa</strong></div><p class="eyebrow">Bienvenido</p><h2>Ingresa a tu espacio docente</h2><p class="muted">Usa la cuenta que fue preparada para ti.</p>${message ? `<div class="form-alert">${icon("warning")}<span>${escapeHtml(message)}</span></div>` : ""}<label class="field"><span>Usuario</span><input name="username" autocomplete="username" maxlength="50" required placeholder="Tu usuario"></label><label class="field"><span>Contraseña</span><div class="password-wrap"><input name="password" type="password" autocomplete="current-password" required placeholder="Tu contraseña"><button id="toggle-password" type="button">Mostrar</button></div></label><button class="button button--primary button--wide" type="submit">Continuar ${icon("chevron")}</button></form></section>
    </main>`;
  const form = document.querySelector("#login-form");
  document.querySelector("#toggle-password").addEventListener("click", (event) => { form.elements.password.type = form.elements.password.type === "password" ? "text" : "password"; event.currentTarget.textContent = form.elements.password.type === "password" ? "Mostrar" : "Ocultar"; });
  form.addEventListener("submit", async (event) => {
    event.preventDefault(); const button = form.querySelector("button[type='submit']"); setLoading(button, true, "Verificando…");
    try { const data = new FormData(form); state.user = await request("/auth/login", { method: "POST", body: JSON.stringify({ username: data.get("username"), password: data.get("password") }) }); await loadWorkspace(); }
    catch (error) { renderLogin(error.message); }
  });
}

async function loadWorkspace() {
  const [profile, grades, subjects, plans] = await Promise.all([request("/profile"), request("/catalogs/grades"), request("/catalogs/subjects"), request("/plans")]);
  Object.assign(state, { profile, grades, subjects, plans });
  if (!profile.completed) renderOnboarding(); else renderShell();
}

function selectionChip(type, item, checked) {
  return `<label class="choice-chip"><input type="checkbox" name="${type}" value="${item.id}" ${checked ? "checked" : ""}><span>${icon("check")}${escapeHtml(item.name)}</span></label>`;
}

function renderOnboarding(editing = false) {
  const selectedGrades = new Set((state.profile?.grades || []).map((item) => item.id));
  const selectedSubjects = new Set((state.profile?.subjects || []).map((item) => item.id));
  app.innerHTML = `<main class="onboarding-page"><section class="onboarding-card"><div class="onboarding-head"><span class="brand-mark">A</span><div><p class="eyebrow">${editing ? "Preferencias docentes" : "Configuración inicial"}</p><h1>${editing ? "Actualiza tu perfil" : `Hola, ${escapeHtml(state.user.username)}`}</h1></div></div><p class="onboarding-lead">Selecciona los años y asignaturas que impartes. Esta información se guardará en tu perfil y no tendrás que repetirla en cada mensaje.</p><form id="profile-form"><fieldset><legend><b>1</b><span>Años de secundaria<small>Marca todos los años con los que trabajas.</small></span></legend><div class="choices-grid">${state.grades.map((item) => selectionChip("grade_ids", item, selectedGrades.has(item.id))).join("")}</div></fieldset><fieldset><legend><b>2</b><span>Asignaturas<small>Puedes seleccionar una o varias.</small></span></legend><div class="choices-grid choices-grid--subjects">${state.subjects.map((item) => selectionChip("subject_ids", item, selectedSubjects.has(item.id))).join("")}</div></fieldset><div class="onboarding-footer"><p>${icon("sparkles")} Podrás cambiar estas opciones después desde tu perfil.</p><div>${editing ? `<button class="button button--ghost" id="cancel-profile" type="button">Cancelar</button>` : ""}<button class="button button--primary" type="submit">Guardar y continuar ${icon("chevron")}</button></div></div></form></section></main>`;
  window.scrollTo(0, 0);
  document.querySelector("#cancel-profile")?.addEventListener("click", renderShell);
  document.querySelector("#profile-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const form = event.currentTarget;
    const gradeIds = [...form.querySelectorAll("input[name='grade_ids']:checked")].map((node) => Number(node.value));
    const subjectIds = [...form.querySelectorAll("input[name='subject_ids']:checked")].map((node) => Number(node.value));
    if (!gradeIds.length || !subjectIds.length) return toast("Selecciona al menos un año y una asignatura.", "error");
    const button = form.querySelector("button[type='submit']"); setLoading(button, true, "Guardando…");
    try { state.profile = await request("/profile", { method: "PUT", body: JSON.stringify({ grade_ids: gradeIds, subject_ids: subjectIds }) }); state.chat = null; renderShell(); toast("Tu perfil docente quedó configurado."); }
    catch (error) { toast(error.message, "error"); setLoading(button, false); }
  });
}

function shellMarkup(content) {
  return `<div class="app-shell ${state.sidebarOpen ? "menu-open" : ""}"><button class="sidebar-backdrop" id="sidebar-backdrop" aria-label="Cerrar menú"></button><aside class="sidebar"><div class="sidebar-brand"><span class="brand-mark">A</span><span><strong>Colegio Alfa</strong><small>Asistente docente</small></span><button class="icon-button sidebar-close" id="sidebar-close">${icon("close")}</button></div><button class="new-chat-button" id="new-chat">${icon("plus")} Nueva conversación</button><nav class="side-nav"><p class="side-label">Tu espacio</p><button class="side-link ${state.view === "chat" ? "is-active" : ""}" data-view="chat">${icon("sparkles")}<span>Asistente</span></button><button class="side-link ${state.view === "plans" ? "is-active" : ""}" data-view="plans">${icon("library")}<span>Planificaciones</span><b>${state.plans.length}</b></button></nav><div class="privacy-note"><span>${icon("sparkles")}</span><div><strong>IA en tu equipo</strong><p>Las propuestas se generan con Ollama y requieren tu revisión.</p></div></div><div class="user-card"><span class="avatar">${escapeHtml(state.user.username[0]?.toUpperCase())}</span><span><strong>${escapeHtml(state.user.username)}</strong><small>Docente</small></span><button class="icon-button" id="profile-settings" title="Perfil">${icon("settings")}</button><button class="icon-button" id="logout" title="Cerrar sesión">${icon("logout")}</button></div></aside><main class="workspace"><header class="topbar"><button class="icon-button menu-button" id="menu-button">${icon("menu")}</button><div><strong>${state.view === "plans" ? "Mis planificaciones" : "Asistente de planificación"}</strong><small>${state.chat && state.view === "chat" ? `${escapeHtml(state.chat.grade.name)} · ${escapeHtml(state.chat.subject.name)}` : "Colegio Alfa"}</small></div><span class="local-badge"><i></i> IA local</span></header>${content}</main></div>`;
}

function renderShell() {
  app.innerHTML = shellMarkup(state.view === "plans" ? plansMarkup() : chatMarkup());
  window.scrollTo(0, 0);
  bindShell();
  if (state.view === "plans") bindPlans(); else bindChat();
  if (state.editingMessage !== null) renderDraftEditor();
}

function bindShell() {
  document.querySelector("#new-chat").addEventListener("click", () => { state.chat = null; state.view = "chat"; state.sidebarOpen = false; renderShell(); });
  document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => { state.view = button.dataset.view; state.sidebarOpen = false; renderShell(); }));
  document.querySelector("#profile-settings").addEventListener("click", () => renderOnboarding(true));
  document.querySelector("#logout").addEventListener("click", async () => { await request("/auth/logout", { method: "POST" }); renderLogin(); });
  document.querySelector("#menu-button")?.addEventListener("click", () => { state.sidebarOpen = true; renderShell(); });
  document.querySelector("#sidebar-close")?.addEventListener("click", () => { state.sidebarOpen = false; renderShell(); });
  document.querySelector("#sidebar-backdrop")?.addEventListener("click", () => { state.sidebarOpen = false; renderShell(); });
}

function chatMarkup() {
  if (!state.chat) {
    const gradeOptions = state.profile.grades.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("");
    const subjectOptions = state.profile.subjects.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("");
    return `<section class="chat-empty"><div class="assistant-orb">${icon("sparkles")}</div><p class="eyebrow">Tu asistente pedagógico</p><h1>¿Qué quieres preparar hoy?</h1><p>Elige el contexto una sola vez para esta conversación. Después escribe con naturalidad, como se lo explicarías a un colega.</p><form id="start-chat-form" class="context-card"><div class="context-fields"><label><span>Año</span><select name="grade_id" required><option value="">Seleccionar año</option>${gradeOptions}</select></label><label><span>Asignatura</span><select name="subject_id" required><option value="">Seleccionar asignatura</option>${subjectOptions}</select></label><label><span>Duración</span><select name="duration"><option value="45">45 minutos</option><option value="60">60 minutos</option><option value="90">90 minutos</option><option value="120">120 minutos</option></select></label></div><button class="button button--primary" type="submit">Comenzar conversación ${icon("chevron")}</button></form><div class="prompt-ideas"><span>Prueba con</span><button data-idea="Necesito una clase participativa para introducir un tema nuevo.">Clase participativa</button><button data-idea="Ayúdame a preparar una actividad de repaso antes de una evaluación.">Actividad de repaso</button><button data-idea="Quiero una planificación inclusiva con materiales sencillos.">Plan inclusivo</button></div></section>`;
  }
  return `<section class="chat-page"><div class="chat-context"><span><b>${escapeHtml(state.chat.grade.name)}</b><small>${escapeHtml(state.chat.subject.name)} · ${state.chat.duration} min</small></span><button class="button button--ghost" id="change-context">Nueva conversación</button></div><div class="message-stream" id="message-stream">${state.chat.messages.length ? state.chat.messages.map(messageMarkup).join("") : welcomeMessageMarkup()}</div><form id="composer" class="composer"><textarea name="message" rows="1" maxlength="4000" required placeholder="Describe la planificación, actividad o ajuste que necesitas…"></textarea><div class="composer-foot"><span>${icon("sparkles")} La IA organizará tu idea y validará el resultado.</span><button class="send-button" type="submit" aria-label="Enviar">${icon("send")}</button></div></form><p class="chat-disclaimer">La IA puede equivocarse. Revisa siempre el contenido antes de utilizarlo o guardarlo.</p></section>`;
}

function welcomeMessageMarkup() {
  return `<article class="message message--assistant"><span class="message-avatar">A</span><div class="message-body"><strong>Asistente Alfa</strong><p>Ya tengo el contexto de <b>${escapeHtml(state.chat.subject.name)}</b> para <b>${escapeHtml(state.chat.grade.name)}</b>. Cuéntame qué quieres lograr con tu clase.</p></div></article>`;
}

function messageMarkup(message, index) {
  if (message.role === "user") return `<article class="message message--user"><div class="user-message">${escapeHtml(message.content)}</div></article>`;
  if (message.loading) return `<article class="message message--assistant"><span class="message-avatar">A</span><div class="message-body"><strong>Asistente Alfa</strong><div class="thinking"><span class="spinner"></span><p>Organizando tu solicitud y comprobando la propuesta…</p></div></div></article>`;
  if (message.error) return `<article class="message message--assistant"><span class="message-avatar message-avatar--error">!</span><div class="message-body"><strong>No pude completar la propuesta</strong><p>${escapeHtml(message.error)}</p></div></article>`;
  const draft = message.draft;
  return `<article class="message message--assistant"><span class="message-avatar">A</span><div class="message-body"><strong>Asistente Alfa</strong><p>${escapeHtml(message.content)}</p><section class="plan-result"><header><div><span class="result-kicker">Borrador generado</span><h2>${escapeHtml(draft.title)}</h2><p>${escapeHtml(draft.learning_objective)}</p></div><span class="schema-badge">v${draft.schema_version}</span></header><div class="plan-tags"><span>${escapeHtml(draft.grade)}</span><span>${escapeHtml(draft.subject)}</span><span>${draft.activities.reduce((sum, item) => sum + item.minutes, 0)} min</span></div><div class="plan-summary"><div><small>Contenido</small><p>${escapeHtml(draft.curriculum_content)}</p></div><div><small>Secuencia</small><p>${draft.activities.map((item) => `${escapeHtml(item.stage)} · ${item.minutes} min`).join(" &nbsp; · &nbsp; ")}</p></div><div><small>Evaluación</small><p>${escapeHtml(draft.assessment.evidence)}</p></div></div><details class="quality-checks"><summary>${icon("check")} Comprobaciones del backend</summary><ul>${message.checks.map((check) => `<li>${escapeHtml(check)}</li>`).join("")}</ul></details><footer><button class="button button--ghost edit-draft" data-index="${index}">${icon("edit")} Revisar y editar</button><button class="button button--primary save-draft" data-index="${index}">${icon("save")} ${message.savedPlanId ? "Actualizar guardado" : "Guardar planificación"}</button></footer></section></div></article>`;
}

function bindChat() {
  const startForm = document.querySelector("#start-chat-form");
  if (startForm) {
    document.querySelectorAll("[data-idea]").forEach((button) => button.addEventListener("click", () => { button.closest(".chat-empty").dataset.idea = button.dataset.idea; toast("Idea preparada. Elige año y asignatura para comenzar."); }));
    startForm.addEventListener("submit", (event) => { event.preventDefault(); const data = new FormData(startForm); const grade = state.profile.grades.find((item) => item.id === Number(data.get("grade_id"))); const subject = state.profile.subjects.find((item) => item.id === Number(data.get("subject_id"))); state.chat = { grade, subject, duration: Number(data.get("duration")), messages: [] }; const idea = startForm.closest(".chat-empty").dataset.idea; renderShell(); if (idea) document.querySelector("#composer textarea").value = idea; });
    return;
  }
  document.querySelector("#change-context").addEventListener("click", () => { state.chat = null; renderShell(); });
  const composer = document.querySelector("#composer"); const textarea = composer.elements.message;
  textarea.addEventListener("input", () => { textarea.style.height = "auto"; textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`; });
  textarea.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); composer.requestSubmit(); } });
  composer.addEventListener("submit", sendChatMessage);
  document.querySelectorAll(".edit-draft").forEach((button) => button.addEventListener("click", () => { state.editingMessage = Number(button.dataset.index); renderDraftEditor(); }));
  document.querySelectorAll(".save-draft").forEach((button) => button.addEventListener("click", () => saveDraft(Number(button.dataset.index), button)));
  requestAnimationFrame(() => document.querySelector("#message-stream")?.lastElementChild?.scrollIntoView({ block: "end", behavior: "smooth" }));
}

async function sendChatMessage(event) {
  event.preventDefault(); const textarea = event.currentTarget.elements.message; const content = textarea.value.trim(); if (content.length < 3) return;
  const history = state.chat.messages.filter((item) => !item.loading && !item.error).slice(-8).map((item) => ({ role: item.role, content: item.role === "assistant" ? `${item.draft.title}. ${item.draft.learning_objective}` : item.content }));
  state.chat.messages.push({ role: "user", content }, { role: "assistant", loading: true }); textarea.value = ""; renderShell();
  try { const response = await request("/chat/generate", { method: "POST", body: JSON.stringify({ grade_id: state.chat.grade.id, subject_id: state.chat.subject.id, message: content, duration_minutes: state.chat.duration, history }) }); state.chat.messages[state.chat.messages.length - 1] = { role: "assistant", content: response.assistant_message, draft: response.draft, checks: response.quality_checks, savedPlanId: null }; }
  catch (error) { state.chat.messages[state.chat.messages.length - 1] = { role: "assistant", error: error.message }; }
  renderShell();
}

async function saveDraft(index, button) {
  const message = state.chat.messages[index]; setLoading(button, true, "Guardando…");
  try {
    if (message.savedPlanId) { await request(`/plans/${message.savedPlanId}`, { method: "PATCH", body: JSON.stringify({ content: message.draft }) }); toast("Planificación actualizada."); }
    else { const saved = await request("/plans", { method: "POST", body: JSON.stringify({ grade_id: state.chat.grade.id, subject_id: state.chat.subject.id, curriculum_content_id: null, content: message.draft }) }); message.savedPlanId = saved.id; toast("Planificación guardada en tu historial."); }
    state.plans = await request("/plans"); renderShell();
  } catch (error) { toast(error.message, "error"); setLoading(button, false); }
}

function renderDraftEditor() {
  const message = state.chat.messages[state.editingMessage]; if (!message?.draft) return; const draft = message.draft;
  const overlay = document.createElement("div"); overlay.className = "editor-overlay"; overlay.id = "editor-overlay";
  overlay.innerHTML = `<section class="editor-panel"><header><div><p class="eyebrow">Revisión docente</p><h2>Edita el borrador</h2><p>La propuesta seguirá siendo validada al guardarse.</p></div><button class="icon-button" id="close-editor">${icon("close")}</button></header><form id="draft-form"><div class="editor-grid"><label class="field field--wide"><span>Título</span><input name="title" maxlength="180" required value="${escapeHtml(draft.title)}"></label><label class="field field--wide"><span>Contenido</span><textarea name="curriculum_content" maxlength="2000" required>${escapeHtml(draft.curriculum_content)}</textarea></label><label class="field field--wide"><span>Objetivo de aprendizaje</span><textarea name="learning_objective" maxlength="1000" required>${escapeHtml(draft.learning_objective)}</textarea></label></div><h3>Secuencia de actividades</h3><div class="activity-editor">${draft.activities.map((activity, index) => `<div class="activity-edit"><span>${escapeHtml(activity.stage)}</span><label class="field"><span>Minutos</span><input name="minutes_${index}" type="number" min="1" max="240" required value="${activity.minutes}"></label><label class="field field--wide"><span>Descripción</span><textarea name="description_${index}" maxlength="1200" required>${escapeHtml(activity.description)}</textarea></label><label class="field field--wide"><span>Recursos (separados por coma)</span><input name="resources_${index}" value="${escapeHtml(activity.resources.join(", "))}"></label></div>`).join("")}</div><h3>Evaluación y apoyos</h3><div class="editor-grid"><label class="field field--wide"><span>Criterios (uno por línea)</span><textarea name="criteria" required>${escapeHtml(draft.assessment.criteria.join("\n"))}</textarea></label><label class="field field--wide"><span>Evidencia</span><textarea name="evidence" maxlength="800" required>${escapeHtml(draft.assessment.evidence)}</textarea></label><label class="field"><span>Materiales (separados por coma)</span><textarea name="materials">${escapeHtml(draft.materials.join(", "))}</textarea></label><label class="field"><span>Notas docentes (una por línea)</span><textarea name="teacher_notes">${escapeHtml(draft.teacher_notes.join("\n"))}</textarea></label></div><footer><button class="button button--ghost" id="cancel-editor" type="button">Cancelar</button><button class="button button--primary" type="submit">${icon("check")} Aplicar cambios</button></footer></form></section>`;
  document.body.append(overlay);
  const close = () => { state.editingMessage = null; overlay.remove(); };
  document.querySelector("#close-editor").addEventListener("click", close); document.querySelector("#cancel-editor").addEventListener("click", close); overlay.addEventListener("click", (event) => { if (event.target === overlay) close(); });
  document.querySelector("#draft-form").addEventListener("submit", (event) => {
    event.preventDefault(); const data = new FormData(event.currentTarget); draft.title = data.get("title").trim(); draft.curriculum_content = data.get("curriculum_content").trim(); draft.learning_objective = data.get("learning_objective").trim();
    draft.activities.forEach((activity, index) => { activity.minutes = Number(data.get(`minutes_${index}`)); activity.description = data.get(`description_${index}`).trim(); activity.resources = data.get(`resources_${index}`).split(",").map((item) => item.trim()).filter(Boolean); });
    draft.assessment.criteria = data.get("criteria").split("\n").map((item) => item.trim()).filter(Boolean); draft.assessment.evidence = data.get("evidence").trim(); draft.materials = data.get("materials").split(",").map((item) => item.trim()).filter(Boolean); draft.teacher_notes = data.get("teacher_notes").split("\n").map((item) => item.trim()).filter(Boolean);
    close(); renderShell(); toast("Cambios aplicados al borrador.");
  });
}

function plansMarkup() {
  if (!state.plans.length) return `<section class="plans-page"><div class="page-heading"><div><p class="eyebrow">Tu biblioteca</p><h1>Planificaciones guardadas</h1><p>Los borradores que decidas conservar aparecerán aquí.</p></div></div><div class="empty-library">${icon("library")}<h2>Aún no has guardado planificaciones</h2><p>Inicia una conversación con el asistente y guarda el borrador que te resulte útil.</p><button class="button button--primary" id="empty-new-chat">${icon("plus")} Crear la primera</button></div></section>`;
  return `<section class="plans-page"><div class="page-heading"><div><p class="eyebrow">Tu biblioteca</p><h1>Planificaciones guardadas</h1><p>Continúa revisando tus borradores cuando lo necesites.</p></div><button class="button button--primary" id="plans-new-chat">${icon("plus")} Nueva conversación</button></div><div class="plans-grid">${state.plans.map((plan) => `<article class="plan-card"><div class="plan-card-top"><span class="subject-monogram">${escapeHtml(plan.content.subject[0] || "A")}</span><time>${new Date(plan.updated_at).toLocaleDateString("es-NI", { day: "numeric", month: "short" })}</time></div><p class="plan-card-grade">${escapeHtml(plan.content.grade)} · ${escapeHtml(plan.content.subject)}</p><h2>${escapeHtml(plan.content.title)}</h2><p>${escapeHtml(plan.content.learning_objective)}</p><div class="plan-card-meta"><span>${plan.content.activities.reduce((sum, item) => sum + item.minutes, 0)} min</span><span>${plan.content.activities.length} actividades</span></div><button class="open-plan" data-plan-id="${plan.id}">Abrir y continuar ${icon("chevron")}</button></article>`).join("")}</div></section>`;
}

function bindPlans() {
  const newChat = () => { state.chat = null; state.view = "chat"; renderShell(); }; document.querySelector("#empty-new-chat")?.addEventListener("click", newChat); document.querySelector("#plans-new-chat")?.addEventListener("click", newChat);
  document.querySelectorAll(".open-plan").forEach((button) => button.addEventListener("click", () => { const plan = state.plans.find((item) => item.id === Number(button.dataset.planId)); const grade = state.profile.grades.find((item) => item.id === plan.grade_id) || { id: plan.grade_id, name: plan.content.grade }; const subject = state.profile.subjects.find((item) => item.id === plan.subject_id) || { id: plan.subject_id, name: plan.content.subject }; state.chat = { grade, subject, duration: plan.content.activities.reduce((sum, item) => sum + item.minutes, 0), messages: [{ role: "assistant", content: "Abrí esta planificación desde tu biblioteca. Puedes editarla, actualizarla o pedirme una nueva propuesta en el mismo contexto.", draft: structuredClone(plan.content), checks: ["Contenido recuperado desde PostgreSQL", "Propiedad docente verificada"], savedPlanId: plan.id }] }; state.view = "chat"; renderShell(); }));
}

async function boot() {
  try { state.user = await request("/auth/me"); await loadWorkspace(); }
  catch (error) { renderLogin(state.user ? error.message : ""); }
}

boot();
