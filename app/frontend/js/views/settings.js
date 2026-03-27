/**
 * Settings view — application configuration.
 */
async function renderSettings() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page-header">
      <div>
        <div class="page-title">Parametres</div>
        <div class="page-subtitle">Configuration de VoxPopulAI</div>
      </div>
    </div>
    <div id="settings-content"><div class="loading-bar"></div></div>
  `;

  try {
    const [settings, models] = await Promise.all([
      API.get("/settings/"),
      API.get("/models/").catch(() => []),
    ]);

    const synthetic = settings.synthetic || {};
    const ollama = settings.ollama || {};
    const selectedPersonaModels = synthetic.persona_models || [];
    const generationModel = synthetic.generation_model || "";
    const syntheticAnalysisModel = synthetic.analysis_model || "";
    const judgeModel = synthetic.judge_model || "";

    const modelOptions = (selected) => {
      if (models.length > 0) {
        return models.map(m => `<option value="${_escapeHtml(m.name)}" ${m.name === selected ? "selected" : ""}>${_escapeHtml(m.name)}</option>`).join("");
      }
      return `<option value="${_escapeHtml(selected)}" selected>${_escapeHtml(selected)}</option>`;
    };

    const judgeModelOptions = models.length > 0
      ? `<option value="" ${!judgeModel ? "selected" : ""}>Desactive</option>` + models.map(m => `<option value="${_escapeHtml(m.name)}" ${m.name === judgeModel ? "selected" : ""}>${_escapeHtml(m.name)}</option>`).join("")
      : `<option value="" ${!judgeModel ? "selected" : ""}>Desactive</option>` + (judgeModel ? `<option value="${_escapeHtml(judgeModel)}" selected>${_escapeHtml(judgeModel)}</option>` : "");

    document.getElementById("settings-content").innerHTML = `
      <div class="settings-layout">
        <div class="settings-section">
          <div class="settings-section-header">
            <h3>Ollama</h3>
            <p>Parametres runtime Ollama.</p>
          </div>
          <form id="ollama-settings-form" class="settings-form">
            <div class="form-section">
              <label class="form-label">Taille contexte (num_ctx)</label>
              <input type="number" id="ollama_num_ctx" class="form-control"
                     value="${ollama.num_ctx ?? ""}" min="1024" max="131072" step="1024" placeholder="8192">
            </div>
            <div class="form-section">
              <label class="form-label">Couches GPU (num_gpu)</label>
              <input type="number" id="ollama_num_gpu" class="form-control"
                     value="${ollama.num_gpu ?? ""}" min="-1" step="1" placeholder="auto">
            </div>
            <div class="form-section">
              <label class="form-label">Top-K</label>
              <input type="number" id="ollama_top_k" class="form-control"
                     value="${ollama.top_k ?? ""}" min="0" step="1" placeholder="40">
            </div>
            <div class="form-section">
              <label class="form-label">Top-P</label>
              <input type="number" id="ollama_top_p" class="form-control"
                     value="${ollama.top_p ?? ""}" min="0" max="1" step="0.05" placeholder="0.9">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Enregistrer</button>
              <span id="ollama-save-status" class="save-status"></span>
            </div>
          </form>
        </div>

        <div class="settings-section">
          <div class="settings-section-header">
            <h3>Generation de personas</h3>
            <p>Modele et parametres pour la creation des personnages synthetiques.</p>
          </div>
          <form id="generation-settings-form" class="settings-form">
            <div class="form-section">
              <label class="form-label">Modele de generation</label>
              <select id="generation_model" class="form-control">${modelOptions(generationModel)}</select>
            </div>
            <div class="form-section">
              <label class="form-label">Temperature</label>
              <input type="number" id="generation_temperature" class="form-control"
                     value="${synthetic.generation_temperature ?? 0.8}" min="0" max="2" step="0.1">
            </div>
            <div class="form-section">
              <label class="form-label">Modele juge</label>
              <select id="judge_model" class="form-control">${judgeModelOptions}</select>
            </div>
            <div id="judge-options" style="${judgeModel ? "" : "display:none"}">
              <div class="form-section">
                <label class="form-label">Temperature du juge</label>
                <input type="number" id="judge_temperature" class="form-control"
                       value="${synthetic.judge_temperature ?? 0.1}" min="0" max="2" step="0.1">
              </div>
              <div class="form-section">
                <label class="form-label">Re-generations max</label>
                <input type="number" id="judge_max_retries" class="form-control"
                       value="${synthetic.judge_max_retries ?? 2}" min="0" max="5" step="1">
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Enregistrer</button>
              <span id="generation-save-status" class="save-status"></span>
            </div>
          </form>
        </div>

        <div class="settings-section">
          <div class="settings-section-header">
            <h3>Vote synthetique</h3>
            <p>Modeles LLM pour les votes des personas.</p>
          </div>
          <form id="synthetic-settings-form" class="settings-form">
            <div class="form-section">
              <label class="form-label">Modeles pour personas</label>
              <div class="form-hint" style="margin-bottom:8px">Modeles utilises pour voter. Un modele sera choisi au hasard pour chaque persona.</div>
              <div id="synthetic-model-chips" class="synthetic-model-chips">
                ${models.length > 0
                  ? models.map(m => `<div class="tool-chip ${selectedPersonaModels.includes(m.name) ? "selected" : ""}" data-model="${_escapeHtml(m.name)}">
                      <input type="checkbox" class="synthetic-model-cb" value="${_escapeHtml(m.name)}"
                             ${selectedPersonaModels.includes(m.name) ? "checked" : ""} style="display:none">
                      ${_escapeHtml(m.name)}
                    </div>`).join("")
                  : selectedPersonaModels.map(m => `<div class="tool-chip selected" data-model="${_escapeHtml(m)}">
                      <input type="checkbox" class="synthetic-model-cb" value="${_escapeHtml(m)}"
                             checked style="display:none">
                      ${_escapeHtml(m)}
                    </div>`).join("")}
              </div>
            </div>
            <div class="form-section">
              <label class="form-label">Modele d'analyse</label>
              <select id="synthetic_analysis_model" class="form-control">${modelOptions(syntheticAnalysisModel)}</select>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Enregistrer</button>
              <span id="synthetic-save-status" class="save-status"></span>
            </div>
          </form>
        </div>
      </div>
    `;

    // Ollama form handler
    document.getElementById("ollama-settings-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const statusEl = document.getElementById("ollama-save-status");
      const _intOrNull = (id) => { const v = document.getElementById(id).value.trim(); return v === "" ? null : parseInt(v, 10); };
      const _floatOrNull = (id) => { const v = document.getElementById(id).value.trim(); return v === "" ? null : parseFloat(v); };
      const data = {};
      const v = _intOrNull("ollama_num_ctx"); if (v !== null) data.num_ctx = v;
      const g = _intOrNull("ollama_num_gpu"); if (g !== null) data.num_gpu = g;
      const k = _intOrNull("ollama_top_k"); if (k !== null) data.top_k = k;
      const p = _floatOrNull("ollama_top_p"); if (p !== null) data.top_p = p;
      try {
        await API.put("/settings/ollama", data);
        statusEl.className = "save-status success"; statusEl.textContent = "Enregistre !";
        setTimeout(() => { statusEl.textContent = ""; statusEl.className = "save-status"; }, 3000);
      } catch (err) { statusEl.className = "save-status error"; statusEl.textContent = "Erreur: " + err.message; }
    });

    // Judge toggle
    document.getElementById("judge_model").addEventListener("change", (e) => {
      document.getElementById("judge-options").style.display = e.target.value ? "" : "none";
    });

    // Model chips
    document.querySelectorAll("#synthetic-model-chips .tool-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const cb = chip.querySelector("input");
        cb.checked = !cb.checked;
        chip.classList.toggle("selected", cb.checked);
      });
    });

    // Generation form handler
    document.getElementById("generation-settings-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const statusEl = document.getElementById("generation-save-status");
      try {
        await API.put("/settings/synthetic", {
          generation_model: document.getElementById("generation_model").value,
          generation_temperature: parseFloat(document.getElementById("generation_temperature").value),
          judge_model: document.getElementById("judge_model").value,
          judge_temperature: parseFloat(document.getElementById("judge_temperature").value),
          judge_max_retries: parseInt(document.getElementById("judge_max_retries").value),
        });
        statusEl.className = "save-status success"; statusEl.textContent = "Enregistre !";
        setTimeout(() => { statusEl.textContent = ""; statusEl.className = "save-status"; }, 3000);
      } catch (err) { statusEl.className = "save-status error"; statusEl.textContent = "Erreur: " + err.message; }
    });

    // Synthetic form handler
    document.getElementById("synthetic-settings-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const statusEl = document.getElementById("synthetic-save-status");
      const selected = Array.from(document.querySelectorAll(".synthetic-model-cb:checked")).map(cb => cb.value);
      if (selected.length === 0) { statusEl.className = "save-status error"; statusEl.textContent = "Selectionnez au moins un modele."; return; }
      try {
        await API.put("/settings/synthetic", {
          persona_models: selected,
          analysis_model: document.getElementById("synthetic_analysis_model").value,
        });
        statusEl.className = "save-status success"; statusEl.textContent = "Enregistre !";
        setTimeout(() => { statusEl.textContent = ""; statusEl.className = "save-status"; }, 3000);
      } catch (err) { statusEl.className = "save-status error"; statusEl.textContent = "Erreur: " + err.message; }
    });
  } catch (err) {
    document.getElementById("settings-content").innerHTML =
      `<div class="empty-state" style="color:var(--error)">${_escapeHtml(err.message)}</div>`;
  }
}
