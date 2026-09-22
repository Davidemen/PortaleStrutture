// #/varianti/<tool> ("Affianca", WORKBENCH_SPEC §19.3): one column per variant, a `<table>` with
// variants as columns and Verdict/Verifiche/Risultati/Dati rows. Full-width page, no Dati/Sintesi
// split -- same shell slot as #/registro and #/progetti (js/main.js `showVarianti`).
import { el, clear } from "./dom.js";
import { navigate } from "./router.js";
import { fetchSchema, runTool } from "./api.js";
import { describeFields } from "./schema.js";
import { describeOutput, extractByPredicate, readPath } from "./output-schema.js";
import { checkMark, buildBar, effectiveUtilisation, displayCheckName, governingCheck } from "./verdict.js";
import { formatValue, formatUnit } from "./format.js";
import { caricaVarianti, salvaVarianti, etichettaTab } from "./varianti-state.js";
import { differenzeCampi, unioneVerifiche, checkPer, deltaRelativo, sameValue } from "./varianti-diff.js";
import { apriTieniDialog } from "./varianti-tieni.js";

function verdictWordOf(report) {
  if (!report) return "! Errore";
  const checks = report.checks || [];
  if (checks.length === 0) return report.ok ? "✓ Calcolo eseguito" : "✕ Non verificato";
  const failing = checks.filter((c) => !c.passed).length;
  return failing === 0 ? "✓ Verificato" : `✕ ${failing} non soddisfatte`;
}

function highlightPairsOf(outputNodes, data) {
  const { matched } = extractByPredicate(outputNodes, (node) => node.kind === "scalar" && node.highlight);
  return matched.map((node) => ({ node, value: readPath(data, node.path) })).filter((pair) => pair.value !== null && pair.value !== undefined);
}

function everyScalarOf(outputNodes, data) {
  const { matched } = extractByPredicate(outputNodes, (node) => node.kind === "scalar");
  return matched.map((node) => ({ node, value: readPath(data, node.path) }));
}

