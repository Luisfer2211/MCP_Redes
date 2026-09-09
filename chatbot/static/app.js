let sessionId = null;
let fittrackMode = "local";
let activeServerFilter = "all";
let logEntries = [];

const messagesEl = document.getElementById("messages");
const logEl = document.getElementById("mcp-log");
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const modeSelect = document.getElementById("fittrack-mode");
const resetBtn = document.getElementById("reset-btn");
const demoBtn = document.getElementById("demo-git-btn");
const statusBar = document.getElementById("status-bar");
const statusText = document.getElementById("status-text");
const statusContext = document.getElementById("status-context");
const suggestionsEl = document.getElementById("suggestions");
const charCountEl = document.getElementById("char-count");
const logCountEl = document.getElementById("log-count");
const copyLogBtn = document.getElementById("copy-log-btn");
const filterButtons = [...document.querySelectorAll(".filter-tab")];
const promptChips = [...document.querySelectorAll(".chip")];

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const serverLabels = { fittrack: "FitTrack", filesystem: "Archivos", git: "Git" };

if (window.marked) {
  window.marked.setOptions({ gfm: true, breaks: true });
}

function setStatus(state, text, context) {
  statusBar.dataset.state = state || "ready";
  statusText.textContent = text;
  if (context) statusContext.textContent = context;
}

function setBusy(isBusy) {
  sendBtn.disabled = isBusy || !input.value.trim();
  input.disabled = isBusy;
  modeSelect.disabled = isBusy;
  demoBtn.disabled = isBusy;
  resetBtn.disabled = isBusy;
  promptChips.forEach((chip) => { chip.disabled = isBusy; });
  form.setAttribute("aria-busy", String(isBusy));
}

function scrollMessages() {
  messagesEl.scrollTo({
    top: messagesEl.scrollHeight,
    behavior: prefersReducedMotion ? "auto" : "smooth",
  });
}

function messageTime() {
  return new Intl.DateTimeFormat("es", { hour: "2-digit", minute: "2-digit" }).format(new Date());
}

function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text).then(() => true).catch(() => false);
  }
  const temp = document.createElement("textarea");
  temp.value = text;
  temp.setAttribute("readonly", "");
  temp.style.position = "fixed";
  temp.style.opacity = "0";
  document.body.appendChild(temp);
  temp.select();
  const copied = document.execCommand("copy");
  temp.remove();
  return Promise.resolve(copied);
}

function decorateMarkdown(container) {
  container.querySelectorAll("a").forEach((link) => {
    if (/^https?:$/i.test(new URL(link.href, window.location.href).protocol)) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  });

  container.querySelectorAll("pre").forEach((pre) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    button.textContent = "Copiar";
    button.setAttribute("aria-label", "Copiar bloque de código");
    button.addEventListener("click", async () => {
      const copied = await copyText(pre.querySelector("code")?.textContent || pre.textContent);
      button.textContent = copied ? "Copiado" : "No se pudo copiar";
      window.setTimeout(() => { button.textContent = "Copiar"; }, 1600);
    });
    pre.appendChild(button);
  });
}

function renderMarkdown(container, text) {
  if (window.marked && window.DOMPurify) {
    const html = window.marked.parse(text || "");
    container.innerHTML = window.DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
    decorateMarkdown(container);
    return;
  }

  const paragraph = document.createElement("p");
  paragraph.textContent = text || "";
  paragraph.style.whiteSpace = "pre-wrap";
  container.appendChild(paragraph);
}

function addSystemNotice(text) {
  const notice = document.createElement("div");
  notice.className = "system-notice";
  notice.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v5m0-8h.01"></path></svg>';
  const copy = document.createElement("span");
  copy.textContent = text;
  notice.appendChild(copy);
  messagesEl.appendChild(notice);
  scrollMessages();
  return notice;
}

