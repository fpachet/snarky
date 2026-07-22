const app = document.querySelector("#app");
const searchInput = document.querySelector("#search-input");
const viewButtons = [...document.querySelectorAll("[data-view]")];
const heroStats = document.querySelector("#hero-stats");

let model;
let state = {
  view: "affects",
  selectedId: "E3DA01",
  query: "",
};

const escapeHtml = (value = "") =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const normalize = (value = "") =>
  String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

const statusLabel = (status = "proved") =>
  status
    .replace("proved_with_", "prouvé avec ")
    .replace("proved_", "prouvé — ")
    .replaceAll("_", " ");

const factLabel = (fact) =>
  typeof fact === "string"
    ? fact
    : `${fact.entity ?? ""}${fact.status ? ` [${fact.status}]` : ""}`;

function renderHeroStats() {
  const counts = model.meta.counts;
  const stats = [
    [counts.propositions, "propositions"],
    [counts.definitions, "affects définis"],
    [counts.proposition_cases + counts.definition_cases, "cas exécutés"],
    [counts.catalogued_rules, "règles cataloguées"],
  ];
  heroStats.innerHTML = stats
    .map(
      ([value, label]) => `
        <div class="hero-stat">
          <strong>${value}</strong>
          <span>${escapeHtml(label)}</span>
        </div>`,
    )
    .join("");
}

function unitsForView() {
  if (state.view === "propositions") return model.propositions;
  if (state.view === "affects") {
    return [...model.definitions, model.general_definition];
  }
  return [];
}

function filteredUnits() {
  const query = normalize(state.query.trim());
  if (!query) return unitsForView();
  return unitsForView().filter((unit) => {
    const searchable = [
      unit.id,
      unit.title,
      unit.family,
      unit.source_text,
      ...(unit.sections ?? []).map((section) => section.text),
      ...(unit.current_rules ?? []),
    ].join(" ");
    return normalize(searchable).includes(query);
  });
}

