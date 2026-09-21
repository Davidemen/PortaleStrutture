// The printed "relazione di calcolo", built FROM THE DATA (WORKBENCH_SPEC §10/§11) -- never by
// printing the interactive results tree. Document order (user rule): cartiglio -> Schizzo (every
// view) -> Dati di ingresso -> Sintesi -> Verifiche -> result groups -> tables -> charts -> avvisi.
// `buildRelazione` is the single place that composes the document; every section it fills is
// reused from the interactive package (sintesi.js, results-groups.js, results-rows.js, verdict.js,
// sketch.js) through an options object rather than a second implementation of the same rendering.
import { el, clear } from "./dom.js";
import { extractByPredicate, readPath, rowsHighlightPairs, firstChartNode } from "./output-schema.js";
import { buildCartiglio } from "./print.js";
import { buildInputsSection } from "./relazione-inputs.js";
import { buildVerificheSection, buildGroupsSection, buildAvvisiSection } from "./relazione-groups.js";
import { buildSviluppoSection } from "./relazione-sviluppo.js";
import { renderSintesi } from "./sintesi.js";
import { renderSketch } from "./sketch.js";

// §11 contract defaults = the COMPLETE §10 report; every key an overlay might one day omit stays
// explicit here so `resolveOptions`/`omittedSections` below are the ONE place that decides what
// "complete" means, reusable by the (future) options overlay instead of re-deriving it.
export const DEFAULT_OPTIONS = {
  preset: "completa",
  sezioni: {
    schizzo: true,
    dati: true,
    sintesi: true,
    verifiche: "tutte", // "tutte" | "non_soddisfatte" | false
    gruppi: {}, // { [output-path]: false } -- missing/true = included
    passaggi: true,
    // docs/architecture-phase2.md §5: "default ON when the tool offers it; hidden otherwise" --
    // the overlay only ever shows this checkbox for a tool whose schema says `relazione: true`
    // (js/relazione-overlay-contenuto.js), and `buildSviluppoSection` itself is a no-op whenever
    // there is no trace/warning to show, so this default stays harmless for every other tool.
    sviluppo: true,
    tabelle: true,
    grafici: true,
    avvisi: true,
    nota_correzioni: true,
  },
  tabelle: { righe: "tutte", n: undefined }, // "tutte" | "prime" | "governanti"
  pagina: { orientamento: "verticale", corpo: "normale", numeri: true, intestazione: true },
  cartiglio: {},
};

// Pure: missing keys default to the complete report, at any nesting depth the §11 contract
// describes -- the overlay only ever needs to pass the keys it actually changed.
export function resolveOptions(options = {}) {
  const sezioni = { ...DEFAULT_OPTIONS.sezioni, ...(options.sezioni || {}) };
  sezioni.gruppi = { ...DEFAULT_OPTIONS.sezioni.gruppi, ...((options.sezioni && options.sezioni.gruppi) || {}) };
  return {
    preset: options.preset || DEFAULT_OPTIONS.preset,
    sezioni,
    tabelle: { ...DEFAULT_OPTIONS.tabelle, ...(options.tabelle || {}) },
    pagina: { ...DEFAULT_OPTIONS.pagina, ...(options.pagina || {}) },
    cartiglio: { ...(options.cartiglio || {}) },
  };
}

const SECTION_LABELS = { schizzo: "Schizzo", dati: "Dati di ingresso", sintesi: "Sintesi", passaggi: "Passaggi di calcolo", tabelle: "Tabelle", grafici: "Grafici", avvisi: "Avvisi" };

// Pure: the "Contenuto ridotto dall'utente — omessi: …" sentence's ingredients, given an already-
// RESOLVED options object -- never mistaken-for-complete when anything was turned off (§11).
export function omittedSections(resolved) {
  const sezioni = resolved.sezioni;
  const omitted = Object.entries(SECTION_LABELS)
    .filter(([key]) => sezioni[key] === false)
    .map(([, label]) => label);
  if (sezioni.verifiche === false) omitted.push("Verifiche");
  else if (sezioni.verifiche === "non_soddisfatte") omitted.push("Verifiche (solo non soddisfatte)");
  const hiddenGroups = Object.values(sezioni.gruppi || {}).filter((v) => v === false).length;
  if (hiddenGroups > 0) omitted.push(`${hiddenGroups} gruppi di risultati`);
  return omitted;
}

function buildSchizzoSection(sketchPairs, data, idPrefix) {
  const section = el("div", { class: "print-schizzo" });
  section.append(el("h2", { text: "Schizzo" }));
  for (const { value } of sketchPairs) {
    if (!value) continue;
    const holder = el("div", { class: "print-schizzo-views" });
    section.append(holder);
    try {
      // Review finding 7: distinct ids from the interactive Sintesi copy (still live in the DOM,
      // merely hidden by print.css) so `url(#sk-terreno-…)`/marker-end references in this copy
      // never resolve to the wrong document-wide element.
      renderSketch(holder, value, { idPrefix });
    } catch {
      holder.remove(); // a broken sketch must never break the printed report
    }
  }
  return section.childElementCount > 1 ? section : null; // only the <h2>: nothing actually drawn
}

