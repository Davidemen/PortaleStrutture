// Accessible equivalent of the sensitivity chart (WORKBENCH_SPEC §24.2, DESIGN_SPEC §3): always
// rendered, one row per point, a row button "Usa questo valore" writes the Dati control.
import { el } from "./dom.js";
import { formatNumber } from "./format.js";
import { checkMark } from "./verdict.js";

function etaCell(value) {
  if (value === null || value === undefined) return "—";
  return formatNumber(value);
}

export function buildTabella({ valori, checks, soloEsito, errori, onUsa }) {
  const erroriByValore = new Map((errori || []).map((e) => [e.valore, e.messaggio]));
  const details = el("details", { class: "sv-tabella", open: true });
  details.append(el("summary", { text: `Tabella (${valori.length} punti)` }));
  const headCells = ["Valore", ...checks.map((c) => c.nome), ...soloEsito.map((c) => c.nome), "Esito", ""];
  const table = el("table", {}, [
    el("caption", { text: "Utilizzazione di ogni verifica al variare del campo" }),
    el("thead", {}, [el("tr", {}, headCells.map((text) => el("th", { text })))]),
  ]);
  const tbody = el("tbody");
  valori.forEach((valore, i) => {
    const errore = erroriByValore.get(valore);
    const row = el("tr");
    row.append(el("td", { text: formatNumber(valore) }));
    for (const check of checks) row.append(el("td", { text: etaCell(check.eta[i]) }));
    for (const check of soloEsito) {
      const esito = check.esito[i];
      row.append(el("td", {}, esito === null || esito === undefined ? ["—"] : [checkMark(esito)]));
    }
    if (errore) {
      row.append(el("td", { class: "sv-errore", text: errore }));
    } else {
      const tutte = [...checks, ...soloEsito].every((c) => c.esito[i] !== false);
      const nonPassano = [...checks, ...soloEsito].filter((c) => c.esito[i] === false).length;
      row.append(
        el("td", {}, [checkMark(tutte), ` ${tutte ? "Tutte passano" : `${nonPassano} non passano`}`]),
      );
    }
    const useBtn = el("button", { type: "button", class: "sv-usa", text: "Usa questo valore" });
    useBtn.disabled = Boolean(errore);
    useBtn.addEventListener("click", () => onUsa(valore));
    row.append(el("td", {}, [useBtn]));
    tbody.append(row);
  });
  table.append(tbody);
  details.append(table);
  return details;
}
