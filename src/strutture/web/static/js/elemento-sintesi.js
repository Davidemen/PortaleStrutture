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

export function computeSintesiEStato(toolName) {
  const { tool: reportTool, report } = getReportState();
  if (!reportTool || reportTool.name !== toolName || !report) return { sintesi: {}, stato: "dati_modificati" };
  if (isStaleOnScreen()) return { sintesi: {}, stato: "dati_modificati" };
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
  const stato = sintesi.ok && allPassed ? "verificato" : "non_verificato";
  return { sintesi, stato };
}
