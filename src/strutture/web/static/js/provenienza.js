// "Usa in..." consumer-side prefill (WORKBENCH_SPEC §15) + provenance tracking for "da
// ricalcolare" (§25.1). When a tool page is reached via `?da=<provider>&<chiave>=<valore>&...`
// (js/usa-in.js builds that link, adding `&da_elemento=&da_revisione=` when the provider is a
// saved, unmodified element) every field whose `accepts` hint matches one of those chiave keys is
// prefilled from the query BEFORE the initial run, gets a "da <SIGLA>" chip next to its label, and
// a dismissible note under the tool title names the provider. Editing a prefilled field clears its
// own chip. `accepts` is read straight off the RAW input schema (`resolveProperty`,
// json-schema.js) rather than through schema.js's own flattened Field -- only this one feature
// needs it, so schema.js's shared contract stays untouched. Mounted directly by js/forms.js's
// `renderForm` (a plain function call, exactly like js/elemento-salva.js's `mountElementoSalva`)
// so the prefill always lands before live.js's first run for this page.
//
// §25.1 "new shape": each tracked item is `{chiave, strumento, percorso, ingresso, valore,
// elemento_id?, revisione_fornitore?}` -- `percorso`/`ingresso` come from the SAME collegamenti
// registry js/usa-in.js already fetches (`ensureCollegamenti`), `valore` is the exact value
// copied into the consumer field. `elemento_id`/`revisione_fornitore` are present only when
// usa-in.js added `da_elemento`/`da_revisione` to the query (provider was a saved, unmodified
// element at link time). On `?elemento=<id>` load, `reconstructProvenienza` rebuilds the session
// from the element's OWN saved `provenienza.collegamenti`: an item whose consumer field still
// holds exactly its saved `valore` gets its chip restored; one that was hand-edited since the
// save is dropped, same as an ordinary edit would do. `activeProvenienza(tool)` is the union of
// still-valid restored items and any prefilled in this session -- no save ever clears the
// provenance of an item the user did not touch.
import { el, clear } from "./dom.js";
import { resolveProperty } from "./json-schema.js";
import { fetchTools } from "./api.js";
import { ensureCollegamenti } from "./collegamenti-api.js";
import { save } from "./form-state.js";
import { requestRun } from "./live.js";
import { azzeraStoriaAnnulla } from "./annulla-ui.js";

// `{tool, chips: Map<fieldName, {chiave, strumento, percorso, ingresso, valore, elementoId?,
// revisioneFornitore?}>}` -- `chips` holds only the fields whose tracked value has NOT been
// edited since; js/elemento-salva.js's `currentPayload` reads this via `activeProvenienza` to
// decide `provenienza.collegamenti`.
let session = { tool: null, chips: new Map() };

function acceptsMap(inputSchema, fields) {
  const properties = (inputSchema && inputSchema.properties) || {};
  const map = new Map();
  for (const field of fields) {
    const raw = properties[field.name];
    if (!raw) continue;
    const resolved = resolveProperty(inputSchema, raw);
    if (resolved.accepts) map.set(field.name, resolved.accepts);
  }
  return map;
}

// Only number/enum fields are ever provenance-linked (src/strutture/shared/collegamenti.py's own
// registry never declares `accepts` on any other kind) -- `undefined` means "ignore this key".
function parseValue(field, raw) {
  if (field.kind === "number") {
    const value = Number(raw);
    return Number.isNaN(value) ? undefined : value;
  }
  if (field.kind === "enum") {
    return (field.enumValues || []).find((candidate) => String(candidate) === raw);
  }
  return undefined;
}

// Numbers compare with a tolerance (query-string round-tripping, JSON round-tripping), everything
// else exactly -- the same discipline the backend's own §25.1 comparison uses for its own values.
function sameValue(a, b) {
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
  return a === b;
}

function insertChip(toolForm, fieldName, chipEl) {
  const wrapper = toolForm.querySelector(`.f-field[data-field="${fieldName}"]`);
  const labelCell = wrapper && (wrapper.querySelector(".f-field-labelcell") || wrapper.querySelector(".f-field-row"));
  if (labelCell) labelCell.append(chipEl);
}

