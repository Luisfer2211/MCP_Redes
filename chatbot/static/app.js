let sessionId = null;

const messagesEl = document.getElementById("messages");
const logEl = document.getElementById("mcp-log");
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const modeSelect = document.getElementById("fittrack-mode");
const resetBtn = document.getElementById("reset-btn");
const demoBtn = document.getElementById("demo-git-btn");

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function refreshLog() {
  if (!sessionId) return;
  const res = await fetch(`/api/mcp-log?session_id=${sessionId}`);
  const data = await res.json();
  logEl.innerHTML = "";
  for (const entry of data.log) {
    const div = document.createElement("div");
    div.className = "log-entry";
    div.innerHTML = `
      <div class="meta">${entry.timestamp} | ${entry.server} | ${entry.direction} | ${entry.method}</div>
      <pre>${JSON.stringify(entry.payload, null, 2)}</pre>
    `;
    logEl.appendChild(div);
  }
  logEl.scrollTop = logEl.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  addMessage("user", text);

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, session_id: sessionId }),
  });
  const data = await res.json();
  if (!res.ok) {
    addMessage("assistant", `Error: ${data.detail || "Request failed"}`);
    return;
  }
  sessionId = data.session_id;
  addMessage("assistant", data.reply);
  await refreshLog();
});

modeSelect.addEventListener("change", async () => {
  if (!sessionId) return;
  await fetch(`/api/fittrack-mode?session_id=${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: modeSelect.value }),
  });
  await refreshLog();
});

resetBtn.addEventListener("click", async () => {
  await fetch(`/api/reset?session_id=${sessionId || ""}`, { method: "POST" });
  sessionId = null;
  messagesEl.innerHTML = "";
  logEl.innerHTML = "";
  addMessage("assistant", "Session reset. MCP servers will reconnect on your next message.");
});

demoBtn.addEventListener("click", async () => {
  addMessage("user", "[Git Demo] Create repo, README, and initial commit");
  demoBtn.disabled = true;
  const res = await fetch(`/api/demo-git?session_id=${sessionId || ""}`, { method: "POST" });
  const data = await res.json();
  demoBtn.disabled = false;
  if (!res.ok) {
    addMessage("assistant", `Demo error: ${data.detail || "Failed"}`);
    return;
  }
  sessionId = data.session_id;
  addMessage("assistant", data.reply);
  await refreshLog();
});

addMessage("assistant", "Welcome to FitTrack MCP Host. Ask about fitness, nutrition, or use the Git Demo button.");
