// "Contenuto" fieldset of the report personalisation overlay's Opzioni pane (WORKBENCH_SPEC §11):
// the preset radio group + every content checkbox. Rebuilt on every change (cheap: a few dozen
// nodes) so disabled/checked state always matches `resolved` without separate bookkeeping --
// unlike the Cartiglio fieldset's free-text inputs, nothing here has a text-cursor position that a
// rebuild could lose.
import { el } from "./dom.js";
import { PRESET_COMPLETA, PRESET_SINTETICA, PRESET_PERSONALIZZATA, sectionLocked, resultGroups } from "./relazione-options.js";

const PRESET_LABELS = [
  [PRESET_COMPLETA, "Completa"],
  [PRESET_SINTETICA, "Sintetica"],
  [PRESET_PERSONALIZZATA, "Personalizzata"],
];

function presetRadios(resolved, onPreset) {
  const wrap = el("div", { class: "rel-preset-group", role: "radiogroup", "aria-label": "Preset del contenuto" });
  for (const [value, label] of PRESET_LABELS) {
    const id = `rel-preset-${value}`;
    const input = el("input", { type: "radio", id, name: "rel-preset", value });
    input.checked = resolved.preset === value;
    input.addEventListener("change", () => onPreset(value));
    wrap.append(el("div", { class: "rel-field-row rel-field-row--check" }, [input, el("label", { for: id, text: label })]));
  }
  return wrap;
}

function checkboxRow(id, label, checked, { disabled = false, onChange, indent = false } = {}) {
  const input = el("input", { type: "checkbox", id });
  input.checked = Boolean(checked);
  input.disabled = disabled;
  if (onChange) input.addEventListener("change", () => onChange(input.checked));
  const row = el("div", { class: `rel-field-row rel-field-row--check${indent ? " rel-field-row--indent" : ""}` }, [
    input,
    el("label", { for: id, text: label }),
  ]);
  return row;
}

function radioRow(name, id, value, label, checked, { disabled = false, onChange, indent = false } = {}) {
  const input = el("input", { type: "radio", id, name, value });
  input.checked = checked;
  input.disabled = disabled;
  if (onChange) input.addEventListener("change", () => onChange(value));
  return el("div", { class: `rel-field-row rel-field-row--check${indent ? " rel-field-row--indent" : ""}` }, [
    input,
    el("label", { for: id, text: label }),
  ]);
}

function verificheRows(resolved, onSezione) {
  const wrap = el("div");
  const checked = resolved.sezioni.verifiche !== false;
  wrap.append(
    checkboxRow("rel-sezione-verifiche", "Verifiche", checked, {
      onChange: (on) => onSezione({ verifiche: on ? "tutte" : false }),
    }),
  );
  if (checked) {
    wrap.append(
      radioRow("rel-verifiche-mode", "rel-verifiche-tutte", "tutte", "Tutte", resolved.sezioni.verifiche === "tutte", {
        indent: true,
        onChange: () => onSezione({ verifiche: "tutte" }),
      }),
      radioRow(
        "rel-verifiche-mode",
        "rel-verifiche-non-soddisfatte",
        "non_soddisfatte",
        "Solo non soddisfatte",
        resolved.sezioni.verifiche === "non_soddisfatte",
        { indent: true, onChange: () => onSezione({ verifiche: "non_soddisfatte" }) },
      ),
    );
  }
  return wrap;
}

function risultatiRows(resolved, outputNodes, onGruppo) {
  const groups = resultGroups(outputNodes);
  if (groups.length === 0) return null;
  const wrap = el("div", { class: "rel-risultati-group" }, [el("p", { class: "rel-subheading", text: "Risultati" })]);
  for (const group of groups) {
    const id = `rel-gruppo-${group.path.replace(/[^a-z0-9]+/gi, "-")}`;
    const included = resolved.sezioni.gruppi[group.path] !== false;
    wrap.append(checkboxRow(id, group.label, included, { indent: true, onChange: (on) => onGruppo(group.path, on) }));
  }
  return wrap;
}

export function buildContenutoFieldset(resolved, { outputNodes, onPreset, onSezione, onGruppo }) {
  const locked = sectionLocked(resolved);
  const fieldset = el("fieldset", { class: "rel-fieldset" }, [el("legend", { text: "Contenuto" }), presetRadios(resolved, onPreset)]);

  fieldset.append(
    checkboxRow("rel-sezione-schizzo", "Schizzo", resolved.sezioni.schizzo, {
      disabled: locked,
      onChange: (on) => onSezione({ schizzo: on }),
    }),
    checkboxRow("rel-sezione-dati", "Dati di ingresso", resolved.sezioni.dati, {
      disabled: locked,
      onChange: (on) => onSezione({ dati: on }),
    }),
    checkboxRow("rel-sezione-sintesi", "Sintesi", resolved.sezioni.sintesi, { onChange: (on) => onSezione({ sintesi: on }) }),
    verificheRows(resolved, onSezione),
  );
  const risultati = risultatiRows(resolved, outputNodes, onGruppo);
  if (risultati) fieldset.append(risultati);
  fieldset.append(
    checkboxRow("rel-sezione-passaggi", "Passaggi di calcolo", resolved.sezioni.passaggi, {
      onChange: (on) => onSezione({ passaggi: on }),
    }),
    checkboxRow("rel-sezione-tabelle", "Tabelle", resolved.sezioni.tabelle, { onChange: (on) => onSezione({ tabelle: on }) }),
    checkboxRow("rel-sezione-grafici", "Grafici", resolved.sezioni.grafici, { onChange: (on) => onSezione({ grafici: on }) }),
    checkboxRow("rel-sezione-avvisi", "Avvisi", resolved.sezioni.avvisi, { onChange: (on) => onSezione({ avvisi: on }) }),
    checkboxRow("rel-sezione-nota", "Nota sulle correzioni", resolved.sezioni.nota_correzioni, {
      onChange: (on) => onSezione({ nota_correzioni: on }),
    }),
  );
  return fieldset;
}