export async function renderVariantiConfronto(root, { tool, owner }) {
  if (root._smOwner !== owner) return;
  clear(root);
  let set = caricaVarianti(tool);
  if (!set) {
    root.append(
      el("h2", { text: "Confronto varianti" }),
      el("p", { text: "Nessuna variante aperta per questo strumento." }),
      el("a", { href: `#/${tool}`, text: "Torna al calcolo" }),
    );
    return;
  }

  let schema;
  try {
    schema = await fetchSchema(tool);
  } catch (error) {
    if (root._smOwner !== owner) return;
    root.append(el("p", { text: "Impossibile caricare lo strumento." }));
    return;
  }
  if (root._smOwner !== owner) return;

  const fields = describeFields(schema.input || {});
  const outputNodes = describeOutput(schema.output || {});
  let mostraTuttiRisultati = false;
  let mostraTuttiDati = false;
  let riferimentoId = set.varianti[0].id;
  const reportsById = new Map(); // id -> {report, error}

  root.append(
    el("h2", { text: `Confronto varianti — ${schema.title || tool}` }),
    el("a", { href: `#/${tool}`, class: "vc-torna", text: "← Torna al calcolo" }),
  );
  const table = el("table", { class: "vc-table", tabindex: "0", "aria-label": "Confronto varianti" });
  root.append(el("div", { class: "r-table-scroll" }, [table]));

  function reportOf(id) {
    return (reportsById.get(id) || {}).report || null;
  }

  async function runOne(variante, colEl) {
    colEl.setAttribute("aria-busy", "true");
    try {
      const { report } = await runTool(tool, variante.inputs);
      reportsById.set(variante.id, { report, error: null });
    } catch (error) {
      reportsById.set(variante.id, { report: null, error: "Impossibile eseguire il calcolo." });
    }
    colEl.setAttribute("aria-busy", "false");
  }

  function buildRefSelector() {
    const select = el("select", { "aria-label": "Confronta con" });
    for (const variante of set.varianti) {
      select.append(el("option", { value: variante.id, text: etichettaTab(variante), selected: variante.id === riferimentoId }));
    }
    select.addEventListener("change", () => {
      riferimentoId = select.value;
      render();
    });
    return el("div", { class: "vc-ref" }, [el("label", { text: "Confronta con " }), select]);
  }

  function deltaCell(value, refValue) {
    if (typeof value !== "number" || typeof refValue !== "number") return el("span", { text: "—" });
    const delta = deltaRelativo(value, refValue);
    if (!delta) return el("span", { text: "—" });
    return el("span", { class: `vc-delta vc-delta--${delta.simbolo === "▲" ? "up" : delta.simbolo === "▼" ? "down" : "eq"}`, text: delta.testo });
  }

  function buildHeadRow() {
    const tr = el("tr");
    tr.append(el("th", { scope: "col", text: "" }));
    for (const variante of set.varianti) {
      const nameInput = el("input", { type: "text", class: "vc-name-input", value: variante.nome, maxlength: "40", "aria-label": `Nome variante ${variante.id}` });
      nameInput.addEventListener("change", () => {
        set = { ...set, varianti: set.varianti.map((v) => (v.id === variante.id ? { ...v, nome: nameInput.value.trim() || v.id } : v)) };
        salvaVarianti(tool, set);
      });
      const originTxt = variante.origine ? `da ${variante.origine.nome || "elemento"}, rev. ${variante.origine.revisione}` : "";
      const teniBtn = el("button", { type: "button", class: "vc-tieni", text: "Tieni questa", onclick: () => apriTieniDialog({ tool, variante, report: reportOf(variante.id), outputNodes, fields }) });
      const th = el("th", { scope: "col", class: "vc-col-head" }, [
        nameInput,
        originTxt ? el("p", { class: "vc-origin", text: originTxt }) : document.createTextNode(""),
        teniBtn,
      ]);
      tr.append(th);
    }
    return tr;
  }

  function buildVerdictRow() {
    const tr = el("tr", { class: "vc-row-verdict" });
    tr.append(el("th", { scope: "row", text: "Esito" }));
    const refReport = reportOf(riferimentoId);
    for (const variante of set.varianti) {
      const info = reportsById.get(variante.id) || {};
      const report = info.report;
      const cell = el("td", {});
      if (info.error) {
        cell.append(el("span", { class: "vc-verdict-err", text: "! Errore" }), el("p", { class: "vc-error-msg", text: info.error }));
      } else if (report) {
        const checks = report.checks || [];
        const ok = checks.length === 0 ? Boolean(report.ok) : checks.every((c) => c.passed);
        cell.append(el("span", {}, [checkMark(ok)]), document.createTextNode(` ${verdictWordOf(report)}`));
        const governing = governingCheck(checks);
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
            const okRef = (refReport.checks || []).every((c) => c.passed);
            if (ok !== okRef) cell.append(el("p", { class: "vc-diff-flag", text: "≠ esito diverso" }));
          }
        }
      }
      tr.append(cell);
    }
    return tr;
  }

  function buildVerificheRows() {
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

  function buildRisultatiRows() {
    const refData = (reportOf(riferimentoId) || {}).data || {};
    const refHighlights = highlightPairsOf(outputNodes, refData);
    const pairsSets = set.varianti.map((v) => {
      const data = (reportOf(v.id) || {}).data || {};
      return mostraTuttiRisultati ? everyScalarOf(outputNodes, data) : highlightPairsOf(outputNodes, data);
    });
    const refPairs = mostraTuttiRisultati ? everyScalarOf(outputNodes, refData) : refHighlights;
    const rows = [];
    for (let i = 0; i < refPairs.length; i += 1) {
      const node = refPairs[i].node;
      const tr = el("tr");
      tr.append(el("th", { scope: "row", text: node.label }));
      pairsSets.forEach((pairs, colIndex) => {
        const pair = pairs.find((p) => p.node.path === node.path);
        const cell = el("td", {});
        if (!pair) {
          cell.append(el("span", { text: "—" }));
        } else {
          const { text } = formatValue(pair.value, pair.node);
          cell.append(document.createTextNode(`${text}${pair.node.unit && pair.node.unit !== "-" ? ` ${formatUnit(pair.node.unit)}` : ""}`));
          if (set.varianti[colIndex].id !== riferimentoId) cell.append(deltaCell(pair.value, refPairs[i].value));
        }
        tr.append(cell);
      });
      rows.push(tr);
    }
    return rows;
  }

  function buildDatiRows() {
    const differenze = differenzeCampi(fields, set.varianti);
    const daMostrare = mostraTuttiDati ? differenze : differenze.filter((voce) => voce.diverso);
    return daMostrare.map((voce) => {
      const tr = el("tr");
      tr.append(el("th", { scope: "row", text: voce.field ? voce.field.label : voce.nome }));
      const riferimentoValore = (set.varianti.find((v) => v.id === riferimentoId) || {}).inputs?.[voce.nome];
      for (const variante of set.varianti) {
        const valore = variante.inputs ? variante.inputs[voce.nome] : undefined;
        const cell = el("td", {});
        if (voce.dettaglio) {
          cell.append(el("span", { text: `tabella: ${voce.dettaglio.diverse} righe diverse su ${voce.dettaglio.totale}` }));
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

  function sectionHead(text) {
    const tr = el("tr", { class: "vc-section" });
    const th = el("th", { colspan: String(set.varianti.length + 1), text });
    tr.append(th);
    return tr;
  }

  function render() {
    clear(table);
    const conta = differenzeCampi(fields, set.varianti).filter((v) => v.diverso).length;
    const totale = fields.length;
    table.append(el("caption", { class: "vc-caption" }, [el("span", { text: `Variante ${set.varianti.findIndex((v) => v.id === set.attiva) + 1} di ${set.varianti.length}` })]));
    const thead = el("thead", {}, [buildHeadRow()]);
    const tbody = el("tbody", {}, [
      buildVerdictRow(),
      sectionHead("Verifiche"),
      ...buildVerificheRows(),
      sectionHead("Risultati"),
      ...buildRisultatiRows(),
      sectionHead(`Dati diversi: ${conta} di ${totale}`),
      ...buildDatiRows(),
    ]);
    table.append(thead, tbody);
  }

  root.insertBefore(buildRefSelector(), table.parentElement);
  const toggleRisultati = el("button", { type: "button", class: "vc-toggle", text: mostraTuttiRisultati ? "Nascondi risultati" : "Mostra tutti i risultati", onclick: () => {
    mostraTuttiRisultati = !mostraTuttiRisultati;
    toggleRisultati.textContent = mostraTuttiRisultati ? "Nascondi risultati" : "Mostra tutti i risultati";
    render();
  } });
  const toggleDati = el("button", { type: "button", class: "vc-toggle", text: mostraTuttiDati ? "Nascondi dati uguali" : "Mostra tutti i dati", onclick: () => {
    mostraTuttiDati = !mostraTuttiDati;
    toggleDati.textContent = mostraTuttiDati ? "Nascondi dati uguali" : "Mostra tutti i dati";
    render();
  } });
  root.insertBefore(el("div", { class: "vc-toggles" }, [toggleRisultati, toggleDati]), table.parentElement);

  render();
  for (const variante of set.varianti) {
    if (root._smOwner !== owner) return;
    const colIndex = set.varianti.findIndex((v) => v.id === variante.id) + 1;
    const colEl = table.querySelector(`thead tr th:nth-child(${colIndex + 1})`) || table;
    await runOne(variante, colEl);
    if (root._smOwner !== owner) return;
    render();
  }

  document.addEventListener("keydown", function onKeydown(event) {
    if (event.key !== "Escape") return;
    document.removeEventListener("keydown", onKeydown);
    navigate(tool);
  });
}
