// The entry's second part in the same Dati column -- WORKBENCH_SPEC §27.3 "optional part". The
// visible part keeps the full single-tool page (js/forms.js and everything mounted on it); this
// module renders the OTHER part's own sections under a heading with its name (shared common data
// are not repeated), keeps its values in the same per-tool storage the single-tool page uses
// (`sm.inputs.<tool>`) and runs it live through the same `POST /api/tools/<name>/run`, so its
// last report is ready when its result tab is shown. Field names are prefixed in the DOM
// (js/voce-comuni.js) because both forms live in one document.
import { el, clear } from "./dom.js";
import { fetchSchema, runTool } from "./api.js";
import { describeFields } from "./schema.js";
import { buildField, setValue, setFieldError } from "./fields.js";
import { groupFields, visibleValues, applyConditions } from "./forms-sections.js";
import { buildSections } from "./form-sections-summary.js";
import { validateValues } from "./validate.js";
import { load, save } from "./form-state.js";
import { isLiveEnabled } from "./live.js";
import { campiCompagno, prefissaCampi, senzaPrefisso } from "./voce-comuni.js";

const PREFISSO = "vo__";
const DEBOUNCE_MS = 300;

function valoreIniziale(field, valori) {
  if (field.name in valori && valori[field.name] !== undefined) return valori[field.name];
  return field.default !== undefined ? field.default : null;
}

// `{ host, voce, parte, staccati, onDecora }` -> handle. `onDecora(form)` lets js/voce.js add the
// "comune alla voce" chips to a detached common field shown here.
export async function montaCompagno({ host, voce, parte, staccati, onDecora }) {
  const schema = await fetchSchema(parte.tool);
  const tutti = describeFields(schema.input || {});
  const mostrati = prefissaCampi(campiCompagno(voce, tutti, staccati), PREFISSO);
  const defaults = Object.fromEntries(tutti.filter((f) => f.default !== undefined).map((f) => [f.name, f.default]));
  let valori = { ...defaults, ...(load(parte.tool) || {}) };
  let report = null;
  let timer = null;
  let inCorso = Promise.resolve();

  clear(host);
  const titoloId = `voce-compagno-titolo`;
  const form = el("form", { class: "f-form vo-compagno-form", id: "voce-compagno-form", novalidate: true, "aria-labelledby": titoloId });
  const { sections, advanced } = groupFields(mostrati);
  const sectionsApi = buildSections(sections, `voce.${parte.tool}`);
  form.append(...sectionsApi.elements);
  if (advanced.length > 0) {
    const details = el("details", { class: "f-section f-advanced" }, [el("summary", { text: "Avanzate" })]);
    advanced.forEach((field) => details.append(buildField(field)));
    form.append(details);
  }
  const errore = el("p", { class: "vo-errore", hidden: true });
  host.append(el("h3", { class: "vo-parte-titolo", id: titoloId, text: `${parte.titolo}: dati` }), form, errore);
  mostrati.forEach((field) => setValue(form, field, valoreIniziale({ ...field, name: field.name.slice(PREFISSO.length) }, valori)));
  applyConditions(form, mostrati);
  sectionsApi.refresh(visibleValues(form, mostrati), {});
  if (onDecora) onDecora(form, PREFISSO);

  // The exact payload the single-tool page would send: every field of the tool, own fields from
  // this form, shared ones from the stored values.
  function payload() {
    const propri = senzaPrefisso(visibleValues(form, mostrati), PREFISSO);
    return Object.fromEntries(tutti.map((field) => [field.name, field.name in propri ? propri[field.name] : valoreIniziale(field, valori)]));
  }

  // `silenzioso`: the first check on mount paints no errors -- same "no error noise on a form
  // nobody has touched yet" rule as js/forms.js.
  function valida({ silenzioso = false } = {}) {
    const errori = validateValues(mostrati, visibleValues(form, mostrati));
    if (silenzioso) return Object.keys(errori).length === 0;
    mostrati.forEach((field) => setFieldError(form, field.name, errori[field.name] || null));
    sectionsApi.refresh(visibleValues(form, mostrati), errori);
    return Object.keys(errori).length === 0;
  }

  async function esegui() {
    timer = null;
    const inputs = payload();
    const corrente = runTool(parte.tool, inputs).then(({ report: nuovo }) => {
      report = nuovo;
      errore.hidden = Boolean(nuovo && nuovo.ok);
      errore.textContent = nuovo && !nuovo.ok ? `${parte.titolo}: ${(nuovo.errors || ["errore di calcolo."])[0]}` : "";
    }).catch(() => {
      errore.hidden = false;
      errore.textContent = `${parte.titolo}: impossibile contattare il server.`;
    });
    inCorso = corrente;
    await corrente;
  }

  function programma({ subito = false, silenzioso = false } = {}) {
    if (timer != null) clearTimeout(timer);
    if (!valida({ silenzioso })) return;
    valori = { ...valori, ...payload() };
    save(parte.tool, valori, tutti);
    if (subito) esegui();
    else if (isLiveEnabled(valori)) timer = setTimeout(esegui, DEBOUNCE_MS);
  }

  form.addEventListener("input", () => { applyConditions(form, mostrati); programma(); });
  form.addEventListener("change", () => { applyConditions(form, mostrati); programma(); });
  form.addEventListener("submit", (event) => event.preventDefault());

  return {
    tool: parte.tool,
    form,
    output: schema.output,
    valori: () => payload(),
    report: () => report,
    // Waits for the debounce and the run in flight, so a save stores the report of these inputs.
    async assestato() {
      if (timer != null) {
        clearTimeout(timer);
        await esegui();
      }
      await inCorso;
    },
    imposta(nuovi) {
      valori = { ...valori, ...nuovi };
      mostrati.forEach((field) => {
        const nome = field.name.slice(PREFISSO.length);
        if (nome in nuovi) setValue(form, field, nuovi[nome]);
      });
      applyConditions(form, mostrati);
      programma();
    },
    esegui: () => programma({ subito: true, silenzioso: true }),
    smonta() {
      if (timer != null) clearTimeout(timer);
      clear(host);
    },
  };
}
