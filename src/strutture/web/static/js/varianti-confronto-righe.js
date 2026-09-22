// Row builders for js/varianti-confronto.js's `<table>` (Modalità/Esito/Schema/Verifiche/
// Risultati/Dati), extracted purely to keep that module under the 400-line cap and its own
// `render()` under a readable size (WORKBENCH_SPEC §19.3). Every function takes a fresh `ctx`
// snapshot built by the caller at the start of each `render()` call -- `{ set, fields,
// outputNodes, riferimentoId, mostraTuttiRisultati, mostraTuttiDati, reportOf, reportsById,
// deltaCell }` -- rather than importing varianti-confronto.js back, so there is no cycle and no
// stale closure over state that changed since the snapshot was taken.
import { el } from "./dom.js";
import { extractByPredicate, readPath } from "./output-schema.js";
import { checkMark, buildBar, effectiveUtilisation, displayCheckName, governingCheck } from "./verdict.js";
import { formatValue, formatUnit } from "./format.js";
import { differenzeCampi, diffRighe, unioneVerifiche, checkPer, sameValue } from "./varianti-diff.js";

export function verdictWordOf(report) {
  if (!report) return "! Errore";
  const checks = report.checks || [];
  if (checks.length === 0) return report.ok ? "✓ Calcolo eseguito" : "✕ Non verificato";
  const failing = checks.filter((c) => !c.passed).length;
  return failing === 0 ? "✓ Verificato" : `✕ ${failing} non soddisfatte`;
}

export function highlightPairsOf(outputNodes, data) {
  const { matched } = extractByPredicate(outputNodes, (node) => node.kind === "scalar" && node.highlight);
  return matched.map((node) => ({ node, value: readPath(data, node.path) })).filter((pair) => pair.value !== null && pair.value !== undefined);
}

// §19.3 row 3: the FIRST `sketch`-kind output with a value, same "one sketch per column" cap the
// Sintesi itself uses -- never the §18 edit-from-drawing wiring (this is a decorative comparison
// row, not the tool page's own editable schizzo).
export function sketchPairOf(outputNodes, data) {
  const { matched } = extractByPredicate(outputNodes, (node) => node.kind === "sketch");
  return matched.map((node) => ({ node, value: readPath(data, node.path) })).find((pair) => pair.value) || null;
}

export function everyScalarOf(outputNodes, data) {
  const { matched } = extractByPredicate(outputNodes, (node) => node.kind === "scalar");
  return matched.map((node) => ({ node, value: readPath(data, node.path) }));
}

// `null` = still running/unknown (never compared); `false` also covers a column that errored
// outright -- an error IS an outcome, and "≠ esito diverso" must fire against it too, not only
// when both columns have a `governing` check.
export function esitoOk(info, report) {
  if (info && info.error) return false;
  if (!report) return null;
  const checks = report.checks || [];
  return checks.length === 0 ? Boolean(report.ok) : checks.every((c) => c.passed);
}

// §10's own per-tool print rule, one column per variant: printed pages never show the on-screen
// "provvisorio"/live chrome, only the mode the calculation actually ran in.
export function buildModalitaRow(ctx) {
  const tr = el("tr", { class: "vc-row-modalita" });
  tr.append(el("th", { scope: "row", text: "Modalità" }));
  for (const variante of ctx.set.varianti) {
    tr.append(el("td", {}, [el("span", { text: variante.inputs && variante.inputs.legacy_compat ? "Excel" : "Standard" })]));
  }
  return tr;
}

export function buildVerdictRow(ctx) {
  const { set, riferimentoId, reportOf, reportsById, deltaCell } = ctx;
  const tr = el("tr", { class: "vc-row-verdict" });
  tr.append(el("th", { scope: "row", text: "Esito" }));
  const refReport = reportOf(riferimentoId);
  const refInfo = reportsById.get(riferimentoId);
  const refOk = esitoOk(refInfo, refReport);
  for (const variante of set.varianti) {
    const info = reportsById.get(variante.id) || {};
    const report = info.report;
    const ok = esitoOk(info, report);
    const cell = el("td", {});
    if (info.error) {
      cell.append(el("span", { class: "vc-verdict-err", text: "! Errore" }), el("p", { class: "vc-error-msg", text: info.error }));
    } else if (report) {
      cell.append(el("span", {}, [checkMark(ok)]), document.createTextNode(` ${verdictWordOf(report)}`));
      const governing = governingCheck(report.checks || []);
      if (governing) {
        const ratio = effectiveUtilisation(governing);
        if (ratio !== null) {
          cell.append(el("p", { class: "vc-eta", text: `η max ${ratio.toFixed(2).replace(".", ",")} — ${displayCheckName(governing.name)}` }));
          cell.append(buildBar(ratio, governing.passed));
        }
        if (refReport && variante.id !== riferimentoId) {
          const refGoverning = (refReport.checks || []).find((c) => c.name === governing.name);
          const refRatio = refGoverning ? effectiveUtilisation(refGoverning) : null;
          if (refRatio !== null && ratio !== null && refRatio !== ratio) cell.append(deltaCell(ratio, refRatio));
        }
      }
    }
    if (variante.id !== riferimentoId && ok !== null && refOk !== null && ok !== refOk) {
      cell.append(el("p", { class: "vc-diff-flag", text: "≠ esito diverso" }));
    }
    tr.append(cell);
  }
  return tr;
}

