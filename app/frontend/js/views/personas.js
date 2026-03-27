/**
 * Vue Personas — gestion, statistiques et generation des personas synthetiques.
 */

let _personasCurrentTab = "overview";
let _personasListPage = 0;
const _PERSONAS_PAGE_SIZE = 50;
let _personasListProfile = "";
let _personasDistProfile = "";

async function renderPersonas() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page-header">
      <div>
        <div class="page-title">Personas</div>
        <div class="page-subtitle">Gestion des personas synthetiques pour le vote a l'assemblee</div>
      </div>
      <div class="personas-actions">
        <button class="btn btn-primary" id="personas-generate-btn">&#43; Generer</button>
      </div>
    </div>

    <div class="personas-tabs">
      <button class="personas-tab ${_personasCurrentTab === "overview" ? "active" : ""}" data-tab="overview">Vue d'ensemble</button>
      <button class="personas-tab ${_personasCurrentTab === "list" ? "active" : ""}" data-tab="list">Liste</button>
      <button class="personas-tab ${_personasCurrentTab === "distributions" ? "active" : ""}" data-tab="distributions">Distributions</button>
      <button class="personas-tab ${_personasCurrentTab === "profiles" ? "active" : ""}" data-tab="profiles">Profils</button>
    </div>

    <div id="personas-content"><div class="loading-bar"></div></div>
  `;

  // Tab handling
  document.querySelectorAll(".personas-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".personas-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      _personasCurrentTab = tab.dataset.tab;
      _loadPersonasTab();
    });
  });

  document.getElementById("personas-generate-btn").addEventListener("click", _showGenerateModal);

  _loadPersonasTab();
}

async function _loadPersonasTab() {
  const container = document.getElementById("personas-content");
  container.innerHTML = '<div class="loading-bar"></div>';

  try {
    if (_personasCurrentTab === "overview") {
      await _renderPersonasOverview(container);
    } else if (_personasCurrentTab === "list") {
      await _renderPersonasList(container);
    } else if (_personasCurrentTab === "distributions") {
      await _renderPersonasDistributions(container);
    } else if (_personasCurrentTab === "profiles") {
      await _renderPersonasProfiles(container);
    }
  } catch (err) {
    container.innerHTML = `<div class="empty-state" style="color:var(--error)">${_escapePersonasHtml(err.message)}</div>`;
  }
}

// ── Overview tab ──

async function _renderPersonasOverview(container) {
  const stats = await API.get("/personas/stats");

  if (stats.total === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">&#128100;</div>
        <div>Aucun persona genere pour le moment.</div>
        <button class="btn btn-primary" onclick="_showGenerateModal()">Generer des personas</button>
      </div>`;
    return;
  }

  let html = '<div class="personas-stats">';
  html += `<div class="personas-stat-card">
    <div class="personas-stat-value">${stats.total}</div>
    <div class="personas-stat-label">Total personas</div>
  </div>`;

  // Per profile
  for (const [profile, count] of Object.entries(stats.by_profile)) {
    html += `<div class="personas-stat-card">
      <div class="personas-stat-value">${count}</div>
      <div class="personas-stat-label">${_escapePersonasHtml(profile)}</div>
    </div>`;
  }

  // Per model
  for (const [model, count] of Object.entries(stats.by_model)) {
    html += `<div class="personas-stat-card">
      <div class="personas-stat-value">${count}</div>
      <div class="personas-stat-label">${_escapePersonasHtml(model)}</div>
    </div>`;
  }
  html += "</div>";

  // Delete actions
  const profiles = Object.keys(stats.by_profile);
  if (profiles.length > 0) {
    html += `
      <div style="margin-top:16px">
        <h4 style="margin-bottom:8px">Suppression</h4>
        <div class="personas-delete-section">
          <select id="personas-delete-profile">
            ${profiles.map((p) => `<option value="${_escapePersonasHtml(p)}">${_escapePersonasHtml(p)}</option>`).join("")}
          </select>
          <select id="personas-delete-model">
            <option value="">Tous les modeles</option>
          </select>
          <button class="btn btn-ghost" id="personas-delete-profile-btn" style="color:var(--error)">Supprimer</button>
        </div>
      </div>`;
  }

  container.innerHTML = html;

  // Populate model dropdown when profile changes
  const profileSelect = document.getElementById("personas-delete-profile");
  const modelSelect = document.getElementById("personas-delete-model");
  if (profileSelect && modelSelect) {
    const loadModels = async () => {
      const profile = profileSelect.value;
      try {
        const data = await API.get(`/personas/${encodeURIComponent(profile)}/models`);
        modelSelect.innerHTML =
          '<option value="">Tous les modeles</option>' +
          data.models
            .map((m) => `<option value="${_escapePersonasHtml(m)}">${_escapePersonasHtml(m)}</option>`)
            .join("");
      } catch {
        modelSelect.innerHTML = '<option value="">Tous les modeles</option>';
      }
    };
    profileSelect.addEventListener("change", loadModels);
    loadModels();
  }

  // Delete handler
  const delBtn = document.getElementById("personas-delete-profile-btn");
  if (delBtn) {
    delBtn.addEventListener("click", async () => {
      const profile = document.getElementById("personas-delete-profile").value;
      const model = document.getElementById("personas-delete-model").value;
      const label = model
        ? `les personas du profil "${profile}" generes par "${model}"`
        : `tous les ${stats.by_profile[profile] || 0} personas du profil "${profile}"`;
      const ok = await showConfirm(`Supprimer ${label} ?`);
      if (!ok) return;
      try {
        const url = model
          ? `/personas/${encodeURIComponent(profile)}/model/${encodeURIComponent(model)}`
          : `/personas/${encodeURIComponent(profile)}`;
        const res = await API.del(url);
        showAlert(`${res.deleted} persona(s) supprime(s).`);
        _loadPersonasTab();
      } catch (err) {
        showAlert("Erreur : " + err.message);
      }
    });
  }
}

