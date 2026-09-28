// Entry page ("voce unica") -- WORKBENCH_SPEC §27. One screen per rail entry: the VISIBLE part is
// the complete single-tool page (js/forms.js, results, print, save, variants... all per tool,
// exactly as today, driven by main.js's own `selectTool`), and this module adds around it:
// - the optional part's checkbox (§27.3) and, when ticked, the other part's own sections
//   (js/voce-compagno.js) plus the result tabs (js/voce-schede.js) that choose the visible part;
// - the common data (§27.4): an edit in the visible part is written into the other part
//   (js/voce-comuni.js), with the "comune alla voce" chip and "Stacca"/"Ricollega" (js/voce-chip.js);
// - the two-element save of §27.7 (js/voce-elementi.js).
// Nothing here changes a run: each part is sent through `POST /api/tools/<name>/run` with the
// payload its own single-tool page would send (§27.1).
import { el } from "./dom.js";
import { readJSON, writeJSON } from "./storage.js";
import { load, save } from "./form-state.js";
import { navigate } from "./router.js";
import { indirizzoVoce, parteDi } from "./voci.js";
import { propaga, stacca, ricollega, valoreDaRicollegare } from "./voce-comuni.js";
import { decoraComuni } from "./voce-chip.js";
import { renderSchede } from "./voce-schede.js";
import { azzeraElementi, impostaCompagno } from "./voce-elementi.js";

let sessione = null; // { voce, attiva, stato, selezionaParte, compagno, token }
let contatore = 0;

function chiaveStato(voce) {
  return `sm.ui.voce.${voce.slug}`;
}

function leggiStato(voce) {
  const salvato = readJSON(chiaveStato(voce), null);
  const stato = salvato && typeof salvato === "object" ? salvato : {};
  return { opzionale: Boolean(stato.opzionale), staccati: stato.staccati && typeof stato.staccati === "object" ? stato.staccati : {} };
}

function aggiornaStato(modifiche) {
  sessione = { ...sessione, stato: { ...sessione.stato, ...modifiche } };
  writeJSON(chiaveStato(sessione.voce), sessione.stato);
}

function opzionale(voce) {
  return voce.parti.find((parte) => parte.casella) || null;
}

function altraParte() {
  return sessione.voce.parti.find((parte) => parte.tool !== sessione.attiva);
}

function nodo(id, crea) {
  return document.getElementById(id) || crea();
}

async function moduloForms() {
  return import("./forms.js");
}

// -- DOM around the single-tool page -------------------------------------------------------------

function preparaDom() {
  const formRoot = document.getElementById("form-root");
  const resultsPane = document.getElementById("results-pane");
  const sintesi = document.getElementById("sintesi");
  if (!formRoot || !resultsPane || !sintesi) return;
  const { voce, attiva, stato } = sessione;
  const parteOpz = opzionale(voce);
  const barra = nodo("voce-bar", () => el("div", { id: "voce-bar", class: "vo-barra" }));
  barra.replaceChildren();
  if (parteOpz) {
    const casella = el("input", { type: "checkbox", id: "voce-opzionale", checked: stato.opzionale });
    casella.addEventListener("change", () => cambiaOpzionale(casella.checked));
    barra.append(el("label", { class: "vo-casella", for: "voce-opzionale" }, [casella, ` ${parteOpz.casella}`]));
  }
  const titolo = nodo("voce-titolo-attiva", () => el("h3", { id: "voce-titolo-attiva", class: "vo-parte-titolo" }));
  const mostrata = parteDi(voce, attiva);
  titolo.textContent = `${mostrata.titolo}: dati`;
  titolo.hidden = !stato.opzionale;
  const compagno = nodo("voce-compagno", () => el("section", { id: "voce-compagno", class: "vo-compagno", "aria-labelledby": "voce-compagno-titolo" }));
  compagno.hidden = !stato.opzionale;
  // Fixed reading order: first part above, second below, whichever one is visible.
  const primaVisibile = voce.parti[0].tool === attiva;
  formRoot.before(barra);
  if (primaVisibile) {
    formRoot.before(titolo);
    formRoot.after(compagno);
  } else {
    formRoot.before(compagno);
    formRoot.before(titolo);
  }
  const schede = nodo("voce-schede", () => el("div", { id: "voce-schede", class: "vo-schede" }));
  sintesi.before(schede);
  schede.hidden = !stato.opzionale;
  renderSchede(schede, { parti: voce.parti, attiva, onScegli: scegliParte });
}

