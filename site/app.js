const app = document.querySelector("#app");
const searchInput = document.querySelector("#search-input");
const viewButtons = [...document.querySelectorAll("[data-view]")];
const heroStats = document.querySelector("#hero-stats");
const moduleUrl = new URL(import.meta.url);
const assetVersion = moduleUrl.searchParams.get("v") ?? "dev";
const modelUrl = new URL("./data/model.json", moduleUrl);
modelUrl.searchParams.set("v", assetVersion);
app.dataset.loadState = "loading";
const GRAPH_DEFAULT_RULE = "E3DA28_EXP_mesestime_de_soi_nait_humilite";

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

function cacheBypassUrl() {
  const requestedHash = window.location.hash || "#rules";
  const safeHash = /^#[a-zA-Z0-9_\-/]+$/.test(requestedHash)
    ? requestedHash
    : "#rules";
  return `${window.location.pathname}?refresh=${Date.now()}${safeHash}`;
}

function renderHeroStats() {
  const counts = model.meta.counts;
  const stats = [
    [counts.propositions, "propositions"],
    [counts.definitions, "affects définis"],
    [counts.explanations, "explications atomisées"],
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
  if (state.view === "explanations") return model.explanations;
  if (state.view === "rules") return model.rules;
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
      unit.parent_id,
      unit.source_text,
      unit.origin,
      unit.status,
      unit.body,
      unit.file,
      unit.note,
      ...(unit.sources ?? []),
      ...(unit.declared_by ?? []),
      ...(unit.case_uses ?? []).flatMap((use) => [use.unit_id, use.case_id]),
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
  if (
    ![
      "propositions",
      "affects",
      "explanations",
      "rules",
      "graph",
      "architecture",
    ].includes(view)
  )
    return;
  if (state.view !== view) {
    state.query = "";
    searchInput.value = "";
  }
  state.view = view;
  if (selectedId) state.selectedId = selectedId;
  if (model) render();
}

function unitListItem(unit) {
  const selected = unit.id === state.selectedId;
  if (unit.kind === "rule") {
    return `
      <li>
        <button
          type="button"
          class="${selected ? "selected" : ""}"
          data-select-unit="${escapeHtml(unit.id)}"
          aria-current="${selected ? "true" : "false"}"
        >
          <span class="unit-code">${escapeHtml(unit.origin)}</span>
          <span>
            <strong>${escapeHtml(unit.id)}</strong>
            <small>${escapeHtml(unit.status ?? "statut non renseigné")}</small>
          </span>
        </button>
      </li>`;
  }
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

function unitHref(unitId) {
  if (unitId.endsWith("-EXP")) return `#explanations/${unitId}`;
  if (unitId.startsWith("E3DA")) return `#affects/${unitId}`;
  if (/^E3P\d{2}$/.test(unitId)) return `#propositions/${unitId}`;
  return null;
}

function referenceItem(reference) {
  const propositionMatch = reference.match(/^E3P\d{2}/);
  const explanationMatch = reference.match(/^E3DA(?:-GENERAL|\d{2})-EXP/);
  const affectMatch = reference.match(/^E3DA(?:-GENERAL|\d{2})/);
  const canonicalId =
    propositionMatch?.[0] ?? explanationMatch?.[0] ?? affectMatch?.[0] ?? reference;
  const href = unitHref(canonicalId);
  return href
    ? `<li><a href="${href}">${escapeHtml(reference)}</a></li>`
    : `<li><span class="rule-chip">${escapeHtml(reference)}</span></li>`;
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
        ${unit.dependencies.map(referenceItem).join("")}
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
              .map(
                (rule) =>
                  `<li><a class="rule-chip" href="#rules/${rule}">${escapeHtml(rule)}</a></li>`,
              )
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
                    `<li><a href="#rules/${rule}">${escapeHtml(rule)}</a> <small>· ${escapeHtml(testCase.rule_origins[ruleIndex] ?? "")}</small></li>`,
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

function linkedReferences(title, references) {
  if (!references?.length) return "";
  return `
    <section class="detail-section">
      <div class="section-title-row">
        <h4>${escapeHtml(title)}</h4>
        <span>${references.length} référence${references.length > 1 ? "s" : ""}</span>
      </div>
      <ul class="dependency-list">${references.map(referenceItem).join("")}</ul>
    </section>`;
}

function renderRuleDetail(rule) {
  if (!rule) {
    return '<div class="detail-panel"><p class="section-copy">Sélectionnez une règle Snark.</p></div>';
  }
  const sourceUrl = `${model.meta.repository}/blob/main/spinoza/systematic/${rule.file}`;
  return `
    <article class="detail-panel rule-detail" aria-labelledby="detail-title">
      <header class="detail-header">
        <div class="detail-meta">
          <span class="tag">Règle Snark</span>
          <span class="tag">${escapeHtml(rule.origin)}</span>
          <span class="tag success">${escapeHtml(rule.status ?? "non renseigné")}</span>
        </div>
        <h3 id="detail-title">${escapeHtml(rule.id)}</h3>
        ${
          rule.note
            ? `<p class="rule-note">${escapeHtml(rule.note)}</p>`
            : ""
        }
        <p class="rule-actions"><a class="button secondary" href="#graph/${escapeHtml(rule.id)}">Voir dans le graphe</a></p>
      </header>
      <section class="detail-section">
        <div class="section-title-row">
          <h4>Code de la règle</h4>
          <a class="source-file-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">${escapeHtml(rule.file)} ↗</a>
        </div>
        <pre class="snark-source"><code>${escapeHtml(rule.body)}</code></pre>
      </section>
      ${linkedReferences("Sources philosophiques", rule.sources)}
      ${linkedReferences("Unités qui déclarent la règle", rule.declared_by)}
      ${
        rule.case_uses.length
          ? `<section class="detail-section">
              <div class="section-title-row">
                <h4>Activations dans les preuves</h4>
                <span>${rule.case_uses.length} cas</span>
              </div>
              <ul class="rule-usage-list">
                ${rule.case_uses
                  .map((use) => {
                    const href = unitHref(use.unit_id);
                    const label = `${use.unit_id} · ${use.case_id}`;
                    return `<li>${href ? `<a href="${href}">${escapeHtml(label)}</a>` : escapeHtml(label)}</li>`;
                  })
                  .join("")}
              </ul>
            </section>`
          : `<section class="detail-section"><p class="section-copy">Cette règle appartient au modèle, mais n’apparaît dans aucune chaîne minimale de preuve publiée.</p></section>`
      }
    </article>`;
}

function renderDetail(unit) {
  if (unit?.kind === "rule" || state.view === "rules") return renderRuleDetail(unit);
  if (!unit) {
    return '<div class="detail-panel"><p class="section-copy">Sélectionnez une unité du corpus.</p></div>';
  }
  const kind =
    unit.kind === "proposition"
      ? "Proposition"
      : unit.kind === "explanation"
        ? "Explication"
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
      ${unit.parent_id ? linkedReferences("Définition expliquée", [unit.parent_id]) : ""}
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
  const listLabel =
    state.view === "propositions"
      ? "propositions"
      : state.view === "explanations"
        ? "explications"
      : state.view === "rules"
        ? "règles Snark"
        : "définitions";
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
        <article class="flow-step"><span>04 · AUDIT</span><h4>Preuve</h4><p>${counts.proposition_cases + counts.definition_cases + counts.explanation_cases} cas conservent profondeur et provenance.</p></article>
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

function graphPredicates(rule) {
  return new Set([
    ...(rule.input_predicates ?? []),
    ...(rule.output_predicates ?? []),
  ]);
}

function graphRuleMatches(query) {
  const normalizedQuery = normalize(query.trim());
  if (!normalizedQuery) return model.rules;
  return model.rules.filter((rule) =>
    normalize(
      [
        rule.id,
        rule.origin,
        rule.status,
        ...(rule.input_predicates ?? []),
        ...(rule.output_predicates ?? []),
      ].join(" "),
    ).includes(normalizedQuery),
  );
}

function graphNode(ruleId, x, y, role) {
  const label = ruleId.length > 38 ? `${ruleId.slice(0, 36)}…` : ruleId;
  return `
    <a href="#graph/${escapeHtml(ruleId)}" aria-label="Sélectionner ${escapeHtml(ruleId)}">
      <g class="graph-node ${role}" transform="translate(${x - 135} ${y - 28})">
        <rect width="270" height="56" rx="3"></rect>
        <text x="14" y="23">${escapeHtml(label)}</text>
        <text class="graph-node-role" x="14" y="42">${escapeHtml(role)}</text>
      </g>
    </a>`;
}

function graphEdge(sourceX, sourceY, targetX, targetY, predicate, role) {
  const label = predicate.length > 29 ? `${predicate.slice(0, 27)}…` : predicate;
  const middleX = (sourceX + targetX) / 2;
  const middleY = (sourceY + targetY) / 2 - 6;
  return `
    <g class="graph-edge ${role}">
      <path d="M ${sourceX} ${sourceY} L ${targetX} ${targetY}" ${role === "shared" ? "" : 'marker-end="url(#graph-arrow)"'}></path>
      <text x="${middleX}" y="${middleY}">${escapeHtml(label)}</text>
    </g>`;
}

function renderRuleGraph() {
  const matches = graphRuleMatches(state.query);
  let selected = model.rules.find((rule) => rule.id === state.selectedId);
  if (state.query && matches.length && !matches.some((rule) => rule.id === selected?.id)) {
    selected = matches[0];
    state.selectedId = selected.id;
  }
  if (!selected) {
    selected =
      model.rules.find((rule) => rule.id === GRAPH_DEFAULT_RULE) ?? model.rules[0];
    state.selectedId = selected.id;
  }

  const predicateIndex = new Map(
    model.rule_graph.predicates.map((predicate) => [predicate.id, predicate]),
  );
  const incomingByRule = new Map();
  for (const predicate of selected.input_predicates ?? []) {
    for (const producer of predicateIndex.get(predicate)?.producers ?? []) {
      if (producer === selected.id) continue;
      if (!incomingByRule.has(producer)) incomingByRule.set(producer, []);
      incomingByRule.get(producer).push(predicate);
    }
  }
  const outgoingByRule = new Map();
  for (const predicate of selected.output_predicates ?? []) {
    for (const consumer of predicateIndex.get(predicate)?.consumers ?? []) {
      if (consumer === selected.id) continue;
      if (!outgoingByRule.has(consumer)) outgoingByRule.set(consumer, []);
      outgoingByRule.get(consumer).push(predicate);
    }
  }
  const allIncoming = [...incomingByRule.entries()].map(
    ([source, predicates]) => ({ source, target: selected.id, predicates }),
  );
  const allOutgoing = [...outgoingByRule.entries()].map(
    ([target, predicates]) => ({ source: selected.id, target, predicates }),
  );
  const incoming = allIncoming.slice(0, 8);
  const outgoing = allOutgoing.slice(0, 8);
  const directedNeighbors = new Set([
    ...allIncoming.map((edge) => edge.source),
    ...allOutgoing.map((edge) => edge.target),
  ]);
  const selectedPredicates = graphPredicates(selected);
  const peers = model.rules
    .filter(
      (rule) => rule.id !== selected.id && !directedNeighbors.has(rule.id),
    )
    .map((rule) => ({
      id: rule.id,
      shared: [...graphPredicates(rule)].filter((predicate) =>
        selectedPredicates.has(predicate),
      ),
    }))
    .filter((peer) => peer.shared.length)
    .sort((left, right) => right.shared.length - left.shared.length)
    .slice(0, 5);

  const verticalPosition = (index, count) =>
    count === 1 ? 320 : 80 + (index * 470) / (count - 1);
  const incomingPositions = incoming.map((_, index) =>
    verticalPosition(index, incoming.length),
  );
  const outgoingPositions = outgoing.map((_, index) =>
    verticalPosition(index, outgoing.length),
  );
  const peerPositions = peers.map((_, index) =>
    peers.length === 1 ? 600 : 250 + (index * 700) / (peers.length - 1),
  );
  const svgEdges = [
    ...incoming.map((edge, index) =>
      graphEdge(
        305,
        incomingPositions[index],
        455,
        320,
        edge.predicates.join(", "),
        "incoming",
      ),
    ),
    ...outgoing.map((edge, index) =>
      graphEdge(
        745,
        320,
        895,
        outgoingPositions[index],
        edge.predicates.join(", "),
        "outgoing",
      ),
    ),
    ...peers.map((peer, index) =>
      graphEdge(
        600,
        348,
        peerPositions[index],
        612,
        peer.shared.join(", "),
        "shared",
      ),
    ),
  ].join("");
  const svgNodes = [
    ...incoming.map((edge, index) =>
      graphNode(edge.source, 170, incomingPositions[index], "producteur"),
    ),
    graphNode(selected.id, 600, 320, "sélection"),
    ...outgoing.map((edge, index) =>
      graphNode(edge.target, 1030, outgoingPositions[index], "consommateur"),
    ),
    ...peers.map((peer, index) =>
      graphNode(peer.id, peerPositions[index], 650, "prédicat commun"),
    ),
  ].join("");
  const suggestions = state.query
    ? `<div class="graph-search-results">
        <span>${matches.length} règle${matches.length > 1 ? "s" : ""} correspondante${matches.length > 1 ? "s" : ""}</span>
        ${matches
          .slice(0, 8)
          .map(
            (rule) =>
              `<a href="#graph/${escapeHtml(rule.id)}">${escapeHtml(rule.id)}</a>`,
          )
          .join("")}
      </div>`
    : "";

  app.innerHTML = `
    <div class="rule-graph-view">
      <header class="graph-heading">
        <div>
          <p class="eyebrow">Réseau producteur–consommateur</p>
          <h3>${escapeHtml(selected.id)}</h3>
        </div>
        <p>
          Une flèche relie une sortie de règle à une entrée d’une autre règle.
          Les liens fins signalent un prédicat commun sans dépendance dirigée.
        </p>
      </header>
      ${suggestions}
      <div class="graph-metrics">
        <span><strong>${allIncoming.length}</strong> producteurs</span>
        <span><strong>${allOutgoing.length}</strong> consommateurs</span>
        <span><strong>${peers.length}</strong> voisins communs affichés</span>
        <span><strong>${model.meta.counts.predicates}</strong> prédicats dans le modèle</span>
      </div>
      <div class="graph-canvas">
        <svg viewBox="0 0 1200 700" role="img" aria-labelledby="graph-title graph-description">
          <title id="graph-title">Voisinage de la règle ${escapeHtml(selected.id)}</title>
          <desc id="graph-description">Producteurs à gauche, règle sélectionnée au centre, consommateurs à droite et règles partageant des prédicats en bas.</desc>
          <defs>
            <marker id="graph-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M 0 0 L 8 4 L 0 8 z"></path>
            </marker>
          </defs>
          ${svgEdges}
          ${svgNodes}
        </svg>
      </div>
      <div class="graph-predicate-columns">
        <section>
          <h4>Prédicats d’entrée</h4>
          <div class="predicate-cloud">
            ${(selected.input_predicates ?? [])
              .map(
                (predicate) =>
                  `<button type="button" class="rule-chip" data-graph-predicate="${escapeHtml(predicate)}">${escapeHtml(predicate)}</button>`,
              )
              .join("") || "<span>Aucun prédicat factuel</span>"}
          </div>
        </section>
        <section>
          <h4>Prédicats de sortie</h4>
          <div class="predicate-cloud">
            ${(selected.output_predicates ?? [])
              .map(
                (predicate) =>
                  `<button type="button" class="rule-chip" data-graph-predicate="${escapeHtml(predicate)}">${escapeHtml(predicate)}</button>`,
              )
              .join("") || "<span>Aucun prédicat ajouté</span>"}
          </div>
        </section>
      </div>
      <p class="graph-footnote">
        Le graphe complet contient ${model.meta.counts.rule_dependencies} dépendances dirigées entre ${model.meta.counts.catalogued_rules} règles. Le voisinage est limité visuellement ; les compteurs conservent les totaux complets.
      </p>
    </div>`;
}

function render() {
  setActiveViewButton();
  if (state.view === "architecture") renderArchitecture();
  else if (state.view === "graph") renderRuleGraph();
  else renderBrowser();
}

viewButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.view = button.dataset.view;
    state.query = "";
    searchInput.value = "";
    state.selectedId =
      state.view === "propositions"
        ? "E3P01"
        : state.view === "explanations"
          ? model.explanations[0].id
        : state.view === "rules"
          ? model.rules[0].id
          : state.view === "graph"
            ? GRAPH_DEFAULT_RULE
            : "E3DA01";
    updateHash(
      state.view,
      state.view === "architecture" ? "" : state.selectedId,
    );
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
  const predicateButton = event.target.closest("[data-graph-predicate]");
  if (predicateButton) {
    const predicate = predicateButton.dataset.graphPredicate;
    state.query = predicate;
    searchInput.value = predicate;
    const match = graphRuleMatches(predicate)[0];
    if (match) state.selectedId = match.id;
    updateHash("graph", state.selectedId);
    render();
    return;
  }
  const button = event.target.closest("[data-select-unit]");
  if (!button) return;
  state.selectedId = button.dataset.selectUnit;
  updateHash(state.view, state.selectedId);
  render();
});

window.addEventListener("hashchange", routeFromHash);

const modelRequest = new AbortController();
const modelTimeout = window.setTimeout(() => modelRequest.abort(), 15000);

fetch(modelUrl, { cache: "no-store", signal: modelRequest.signal })
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((payload) => {
    model = payload;
    app.dataset.loadState = "ready";
    renderHeroStats();
    routeFromHash();
    if (!window.location.hash || window.location.hash === "#accueil") render();
  })
  .catch((error) => {
    app.dataset.loadState = "error";
    const message =
      error.name === "AbortError"
        ? "Le chargement a dépassé quinze secondes."
        : error.message;
    app.innerHTML = `
      <div class="loading-panel loading-help">
        <p>Le corpus n’a pas pu être chargé.</p>
        <small>${escapeHtml(message)}</small>
        <a class="button primary" href="${escapeHtml(cacheBypassUrl())}">Recharger la dernière version</a>
      </div>`;
  })
  .finally(() => window.clearTimeout(modelTimeout));