// ── List tab ──

async function _renderPersonasList(container) {
  // Load profiles for filter
  let profileOptions = '<option value="">Tous les profils</option>';
  try {
    const stats = await API.get("/personas/stats");
    for (const p of Object.keys(stats.by_profile)) {
      const sel = p === _personasListProfile ? "selected" : "";
      profileOptions += `<option value="${_escapePersonasHtml(p)}" ${sel}>${_escapePersonasHtml(p)}</option>`;
    }
  } catch { /* ignore */ }

  const offset = _personasListPage * _PERSONAS_PAGE_SIZE;
  const profileParam = _personasListProfile ? `&profile=${encodeURIComponent(_personasListProfile)}` : "";
  const data = await API.get(`/personas?offset=${offset}&limit=${_PERSONAS_PAGE_SIZE}${profileParam}`);

  let html = `
    <div class="personas-filter">
      <label>Profil :</label>
      <select id="personas-list-profile-filter">${profileOptions}</select>
    </div>`;

  if (data.personas.length === 0) {
    html += '<div class="empty-state">Aucun persona trouve.</div>';
    container.innerHTML = html;
    document.getElementById("personas-list-profile-filter").addEventListener("change", (e) => {
      _personasListProfile = e.target.value;
      _personasListPage = 0;
      _loadPersonasTab();
    });
    return;
  }

  html += '<div class="personas-table-wrap"><table class="personas-table">';
  html += `<thead><tr>
    <th>Nom</th>
    <th>Profil</th>
    <th>Attributs</th>
    <th>Modele</th>
    <th>Date</th>
  </tr></thead><tbody>`;

  for (const p of data.personas) {
    const attrs = Object.entries(p.attributes || {})
      .map(([k, v]) => `<span class="personas-attr-chip">${_escapePersonasHtml(k)}: ${_escapePersonasHtml(v)}</span>`)
      .join(" ");
    const date = p.created_at ? new Date(p.created_at).toLocaleDateString("fr-FR") : "-";
    html += `<tr class="expandable" data-persona-id="${_escapePersonasHtml(p.id)}">
      <td>${_escapePersonasHtml(p.name)}</td>
      <td>${_escapePersonasHtml(p.profile_name)}</td>
      <td>${attrs}</td>
      <td>${_escapePersonasHtml(p.model || "-")}</td>
      <td>${date}</td>
    </tr>
    <tr class="personas-detail-row" data-detail-for="${_escapePersonasHtml(p.id)}" style="display:none">
      <td colspan="5">
        <div class="personas-detail-content">
          <div>
            <div class="personas-detail-label">Background</div>
            <div class="personas-detail-text">${_escapePersonasHtml(p.background || "-")}</div>
          </div>
          <div>
            <div class="personas-detail-label">System Prompt</div>
            <div class="personas-detail-text">${_escapePersonasHtml(p.system_prompt || "-")}</div>
          </div>
        </div>
      </td>
    </tr>`;
  }
  html += "</tbody></table></div>";

  // Pagination
  const totalPages = Math.ceil(data.total / _PERSONAS_PAGE_SIZE);
  html += `<div class="personas-pagination">
    <button id="personas-prev" ${_personasListPage === 0 ? "disabled" : ""}>&#8592; Precedent</button>
    <span>Page ${_personasListPage + 1} / ${totalPages}</span>
    <button id="personas-next" ${_personasListPage + 1 >= totalPages ? "disabled" : ""}>Suivant &#8594;</button>
  </div>`;

  container.innerHTML = html;

  // Expand/collapse rows
  container.querySelectorAll("tr.expandable").forEach((row) => {
    row.addEventListener("click", () => {
      const id = row.dataset.personaId;
      const detail = container.querySelector(`tr[data-detail-for="${id}"]`);
      if (detail) {
        detail.style.display = detail.style.display === "none" ? "" : "none";
      }
    });
  });

  // Filter
  document.getElementById("personas-list-profile-filter").addEventListener("change", (e) => {
    _personasListProfile = e.target.value;
    _personasListPage = 0;
    _loadPersonasTab();
  });

  // Pagination
  document.getElementById("personas-prev").addEventListener("click", () => {
    if (_personasListPage > 0) { _personasListPage--; _loadPersonasTab(); }
  });
  document.getElementById("personas-next").addEventListener("click", () => {
    if (_personasListPage + 1 < totalPages) { _personasListPage++; _loadPersonasTab(); }
  });
}

