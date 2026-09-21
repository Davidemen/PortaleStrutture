// Print-only Verifiche + result groups + Avvisi (WORKBENCH_SPEC §10: EVERY check, no fold, no
// "Solo non soddisfatte" filter; every group; warnings in full). Reuses the SAME row/group
// builders as the interactive results sheet (results-groups.js/results-rows.js/verdict.js) via
// their `print: true` reuse path -- see results-toolbar.js `mountGroup` for why print builds
// fresh, under prefixed ids, instead of reconciling against the live DOM.
import { el } from "./dom.js";
import { buildCheckRow, sortChecks } from "./verdict.js";
import { appendScalarGroup, appendGroupSection } from "./results-groups.js";
import { appendRowsSection } from "./results-rows.js";

function groupEnabled(sezioni, path) {
  const gruppi = sezioni.gruppi || {};
  return gruppi[path] !== false;
}

// `sezioni.verifiche`: "tutte" (default) | "non_soddisfatte" | false.
export function buildVerificheSection(container, checks, sezioni) {
  const wanted = sezioni.verifiche;
  if (!wanted || checks.length === 0) return;
  const filtered = wanted === "non_soddisfatte" ? checks.filter((c) => !c.passed) : checks;
  if (filtered.length === 0) return;
  const section = el("section", { class: "r-group r-group--print" });
  section.append(el("h3", { class: "r-group-title", text: `Verifiche (${filtered.length})` }));
  const body = el("div", { class: "r-group-body" });
  for (const check of sortChecks(filtered)) body.append(buildCheckRow(check));
  section.append(body);
  container.append(section);
}

// `tabellePolicy` (WORKBENCH_SPEC §11 "Tabelle": `{righe, n}`) is the overlay's row-policy
// override, separate from `sezioni.tabelle` (the plain on/off content checkbox, same name by
// contract coincidence) -- threaded down to every row-table this tool has via `ctx`.
export function buildGroupsSection(container, treeNodes, data, toolName, sezioni, tabellePolicy) {
  const ctx = { print: true, chart: sezioni.grafici !== false, tabellePolicy };
  if (sezioni.passaggi) {
    const passaggiNodes = treeNodes.filter((node) => node.kind === "scalar");
    appendScalarGroup(container, "r-group-passaggi", "Passaggi di calcolo", passaggiNodes, data, ctx);
  }
  for (const node of treeNodes) {
    if (!groupEnabled(sezioni, node.path)) continue;
    if (node.kind === "group") {
      appendGroupSection(container, node, data, toolName, ctx);
    } else if (node.kind === "rows" && sezioni.tabelle !== false) {
      appendRowsSection(container, node, data, toolName, ctx);
    }
  }
}

export function buildAvvisiSection(container, warnings, sezioni) {
  if (!sezioni.avvisi || !warnings || warnings.length === 0) return;
  const section = el("section", { class: "r-group r-group--print" });
  section.append(el("h3", { class: "r-group-title", text: "Avvisi" }));
  const body = el("div", { class: "r-group-body" });
  for (const message of warnings) body.append(el("p", { text: message }));
  section.append(body);
  container.append(section);
}
