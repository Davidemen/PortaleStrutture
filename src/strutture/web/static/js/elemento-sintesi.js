// Pure helper split out of js/elemento-salva.js purely to keep that file under the spec's own
// 400-line cap: `sintesi`/`stato` (docs/architecture-phase3.md) for the element an engineer is
// about to save, built from the LAST successful run of THIS tool -- the same `getReportState()`
// snapshot js/relazione-print.js reads for the printed report, never a copy that could drift from
// what the Sintesi/results sheet is showing right now.
import { getReportState } from "./results.js";
import { isStaleOnScreen } from "./relazione-print.js";
import { governingCheck, effectiveUtilisation } from "./verdict.js";
import { extractByPredicate, readPath, rowsHighlightPairs } from "./output-schema.js";

export function computeSintesiEStato(toolName) {
  const { tool: reportTool, report } = getReportState();
  if (!reportTool || reportTool.name !== toolName || !report) return { sintesi: {}, stato: "dati_modificati" };
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
  const sintesi = {
    ok: Boolean(report.ok),
    ...(ratio === null ? {} : { eta_max: ratio }),
    ...(governing ? { verifica_governante: governing.name } : {}),
    evidenze,
  };
  const allPassed = checks.length === 0 || checks.every((check) => check.passed);
  const stato = isStaleOnScreen() ? "dati_modificati" : sintesi.ok && allPassed ? "verificato" : "non_verificato";
  return { sintesi, stato };
}
