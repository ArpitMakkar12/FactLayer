/* ═══════════════════════════════════════════════════════════
   FactLayer — Clean SPA v2
   ═══════════════════════════════════════════════════════════ */

// Initialize Theme
const isDark = localStorage.getItem("theme") === "dark" || (!("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches);
if (isDark) document.body.classList.add("dark-theme");

document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-theme");
      const isNowDark = document.body.classList.contains("dark-theme");
      localStorage.setItem("theme", isNowDark ? "dark" : "light");
    });
  }
});

const API = "/api/v1";

/* ── Minimal SVG icons ── */
const I = {
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  x: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`,
  bulb: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>`,
  hash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>`,
  layers: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
  shield: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  zap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
};

function ic(name, cls = "") {
  return `<span class="nav-icon ${cls}" style="display:inline-flex;align-items:center">${I[name] || ""}</span>`;
}

/* ── Helpers ── */
const $ = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => [...c.querySelectorAll(s)];
function esc(s) { const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }
function trunc(s, n = 120) { return s && s.length > n ? s.slice(0, n) + "…" : s || ""; }

async function api(path, opts = {}) {
  const r = await fetch(API + path, opts);
  return r.json();
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById("toast-container").append(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; setTimeout(() => el.remove(), 300); }, 3000);
}

/* ── Routing ── */
/* Only 3 user-facing tabs: Upload, Cases (the hero!), and Explore */
const ROUTES = [
  { hash: "#/upload",  label: "Upload",  view: viewUpload },
  { hash: "#/cases",   label: "Cases",   view: viewCases },
  { hash: "#/explore", label: "Explore", view: viewExplore },
];

let _counts = { documents: 0, facts: 0, relations: 0, failures: 0 };

async function refreshCounts() {
  try {
    const s = await api("/stats");
    _counts.documents = s.documents || 0;
    _counts.facts = s.facts || 0;
    _counts.relations = s.relations || 0;
    _counts.failures = s.failures || 0;
    _counts.byType = s.relations_by_type || {};
  } catch (e) { /* offline */ }
}

function buildNav() {
  const nav = document.getElementById("nav");
  nav.innerHTML = ROUTES.map(r => {
    return `<a href="${r.hash}" data-route="${r.hash}">${r.label}</a>`;
  }).join("");
}

async function route() {
  const h = location.hash || "#/cases";
  await refreshCounts();
  buildNav();
  $$("[data-route]").forEach(a => a.classList.toggle("active", a.dataset.route === h));
  const r = ROUTES.find(r => r.hash === h) || ROUTES[1]; // default to Cases
  const app = document.getElementById("app");
  app.style.animation = "none"; app.offsetHeight; app.style.animation = "";
  try {
    app.innerHTML = '<div style="display:flex;align-items:center;gap:10px;padding:48px;color:var(--text-tertiary)"><div class="spinner"></div>Loading…</div>';
    await r.view(app);
  } catch (e) {
    app.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${esc(e.message)}</p></div>`;
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("load", () => { if (!location.hash) location.hash = "#/cases"; route(); });

/* ═══════════════════════ VIEWS ═══════════════════════ */

/* ── UPLOAD ── */
async function viewUpload(app) {
  const data = await api("/documents");
  const docs = data.items || [];

  // Group docs by collection
  const groups = {};
  docs.forEach(d => {
    const col = d.collection || "Ungrouped";
    if (!groups[col]) groups[col] = [];
    groups[col].push(d);
  });
  const collectionNames = Object.keys(groups).sort((a, b) => a === "Ungrouped" ? 1 : b === "Ungrouped" ? -1 : a.localeCompare(b));

  // Unique collection names for datalist
  const existingCols = [...new Set(docs.map(d => d.collection).filter(Boolean))];

  app.innerHTML = `
    <div class="page-header">
      <h1>Upload Documents</h1>
      <p>Add PDF files to your knowledge layer. <br>Group related documents into collections — relations are still computed across all documents.</p>
    </div>

    <div style="display:flex;gap:10px;align-items:end;margin-bottom:12px">
      <div style="flex:1">
        <label style="font-size:12px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:4px">Collection (optional)</label>
        <input type="text" id="collection-input" list="col-list" placeholder="e.g. Delhivery, India Macro…"
          style="width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;outline:none;background:var(--surface);color:var(--text)" />
        <datalist id="col-list">${existingCols.map(c => `<option value="${esc(c)}">`).join("")}</datalist>
      </div>
    </div>

    <div class="dropzone" id="dropzone">
      <div class="dropzone-icon">${I.upload}</div>
      <h3>Drop PDF(s) here or click to browse</h3>
      <p>Duplicate files are detected by SHA-256 hash. <br>Collection tag is applied automatically.</p>
      <input type="file" id="pdf-input" accept="application/pdf" multiple />
    </div>
    <div class="upload-status" id="upload-status"></div>

    <div class="section-head">
      <h2>Documents (${docs.length})</h2>
    </div>
    <div id="doc-list">
      ${docs.length ? collectionNames.map(col => `
        <div style="margin-bottom:16px">
          <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-tertiary);margin-bottom:6px;padding-left:2px">${esc(col)} (${groups[col].length})</div>
          ${groups[col].map(docRow).join("")}
        </div>
      `).join("") : '<div class="empty-state"><h3>No documents yet</h3><p>Upload a PDF to get started.</p></div>'}
    </div>

    <div class="section-head" style="margin-top:32px">
      <h2>Features &amp; Brownie Points</h2>
    </div>
    <div class="brownie-grid">
      <div class="brownie-card">
        <div class="brownie-icon">${I.hash}</div>
        <h4>SHA-256 Dedup</h4>
        <p>Identical files are detected by content hash and reused — no duplicate ingestion.</p>
        <span class="brownie-check">${I.check} Implemented</span>
      </div>
      <div class="brownie-card">
        <div class="brownie-icon">${I.layers}</div>
        <h4>Incremental Ingest</h4>
        <p>Only new facts are linked against existing ones. Re-uploading doesn't recompute the whole layer.</p>
        <span class="brownie-check">${I.check} Implemented</span>
      </div>
      <div class="brownie-card">
        <div class="brownie-icon">${I.shield}</div>
        <h4>Quote Verification</h4>
        <p>Every fact's quote is checked against actual page text. Mismatches become logged failures, not silent errors.</p>
        <span class="brownie-check">${I.check} Implemented</span>
      </div>
    </div>
  `;

  // Upload handlers
  const dz = $("#dropzone");
  const fi = $("#pdf-input");
  dz.addEventListener("dragover", e => { e.preventDefault(); dz.classList.add("drag-over"); });
  dz.addEventListener("dragleave", () => dz.classList.remove("drag-over"));
  dz.addEventListener("drop", e => { e.preventDefault(); dz.classList.remove("drag-over"); if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files); });
  fi.addEventListener("change", () => { if (fi.files.length) uploadFiles(fi.files); });
}