export function buildSchemaRow(ctx) {
  const { set, outputNodes, reportOf } = ctx;
  const tr = el("tr", { class: "vc-row-schema" });
  tr.append(el("th", { scope: "row", text: "Schema" }));
  for (const variante of set.varianti) {
    const data = (reportOf(variante.id) || {}).data || {};
    const pair = sketchPairOf(outputNodes, data);
    const cell = el("td", {});
    if (pair) {
      const holder = el("div", { class: "vc-sketch-holder" });
      const figure = el("figure", { class: "vc-sketch", "aria-hidden": "true" }, [holder, el("figcaption", { text: "Schema" })]);
      cell.append(figure);
      import("./sketch.js")
        .then(({ renderSketch }) => renderSketch(holder, pair.value, {}))
        .catch(() => figure.remove());
    } else {
      cell.append(el("span", { text: "—" }));
    }
    tr.append(cell);
  }
  return tr;
}

export function buildVerificheRows(ctx) {
  const { set, riferimentoId, reportOf, deltaCell } = ctx;
  const reports = set.varianti.map((v) => reportOf(v.id));
  const nomi = unioneVerifiche(reports, set.varianti.findIndex((v) => v.id === riferimentoId));
  const rows = [];
  for (const nome of nomi) {
    const tr = el("tr");
    tr.append(el("th", { scope: "row", text: displayCheckName(nome) }));
    const refCheck = checkPer(reportOf(riferimentoId), nome);
    const refRatio = refCheck ? effectiveUtilisation(refCheck) : null;
    for (const variante of set.varianti) {
      const check = checkPer(reportOf(variante.id), nome);
      const cell = el("td", {});
      if (!check) {
        cell.append(el("span", { text: "—" }));
      } else {
        const ratio = effectiveUtilisation(check);
        cell.append(el("span", {}, [checkMark(check.passed)]));
        if (ratio !== null) cell.append(document.createTextNode(` ${ratio.toFixed(2).replace(".", ",")}`));
        if (variante.id !== riferimentoId && ratio !== null && refRatio !== null && ratio !== refRatio) cell.append(deltaCell(ratio, refRatio));
      }
      tr.append(cell);
    }
    rows.push(tr);
  }
  return rows;
}

export function buildRisultatiRows(ctx) {
  const { set, outputNodes, riferimentoId, mostraTuttiRisultati, reportOf, deltaCell } = ctx;
  const pairsSets = set.varianti.map((v) => {
    const data = (reportOf(v.id) || {}).data || {};
    return mostraTuttiRisultati ? everyScalarOf(outputNodes, data) : highlightPairsOf(outputNodes, data);
  });
  const refIndex = set.varianti.findIndex((v) => v.id === riferimentoId);
  const refPairsByPath = new Map((pairsSets[refIndex] || []).map((p) => [p.node.path, p]));
  // Union of every path ANY column produced, in the reference column's own order first, then
  // whatever else the other columns have -- never just the reference's own paths, or a failed
  // reference column (no report at all) empties the whole section for every other column too.
  const seen = new Set();
  const nodes = [];
  for (const pairs of pairsSets) {
    for (const pair of pairs) {
      if (seen.has(pair.node.path)) continue;
      seen.add(pair.node.path);
      nodes.push(pair.node);
    }
  }
  const rows = [];
  for (const node of nodes) {
    const tr = el("tr");
    tr.append(el("th", { scope: "row", text: node.label }));
    const refPair = refPairsByPath.get(node.path);
    pairsSets.forEach((pairs, colIndex) => {
      const pair = pairs.find((p) => p.node.path === node.path);
      const cell = el("td", {});
      if (!pair) {
        cell.append(el("span", { text: "—" }));
      } else {
        const { text } = formatValue(pair.value, pair.node);
        cell.append(document.createTextNode(`${text}${pair.node.unit && pair.node.unit !== "-" ? ` ${formatUnit(pair.node.unit)}` : ""}`));
        if (set.varianti[colIndex].id !== riferimentoId && refPair) cell.append(deltaCell(pair.value, refPair.value));
      }
      tr.append(cell);
    });
    rows.push(tr);
  }
  return rows;
}

export function buildDatiRows(ctx) {
  const { set, fields, riferimentoId, mostraTuttiDati } = ctx;
  const refIndex = set.varianti.findIndex((v) => v.id === riferimentoId);
  const differenze = differenzeCampi(fields, set.varianti, refIndex);
  const daMostrare = mostraTuttiDati ? differenze : differenze.filter((voce) => voce.diverso);
  return daMostrare.map((voce) => {
    const tr = el("tr");
    tr.append(el("th", { scope: "row", text: voce.field ? voce.field.label : voce.nome }));
    const riferimentoValore = (set.varianti.find((v) => v.id === riferimentoId) || {}).inputs?.[voce.nome];
    for (const variante of set.varianti) {
      const valore = variante.inputs ? variante.inputs[voce.nome] : undefined;
      const cell = el("td", {});
      if (voce.dettaglio) {
        // Per-column, against the CURRENT reference -- never the single aggregate summary
        // `differenzeCampi` computed once against its own first-diverging column, which showed
        // the identical text in every cell regardless of that column's own comparison.
        if (variante.id === riferimentoId) {
          cell.append(el("span", { text: "= uguale" }));
        } else {
          const { diverse, totale } = diffRighe(riferimentoValore, valore);
          cell.append(el("span", { text: diverse === 0 ? "= uguale" : `tabella: ${diverse} righe diverse su ${totale}` }));
        }
      } else {
        const { text } = formatValue(valore, {});
        cell.append(document.createTextNode(text || "—"));
        if (variante.id !== riferimentoId && !sameValue(valore, riferimentoValore)) cell.append(el("span", { class: "vc-diff-flag", text: " ≠ diverso" }));
      }
      tr.append(cell);
    }
    return tr;
  });
}

export function sectionHead(ctx, text) {
  const tr = el("tr", { class: "vc-section" });
  const th = el("th", { colspan: String(ctx.set.varianti.length + 1), text });
  tr.append(th);
  return tr;
}