// ── Distributions tab ──

async function _renderPersonasDistributions(container) {
  // Load profiles
  const stats = await API.get("/personas/stats");
  const profiles = Object.keys(stats.by_profile);

  if (profiles.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucun persona genere. Generez des personas pour voir les distributions.</div>';
    return;
  }

  if (!_personasDistProfile || !profiles.includes(_personasDistProfile)) {
    _personasDistProfile = profiles[0];
  }

  let html = `
    <div class="personas-filter">
      <label>Profil :</label>
      <select id="personas-dist-profile-filter">
        ${profiles.map((p) => `<option value="${_escapePersonasHtml(p)}" ${p === _personasDistProfile ? "selected" : ""}>${_escapePersonasHtml(p)}</option>`).join("")}
      </select>
      <span style="color:var(--text-muted);font-size:13px">${stats.by_profile[_personasDistProfile] || 0} personas</span>
    </div>
    <div id="personas-dist-content"><div class="loading-bar"></div></div>`;

  container.innerHTML = html;

  document.getElementById("personas-dist-profile-filter").addEventListener("change", (e) => {
    _personasDistProfile = e.target.value;
    _loadPersonasTab();
  });

  // Load distribution data
  const dist = await API.get(`/personas/distribution/${encodeURIComponent(_personasDistProfile)}`);
  const distContainer = document.getElementById("personas-dist-content");

  if (Object.keys(dist.actual).length === 0) {
    distContainer.innerHTML = '<div class="empty-state">Aucune donnee de distribution.</div>';
    return;
  }

  let distHtml = "";
  for (const [dim, values] of Object.entries(dist.actual)) {
    const total = Object.values(values).reduce((a, b) => a + b, 0);
    const theoretical = dist.theoretical[dim] || {};

    distHtml += `<div class="personas-dist-section">
      <div class="personas-dist-title">${_escapePersonasHtml(dim)}</div>`;

    // Sort values by count descending
    const sorted = Object.entries(values).sort((a, b) => b[1] - a[1]);

    for (const [val, count] of sorted) {
      const pct = total > 0 ? (count / total * 100) : 0;
      const expectedPct = theoretical[val] ? (theoretical[val] * 100) : null;
      const expectedMarker = expectedPct !== null
        ? `<div class="personas-dist-expected" style="left:${Math.min(expectedPct, 100)}%" title="Attendu: ${expectedPct.toFixed(1)}%"></div>`
        : "";
      const expectedText = expectedPct !== null ? ` (att. ${expectedPct.toFixed(0)}%)` : "";

      distHtml += `<div class="personas-dist-bar-row">
        <div class="personas-dist-label" title="${_escapePersonasHtml(val)}">${_escapePersonasHtml(val)}</div>
        <div class="personas-dist-bar-track">
          <div class="personas-dist-bar" style="width:${pct.toFixed(1)}%"></div>
          ${expectedMarker}
        </div>
        <div class="personas-dist-value">${pct.toFixed(1)}%${expectedText}</div>
      </div>`;
    }

    distHtml += "</div>";
  }

  distContainer.innerHTML = distHtml;
}