function docRow(d) {
  const st = d.status || "uploaded";
  return `
    <div class="card doc-row">
      <div class="doc-icon-box">${I.file}</div>
      <div class="doc-body">
        <div class="doc-name">${esc(d.filename)} <span class="tag ${st}">${st}</span></div>
        <div class="doc-meta">
          <span>${d.page_count ?? "?"} pages</span>
          <span>${d.fact_count ?? 0} facts</span>
          <span>${d.relation_count ?? 0} relations</span>
        </div>
      </div>
      <div style="display:flex;gap:6px;align-items:center">
        ${["uploaded","parsed","extracted","normalized"].includes(st) ? `<button class="btn btn-primary btn-sm" onclick="ingestDoc('${d.id}')">Ingest</button>` : ""}
        <button class="btn btn-outline btn-sm" onclick="deleteDoc('${d.id}','${esc(d.filename)}')" style="color:var(--red);border-color:var(--red)" title="Delete document">✕</button>
      </div>
    </div>`;
}

async function uploadFiles(files) {
  const status = $("#upload-status");
  status.className = "upload-status show info";
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    status.innerHTML = `<div class="spinner"></div> Uploading ${esc(file.name)} (${i+1}/${files.length})…`;
    try {
      const fd = new FormData(); fd.append("file", file);
      const colInput = $("#collection-input");
      if (colInput && colInput.value.trim()) fd.append("collection", colInput.value.trim());
      
      const r = await fetch(API + "/documents", { method: "POST", body: fd });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error?.message || "Upload failed");
      
      if (d.reused) {
        toast(`Reused: ${esc(file.name)}`);
      } else {
        status.innerHTML = `<div class="spinner"></div> Ingesting ${esc(file.name)} (${i+1}/${files.length})…`;
        await fetch(API + `/documents/${d.id}/ingest`, { method: "POST" });
        toast(`Ingesting: ${esc(file.name)}`);
        pollDoc(d.id);
      }
    } catch (e) {
      toast(`Error on ${esc(file.name)}: ${e.message}`, "error");
    }
  }
  
  status.className = "upload-status show success";
  status.textContent = `All ${files.length} file(s) processed.`;
  setTimeout(() => { if (status.className.includes("success")) status.classList.remove("show"); }, 3000);
  route();
}

