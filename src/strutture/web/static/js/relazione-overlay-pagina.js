// "Tabelle" (row policy) + "Pagina" (layout) fieldsets of the report personalisation overlay's
// Opzioni pane (WORKBENCH_SPEC §11). Orthogonal to Contenuto/presets on purpose: printing the
// complete report landscape, or with only the governing table rows, is not "a reduced report".
import { el } from "./dom.js";

function radioRow(name, id, value, label, checked, onChange, extra) {
  const input = el("input", { type: "radio", id, name, value });
  input.checked = checked;
  input.addEventListener("change", () => onChange(value));
  const row = el("div", { class: "rel-field-row rel-field-row--check" }, [input, el("label", { for: id, text: label })]);
  if (extra) row.append(extra);
  return row;
}

function checkboxRow(id, label, checked, onChange) {
  const input = el("input", { type: "checkbox", id });
  input.checked = Boolean(checked);
  input.addEventListener("change", () => onChange(input.checked));
  return el("div", { class: "rel-field-row rel-field-row--check" }, [input, el("label", { for: id, text: label })]);
}

export function buildTabelleFieldset(tabelle, { onRighe, onN }) {
  const fieldset = el("fieldset", { class: "rel-fieldset" }, [el("legend", { text: "Tabelle" }), el("p", { class: "rel-subheading", text: "Righe" })]);
  const nInput = el("input", { type: "number", id: "rel-righe-n", min: "1", step: "1", class: "rel-n-input" });
  nInput.value = String(tabelle.n || 50);
  nInput.disabled = tabelle.righe !== "prime";
  nInput.addEventListener("input", () => onN(Math.max(1, Number(nInput.value) || 1)));
  fieldset.append(
    radioRow("rel-righe", "rel-righe-tutte", "tutte", "Tutte", tabelle.righe === "tutte", onRighe),
    radioRow("rel-righe", "rel-righe-prime", "prime", "Prime N", tabelle.righe === "prime", onRighe, nInput),
    radioRow("rel-righe", "rel-righe-governanti", "governanti", "Solo governanti", tabelle.righe === "governanti", onRighe),
  );
  return fieldset;
}

export function buildPaginaFieldset(pagina, { onOrientamento, onCorpo, onNumeri, onIntestazione }) {
  const fieldset = el("fieldset", { class: "rel-fieldset" }, [el("legend", { text: "Pagina" })]);
  fieldset.append(
    el("p", { class: "rel-subheading", text: "Orientamento" }),
    radioRow("rel-orientamento", "rel-orientamento-verticale", "verticale", "Verticale", pagina.orientamento === "verticale", onOrientamento),
    radioRow("rel-orientamento", "rel-orientamento-orizzontale", "orizzontale", "Orizzontale", pagina.orientamento === "orizzontale", onOrientamento),
    el("p", { class: "rel-subheading", text: "Corpo del testo" }),
    radioRow("rel-corpo", "rel-corpo-normale", "normale", "Normale", pagina.corpo === "normale", onCorpo),
    radioRow("rel-corpo", "rel-corpo-compatto", "compatto", "Compatto", pagina.corpo === "compatto", onCorpo),
    checkboxRow("rel-numeri", "Numeri di pagina", pagina.numeri, onNumeri),
    checkboxRow("rel-intestazione", "Intestazione ripetuta", pagina.intestazione, onIntestazione),
  );
  return fieldset;
}
