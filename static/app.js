const out = document.getElementById("out");
const askBtn = document.getElementById("ask");
const questionEl = document.getElementById("question");
const statusBar = document.getElementById("status-bar");
const statusText = document.getElementById("status-text");
const repoLink = document.getElementById("repo-link");

const samples = document.querySelectorAll(".samples button[data-q]");
samples.forEach((btn) => {
  btn.addEventListener("click", () => {
    questionEl.value = btn.getAttribute("data-q") || "";
    questionEl.focus();
  });
});

questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    askBtn.click();
  }
});

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(" ");
  }
  return JSON.stringify(detail);
}

function renderTable(columns, rows) {
  if (!columns.length) {
    return "<p class='muted'>No rows returned.</p>";
  }
  const head = columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("");
  const body = rows
    .map(
      (row) =>
        "<tr>" + row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("") + "</tr>"
    )
    .join("");
  return `<div class="table-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

async function loadMeta() {
  statusBar.hidden = false;
  statusText.textContent = "Loading…";
  try {
    const res = await fetch("/api/meta");
    const data = await res.json();
    statusBar.classList.remove("live", "stub");
    if (data.repo) {
      repoLink.href = data.repo;
    }
    const caps = `Row cap ${data.max_rows || "200"} · up to ${data.max_retries || "3"} SQL fixes`;
    if (data.llm_mode === "stub") {
      statusBar.classList.add("stub");
      statusText.innerHTML =
        "<strong>Stub mode</strong> <span class='muted'>— deterministic SQL patterns (CI). " +
        caps +
        ". Set OPENAI_API_KEY on the server for live drafting.</span>";
    } else {
      statusBar.classList.add("live");
      statusText.innerHTML =
        `<strong>Live</strong> <span class='muted'>— ${escapeHtml(data.model || "OpenAI")} · ${escapeHtml(data.database || "demo")} · ${caps}</span>`;
    }
  } catch {
    statusBar.classList.remove("live", "stub");
    statusText.textContent = "Could not load server status. Try a hard refresh.";
  }
}

function bindCopy(btnId, sql) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(sql);
      btn.textContent = "Copied";
      setTimeout(() => {
        btn.textContent = "Copy";
      }, 1500);
    } catch {
      btn.textContent = "Failed";
    }
  });
}

askBtn.addEventListener("click", async () => {
  const question = questionEl.value.trim();
  if (question.length < 3) {
    out.innerHTML =
      '<p class="error panel">Type a question with at least 3 characters, then click Ask.</p>';
    return;
  }

  askBtn.disabled = true;
  out.innerHTML =
    '<div class="panel"><span class="spinner"></span> Running LangGraph for: “' +
    escapeHtml(question) +
    "”…</div>";

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    if (!res.ok) {
      out.innerHTML = `<div class="panel error">${escapeHtml(formatDetail(data.detail))}</div>`;
      return;
    }

    const badgeClass = data.status === "ok" ? "ok" : data.status;
    const copyId = "copy-sql-" + Date.now();
    const sqlText = data.sql_query || "";

    let extra = "";
    if (data.retry_count > 0) {
      extra += `<p class="hint" style="margin:0.5rem 0 0">SQL revised ${data.retry_count} time(s) after validation or execution errors.</p>`;
    }
    if (data.status !== "ok" && data.error_log && data.error_log.length) {
      extra +=
        "<p class='error' style='margin:0.5rem 0 0;font-size:0.85rem'>" +
        escapeHtml(data.error_log.join(" · ")) +
        "</p>";
    }

    out.innerHTML =
      '<div class="panel"><h2>Answer</h2>' +
      `<span class="badge ${badgeClass}">${escapeHtml(data.status)}</span>` +
      `<p class="answer">${escapeHtml(data.answer)}</p>${extra}</div>` +
      '<div class="panel"><h2>Question</h2><p style="margin:0">' +
      escapeHtml(data.question) +
      "</p></div>" +
      '<div class="panel"><h2>SQL (after safety check)</h2><div class="sql-wrap">' +
      (sqlText
        ? `<button type="button" class="copy-btn" id="${copyId}">Copy</button><pre>${escapeHtml(sqlText)}</pre>`
        : "<pre><em>No SQL executed.</em></pre>") +
      "</div></div>" +
      '<div class="panel"><h2>Result set</h2>' +
      renderTable(data.query_columns || [], data.query_rows || []) +
      "</div>";

    if (sqlText) bindCopy(copyId, sqlText);
  } catch (err) {
    out.innerHTML =
      '<div class="panel error">Could not reach the server. Check that the API is running.</div>';
    console.error(err);
  } finally {
    askBtn.disabled = false;
  }
});

loadMeta();