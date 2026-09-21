// "Sviluppo dei calcoli" print section (docs/architecture-phase2.md §5, extends WORKBENCH_SPEC
// §10/§11): one block per `Traccia`, one equation group per `Passo` -- the symbolic formula (with
// its clause right-aligned in muted ink), the substitution, and the result (unit, or a check's
// outcome as icon + word). Composes `js/relazione-formule.js`'s three line builders; owns only the
// per-Passo/per-Traccia LAYOUT and the "trace unavailable" fallback sentence.
import { el } from "./dom.js";
import { checkMark } from "./verdict.js";
import { formatUnit } from "./format.js";
import { buildFormulaLine, buildSubstitutionLine, buildResultLine } from "./relazione-formule.js";

// Verbatim (docs/architecture-phase2.md §1 / src/strutture/shared/tool.py): a failing trace or an
// Excel-mode run never carries a `relazione`, only one of these two Italian warnings -- printed in
// place of the section itself (task brief: "print that sentence instead of the section").
const AVVISO_RELAZIONE_NON_DISPONIBILE = "Sviluppo dei calcoli non disponibile per questi dati.";
const AVVISO_RELAZIONE_MODALITA_EXCEL = "Lo sviluppo dei calcoli descrive la modalità standard: non è disponibile in modalità Excel.";
const AVVISI_SVILUPPO_ASSENTE = [AVVISO_RELAZIONE_NON_DISPONIBILE, AVVISO_RELAZIONE_MODALITA_EXCEL];

function buildClausola(passo) {
  return passo.clausola ? el("span", { class: "r-passo-clausola", text: passo.clausola }) : null;
}

// The dimensionless unit "-" is never printed (docs/architecture-phase2.md §3); a check step's
// result already carries its own comparison + esito, no separate unit suffix.
function buildUnitaSuffix(passo) {
  if (passo.esito || !passo.unita || passo.unita === "-") return null;
  return el("span", { class: "r-passo-unita", text: ` ${formatUnit(passo.unita)}` });
}

function buildEsito(passo) {
  if (!passo.esito) return null;
  const soddisfatta = passo.esito === "soddisfatta";
  return el("span", { class: `r-passo-esito ${soddisfatta ? "r-passo-esito--ok" : "r-passo-esito--ko"}` }, [
    checkMark(soddisfatta),
    el("span", { class: "r-passo-esito-word", text: passo.esito }),
  ]);
}

function buildPassoNode(passo) {
  const righeFormula = [buildFormulaLine(passo), buildClausola(passo)].filter(Boolean);
  const righeRisultato = [buildResultLine(passo), buildUnitaSuffix(passo), buildEsito(passo)].filter(Boolean);
  const children = [
    el("div", { class: "r-passo-riga r-passo-riga--formula" }, righeFormula),
    el("div", { class: "r-passo-riga r-passo-riga--sostituzione" }, [buildSubstitutionLine(passo)]),
    el("div", { class: "r-passo-riga r-passo-riga--risultato" }, righeRisultato),
  ];
  if (passo.nota) children.push(el("p", { class: "r-passo-nota", text: passo.nota }));
  return el("div", { class: "r-passo" }, children);
}

function buildTracciaNode(traccia) {
  const body = el("div", { class: "r-group-body" });
  for (const passo of traccia.passi) body.append(buildPassoNode(passo));
  return el("section", { class: "r-group r-group--print r-traccia" }, [
    el("h3", { class: "r-group-title", text: traccia.titolo }),
    body,
  ]);
}

function buildHeading() {
  return el("h2", { text: "Sviluppo dei calcoli" });
}

// `tracce` = `report.relazione` (may be empty), `warnings` = `report.warnings`. Returns `null`
// when there is nothing to show at all (the tool never offers a trace and this run carries neither
// of the two "non disponibile" sentences) -- the caller then appends nothing, same as an empty
// Schizzo section.
export function buildSviluppoSection(tracce, warnings) {
  if (tracce && tracce.length > 0) {
    const container = el("div", { class: "r-sviluppo" }, [buildHeading()]);
    for (const traccia of tracce) container.append(buildTracciaNode(traccia));
    return container;
  }
  const assente = (warnings || []).find((messaggio) => AVVISI_SVILUPPO_ASSENTE.includes(messaggio));
  if (!assente) return null;
  return el("div", { class: "r-sviluppo" }, [buildHeading(), el("p", { class: "r-sviluppo-assente", text: assente })]);
}