async function pollDoc(id) {
  const poll = setInterval(async () => {
    try {
      const d = await api(`/documents/${id}`);
      if (d.status === "ready" || d.status === "failed") {
        clearInterval(poll);
        toast(d.status === "ready" ? "Ingest complete!" : "Ingest failed", d.status === "ready" ? "success" : "error");
        route();
      }
    } catch (e) { clearInterval(poll); }
  }, 1500);
}

function customConfirm(title, message, confirmText = "Delete") {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box">
        <div class="modal-header">
          <h3>${esc(title)}</h3>
        </div>
        <div class="modal-body">
          ${esc(message)}
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" id="modal-cancel">Cancel</button>
          <button class="btn btn-primary" id="modal-confirm" style="background:var(--red);color:#fff">${esc(confirmText)}</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    
    // trigger reflow for animation
    overlay.offsetHeight; 
    overlay.classList.add("show");

    const close = (result) => {
      overlay.classList.remove("show");
      setTimeout(() => overlay.remove(), 250);
      resolve(result);
    };

    overlay.querySelector("#modal-cancel").addEventListener("click", () => close(false));
    overlay.querySelector("#modal-confirm").addEventListener("click", () => close(true));
  });
}

window.deleteDoc = async function(id, name) {
  const isConfirmed = await customConfirm(
    "Delete Document",
    `Are you sure you want to delete "${name}"?\nThis will also remove its facts and relations.`
  );
  if (!isConfirmed) return;
  
  try {
    await fetch(API + `/documents/${id}`, { method: "DELETE" });
    toast("Document deleted");
    route();
  } catch (e) {
    toast("Failed to delete document", "error");
  }
};

window.ingestDoc = async function(id) {
  try {
    await fetch(API + `/documents/${id}/ingest`, { method: "POST" });
    toast("Ingesting…");
    pollDoc(id);
  } catch (e) { toast("Failed", "error"); }
};

/* ── CASES (Hero page — default view) ── */
async function viewCases(app) {
  const [casesData, statsData] = await Promise.all([
    api("/cases"),
    refreshCounts().then(() => _counts),
  ]);
  const cases = casesData.items || [];

  app.innerHTML = `
    <div class="page-header">
      <h1>FactLayer — Knowledge Layer Inspector</h1>
      <p>Upload PDFs → extract grounded facts → compute cross-document relations → inspect evidence. <br>Every claim is backed by a verbatim quote from the source page.</p>
    </div>

    <div class="stats-row">
      <div class="stat-card s-blue">
        <div class="stat-value">${_counts.documents}</div>
        <div class="stat-label">Documents</div>
      </div>
      <div class="stat-card s-green">
        <div class="stat-value">${_counts.facts}</div>
        <div class="stat-label">Grounded Facts</div>
      </div>
      <div class="stat-card s-purple">
        <div class="stat-value">${_counts.relations}</div>
        <div class="stat-label">Relations</div>
      </div>
      <div class="stat-card s-red">
        <div class="stat-value">${_counts.failures}</div>
        <div class="stat-label">Failures Logged</div>
      </div>
    </div>

    <h2 style="margin-top:8px;margin-bottom:4px">Four Required Cases</h2>
    <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px">Pinned from live pipeline output. Each demonstrates a distinct judgment behavior — not hardcoded filenames.</p>

    <div id="case-list">${cases.map(caseCard).join("")}</div>
  `;
}