// ── Profiles tab ──

let _profilesExpandedMap = {};

async function _renderPersonasProfiles(container) {
  const profilesRes = await API.get("/profiles/");
  const profiles = profilesRes.profiles || [];

  if (profiles.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucun profil de population defini.</div>';
    return;
  }

  // Also load persona counts per profile
  let counts = {};
  try {
    const stats = await API.get("/personas/stats");
    counts = stats.by_profile || {};
  } catch { /* ignore */ }

  // Load theoretical weights for all profiles in parallel
  const weightResults = await Promise.all(
    profiles.map((p) =>
      API.get(`/personas/distribution/${encodeURIComponent(p.name)}`)
        .then((d) => ({ name: p.name, theoretical: d.theoretical }))
        .catch(() => ({ name: p.name, theoretical: {} }))
    )
  );
  const weightsByProfile = {};
  for (const w of weightResults) {
    weightsByProfile[w.name] = w.theoretical;
  }

  let html = "";
  for (const profile of profiles) {
    const personaCount = counts[profile.name] || 0;
    const dims = profile.dimensions || {};
    const dimCount = Object.keys(dims).length;
    const totalValues = Object.values(dims).reduce((sum, arr) => sum + arr.length, 0);
    const isExpanded = _profilesExpandedMap[profile.name] || false;
    const theoretical = weightsByProfile[profile.name] || {};

    html += `<div class="profile-card">
      <div class="profile-card-header" data-profile="${_escapePersonasHtml(profile.name)}">
        <div class="profile-card-header-left">
          <span class="profile-card-toggle">${isExpanded ? "&#9660;" : "&#9654;"}</span>
          <span class="profile-card-name">${_escapePersonasHtml(profile.name)}</span>
          <span class="profile-card-badge">${dimCount} dimensions</span>
          <span class="profile-card-badge">${totalValues} valeurs</span>
          ${personaCount > 0 ? `<span class="profile-card-badge profile-card-badge-accent">${personaCount} personas</span>` : ""}
        </div>
      </div>
      <div class="profile-card-desc">${_escapePersonasHtml(profile.description)}</div>
      ${profile.context ? `<div class="profile-card-context"><span class="profile-card-context-label">Contexte :</span> ${_escapePersonasHtml(profile.context)}</div>` : ""}
      ${profile.sources && profile.sources.length > 0 ? `<div class="profile-card-sources"><span class="profile-card-sources-label">Sources :</span> ${profile.sources.map((s) => `<span class="profile-card-source-chip">${_escapePersonasHtml(s)}</span>`).join(" ")}</div>` : ""}
      <div class="profile-card-body" style="${isExpanded ? "" : "display:none"}" data-body="${_escapePersonasHtml(profile.name)}">`;

    // Show each dimension with values and weights
    for (const [dim, values] of Object.entries(dims)) {
      const dimWeights = theoretical[dim] || {};
      const hasWeights = Object.keys(dimWeights).length > 0;

      html += `<div class="profile-dim">
        <div class="profile-dim-title">${_escapePersonasHtml(dim)} <span class="profile-dim-count">(${values.length})</span></div>
        <div class="profile-dim-values">`;

      for (const val of values) {
        const weight = dimWeights[val];
        const weightText = hasWeights && weight != null ? `<span class="profile-dim-weight">${(weight * 100).toFixed(1)}%</span>` : "";
        html += `<div class="profile-dim-value-row">
          <span class="profile-dim-value">${_escapePersonasHtml(val)}</span>
          ${weightText}
        </div>`;
      }

      html += `</div></div>`;
    }

    html += `</div></div>`;
  }

  container.innerHTML = html;

  // Toggle expand/collapse
  container.querySelectorAll(".profile-card-header").forEach((header) => {
    header.addEventListener("click", () => {
      const name = header.dataset.profile;
      _profilesExpandedMap[name] = !_profilesExpandedMap[name];
      const body = container.querySelector(`[data-body="${name}"]`);
      const toggle = header.querySelector(".profile-card-toggle");
      if (body) {
        body.style.display = _profilesExpandedMap[name] ? "" : "none";
      }
      if (toggle) {
        toggle.innerHTML = _profilesExpandedMap[name] ? "&#9660;" : "&#9654;";
      }
    });
  });
}

