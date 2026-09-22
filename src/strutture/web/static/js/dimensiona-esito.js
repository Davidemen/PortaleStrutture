// Builds the result block of the "Dimensiona" dialog (WORKBENCH_SPEC §23.5): the headline value,
// the reliability line (icon + word + motivi) and the accessible "Campioni" table. Pure DOM
// building from the `/dimensiona` response -- no fetching, no state, so js/dimensiona.js stays
// focused on the dialog's own lifecycle.
import { el } from "./dom.js";
import { symbolNode } from "./symbols.js";
import { formatNumber, formatUnit } from "./format.js";
import { checkMark } from "./verdict.js";

const ESITO_LABEL = {
  trovato: "Valore trovato",
  estremo_sufficiente: "Già l'estremo dell'intervallo soddisfa le verifiche",
  nessun_valore: "Nessun valore soddisfa le verifiche nell'intervallo",
  interrotta: "Ricerca interrotta: limiti di tempo o di calcoli raggiunti",
  limite_validita: "Il valore trovato è il limite di validità del metodo",
};

function reliabilityLine(esito) {
  const icon = checkMark(esito.affidabile);
  const word = esito.affidabile ? "Affidabile" : "Da controllare";
  const p = el("p", { class: `dm-affidabile ${esito.affidabile ? "dm-affidabile--si" : "dm-affidabile--no"}` }, [icon, ` ${word}`]);
  return p;
}

function motiviList(motivi) {
  if (!motivi || motivi.length === 0) return null;
  const ul = el("ul", { class: "dm-motivi" });
  for (const motivo of motivi) ul.append(el("li", { text: motivo }));
  return ul;
}

function modeCaveat(esito) {
  const lines = [];
  if (esito.modalita === "excel") {
    lines.push("⚠ Valore trovato riproducendo il foglio Excel, errori inclusi.");
  }
  const correzioni = esito.correzioni || {};
  if ((correzioni.da_confermare || 0) > 0 || (correzioni.respinto || 0) > 0) {
    lines.push("◐ Provvisorio: il calcolo si appoggia a correzioni del registro non ancora confermate.");
  }
  if (!lines.length) return null;
  const box = el("div", { class: "dm-caveat" });
  for (const line of lines) box.append(el("p", { text: line }));
  return box;
}

// `field` = the chosen Campo descriptor (symbol/unit); `esito` = the `/dimensiona` response body.
export function buildEsito(field, esito) {
  const wrap = el("div", { class: "dm-esito" });
  wrap.append(el("p", { class: "dm-esito-titolo", text: ESITO_LABEL[esito.esito] || esito.esito }));

  if (esito.valore !== null && esito.valore !== undefined) {
    const headline = el("p", { class: "dm-headline" });
    if (field && field.symbol) headline.append(symbolNode(field.symbol), " = ");
    else headline.append(`${field ? field.label : esito.campo} = `);
    const unit = field && field.unit && field.unit !== "-" ? ` ${formatUnit(field.unit)}` : "";
    headline.append(`${formatNumber(esito.valore)}${unit}`);
    wrap.append(headline);
  }

  if (esito.governante) {
    wrap.append(
      el("p", { class: "dm-governante", text: `Verifica governante: ${esito.governante.nome} (η = ${formatNumber(esito.governante.eta)})` }),
    );
  }

  wrap.append(reliabilityLine(esito));
  const motivi = motiviList(esito.motivi);
  if (motivi) wrap.append(motivi);
  const caveat = modeCaveat(esito);
  if (caveat) wrap.append(caveat);

  if (esito.verifiche_solo_esito && esito.verifiche_solo_esito.length > 0) {
    wrap.append(
      el("p", { class: "dm-solo-esito", text: `Considerate solo come esito, senza obiettivo: ${esito.verifiche_solo_esito.join(", ")}` }),
    );
  }
  if (esito.verifiche_senza_obiettivo && esito.verifiche_senza_obiettivo.length > 0) {
    wrap.append(
      el("p", { class: "dm-senza-obiettivo", text: `Obiettivo non applicato (verifiche di minimo): ${esito.verifiche_senza_obiettivo.join(", ")}` }),
    );
  }

  wrap.append(buildCampioniTable(esito.campioni || []));
  return wrap;
}

function buildCampioniTable(campioni) {
  const details = el("details", { class: "dm-campioni" });
  details.append(el("summary", { text: `Campioni (${campioni.length})` }));
  const table = el("table", {}, [
    el("caption", { text: "Valori campionati durante la ricerca" }),
    el("thead", {}, [el("tr", {}, ["Valore", "Esito", "η max", "Avvisi nuovi"].map((text) => el("th", { text })))]),
  ]);
  const tbody = el("tbody");
  for (const campione of campioni) {
    tbody.append(
      el("tr", {}, [
        el("td", { text: formatNumber(campione.valore) }),
        el("td", { text: campione.esito }),
        el("td", { text: campione.eta_max != null ? formatNumber(campione.eta_max) : "—" }),
        el("td", { text: (campione.avvisi_nuovi || []).join("; ") || "—" }),
      ]),
    );
  }
  table.append(tbody);
  details.append(table);
  return details;
}