function caseCard(c) {
  const n = c.slot;
  const rel = c.relation;
  const fail = c.failure;

  let body = "";
  if (rel) {
    const fa = rel.fact_a || {};
    const fb = rel.fact_b || {};
    body = `
      <div class="rel-top">
        <span class="tag ${rel.type}">${rel.type}</span>
        ${rel.axis ? `<span class="tag ${rel.axis}">axis: ${rel.axis}</span>` : ""}
      </div>
      <div class="rel-reason">${esc(rel.explanation)}</div>
      <div class="compare-grid">
        <div class="compare-side">
          <div class="quote-block">${esc(fa.quote || "—")}</div>
          <div class="quote-source">${ic("file")} p.${fa.page ?? "?"} · ${esc(fa.document_filename || "Doc A")}</div>
        </div>
        <div class="compare-side">
          <div class="quote-block">${esc(fb.quote || "—")}</div>
          <div class="quote-source">${ic("file")} p.${fb.page ?? "?"} · ${esc(fb.document_filename || "Doc B")}</div>
        </div>
      </div>`;
  } else if (fail) {
    body = failureBody(fail);
  } else {
    body = `<div style="color:var(--text-tertiary);padding:16px;text-align:center">No data pinned yet — ingest PDFs to populate.</div>`;
  }

  return `
    <div class="case-card">
      <div class="case-top">
        <div class="case-num c${n}">${n}</div>
        <div>
          <div class="case-title">${esc(c.title)}</div>
          <div class="case-note">${esc(c.curator_note)}</div>
        </div>
      </div>
      <div class="case-body">${body}</div>
    </div>`;
}

/* ── EXPLORE (Facts + Relations + Failures all in one tab) ── */
async function viewExplore(app) {
  app.innerHTML = `
    <div class="page-header">
      <h1>Explore the Knowledge Layer</h1>
      <p>Browse all extracted facts, cross-document relations, and pipeline failures in one place.</p>
    </div>
    <div class="filter-tabs" id="explore-tabs">
      <button class="filter-tab active" data-tab="facts">Facts</button>
      <button class="filter-tab" data-tab="relations">Relations</button>
      <button class="filter-tab" data-tab="failures">Failures</button>
    </div>
    <div id="explore-content"></div>
  `;

  const tabs = $$("#explore-tabs .filter-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      loadExploreTab(tab.dataset.tab);
    });
  });

  // Load default
  await loadExploreTab("facts");
}

async function loadExploreTab(tab) {
  const el = $("#explore-content");
  el.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:24px;color:var(--text-tertiary)"><div class="spinner"></div>Loading…</div>';

  if (tab === "facts") await renderFacts(el);
  else if (tab === "relations") await renderRelations(el);
  else if (tab === "failures") await renderFailures(el);
}