function smontaDom() {
  ["voce-bar", "voce-titolo-attiva", "voce-compagno", "voce-schede"].forEach((id) => {
    const node = document.getElementById(id);
    if (node) node.remove();
  });
}

// -- the visible part ----------------------------------------------------------------------------

// The page can be left while any of the awaits below is pending: every async step re-checks
// `sessione` (null once js/main.js has called `smontaVoce`) before touching it.
async function valoriAttivi() {
  const attiva = sessione && sessione.attiva;
  const { current } = await moduloForms();
  if (!attiva) return {};
  return current.api && current.tool === attiva ? current.api.values() : load(attiva) || {};
}

async function decoraAttiva() {
  const form = document.getElementById("tool-form");
  if (!form || !sessione) return;
  decoraComuni(form, { voce: sessione.voce, staccati: sessione.stato.staccati, onStacca: (campo) => staccaCampo(sessione.attiva, campo), onRicollega: (campo) => ricollegaCampo(sessione.attiva, campo) });
}

async function eseguiAttiva() {
  const [{ current }, { requestRun }, { validateValues }] = await Promise.all([moduloForms(), import("./live.js"), import("./validate.js")]);
  if (!sessione || !current.api || current.tool !== sessione.attiva) return;
  const values = current.api.values();
  if (Object.keys(validateValues(current.fields, values)).length === 0) requestRun(current.tool, values, "live");
}

// -- the other part ------------------------------------------------------------------------------

function smontaCompagno() {
  if (sessione && sessione.compagno) sessione.compagno.smonta();
  if (sessione) sessione = { ...sessione, compagno: null };
  impostaCompagno(null);
}

async function montaAltra(token) {
  const host = document.getElementById("voce-compagno");
  if (!host || !sessione) return;
  const parte = altraParte();
  const { montaCompagno } = await import("./voce-compagno.js");
  if (token !== sessione?.token) return;
  const { voce, stato } = sessione;
  const handle = await montaCompagno({
    host,
    voce,
    parte,
    staccati: stato.staccati,
    onDecora: (form, prefisso) => decoraComuni(form, { voce, staccati: stato.staccati, prefisso, onStacca: (campo) => staccaCampo(parte.tool, campo), onRicollega: (campo) => ricollegaCampo(parte.tool, campo) }),
  });
  if (token !== sessione?.token) {
    handle.smonta();
    return;
  }
  sessione = { ...sessione, compagno: handle };
  registraCompagno(handle, parte);
  handle.esegui(); // its report is ready when its result tab is shown / the pair is saved
}

function registraCompagno(handle, parte) {
  const indice = (tool) => sessione.voce.parti.findIndex((p) => p.tool === tool) + 1;
  impostaCompagno({
    attiva: sessione.attiva,
    tool: parte.tool,
    titolo: parte.titolo,
    indiceAttiva: indice(sessione.attiva),
    indice: indice(parte.tool),
    payload: async (nome, sigla, nota) => {
      const [{ computeSintesiEStato }, { describeOutput }, { buildElementoPayload }] = await Promise.all([
        import("./elemento-sintesi.js"), import("./output-schema.js"), import("./elemento-salva.js"),
      ]);
      await handle.assestato();
      const reportTool = { name: parte.tool, outputNodes: describeOutput(handle.output) };
      const { sintesi, stato } = computeSintesiEStato(parte.tool, { report: handle.report(), reportTool, stale: false });
      return buildElementoPayload({ tool: parte.tool, values: handle.valori(), sintesi, stato, nome, provenienza: {}, sigla, nota });
    },
  });
}

// -- common data ---------------------------------------------------------------------------------

function valoriDelleAltre() {
  return Object.fromEntries(
    sessione.voce.parti
      .filter((parte) => parte.tool !== sessione.attiva)
      .map((parte) => [parte.tool, sessione.compagno && sessione.compagno.tool === parte.tool ? sessione.compagno.valori() : load(parte.tool) || {}]),
  );
}

function propagaDa(values) {
  if (!sessione) return;
  const { voce, attiva, stato, compagno } = sessione;
  const nuovi = propaga(voce, attiva, values, stato.staccati, valoriDelleAltre());
  for (const [tool, valori] of Object.entries(nuovi)) {
    if (compagno && compagno.tool === tool) compagno.imposta(valori);
    else save(tool, valori);
  }
}

