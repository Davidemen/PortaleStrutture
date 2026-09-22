// Pure helper split out of js/elemento-salva.js purely to keep that file under the spec's own
// 400-line cap: `sintesi`/`stato` (docs/architecture-phase3.md) for the element an engineer is
// about to save, built from the LAST successful run of THIS tool -- the same `getReportState()`
// snapshot js/relazione-print.js reads for the printed report, never a copy that could drift from
// what the Sintesi/results sheet is showing right now.
import { getReportState } from "./results.js";
import { isStaleOnScreen } from "./relazione-print.js";
import { governingCheck, effectiveUtilisation } from "./verdict.js";
import { extractByPredicate, readPath, rowsHighlightPairs } from "./output-schema.js";

// WORKBENCH_SPEC §20.1: `Report.warnings` verbatim strings a failing trace appends -- not a real
// avviso of the calculation itself (the mode is already shown by `modalita`), so it never counts
// towards the table's "Avvisi" cell. Kept in sync by hand with `strutture.shared.tool` (frontend
// has no import path into the Python package).
const AVVISI_ESCLUSI_DALLA_TRACCIA = new Set([
  "Sviluppo dei calcoli non disponibile per questi dati.",
  "Lo sviluppo dei calcoli descrive la modalità standard: non è disponibile in modalità Excel.",
]);

// WORKBENCH_SPEC §19.5: "build sintesi/stato from a given report, not only from
// getReportState()" -- js/varianti-tieni.js (§19.4) computes this for a variant's OWN just-run
// report, which is never the same one `getReportState()` holds (that always reflects the tool
// page's CURRENT active variant, not whichever one the engineer is "Tieni questa"-ing).
// `overrides.report`/`overrides.reportTool` default to the shared state so every existing caller
// (js/elemento-salva.js) keeps its original behaviour untouched.
export function computeSintesiEStato(toolName, overrides = {}) {
  const shared = getReportState();
  const reportTool = overrides.reportTool !== undefined ? overrides.reportTool : shared.tool;
  const report = overrides.report !== undefined ? overrides.report : shared.report;
  if (!reportTool || reportTool.name !== toolName || !report) return { sintesi: {}, stato: "dati_modificati" };
  // §14.1/§20.2: a "stale" screen (input changed, run not settled/saved yet) still shows the
  // sintesi from the LAST successful report -- only `stato` is forced to "dati_modificati". Never
  // drop straight to `{}` here, or a saved element loses eta_max/evidenze/avvisi on the table.
  const stale = overrides.stale !== undefined ? overrides.stale : isStaleOnScreen();
  if (!report.ok) {
    const errore = (report.errors && report.errors[0]) || "Errore di calcolo.";
    return { sintesi: { ok: false, errore }, stato: "non_verificato" };
  }
  const checks = report.checks || [];
  const data = report.data || {};
  const outputNodes = reportTool.outputNodes || [];
  const legacySplit = extractByPredicate(outputNodes, (node) => node.legacyOnly);
  const sketchSplit = extractByPredicate(legacySplit.rest, (node) => node.kind === "sketch");
  const highlightSplit = extractByPredicate(sketchSplit.rest, (node) => node.kind === "scalar" && node.highlight);
  const treeNodes = highlightSplit.rest;
  const scalarHighlights = highlightSplit.matched
    .map((node) => ({ node, value: readPath(data, node.path) }))
    .filter((pair) => pair.value !== null && pair.value !== undefined);
  const evidenze = [...scalarHighlights, ...rowsHighlightPairs(treeNodes, data)].slice(0, 3).map(({ node, value }) => ({
    ...(node.symbol ? { simbolo: node.symbol } : { label: node.label }),
    valore: value,
    ...(node.unit && node.unit !== "-" ? { unita: node.unit } : {}),
  }));
  const governing = governingCheck(checks);
  const ratio = governing ? effectiveUtilisation(governing) : null;
  const avvisiContati = (report.warnings || []).filter((testo) => !AVVISI_ESCLUSI_DALLA_TRACCIA.has(testo));
  const sintesi = {
    ok: Boolean(report.ok),
    ...(ratio === null ? {} : { eta_max: ratio }),
    ...(governing ? { verifica_governante: governing.name } : {}),
    evidenze,
    avvisi: { n: avvisiContati.length, primo: avvisiContati[0] || "" },
  };
  const allPassed = checks.length === 0 || checks.every((check) => check.passed);
  const stato = stale ? "dati_modificati" : sintesi.ok && allPassed ? "verificato" : "non_verificato";
  return { sintesi, stato };
}