/* ── Facts sub-view ── */
async function renderFacts(el) {
  const data = await api("/facts?limit=200");
  const facts = data.items || [];

  el.innerHTML = `
    <div class="search-bar">
      <span class="search-icon">${I.search}</span>
      <input type="text" id="fact-search" placeholder="Search facts by statement…" />
    </div>
    <p style="font-size:12px;color:var(--text-tertiary);margin-bottom:12px">${facts.length} grounded facts — each backed by a verified quote on a source page.</p>
    <div class="split-view">
      <div id="fact-list">${facts.map(factItem).join("") || emptyMsg("No facts yet", "Upload and ingest PDFs first.")}</div>
      <div id="fact-detail">
        <div class="card" style="text-align:center;padding:40px 20px;color:var(--text-tertiary)">
          <p>Select a fact to view its evidence and attributes.</p>
        </div>
      </div>
    </div>
  `;

  // Search
  const search = $("#fact-search");
  search.addEventListener("input", () => {
    const q = search.value.toLowerCase();
    $$("#fact-list .card").forEach(card => {
      const f = facts.find(f => f.id === card.dataset.id);
      if (!f) return;
      card.style.display = (!q || (f.statement || "").toLowerCase().includes(q)) ? "" : "none";
    });
  });

  // Click to show detail
  $$("#fact-list .card").forEach(card => {
    card.addEventListener("click", () => {
      $$("#fact-list .card").forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      const f = facts.find(f => f.id === card.dataset.id);
      if (f) showFactDetail(f);
    });
  });
}

function factItem(f) {
  return `
    <div class="card card-clickable fact-item" data-id="${f.id}">
      <div class="fact-stmt">${esc(f.statement)}</div>
      <div class="fact-chips">
        <span class="tag fact">${esc(f.predicate)}</span>
        ${f.period_norm ? `<span class="chip-sep">·</span><span>${esc(f.period_norm)}</span>` : ""}
        ${f.value_num != null ? `<span class="chip-sep">·</span><strong>${f.value_num}</strong>` : ""}
        ${f.unit_norm ? ` ${esc(f.unit_norm)}` : ""}
        <span class="chip-sep">·</span><span>p.${f.page ?? "?"}</span>
        <span class="chip-sep">·</span><span>${(f.confidence * 100).toFixed(0)}%</span>
      </div>
    </div>`;
}

function showFactDetail(f) {
  const detail = $("#fact-detail");
  const extra = f.extra ? (typeof f.extra === "string" ? JSON.parse(f.extra || "{}") : f.extra) : {};
  const extraKeys = Object.keys(extra).filter(k => extra[k]);

  detail.innerHTML = `
    <div class="card">
      <h3 style="font-size:14px;margin-bottom:12px">${esc(f.statement)}</h3>
      <table class="kv-table">
        <tr><td>Subject</td><td>${esc(f.subject)}</td></tr>
        <tr><td>Predicate</td><td><span class="tag fact">${esc(f.predicate)}</span></td></tr>
        <tr><td>Value</td><td>${f.value_num != null ? `<strong>${f.value_num}</strong> ${esc(f.unit_norm || f.unit || "")}` : "—"}</td></tr>
        <tr><td>Raw Object</td><td><code style="font-size:12px">${esc(f.object_raw)}</code></td></tr>
        <tr><td>Period</td><td>${esc(f.period_norm || f.period || "—")}</td></tr>
        <tr><td>Scope</td><td>${esc(f.scope || "—")}</td></tr>
        <tr><td>Confidence</td><td>${(f.confidence * 100).toFixed(0)}%</td></tr>
        ${extraKeys.map(k => `<tr><td>${esc(k)}</td><td>${esc(String(extra[k]))}</td></tr>`).join("")}
      </table>

      <hr class="divider">
      <h3 style="font-size:13px;margin-bottom:4px">📄 Source Evidence</h3>
      <div class="quote-block">${esc(f.quote)}</div>
      <div class="quote-source">
        ${ic("file")} Page ${f.page ?? "?"} · ${esc(f.document_filename || f.document_id?.slice(0, 8) || "?")}
      </div>
    </div>`;
}

/* ── Relations sub-view (paginated) ── */
const REL_PAGE_SIZE = 20;
let _relState = { type: "all", offset: 0, query: "" };