// `data = {tool: {name,title,norm}, report, outputNodes, fields}` -- report+input/output schema,
// exactly the §10 rule "built FROM THE DATA". `options` is the raw (possibly partial) §11 object;
// missing keys = the complete report, always the caller's default. `idPrefix` (review finding 7,
// extended): this function is called for TWO independent documents that can be alive in the DOM at
// once -- the actual print root (`relazione-print.js`, default "p") and the overlay's own live A4
// preview (`relazione-preview.js`, "v") -- each needs ids distinct from the other and from the
// never-removed interactive Sintesi sketch (no prefix), or their `url(#id)` fills/markers collide.
export function buildRelazione(container, { tool, report, outputNodes, fields } = {}, options = {}, idPrefix = "p") {
  clear(container);
  if (!report) return;
  const resolved = resolveOptions(options);
  const data = report.data || {};
  const legacyMode = Boolean(report.inputs_echo && report.inputs_echo.legacy_compat);

  container.append(buildCartiglio(tool, legacyMode ? "foglio Excel" : "standard", resolved.cartiglio));
  // "Sviluppo dei calcoli" is only ever relevant for a tool whose schema says `relazione: true`
  // (`tool.relazione`, results.js) -- `omittedSections` itself stays tool-agnostic (pure over
  // `options` alone, reused by every other §11 caller), so a tool that never had formulas can
  // never be misreported as having had this section "reduced" out of it.
  const omitted = [
    ...omittedSections(resolved),
    ...(!resolved.sezioni.sviluppo && tool && tool.relazione ? ["Sviluppo dei calcoli"] : []),
  ];
  if (omitted.length > 0) {
    container.append(el("p", { class: "print-omessi", text: `Contenuto ridotto dall'utente — omessi: ${omitted.join(", ")}` }));
  }

  const sketchSplit = extractByPredicate(outputNodes || [], (node) => node.kind === "sketch");
  const highlightSplit = extractByPredicate(sketchSplit.rest, (node) => node.kind === "scalar" && node.highlight);
  const treeNodes = highlightSplit.rest;
  const scalarHighlights = highlightSplit.matched.map((node) => ({ node, value: readPath(data, node.path) })).filter((p) => p.value !== null && p.value !== undefined);
  const highlightPairs = [...scalarHighlights, ...rowsHighlightPairs(treeNodes, data)].slice(0, 3);
  const sketchPairs = sketchSplit.matched.map((node) => ({ node, value: readPath(data, node.path) }));
  // Orchestrator finding, print too: no checks/highlights/sketch would otherwise leave the
  // printed Sintesi section empty.
  const checks = report.checks || [];
  const chartFallback =
    checks.length === 0 && highlightPairs.length === 0 && sketchPairs.length === 0
      ? (() => {
          const node = firstChartNode(treeNodes);
          const rows = node ? readPath(data, node.path) : undefined;
          return node && Array.isArray(rows) && rows.length > 0 ? { node, rows } : null;
        })()
      : null;

  if (resolved.sezioni.schizzo) {
    const schizzo = buildSchizzoSection(sketchPairs, data, idPrefix);
    if (schizzo) container.append(schizzo);
  }
  if (resolved.sezioni.dati) container.append(buildInputsSection(fields || [], report.inputs_echo || {}));
  if (resolved.sezioni.sintesi) {
    const sintesiRoot = el("div", { class: "print-sintesi" });
    container.append(sintesiRoot);
    renderSintesi(sintesiRoot, { report, highlightPairs, chartFallback, options: { copy: false, sketches: false, warnings: false } });
  }
  buildVerificheSection(container, report.checks || [], resolved.sezioni);
  // docs/architecture-phase2.md §5: "Sviluppo dei calcoli" AFTER "Verifiche", before the plain
  // result groups/tables/charts.
  if (resolved.sezioni.sviluppo) {
    const sviluppo = buildSviluppoSection(report.relazione || [], report.warnings || []);
    if (sviluppo) container.append(sviluppo);
  }
  buildGroupsSection(container, treeNodes, data, tool ? tool.name : "", resolved.sezioni, resolved.tabelle);
  buildAvvisiSection(container, report.warnings || [], resolved.sezioni);
  // Review finding 24: a closing signature line -- unconditional (not a §11 toggle), the last
  // thing on the page whatever content above it was included/omitted.
  container.append(el("p", { class: "print-signature", text: "Il progettista" }));
}