function addMessage(role, text, options = {}) {
  if (role === "system") return addSystemNotice(text);

  const article = document.createElement("article");
  article.className = `message ${role}${options.error ? " error" : ""}${options.thinking ? " thinking" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "Tú" : "FT";

  const stack = document.createElement("div");
  stack.className = "message-stack";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const author = document.createElement("strong");
  author.textContent = role === "user" ? "Tú" : "FitTrack";
  const time = document.createElement("time");
  time.textContent = options.thinking ? "pensando…" : messageTime();
  meta.append(author, time);

  const content = document.createElement("div");
  content.className = "message-content";
  if (options.thinking) {
    content.innerHTML = '<span class="typing-dots" aria-label="FitTrack está preparando una respuesta"><i></i><i></i><i></i></span>';
  } else if (role === "assistant") {
    renderMarkdown(content, text);
  } else {
    content.textContent = text;
  }

  stack.append(meta, content);
  article.append(avatar, stack);
  messagesEl.appendChild(article);
  scrollMessages();
  return article;
}

function showWelcome() {
  addMessage(
    "assistant",
    "¡Hola! Soy tu asistente de **fitness y nutrición**. Puedo responder preguntas o usar herramientas MCP para:\n\n- Crear perfiles y calcular macros\n- Registrar comidas y actividad\n- Consultar tu progreso\n- Trabajar con archivos y Git\n\n¿Qué te gustaría hacer hoy?"
  );
}

function autoResizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 128)}px`;
  charCountEl.textContent = `${input.value.length} / ${input.maxLength}`;
  if (!form.hasAttribute("aria-busy") || form.getAttribute("aria-busy") === "false") {
    sendBtn.disabled = !input.value.trim();
  }
}

function formatTimestamp(value) {
  if (!value) return "ahora";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "ahora";
  return new Intl.DateTimeFormat("es", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(date);
}

function visibleEntries() {
  return activeServerFilter === "all"
    ? logEntries
    : logEntries.filter((entry) => entry.server === activeServerFilter);
}

function methodLabel(entry) {
  const toolName = entry.payload?.params?.name;
  return toolName && entry.method === "tools/call" ? `${entry.method} · ${toolName}` : entry.method;
}

function createEmptyLog(filtered = false) {
  const empty = document.createElement("div");
  if (filtered) {
    empty.className = "no-results";
    empty.textContent = "No hay eventos de este servidor en la sesión actual.";
    return empty;
  }
  empty.className = "log-empty";
  empty.innerHTML = `
    <div class="empty-state">
      <span class="empty-visual" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="M8 9 4 12l4 3m8-6 4 3-4 3m-5-9-2 12"></path></svg>
      </span>
      <strong>Sin actividad todavía</strong>
      <p>Cuando el asistente use una herramienta, la solicitud y su respuesta aparecerán aquí.</p>
    </div>`;
  return empty;
}

function renderLog() {
  const entries = visibleEntries();
  logEl.replaceChildren();
  logCountEl.textContent = String(logEntries.length);
  logCountEl.setAttribute("aria-label", `${logEntries.length} eventos MCP`);
  copyLogBtn.disabled = logEntries.length === 0;

  if (!entries.length) {
    logEl.appendChild(createEmptyLog(logEntries.length > 0));
    return;
  }

  entries.forEach((entry, index) => {
    const details = document.createElement("details");
    details.className = "log-entry";
    details.dataset.direction = entry.direction || "OUT";
    details.open = entries.length <= 2 || (index === entries.length - 1 && entry.method === "tools/call");

    const summary = document.createElement("summary");
    const direction = document.createElement("span");
    direction.className = `direction-badge${entry.direction === "IN" ? " in" : ""}`;
    direction.textContent = entry.direction === "IN" ? "Entrada" : "Salida";

    const summaryMain = document.createElement("span");
    summaryMain.className = "log-summary-main";
    const method = document.createElement("span");
    method.className = "log-method";
    method.textContent = methodLabel(entry);
    const meta = document.createElement("span");
    meta.className = "log-meta";
    const serverDot = document.createElement("span");
    serverDot.className = `server-dot ${entry.server || ""}`;
    serverDot.setAttribute("aria-hidden", "true");
    const server = document.createElement("span");
    server.textContent = serverLabels[entry.server] || entry.server || "Servidor";
    const timestamp = document.createElement("time");
    timestamp.textContent = formatTimestamp(entry.timestamp);
    meta.append(serverDot, server, "·", timestamp);
    summaryMain.append(method, meta);
    summary.append(direction, summaryMain);

    const body = document.createElement("div");
    body.className = "log-body";
    const payload = JSON.stringify(entry.payload, null, 2);
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.className = "log-copy";
    copyButton.textContent = "Copiar JSON";
    copyButton.addEventListener("click", async () => {
      const copied = await copyText(payload);
      copyButton.textContent = copied ? "Copiado" : "Error al copiar";
      window.setTimeout(() => { copyButton.textContent = "Copiar JSON"; }, 1600);
    });
    const pre = document.createElement("pre");
    pre.textContent = payload;
    body.append(copyButton, pre);
    details.append(summary, body);
    logEl.appendChild(details);
  });

  logEl.scrollTop = logEl.scrollHeight;
}

async function refreshLog() {
  if (!sessionId) {
    logEntries = [];
    renderLog();
    return;
  }
  try {
    const res = await fetch(`/api/mcp-log?session_id=${encodeURIComponent(sessionId)}`);
    if (!res.ok) throw new Error("No se pudo cargar el registro");
    const data = await res.json();
    logEntries = Array.isArray(data.log) ? data.log : [];
    renderLog();
  } catch (error) {
    console.error(error);
    setStatus("error", "No se pudo actualizar la actividad MCP");
  }
}

async function responseData(response) {
  try {
    return await response.json();
  } catch {
    return { detail: `El servidor respondió con estado ${response.status}` };
  }
}

async function sendMessage(rawText) {
  const text = rawText.trim();
  if (!text || form.getAttribute("aria-busy") === "true") return;

  suggestionsEl.hidden = true;
  addMessage("user", text);
  const thinkingMessage = addMessage("assistant", "", { thinking: true });
  setBusy(true);
  setStatus(
    "busy",
    "Preparando respuesta…",
    sessionId ? "Procesando con el contexto de esta sesión" : "Conectando herramientas MCP por primera vez"
  );

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId, fittrack_mode: fittrackMode }),
    });
    const data = await responseData(res);
    thinkingMessage.remove();

    if (!res.ok) {
      setStatus("error", "No se pudo completar la solicitud", "Puedes volver a intentarlo sin perder la conversación");
      addMessage("assistant", `**Ocurrió un error:** ${data.detail || "No se pudo completar la solicitud."}`, { error: true });
      return;
    }

    sessionId = data.session_id;
    addMessage("assistant", data.reply || "La respuesta llegó vacía. Intenta reformular tu solicitud.");
    setStatus("ready", "Respuesta completada", "Consulta la actividad MCP para verificar las herramientas utilizadas");
    await refreshLog();
  } catch (error) {
    thinkingMessage.remove();
    setStatus("error", "Sin conexión con el servidor", "Revisa que el host de FitTrack esté en ejecución");
    addMessage("assistant", `**Error de red:** ${error.message}`, { error: true });
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value;
  if (!text.trim()) return;
  input.value = "";
  autoResizeInput();
  await sendMessage(text);
});