// ── Generate modal ──

async function _showGenerateModal() {
  const profilesRes = await API.get("/profiles/");

  const profiles = profilesRes.profiles || [];
  if (profiles.length === 0) {
    showAlert("Aucun profil de population disponible.");
    return;
  }

  const overlay = document.createElement("div");
  overlay.className = "personas-modal-overlay";

  let profilesHtml = profiles.map((p, i) => `
    <div class="vote-profile-option">
      <label>
        <input type="radio" name="gen-profile" value="${_escapePersonasHtml(p.name)}" ${i === 0 ? "checked" : ""}>
        <span class="vote-profile-name">${_escapePersonasHtml(p.name)}</span>
        <span class="vote-profile-desc">${_escapePersonasHtml(p.description)}</span>
      </label>
    </div>`).join("");

  overlay.innerHTML = `
    <div class="personas-modal">
      <div class="personas-modal-title">Generer des personas</div>

      <div class="form-section">
        <label class="form-label">Profil de population</label>
        <div class="vote-profile-list">${profilesHtml}</div>
      </div>

      <div class="form-section">
        <label class="form-label">Nombre de personas : <strong id="gen-count-display">20</strong></label>
        <input type="range" id="gen-count" min="1" max="100" value="20" class="vote-slider" style="width:100%">
      </div>

      <div class="form-hint" style="margin-top:4px">Les modeles LLM sont configures dans Parametres &gt; Vote synthetique.</div>

      <div class="personas-modal-actions">
        <button class="btn btn-ghost" id="gen-cancel">Annuler</button>
        <button class="btn btn-primary" id="gen-submit">Generer</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  // Slider display
  const slider = overlay.querySelector("#gen-count");
  const display = overlay.querySelector("#gen-count-display");
  slider.addEventListener("input", () => { display.textContent = slider.value; });

  // Cancel
  overlay.querySelector("#gen-cancel").addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });

  // Submit
  overlay.querySelector("#gen-submit").addEventListener("click", async () => {
    const profile = overlay.querySelector('input[name="gen-profile"]:checked')?.value;
    if (!profile) { showAlert("Selectionnez un profil."); return; }

    const count = parseInt(slider.value, 10);
    const actionsEl = overlay.querySelector(".personas-modal-actions");
    actionsEl.innerHTML = `
      <div class="progress-container">
        <div class="progress-label" id="gen-progress-label">0/${count} personas generees</div>
        <div class="progress-bar-track"><div class="progress-bar-fill" id="gen-progress-fill"></div></div>
      </div>
      <button class="btn btn-ghost btn-stop" id="gen-stop">Stop</button>`;

    const progressLabel = overlay.querySelector("#gen-progress-label");
    const progressFill = overlay.querySelector("#gen-progress-fill");
    let lastResult = null;
    let generated = 0;

    const { promise, cancel } = API.stream(
      "/personas/generate/stream",
      { profile_name: profile, count },
      (event) => {
        if (event.type === "progress") {
          generated = event.current;
          progressLabel.textContent = `${event.current}/${event.total} personas generees`;
          progressFill.style.width = (event.current / event.total * 100).toFixed(0) + "%";
        } else if (event.type === "done") {
          lastResult = event;
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }
    );

    let stopped = false;
    overlay.querySelector("#gen-stop").addEventListener("click", () => {
      stopped = true;
      cancel();
    });

    try {
      await promise;
      overlay.remove();
      if (lastResult) {
        showAlert(`${lastResult.generated} persona(s) genere(s) pour "${profile}" avec ${lastResult.model}.`);
      }
      _loadPersonasTab();
    } catch (err) {
      if (stopped) {
        overlay.remove();
        showAlert(`Interrompu — ${generated} persona(s) genere(s).`);
        _loadPersonasTab();
      } else {
        actionsEl.innerHTML = `
          <button class="btn btn-ghost" id="gen-cancel-retry">Fermer</button>`;
        overlay.querySelector("#gen-cancel-retry").addEventListener("click", () => overlay.remove());
        showAlert("Erreur : " + err.message);
      }
    }
  });
}

// ── Utils ──

function _escapePersonasHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