async function renderRelations(el) {
  _relState = { type: "all", offset: 0, query: "" };
  const bt = _counts.byType || {};
  const totalAll = (bt.corroborates || 0) + (bt.contradicts || 0) + (bt.reconciled || 0);

  el.innerHTML = `
    <div class="filter-tabs" id="rel-tabs">
      <button class="filter-tab active" data-type="all">All <span class="tab-count">${totalAll}</span></button>
      <button class="filter-tab" data-type="corroborates">Corroborates <span class="tab-count">${bt.corroborates || 0}</span></button>
      <button class="filter-tab" data-type="contradicts">Contradicts <span class="tab-count">${bt.contradicts || 0}</span></button>
      <button class="filter-tab" data-type="reconciled">Reconciled <span class="tab-count">${bt.reconciled || 0}</span></button>
    </div>
    <div class="search-bar" style="margin-bottom:12px">
      <span class="search-icon">${I.search}</span>
      <input type="text" id="rel-search" placeholder="Search relations by keyword (e.g. revenue, employees, FY2024)…" />
    </div>
    <div id="rel-pager"></div>
    <div id="rel-list"></div>
  `;

  // Type tabs
  $$("#rel-tabs .filter-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      $$("#rel-tabs .filter-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      _relState.type = tab.dataset.type;
      _relState.offset = 0;
      loadRelPage();
    });
  });

  // Search with debounce
  let searchTimer;
  $("#rel-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      _relState.query = e.target.value.trim();
      _relState.offset = 0;
      loadRelPage();
    }, 400);
  });

  await loadRelPage();
}