function removeChip(toolForm, fieldName) {
  const wrapper = toolForm.querySelector(`.f-field[data-field="${fieldName}"]`);
  const chip = wrapper && wrapper.querySelector(".pv-chip");
  if (chip) chip.remove();
}

function buildNoteContent(note, providerTitle, providerName, count) {
  clear(note);
  note.append(
    el("span", { text: `Dati ricevuti da ${providerTitle}: ${count} camp${count === 1 ? "o" : "i"}. ` }),
    el("a", { class: "pv-note-link", href: `#/${encodeURIComponent(providerName)}`, text: providerTitle }),
    document.createTextNode(" "),
    el("button", { type: "button", class: "pv-note-close", text: "Chiudi", onclick: () => { note.hidden = true; } }),
  );
}

// `percorso`/`ingresso` for `chiave` as supplied by `strumento` (§25.1's shape) -- `undefined`
// when the registry has not resolved yet or the pair is not a real fornitore (should not happen
// for a `chiave` that reached us via `?da=`/a saved `provenienza`, but this stays defensive).
async function fornitoreInfo(chiave, strumento) {
  try {
    const registry = await ensureCollegamenti();
    const link = registry.chiavi[chiave];
    const fornitore = link && link.fornitori.find((f) => f.strumento === strumento);
    return fornitore ? { percorso: fornitore.percorso, ingresso: fornitore.ingresso } : undefined;
  } catch (error) {
    return undefined;
  }
}

export function mountProvenienza({ toolForm, tool, fields, params, input, getApi }) {
  const note = el("p", { class: "pv-note" });
  note.hidden = true;
  session = { tool, chips: new Map() };

  async function applyFromParams() {
    if (!params || !params.da) return;
    const map = acceptsMap(input, fields);
    const toApply = new Map(); // fieldName -> {value, chiave}
    for (const [fieldName, chiave] of map) {
      if (!(chiave in params)) continue;
      const field = fields.find((candidate) => candidate.name === fieldName);
      if (!field) continue;
      const value = parseValue(field, params[chiave]);
      if (value === undefined) continue;
      toApply.set(fieldName, { value, chiave });
    }
    if (toApply.size === 0) return;
    // Let renderForm finish assigning `api` (still a few statements away, js/forms.js) -- same
    // temporal-dead-zone wait js/elemento-salva.js's own `loadElementoFromParams` uses.
    await Promise.resolve();
    const api = getApi();
    if (!api) return;
    const nextValues = { ...api.values() };
    for (const [fieldName, { value }] of toApply) nextValues[fieldName] = value;
    api.setValues(nextValues);
    azzeraStoriaAnnulla(); // WORKBENCH_SPEC §21.1: a "Usa in…" arrival is a history boundary

    let providerTitle = params.da;
    let providerSigla = "?";
    try {
      const tools = await fetchTools();
      const providerTool = tools.find((candidate) => candidate.name === params.da);
      if (providerTool) {
        providerTitle = providerTool.title;
        providerSigla = providerTool.sigla;
      }
    } catch (error) {
      // provider title/sigla fall back to the raw tool name / "?" -- the prefill already happened
    }

    const elementoId = params.da_elemento || undefined;
    const revisioneFornitore = elementoId && params.da_revisione ? Number(params.da_revisione) : undefined;
    const nextChips = new Map();
    for (const [fieldName, { chiave, value }] of toApply) {
      const info = await fornitoreInfo(chiave, params.da);
      nextChips.set(fieldName, {
        chiave, strumento: params.da, valore: value,
        percorso: info ? info.percorso : "", ingresso: info ? info.ingresso : true,
        elementoId, revisioneFornitore,
      });
    }
    session = { tool, chips: nextChips };
    for (const [fieldName, { chiave, valore }] of nextChips) {
      const title = `Valore preso da ${providerTitle}: ${chiave} = ${valore}`;
      insertChip(toolForm, fieldName, el("span", { class: "pv-chip", title, text: `da ${providerSigla}` }));
    }
    buildNoteContent(note, providerTitle, params.da, nextChips.size);
    note.hidden = false;

    const values = api.values();
    save(tool, values, fields);
    requestRun(tool, values, "manual");
  }

  applyFromParams();

  function handleEdit(event) {
    const wrapper = event.target.closest(".f-field");
    if (!wrapper || session.tool !== tool) return;
    const name = wrapper.dataset.field;
    if (!session.chips.has(name)) return;
    const nextChips = new Map(session.chips);
    nextChips.delete(name);
    session = { ...session, chips: nextChips };
    removeChip(toolForm, name);
  }
  toolForm.addEventListener("input", handleEdit);
  toolForm.addEventListener("change", handleEdit);

  return note;
}