function setActiveViewButton() {
  viewButtons.forEach((button) => {
    const active = button.dataset.view === state.view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function updateHash(view, selectedId) {
  const suffix = selectedId ? `/${selectedId}` : "";
  const target = `#${view}${suffix}`;
  if (window.location.hash !== target) window.location.hash = target;
}

function routeFromHash() {
  const route = window.location.hash.slice(1);
  if (!route || route === "accueil") return;
  const [view, selectedId] = route.split("/");
  if (!["propositions", "affects", "architecture"].includes(view)) return;
  state.view = view;
  if (selectedId) state.selectedId = selectedId;
  if (model) render();
}

function unitListItem(unit) {
  const selected = unit.id === state.selectedId;
  const subtitle = unit.family ?? unit.source_text;
  return `
    <li>
      <button
        type="button"
        class="${selected ? "selected" : ""}"
        data-select-unit="${escapeHtml(unit.id)}"
        aria-current="${selected ? "true" : "false"}"
      >
        <span class="unit-code">${escapeHtml(unit.id)}</span>
        <span>
          <strong>${escapeHtml(unit.title)}</strong>
          <small>${escapeHtml(subtitle)}</small>
        </span>
      </button>
    </li>`;
}

function dependenciesSection(unit) {
  if (!unit.dependencies?.length) return "";
  return `
    <section class="detail-section">
      <div class="section-title-row">
        <h4>Dépendances canoniques</h4>
        <span>${unit.dependencies.length} référence${unit.dependencies.length > 1 ? "s" : ""}</span>
      </div>
      <ul class="dependency-list">
        ${unit.dependencies
          .map((reference) => {
            const propositionId = reference.startsWith("E3P")
              ? reference.slice(0, 5)
              : null;
            return propositionId
              ? `<li><a href="#propositions/${propositionId}">${escapeHtml(reference)}</a></li>`
              : `<li><span class="rule-chip">${escapeHtml(reference)}</span></li>`;
          })
          .join("")}
      </ul>
    </section>`;
}

function sourceSections(unit) {
  if (!unit.sections?.length) return "";
  return `
    <section class="detail-section">
      <div class="section-title-row">
        <h4>Développement du texte</h4>
        <span>${unit.sections.length} section${unit.sections.length > 1 ? "s" : ""}</span>
      </div>
      ${unit.sections
        .map(
          (section, index) => `
            <details class="text-section" ${index === 0 ? "open" : ""}>
              <summary>${escapeHtml(section.label ?? section.type)}</summary>
              <p>${escapeHtml(section.text)}</p>
            </details>`,
        )
        .join("")}
    </section>`;
}

function rulesSection(unit) {
  const rules = unit.current_rules ?? [];
  const supportCount = unit.support_rules?.length ?? 0;
  return `
    <section class="detail-section">
      <div class="section-title-row">
        <h4>Règles de formalisation</h4>
        <span>${rules.length} locale${rules.length > 1 ? "s" : ""}${supportCount ? ` · ${supportCount} antérieure${supportCount > 1 ? "s" : ""}` : ""}</span>
      </div>
      ${
        rules.length
          ? `<ul class="rule-list">${rules
              .map((rule) => `<li class="rule-chip">${escapeHtml(rule)}</li>`)
              .join("")}</ul>`
          : '<p class="section-copy">Les règles décisives apparaissent dans les chaînes de preuve ci-dessous.</p>'
      }
    </section>`;
}

function caseCard(testCase, index) {
  const positive = testCase.goals.length > 0;
  const rules = testCase.rule_names ?? [];
  const allGoals = [
    ...testCase.goals.map((goal) => ["But", goal]),
    ...testCase.must_not_derive.map((goal) => ["Interdit", goal]),
  ];
  return `
    <details class="case-card" ${index === 0 ? "open" : ""}>
      <summary>
        <strong>${escapeHtml(testCase.id)}</strong>
        <span>${positive ? "preuve obtenue" : "frontière vérifiée"}</span>
      </summary>
      <div class="case-body">
        <div class="case-metrics">
          <div><strong>${testCase.initial_fact_count}</strong><small>faits initiaux</small></div>
          <div><strong>${testCase.derived_fact_count}</strong><small>faits dérivés</small></div>
          <div><strong>${testCase.derivation_count}</strong><small>dérivations</small></div>
        </div>
        ${
          rules.length
            ? `<ol class="proof-chain">${rules
                .map(
                  (rule, ruleIndex) =>
                    `<li>${escapeHtml(rule)} <small>· ${escapeHtml(testCase.rule_origins[ruleIndex] ?? "")}</small></li>`,
                )
                .join("")}</ol>`
            : '<p class="section-copy">Aucune règle ne franchit cette frontière : la conclusion interdite n’est pas dérivée.</p>'
        }
        <div class="case-goals">
          ${allGoals
            .map(
              ([kind, fact]) =>
                `<p><strong>${kind}</strong> · ${escapeHtml(factLabel(fact))}</p>`,
            )
            .join("")}
        </div>
      </div>
    </details>`;
}

function casesSection(unit) {
  return `
    <section class="detail-section">
      <div class="section-title-row">
        <h4>Cas exécutables</h4>
        <span>${unit.cases.length} cas</span>
      </div>
      <div class="case-grid">
        ${unit.cases.map(caseCard).join("")}
      </div>
    </section>`;
}

function limitationsSection(unit) {
  const items = [...(unit.limitations ?? []), ...(unit.known_divergences ?? [])];
  if (!items.length) return "";
  return `
    <section class="detail-section">
      <div class="section-title-row">
        <h4>Limites et divergences</h4>
        <span>${items.length} note${items.length > 1 ? "s" : ""}</span>
      </div>
      ${items.map((item) => `<p class="section-copy">${escapeHtml(item)}</p>`).join("")}
    </section>`;
}

function renderDetail(unit) {
  if (!unit) {
    return '<div class="detail-panel"><p class="section-copy">Sélectionnez une unité du corpus.</p></div>';
  }
  const kind =
    unit.kind === "proposition"
      ? "Proposition"
      : unit.kind === "general_definition"
        ? "Synthèse"
        : unit.family;
  return `
    <article class="detail-panel" aria-labelledby="detail-title">
      <header class="detail-header">
        <div class="detail-meta">
          <span class="tag">${escapeHtml(unit.id)}</span>
          <span class="tag">${escapeHtml(kind)}</span>
          <span class="tag success">${escapeHtml(statusLabel(unit.status))}</span>
        </div>
        <h3 id="detail-title">${escapeHtml(unit.title)}</h3>
        <blockquote class="source-quote">${escapeHtml(unit.source_text)}</blockquote>
      </header>
      ${dependenciesSection(unit)}
      ${sourceSections(unit)}
      ${rulesSection(unit)}
      ${casesSection(unit)}
      ${limitationsSection(unit)}
    </article>`;
}

function renderBrowser() {
  const units = filteredUnits();
  let selected = units.find((unit) => unit.id === state.selectedId);
  if (!selected && units.length && !state.query) {
    selected = units[0];
    state.selectedId = selected.id;
  }
  const listLabel = state.view === "propositions" ? "propositions" : "définitions";
  app.innerHTML = `
    <div class="browser-layout">
      <aside class="unit-list-panel" aria-label="Liste des ${listLabel}">
        <div class="list-summary">
          <span>${units.length} résultat${units.length > 1 ? "s" : ""}</span>
          <span>${state.query ? "filtré" : "corpus complet"}</span>
        </div>
        <ul class="unit-list">
          ${
            units.length
              ? units.map(unitListItem).join("")
              : '<li class="empty-list">Aucun résultat. Essayez un autre terme.</li>'
          }
        </ul>
      </aside>
      ${renderDetail(selected)}
    </div>`;
}

function renderArchitecture() {
  const counts = model.meta.counts;
  const edgeCount = model.proposition_graph.edges?.length ?? 0;
  app.innerHTML = `
    <div class="architecture-view">
      <div class="architecture-intro">
        <h3>Du texte à la conséquence.</h3>
        <p>
          Le modèle sépare quatre couches : le corpus source, les faits d’un
          cas, les règles autorisées et la clôture calculée. ${edgeCount}
          dépendances relient les propositions ; les définitions finales
          déclarent à leur tour leurs références canoniques.
        </p>
      </div>
      <div class="flow-map" aria-label="Chaîne de formalisation">
        <article class="flow-step"><span>01 · SOURCE</span><h4>Texte</h4><p>Énoncés, démonstrations, scolies et explications de la traduction Appuhn.</p></article>
        <article class="flow-step"><span>02 · MONDE</span><h4>Faits</h4><p>Une instanciation finie rend explicites sujets, objets, causes et contextes.</p></article>
        <article class="flow-step"><span>03 · INFÉRENCE</span><h4>Règles</h4><p>${counts.catalogued_rules} règles portent une origine textuelle, externe ou interprétative.</p></article>
        <article class="flow-step"><span>04 · AUDIT</span><h4>Preuve</h4><p>${counts.proposition_cases + counts.definition_cases} cas conservent profondeur et provenance.</p></article>
      </div>
      <section class="family-map">
        <h4>Les sept familles des affects</h4>
        <div class="family-grid">
          ${model.families
            .map(
              (family) => `
                <a class="family-card" href="#affects/E3DA${String(family.start).padStart(2, "0")}">
                  <span>E3DA${String(family.start).padStart(2, "0")}–E3DA${String(family.end).padStart(2, "0")}</span>
                  <strong>${escapeHtml(family.label)}</strong>
                  <small>${family.end - family.start + 1} définitions</small>
                </a>`,
            )
            .join("")}
          <a class="family-card" href="#affects/E3DA-GENERAL">
            <span>E3DA-GENERAL</span>
            <strong>Synthèse</strong>
            <small>idée, corps et puissance</small>
          </a>
        </div>
      </section>
    </div>`;
}

function render() {
  setActiveViewButton();
  if (state.view === "architecture") renderArchitecture();
  else renderBrowser();
}

viewButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    state.query = "";
    searchInput.value = "";
    state.selectedId = state.view === "propositions" ? "E3P01" : "E3DA01";
    updateHash(state.view, state.view === "architecture" ? "" : state.selectedId);
    render();
  });
});

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  if (state.view === "architecture") state.view = "affects";
  render();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== searchInput) {
    event.preventDefault();
    searchInput.focus();
  }
  if (event.key === "Escape" && document.activeElement === searchInput) {
    searchInput.value = "";
    state.query = "";
    searchInput.blur();
    render();
  }
});

app.addEventListener("click", (event) => {
  const button = event.target.closest("[data-select-unit]");
  if (!button) return;
  state.selectedId = button.dataset.selectUnit;
  updateHash(state.view, state.selectedId);
  render();
});

window.addEventListener("hashchange", routeFromHash);

fetch("./data/model.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((payload) => {
    model = payload;
    renderHeroStats();
    routeFromHash();
    if (!window.location.hash || window.location.hash === "#accueil") render();
  })
  .catch((error) => {
    app.innerHTML = `
      <div class="loading-panel">
        <p>Le corpus n’a pas pu être chargé.</p>
        <small>${escapeHtml(error.message)}</small>
      </div>`;
  });