async function loadRelPage() {
  const list = $("#rel-list");
  const pager = $("#rel-pager");
  list.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:24px;color:var(--text-tertiary)"><div class="spinner"></div>Loading…</div>';

  const typeParam = _relState.type === "all" ? "" : `&type=${_relState.type}`;
  const qParam = _relState.query ? `&q=${encodeURIComponent(_relState.query)}` : "";
  const data = await api(`/relations?limit=${REL_PAGE_SIZE}&offset=${_relState.offset}${typeParam}${qParam}`);
  const rels = data.items || [];
  const total = data.total || 0;
  const page = Math.floor(_relState.offset / REL_PAGE_SIZE) + 1;
  const totalPages = Math.ceil(total / REL_PAGE_SIZE);

  // Pager
  pager.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;font-size:13px">
      <span style="color:var(--text-tertiary)">${total} relations · Page ${page} of ${totalPages}</span>
      <div style="display:flex;gap:6px">
        <button class="btn btn-outline btn-sm" id="rel-prev" ${_relState.offset <= 0 ? "disabled" : ""}>← Prev</button>
        <button class="btn btn-outline btn-sm" id="rel-next" ${!data.has_more ? "disabled" : ""}>Next →</button>
      </div>
    </div>
  `;

  list.innerHTML = rels.map(relCard).join("") || emptyMsg("No relations", "Upload a second PDF to see cross-document comparisons.");

  // Wire buttons
  const prevBtn = $("#rel-prev");
  const nextBtn = $("#rel-next");
  if (prevBtn) prevBtn.addEventListener("click", () => {
    _relState.offset = Math.max(0, _relState.offset - REL_PAGE_SIZE);
    loadRelPage();
  });
  if (nextBtn) nextBtn.addEventListener("click", () => {
    if (data.has_more) {
      _relState.offset += REL_PAGE_SIZE;
      loadRelPage();
    }
  });
}

function relCard(r) {
  const fa = r.fact_a || {};
  const fb = r.fact_b || {};
  return `
    <div class="card rel-card" data-type="${r.type}">
      <div class="rel-top">
        <span class="tag ${r.type}">${r.type}</span>
        ${r.axis ? `<span class="tag ${r.axis}">axis: ${r.axis}</span>` : ""}
        <span style="margin-left:auto;font-size:12px;color:var(--text-tertiary)">${(r.confidence * 100).toFixed(0)}%</span>
      </div>
      <div class="rel-reason">${esc(r.explanation)}</div>
      <div class="compare-grid">
        <div class="compare-side">
          <div class="quote-block">${esc(fa.quote || "—")}</div>
          <div class="quote-source">${ic("file")} p.${fa.page ?? "?"} · ${esc(fa.document_filename || "Doc A")}</div>
        </div>
        <div class="compare-side">
          <div class="quote-block">${esc(fb.quote || "—")}</div>
          <div class="quote-source">${ic("file")} p.${fb.page ?? "?"} · ${esc(fb.document_filename || "Doc B")}</div>
        </div>
      </div>
    </div>`;
}

/* ── Failures sub-view (paginated) ── */
const FAIL_PAGE_SIZE = 20;
let _failState = { offset: 0, query: "" };

async function renderFailures(el) {
  _failState = { offset: 0, query: "" };

  el.innerHTML = `
    <div class="search-bar" style="margin-bottom:12px">
      <span class="search-icon">${I.search}</span>
      <input type="text" id="fail-search" placeholder="Search failures by note, stage, or payload…" />
    </div>
    <div id="fail-pager"></div>
    <div id="fail-list"></div>
  `;

  // Search with debounce
  let searchTimer;
  $("#fail-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      _failState.query = e.target.value.trim();
      _failState.offset = 0;
      loadFailPage();
    }, 400);
  });

  await loadFailPage();
}

async function loadFailPage() {
  const list = $("#fail-list");
  const pager = $("#fail-pager");
  list.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:24px;color:var(--text-tertiary)"><div class="spinner"></div>Loading…</div>';

  const qParam = _failState.query ? `&q=${encodeURIComponent(_failState.query)}` : "";
  const data = await api(`/failures?limit=${FAIL_PAGE_SIZE}&offset=${_failState.offset}${qParam}`);
  const fails = data.items || [];
  const total = data.total || 0;
  const page = Math.floor(_failState.offset / FAIL_PAGE_SIZE) + 1;
  const totalPages = Math.ceil(total / FAIL_PAGE_SIZE) || 1;

  // Pager
  pager.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;font-size:13px">
      <span style="color:var(--text-tertiary)">${total} failed candidates · Page ${page} of ${totalPages}</span>
      <div style="display:flex;gap:6px">
        <button class="btn btn-outline btn-sm" id="fail-prev" ${_failState.offset <= 0 ? "disabled" : ""}>← Prev</button>
        <button class="btn btn-outline btn-sm" id="fail-next" ${!data.has_more ? "disabled" : ""}>Next →</button>
      </div>
    </div>
  `;

  list.innerHTML = fails.map(f => `<div class="card failure-card">${failureBody(f)}</div>`).join("") || emptyMsg("No failures found", "All candidates passed verification, or no documents ingested yet.");

  // Wire buttons
  const prevBtn = $("#fail-prev");
  const nextBtn = $("#fail-next");
  if (prevBtn) prevBtn.addEventListener("click", () => {
    _failState.offset = Math.max(0, _failState.offset - FAIL_PAGE_SIZE);
    loadFailPage();
  });
  if (nextBtn) nextBtn.addEventListener("click", () => {
    if (data.has_more) {
      _failState.offset += FAIL_PAGE_SIZE;
      loadFailPage();
    }
  });
}

function failureBody(f) {
  let payload = {};
  try { payload = typeof f.payload_json === "string" ? JSON.parse(f.payload_json) : (f.payload_json || {}); } catch (e) { payload = {}; }
  const keys = Object.keys(payload);

  return `
    <div class="failure-header">
      <span class="tag ${f.stage || "verify"}">${esc(f.stage || "verify")}</span>
    </div>
    <div class="failure-note">${esc(f.human_note)}</div>
    ${keys.length ? `
      <div class="failure-detail">
        ${keys.map(k => `<div class="fd-row"><span class="fd-key">${esc(k)}</span><span class="fd-val">${esc(trunc(String(payload[k]), 200))}</span></div>`).join("")}
      </div>` : ""}
    <div class="failure-improve">
      ${I.bulb}
      <span><strong>Improvement:</strong> ${esc(payload.note || "A fuzzy-match fallback for quotes with table-join or hyphenation artifacts would catch these.")}</span>
    </div>`;
}

/* ── Shared ── */
function emptyMsg(title, desc) {
  return `<div class="empty-state"><h3>${title}</h3><p>${desc}</p></div>`;
}