function suCambioAttiva(event) {
  const detail = event.detail || {};
  if (!sessione || detail.name !== sessione.attiva || detail.valid === false || !detail.values) return;
  propagaDa(detail.values);
}

document.addEventListener("strutture:inputs-changed", suCambioAttiva);
document.addEventListener("strutture:run-request", suCambioAttiva);

async function rimontaAltra() {
  if (!sessione) return;
  smontaCompagno();
  if (sessione.stato.opzionale) await montaAltra(sessione.token);
}

async function staccaCampo(tool, campo) {
  if (!sessione) return;
  aggiornaStato({ staccati: stacca(sessione.stato.staccati, tool, campo) });
  await decoraAttiva();
  await rimontaAltra();
}

async function ricollegaCampo(tool, campo) {
  if (!sessione) return;
  const valoriDi = { ...valoriDelleAltre(), [sessione.attiva]: await valoriAttivi() };
  const valore = valoreDaRicollegare(sessione.voce, tool, campo, valoriDi);
  if (!sessione) return;
  aggiornaStato({ staccati: ricollega(sessione.stato.staccati, campo) });
  if (tool === sessione.attiva && valore !== undefined) {
    const { current } = await moduloForms();
    if (current.api) {
      current.api.setValues({ ...current.api.allValues(), [campo]: valore });
      const form = document.getElementById("tool-form");
      if (form) form.dispatchEvent(new Event("change", { bubbles: true })); // save + live run, as a typed edit
    }
  } else if (sessione.compagno && valore !== undefined) {
    sessione.compagno.imposta({ [campo]: valore });
  }
  await decoraAttiva();
  await rimontaAltra();
}

// -- page lifecycle ------------------------------------------------------------------------------

async function rendi(params) {
  const token = ++contatore;
  sessione = { ...sessione, token };
  smontaCompagno();
  preparaDom();
  await sessione.selezionaParte(sessione.attiva, params);
  if (token !== sessione?.token) return;
  await decoraAttiva();
  if (sessione.stato.opzionale) {
    const valori = await valoriAttivi();
    if (token !== sessione?.token) return;
    propagaDa(valori);
    await montaAltra(token);
  }
}

async function scegliParte(tool) {
  if (!sessione || tool === sessione.attiva) return;
  const focusNelleSchede = Boolean(document.activeElement && document.activeElement.closest("#voce-schede"));
  sessione = { ...sessione, attiva: tool };
  const { path, params } = indirizzoVoce(sessione.voce, tool);
  navigate(path, params, { replace: true });
  await rendi({});
  if (!sessione) return;
  await eseguiAttiva();
  if (focusNelleSchede) {
    const scheda = document.getElementById(`voce-scheda-${tool}`);
    if (scheda) scheda.focus();
  }
}

async function cambiaOpzionale(spuntata) {
  aggiornaStato({ opzionale: spuntata });
  const parteOpz = opzionale(sessione.voce);
  if (!spuntata && parteOpz && sessione.attiva === parteOpz.tool) {
    await scegliParte(sessione.voce.predefinita);
    return;
  }
  preparaDom();
  smontaCompagno();
  if (spuntata) {
    const valori = await valoriAttivi();
    if (!sessione) return;
    propagaDa(valori);
    await montaAltra(sessione.token);
  }
}

// `selezionaParte(tool, params)` = main.js's own `selectTool`. Every route into an entry is a
// fresh start (a remembered element belongs to the tab switches of ONE visit).
export async function mostraVoce({ voce, parte, params, selezionaParte }) {
  azzeraElementi(true);
  const precedente = sessione;
  if (precedente && precedente.compagno) precedente.compagno.smonta();
  let stato = leggiStato(voce);
  const parteOpz = opzionale(voce);
  if (parteOpz && parte === parteOpz.tool && !stato.opzionale) {
    stato = { ...stato, opzionale: true }; // §27.3: ticked when a link/element of the optional tool opens
    writeJSON(chiaveStato(voce), stato);
  }
  sessione = { voce, attiva: parte, stato, selezionaParte, compagno: null, token: 0 };
  await rendi(params);
}

export function smontaVoce() {
  if (!sessione) return;
  smontaCompagno();
  smontaDom();
  sessione = null;
  azzeraElementi(false);
}
