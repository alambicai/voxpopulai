/**
 * History view — past voting sessions.
 */

let _histPageOffset = 0;
const _HIST_PAGE_LIMIT = 10;

async function renderHistory() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page-header">
      <div>
        <div class="page-title">Historique</div>
        <div class="page-subtitle">Retrouvez toutes les sessions de vote passees</div>
      </div>
    </div>
    <div id="history-filters"></div>
    <div id="history-list"></div>
    <div id="history-detail"></div>
  `;

  _histPageOffset = 0;
  _loadHistoryPage();
}

async function _loadHistoryPage(search) {
  const filtersEl = document.getElementById("history-filters");
  const listEl = document.getElementById("history-list");
  if (!filtersEl || !listEl) return;

  const params = new URLSearchParams({ limit: _HIST_PAGE_LIMIT, offset: _histPageOffset, mode: "synthetic_vote" });
  if (search) params.set("search", search);

  filtersEl.innerHTML = `
    <div class="history-filters">
      <input type="text" id="hist-search" placeholder="Rechercher..." value="${_escapeHtml(search || "")}">
    </div>
  `;

  let _searchDebounce;
  document.getElementById("hist-search").addEventListener("input", (e) => {
    clearTimeout(_searchDebounce);
    _searchDebounce = setTimeout(() => {
      _histPageOffset = 0;
      _loadHistoryPage(e.target.value.trim());
    }, 400);
  });

  try {
    const resp = await API.get(`/history/?${params}`);
    const sessions = resp.sessions || [];
    const total = resp.total || 0;

    if (!sessions.length) {
      listEl.innerHTML = '<div class="empty-state">Aucune session enregistree.</div>';
      return;
    }

    listEl.innerHTML = `
      <div class="history-list">
        ${sessions.map(s => _renderHistItem(s)).join("")}
        ${total > _HIST_PAGE_LIMIT ? `
          <div class="history-pagination">
            ${_histPageOffset > 0 ? `<button class="btn btn-sm" id="hist-prev">Precedent</button>` : ""}
            <span>${_histPageOffset + 1}-${Math.min(_histPageOffset + _HIST_PAGE_LIMIT, total)} sur ${total}</span>
            ${_histPageOffset + _HIST_PAGE_LIMIT < total ? `<button class="btn btn-sm" id="hist-next">Suivant</button>` : ""}
          </div>
        ` : ""}
      </div>
    `;

    const prevBtn = document.getElementById("hist-prev");
    const nextBtn = document.getElementById("hist-next");
    if (prevBtn) prevBtn.addEventListener("click", () => {
      _histPageOffset = Math.max(0, _histPageOffset - _HIST_PAGE_LIMIT);
      _loadHistoryPage(search);
    });
    if (nextBtn) nextBtn.addEventListener("click", () => {
      _histPageOffset += _HIST_PAGE_LIMIT;
      _loadHistoryPage(search);
    });

    document.querySelectorAll(".history-item").forEach(item => {
      item.addEventListener("click", () => _viewSessionDetail(item.dataset.collabId));
    });

  } catch {
    listEl.innerHTML = '<div class="empty-state">Erreur de chargement.</div>';
  }
}

function _renderHistItem(session) {
  const topic = session.topic || session.question || "";
  const ts = session.timestamp ? _fmtTs(session.timestamp) : "";
  const profile = session.population_profile || "";
  
  return `
    <div class="history-item" data-collab-id="${_escapeHtml(session.collaboration_id)}">
      <div class="history-item-icon">🗳️</div>
      <div class="history-item-info">
        <div class="history-item-topic">${_escapeHtml(topic)}</div>
        <div class="history-item-meta">
          <span class="tag muted">${_escapeHtml(profile)}</span>
        </div>
      </div>
      <div class="history-item-time">${_escapeHtml(ts)}</div>
    </div>
  `;
}

function _fmtTs(isoStr) {
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return "A l'instant";
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)}min`;
    if (diff < 86400000) return `Il y a ${Math.floor(diff / 3600000)}h`;
    return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

async function _viewSessionDetail(collabId) {
  const detailEl = document.getElementById("history-detail");
  detailEl.innerHTML = '<div class="card"><div class="loading-bar"></div><p style="text-align:center;color:var(--text-muted);margin-top:12px">Chargement...</p></div>';
  detailEl.scrollIntoView({ behavior: "smooth" });

  try {
    const session = await API.get(`/history/${encodeURIComponent(collabId)}`);
    const result = session.result;

    const wrapper = document.createElement("div");
    wrapper.id = "vote-result";
    detailEl.innerHTML = "";
    detailEl.appendChild(wrapper);
    _renderVoteResult(result);
  } catch (err) {
    detailEl.innerHTML = `<div class="card" style="border-color:var(--error)"><p style="color:var(--error)">Erreur : ${_escapeHtml(err.message)}</p></div>`;
  }
}
