/**
 * Vote view — synthetic population voting.
 */

const DEFAULT_PROFILE_ICON = "🗳️";

function _escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function _renderMarkdown(md) {
  let html = _escapeHtml(md);
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="code-block">${code}</pre>`;
  });
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';
  return html;
}

async function renderVote() {
  const app = document.getElementById("app");

  app.innerHTML = `
    <div class="vote-simple-container">
      <div class="vote-simple-hero">
        <div class="vote-simple-logo">🗳️</div>
        <h1 class="vote-simple-title">VoxPopulAI</h1>
        <p class="vote-simple-subtitle">Simulateur de vote par population synthetique</p>
      </div>
      
      <div class="vote-simple-form">
        <div class="vote-simple-question">
          <textarea 
            class="vote-simple-input" 
            id="vf-topic" 
            rows="3" 
            placeholder="Posez votre question ici..."
            autofocus
          ></textarea>
        </div>
        
        <div class="vote-simple-options">
          <div class="vote-simple-field">
            <label class="vote-simple-label">Population</label>
            <select class="vote-simple-select" id="vf-profile">
              <option value="">Chargement...</option>
            </select>
          </div>
          
          <div class="vote-simple-field vote-simple-voters">
            <label class="vote-simple-label">Votants</label>
            <div class="vote-simple-voters-control">
              <input type="range" class="vote-simple-slider" id="vf-voters" min="5" max="100" value="20" step="1">
              <span class="vote-simple-voters-value" id="vf-voters-val">20</span>
            </div>
          </div>
        </div>
        
        <div class="vote-simple-advanced" id="vf-advanced">
          <label class="vote-simple-checkbox">
            <input type="checkbox" id="vf-reuse">
            <span>Reutiliser les personas existants</span>
          </label>
          <div class="vote-simple-disclaimer">
            ⚠️ SIMULATION — Les votes proviennent de personas generes par IA
          </div>
        </div>
        
        <button class="vote-simple-btn" id="vf-run">
          <span>Lancer le vote</span>
        </button>
      </div>
      
      <div id="vote-result"></div>
    </div>
  `;

  // Load profiles
  API.get("/profiles/").then(resp => {
    const profiles = resp.profiles || [];
    const select = document.getElementById("vf-profile");
    if (!profiles.length) {
      select.innerHTML = '<option value="">Aucun profil</option>';
      return;
    }
    select.innerHTML = profiles.map((p, i) => `
      <option value="${_escapeHtml(p.name)}" ${i === 0 ? "selected" : ""}>
        ${_escapeHtml(p.icon || DEFAULT_PROFILE_ICON)} ${_escapeHtml(p.name)}
      </option>
    `).join("");
  }).catch(() => {
    document.getElementById("vf-profile").innerHTML = '<option value="">Erreur</option>';
  });

  // Slider live value
  document.getElementById("vf-voters").addEventListener("input", (e) => {
    document.getElementById("vf-voters-val").textContent = e.target.value;
  });

  // Run vote
  document.getElementById("vf-run").addEventListener("click", async () => {
    const profileSelect = document.getElementById("vf-profile");
    if (!profileSelect.value) { showAlert("Selectionnez un profil."); return; }
    const topic = document.getElementById("vf-topic").value.trim();
    if (!topic) { showAlert("Entrez une question."); return; }
    const data = {
      question: topic,
      population_profile: profileSelect.value,
      num_voters: parseInt(document.getElementById("vf-voters").value),
      reuse_personas: document.getElementById("vf-reuse").checked,
    };
    await _runVote(data);
  });
}

async function _runVote(data) {
  const resultEl = document.getElementById("vote-result");
  const formEl = document.querySelector(".vote-simple-form");
  
  // Cache le formulaire et montre la progression
  formEl.style.display = "none";
  resultEl.innerHTML = `
    <div class="vote-simple-progress">
      <div class="vote-simple-progress-label" id="vote-progress-label">Preparation...</div>
      <div class="vote-simple-progress-bar">
        <div class="vote-simple-progress-fill" id="vote-progress-bar"></div>
      </div>
      <div class="vote-simple-progress-phase" id="vote-progress-phase"></div>
      <button class="btn btn-ghost btn-stop" id="vote-stop">Annuler</button>
    </div>
  `;

  const bar = document.getElementById("vote-progress-bar");
  const label = document.getElementById("vote-progress-label");
  const phase = document.getElementById("vote-progress-phase");
  let lastProgress = null;

  const { promise, cancel } = API.stream("/vote/stream", data, (event) => {
    if (event.type === "progress") {
      lastProgress = event;
      if (event.phase === "personas") {
        const pct = Math.round((event.current / event.total) * 40);
        bar.style.width = pct + "%";
        label.textContent = `Generation des personas — ${event.current}/${event.total}`;
        phase.textContent = "Phase 1/3";
      } else if (event.phase === "votes") {
        const pct = 40 + Math.round((event.current / event.total) * 50);
        bar.style.width = pct + "%";
        label.textContent = `Votes — ${event.current}/${event.total}`;
        phase.textContent = "Phase 2/3";
      } else if (event.phase === "analysis") {
        bar.style.width = "92%";
        label.textContent = "Analyse en cours...";
        phase.textContent = "Phase 3/3";
      }
    } else if (event.type === "done") {
      bar.style.width = "100%";
      label.textContent = "Termine !";
      phase.textContent = "";
      setTimeout(() => _renderVoteResult(event.result), 400);
    } else if (event.type === "error") {
      resultEl.innerHTML = `<div class="vote-simple-error">Erreur : ${_escapeHtml(event.message)}</div>`;
      formEl.style.display = "block";
    }
  });

  let stopped = false;
  document.getElementById("vote-stop").addEventListener("click", () => {
    stopped = true;
    cancel();
  });

  try {
    await promise;
  } catch (err) {
    if (stopped) {
      const info = lastProgress
        ? `Interrompu — ${lastProgress.phase} : ${lastProgress.current}/${lastProgress.total}`
        : "Interrompu";
      resultEl.innerHTML = `<div class="vote-simple-error">${_escapeHtml(info)}</div>`;
    } else {
      resultEl.innerHTML = `<div class="vote-simple-error">Erreur : ${_escapeHtml(err.message)}</div>`;
    }
    formEl.style.display = "block";
  }
}

function _buildCrossTabs(votes) {
  const tabs = {};
  for (const v of votes) {
    const attrs = v.persona?.attributes || {};
    const pos = v.position;
    for (const [dim, val] of Object.entries(attrs)) {
      if (!tabs[dim]) tabs[dim] = {};
      if (!tabs[dim][val]) tabs[dim][val] = {oui: 0, non: 0, abstention: 0, total: 0};
      tabs[dim][val][pos] = (tabs[dim][val][pos] || 0) + 1;
      tabs[dim][val].total += 1;
    }
  }
  tabs["modele"] = {};
  for (const v of votes) {
    const model = v.persona?.model || "?";
    if (!tabs["modele"][model]) tabs["modele"][model] = {oui: 0, non: 0, abstention: 0, total: 0};
    tabs["modele"][model][v.position] = (tabs["modele"][model][v.position] || 0) + 1;
    tabs["modele"][model].total += 1;
  }
  return tabs;
}

function _renderCrossTabs(crossTabs) {
  let html = "";
  for (const [dim, values] of Object.entries(crossTabs)) {
    const rows = Object.entries(values)
      .sort((a, b) => b[1].total - a[1].total)
      .map(([val, counts]) => {
        const t = counts.total || 1;
        const oP = (counts.oui / t * 100);
        const aP = (counts.abstention / t * 100);
        const nP = (counts.non / t * 100);
        return `<div class="vote-crosstab-row">
          <span class="vote-crosstab-label" title="${_escapeHtml(val)}">${_escapeHtml(val)}</span>
          <div class="vote-stacked-bar vote-crosstab-bar">
            <div class="vote-stacked-segment vote-bar-oui" style="width:${oP}%" title="Oui: ${counts.oui}"></div>
            <div class="vote-stacked-segment vote-bar-abstention" style="width:${aP}%" title="Abstention: ${counts.abstention}"></div>
            <div class="vote-stacked-segment vote-bar-non" style="width:${nP}%" title="Non: ${counts.non}"></div>
          </div>
          <span class="vote-crosstab-value">${counts.oui}/${t}</span>
        </div>`;
      }).join("");
    html += `<div class="vote-crosstab-dim">
      <div class="vote-crosstab-dim-title">${_escapeHtml(dim)}</div>
      ${rows}
    </div>`;
  }
  return html;
}

function _renderVoteResult(result) {
  const el = document.getElementById("vote-result");
  const tally = result.tally || {};
  const analysis = result.analysis || {};
  const votes = result.votes || [];

  const posColor = (pos) => pos === "oui" ? "vote-oui" : pos === "non" ? "vote-non" : "vote-abstention";
  const posEmoji = (pos) => pos === "oui" ? "✅" : pos === "non" ? "❌" : "➖";

  const consensusLabels = { fort: "Consensus fort", modere: "Consensus modere", faible: "Consensus faible", aucun: "Pas de consensus" };

  const keyArgs = analysis.key_arguments || {};
  const argsHtml = (keyArgs.oui || keyArgs.non) ? `
    <div class="vote-arguments">
      <div class="vote-section-header">Arguments cles</div>
      <div class="vote-arguments-cols">
        <div class="vote-arguments-col">
          <div class="vote-arguments-col-title vote-oui">✅ Oui</div>
          <ul>${(keyArgs.oui || []).map(a => `<li>${_escapeHtml(a)}</li>`).join("")}</ul>
        </div>
        <div class="vote-arguments-col">
          <div class="vote-arguments-col-title vote-non">❌ Non</div>
          <ul>${(keyArgs.non || []).map(a => `<li>${_escapeHtml(a)}</li>`).join("")}</ul>
        </div>
      </div>
    </div>
  ` : "";

  const patterns = analysis.demographic_patterns || [];
  const patternsHtml = patterns.length ? `
    <div class="vote-patterns">
      <div class="vote-section-header">Tendances demographiques</div>
      <ul>${patterns.map(p => `<li>${_escapeHtml(p)}</li>`).join("")}</ul>
    </div>
  ` : "";

  const detailRows = votes.map(v => {
    const p = v.persona || {};
    const attrs = p.attributes || {};
    const attrStr = Object.entries(attrs).map(([k, val]) => `${_escapeHtml(k)}: ${_escapeHtml(val)}`).join(", ");
    return `<tr>
      <td>${_escapeHtml(p.name || "—")}</td>
      <td class="vote-detail-attrs">${attrStr}</td>
      <td><span class="tag ${posColor(v.position)}">${_escapeHtml(v.position)}</span></td>
      <td>${_escapeHtml(v.reasoning || "")}</td>
    </tr>`;
  }).join("");

  const total = (tally.oui || 0) + (tally.non || 0) + (tally.abstention || 0);
  const ouiPct = total > 0 ? ((tally.oui || 0) / total * 100) : 0;
  const nonPct = total > 0 ? ((tally.non || 0) / total * 100) : 0;
  const abstPct = total > 0 ? ((tally.abstention || 0) / total * 100) : 0;

  const dominant = analysis.dominant_position || "indecis";
  const marginPct = analysis.margin != null ? (analysis.margin * 100).toFixed(0) : "0";
  const consensusLevel = analysis.consensus_level || "aucun";

  el.innerHTML = `<div class="vote-result card">
    <div class="vote-simple-back">
      <button class="btn btn-ghost" onclick="renderVote()">← Nouveau vote</button>
    </div>
    
    <div class="card-header">
      <span class="card-title">Resultats du vote</span>
      <span class="tag">${result.total_voters || votes.length} votants</span>
      <span class="tag muted">${_escapeHtml(result.population_profile || "")}</span>
    </div>

    <div class="vote-disclaimer">⚠️ ${_escapeHtml(result.disclaimer || "")}</div>

    <div class="vote-hero">
      <div class="vote-hero-verdict ${posColor(dominant)}">
        <span class="vote-hero-icon">${posEmoji(dominant)}</span>
        <span class="vote-hero-position">${_escapeHtml(dominant === "indecis" ? "Indecis" : dominant.charAt(0).toUpperCase() + dominant.slice(1))}</span>
        <span class="vote-hero-margin">${marginPct}% d'ecart</span>
      </div>
      <div class="vote-hero-consensus vote-consensus-${consensusLevel}">${_escapeHtml(consensusLabels[consensusLevel] || consensusLevel)}</div>
    </div>

    <div class="vote-tally">
      <div class="vote-stacked-bar">
        <div class="vote-stacked-segment vote-bar-oui" style="width:${ouiPct}%" title="Oui: ${ouiPct.toFixed(1)}%">
          ${ouiPct >= 10 ? `<span class="vote-stacked-label">${ouiPct.toFixed(0)}%</span>` : ""}
        </div>
        <div class="vote-stacked-segment vote-bar-abstention" style="width:${abstPct}%" title="Abstention: ${abstPct.toFixed(1)}%">
          ${abstPct >= 10 ? `<span class="vote-stacked-label">${abstPct.toFixed(0)}%</span>` : ""}
        </div>
        <div class="vote-stacked-segment vote-bar-non" style="width:${nonPct}%" title="Non: ${nonPct.toFixed(1)}%">
          ${nonPct >= 10 ? `<span class="vote-stacked-label">${nonPct.toFixed(0)}%</span>` : ""}
        </div>
      </div>
      <div class="vote-tally-legend">
        <span class="vote-tally-legend-item"><span class="vote-tally-dot vote-bar-oui"></span> Oui ${tally.oui || 0}</span>
        <span class="vote-tally-legend-item"><span class="vote-tally-dot vote-bar-abstention"></span> Abstention ${tally.abstention || 0}</span>
        <span class="vote-tally-legend-item"><span class="vote-tally-dot vote-bar-non"></span> Non ${tally.non || 0}</span>
      </div>

      <div class="vote-tally-bars">
        <div class="vote-tally-row">
          <span class="vote-tally-label vote-oui">Oui</span>
          <div class="vote-tally-bar-track"><div class="vote-tally-bar vote-bar-oui" style="width:${tally.oui_pct || 0}%"></div></div>
          <span class="vote-tally-value">${tally.oui_pct || 0}% (${tally.oui || 0})</span>
        </div>
        <div class="vote-tally-row">
          <span class="vote-tally-label vote-non">Non</span>
          <div class="vote-tally-bar-track"><div class="vote-tally-bar vote-bar-non" style="width:${tally.non_pct || 0}%"></div></div>
          <span class="vote-tally-value">${tally.non_pct || 0}% (${tally.non || 0})</span>
        </div>
        <div class="vote-tally-row">
          <span class="vote-tally-label vote-abstention">Abstention</span>
          <div class="vote-tally-bar-track"><div class="vote-tally-bar vote-bar-abstention" style="width:${tally.abstention_pct || 0}%"></div></div>
          <span class="vote-tally-value">${tally.abstention_pct || 0}% (${tally.abstention || 0})</span>
        </div>
      </div>
    </div>

    ${argsHtml}
    ${patternsHtml}

    <details class="vote-crosstabs">
      <summary class="vote-detail-toggle">Analyse par attribut</summary>
      ${_renderCrossTabs(_buildCrossTabs(votes))}
    </details>

    <details class="vote-detail">
      <summary class="vote-detail-toggle">Detail des votes (${votes.length})</summary>
      <div class="vote-detail-table-wrap">
        <table class="vote-detail-table">
          <thead>
            <tr><th>Persona</th><th>Attributs</th><th>Position</th><th>Raisonnement</th></tr>
          </thead>
          <tbody>${detailRows}</tbody>
        </table>
      </div>
    </details>
  </div>`;
}