// WORKBENCH_SPEC §25.1 "reconstruction on open": called by js/elemento-salva.js right after an
// `?elemento=<id>` load fills the form. `provenienza` is the loaded element's own saved
// `{collegamenti: [...]}` (old-shape items, with no `percorso`/`valore`, are skipped -- "elements
// saved before this change lack it"). Restores a "da <sigla>" chip for every item whose field
// STILL holds exactly its saved `valore`; a hand-edited field is silently dropped, as an ordinary
// edit would do.
export async function reconstructProvenienza({ toolForm, tool, fields, input, values, provenienza }) {
  const collegamenti = (provenienza && Array.isArray(provenienza.collegamenti) ? provenienza.collegamenti : [])
    .filter((item) => item && typeof item === "object" && "valore" in item && "percorso" in item);
  if (collegamenti.length === 0) return;
  const map = acceptsMap(input, fields);
  const byChiave = new Map(Array.from(map, ([fieldName, chiave]) => [chiave, fieldName]));
  let tools = [];
  try {
    tools = await fetchTools();
  } catch (error) {
    tools = [];
  }
  const nextChips = session.tool === tool ? new Map(session.chips) : new Map();
  const byProvider = new Map(); // providerName -> {title, sigla, count}
  for (const item of collegamenti) {
    const fieldName = byChiave.get(item.chiave);
    if (!fieldName || !sameValue(values[fieldName], item.valore)) continue;
    nextChips.set(fieldName, {
      chiave: item.chiave, strumento: item.strumento, valore: item.valore,
      percorso: item.percorso, ingresso: Boolean(item.ingresso),
      elementoId: item.elemento_id || undefined, revisioneFornitore: item.revisione_fornitore,
    });
    const providerTool = tools.find((candidate) => candidate.name === item.strumento);
    const title = providerTool ? providerTool.title : item.strumento;
    const sigla = providerTool ? providerTool.sigla : "?";
    const entry = byProvider.get(item.strumento) || { title, sigla, count: 0 };
    byProvider.set(item.strumento, { ...entry, count: entry.count + 1 });
    insertChip(toolForm, fieldName, el("span", {
      class: "pv-chip", text: `da ${sigla}`,
      title: `Valore preso da ${title}: ${item.chiave} = ${item.valore}`,
    }));
  }
  session = { tool, chips: nextChips };
  return byProvider;
}

// js/elemento-salva.js's `currentPayload`: every field whose chip is STILL present (untouched
// since the prefill/reconstruction) -> `{collegamenti: [{chiave, strumento, percorso, ingresso,
// valore, elemento_id?, revisione_fornitore?}]}`; otherwise `{}`. Never omits an item because a
// SAVE happened -- only editing a field drops its own item (§25.1: "no save ever clears the
// provenance of an item the user did not touch").
export function activeProvenienza(tool) {
  if (session.tool !== tool || session.chips.size === 0) return {};
  return {
    collegamenti: Array.from(session.chips.values(), (item) => ({
      chiave: item.chiave, strumento: item.strumento, percorso: item.percorso, ingresso: item.ingresso,
      valore: item.valore,
      ...(item.elementoId ? { elemento_id: item.elementoId } : {}),
      ...(item.elementoId && item.revisioneFornitore != null ? { revisione_fornitore: item.revisioneFornitore } : {}),
    })),
  };
}