input.addEventListener("input", autoResizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

promptChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    const prompt = chip.dataset.prompt;
    if (prompt) sendMessage(prompt);
  });
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activeServerFilter = button.dataset.server;
    filterButtons.forEach((item) => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    renderLog();
  });
});

copyLogBtn.addEventListener("click", async () => {
  const copied = await copyText(JSON.stringify(logEntries, null, 2));
  copyLogBtn.title = copied ? "Registro copiado" : "No se pudo copiar";
  copyLogBtn.setAttribute("aria-label", copyLogBtn.title);
  window.setTimeout(() => {
    copyLogBtn.title = "Copiar registro";
    copyLogBtn.setAttribute("aria-label", "Copiar registro MCP");
  }, 1600);
});

modeSelect.addEventListener("change", async () => {
  fittrackMode = modeSelect.value;
  const label = fittrackMode === "remote" ? "Cloud Run" : "local";
  setStatus("busy", `Cambiando a FitTrack ${label}…`, "Actualizando el servidor de herramientas");

  try {
    if (sessionId) {
      const res = await fetch(`/api/fittrack-mode?session_id=${encodeURIComponent(sessionId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: fittrackMode }),
      });
      if (!res.ok) throw new Error("No se pudo cambiar el servidor");
      await refreshLog();
    }
    setStatus("ready", `FitTrack ${label} seleccionado`, `Las próximas herramientas usarán el servidor ${label}`);
  } catch (error) {
    setStatus("error", error.message, "Conserva la sesión y vuelve a intentarlo");
  }
});

resetBtn.addEventListener("click", async () => {
  resetBtn.disabled = true;
  try {
    await fetch(`/api/reset?session_id=${encodeURIComponent(sessionId || "")}`, { method: "POST" });
  } catch (error) {
    console.error(error);
  }
  sessionId = null;
  messagesEl.replaceChildren();
  suggestionsEl.hidden = false;
  input.value = "";
  autoResizeInput();
  logEntries = [];
  renderLog();
  setStatus("ready", "Nueva sesión iniciada", `FitTrack ${fittrackMode === "remote" ? "Cloud Run" : "local"} · Herramientas bajo demanda`);
  addSystemNotice("Sesión anterior cerrada. Tu próxima consulta comenzará con un contexto nuevo.");
  showWelcome();
  resetBtn.disabled = false;
  input.focus();
});

demoBtn.addEventListener("click", () => {
  sendMessage("Crea un repositorio git, crea README.md con una descripción breve del proyecto FitTrack MCP, agrégalo y haz un commit con el mensaje 'Initial commit'.");
});

autoResizeInput();
renderLog();
showWelcome();
