// "Tieni questa" (WORKBENCH_SPEC §19.4): the dialog opened from a variant column in #/varianti/
// <tool> -- three outcomes, all through existing code paths (elemento-salva.js's own payload
// builder, progetti-api.js, the extracted 409 dialog).
import { el } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { navigate } from "./router.js";
import { save } from "./form-state.js";
import { getCurrentProgetto, setCurrentProgetto } from "./progetto-picker.js";
import { buildElementoPayload } from "./elemento-salva.js";
import { computeSintesiEStato } from "./elemento-sintesi.js";
import { apriConflittoDialog } from "./elemento-conflitto.js";
import { chiudiVarianti } from "./varianti-state.js";
import { fetchProgetti, createElemento, updateElemento } from "./progetti-api.js";

let dialogEl = null;
let releaseTrap = null;

function close() {
  if (releaseTrap) {
    releaseTrap();
    releaseTrap = null;
  }
  if (dialogEl) {
    const node = dialogEl;
    dialogEl = null;
    node.close();
    node.remove();
  }
}

function useOnlyInForm(tool, variante, fields) {
  save(tool, variante.inputs, fields);
  chiudiVarianti(tool);
  close();
  navigate(tool);
}

function payloadFor(tool, variante, report, outputNodes, nome, nota) {
  const { sintesi, stato } = computeSintesiEStato(tool, { reportTool: { name: tool, outputNodes: outputNodes || [] }, report, stale: false });
  return buildElementoPayload({ tool, values: variante.inputs, sintesi, stato, nome, provenienza: {}, nota });
}

// §19.4: on success the set closes (its work is done: the origin element now IS this variant)
// and the tool page shows the just-kept inputs, exactly like `useOnlyInForm` -- never just a
// silent `close()`, which left the confronto page open on stale columns and never re-fetched the
// element's own new `revisione`, so a SECOND "Aggiorna" always hit the 409 dialog below.
async function doAggiorna(tool, title, variante, report, outputNodes, fields, notaInput, errorEl) {
  const origine = variante.origine;
  const nome = origine.nome || variante.nome;
  const body = { ...payloadFor(tool, variante, report, outputNodes, nome, notaInput.value.trim()), revisione: origine.revisione };
  try {
    const result = await updateElemento(origine.elemento_id, body);
    if (result.conflict) {
      close();
      apriConflittoDialog({
        attuale: result.attuale,
        onRicarica: () => navigate(tool, { elemento: origine.elemento_id }),
        onSalvaCopia: () => apriTieniDialog({ tool, title, variante, report, outputNodes, fields, defaultAzione: "nuovo" }),
      });
      return;
    }
    save(tool, variante.inputs, fields || []);
    chiudiVarianti(tool);
    close();
    navigate(tool, { elemento: origine.elemento_id });
  } catch (error) {
    errorEl.textContent = error.message || "Impossibile aggiornare l'elemento.";
    errorEl.hidden = false;
  }
}

async function doSalvaComeNuovo(tool, variante, report, outputNodes, progettoId, nomeInput, errorEl, chiudiCheckbox) {
  const nome = nomeInput.value.trim();
  if (!nome) {
    errorEl.textContent = "Il nome dell'elemento è obbligatorio.";
    errorEl.hidden = false;
    return;
  }
  try {
    await createElemento(progettoId, payloadFor(tool, variante, report, outputNodes, nome));
    if (chiudiCheckbox.checked) {
      chiudiVarianti(tool);
      close();
      navigate(tool);
    } else {
      close();
    }
  } catch (error) {
    errorEl.textContent = error.message || "Impossibile salvare l'elemento.";
    errorEl.hidden = false;
  }
}

// `defaultAzione` ("nuovo"): used by the "Salva come copia" branch of the 409 dialog above, which
// must land straight on "Salva come nuovo elemento" rather than re-offering "Aggiorna" for an
// element that just proved to be out of date. `tuttiId` (every id currently in the set, §19.2's
// own A/B/C/D) feeds the default "Variante X scelta fra A, B, C" revision note -- editable, never
// baked in.
export async function apriTieniDialog({ tool, title, variante, report, outputNodes = [], fields, defaultAzione = null, tuttiId = [variante.id] }) {
  close();
  const titleId = "vt-title";
  const current = getCurrentProgetto();
  // Aggiorna needs BOTH a saved origin AND a current project (§19.4: it PUTs to the origin
  // element, which only makes sense once a project is selected -- offering it with none invites
  // a save that has nowhere consistent to land).
  const puoAggiornare = Boolean(variante.origine) && Boolean(current) && defaultAzione !== "nuovo";
  const puoSalvareNuovo = Boolean(current);

  const errorEl = el("p", { class: "es-dialog-error", role: "alert" });
  errorEl.hidden = true;

  const body = [];
  if (puoAggiornare) {
    const notaInput = el("input", {
      type: "text", class: "vt-nota-input", maxlength: "500", "aria-label": "Nota della revisione",
      value: `Variante ${variante.id} scelta fra ${tuttiId.join(", ")}`,
    });
    body.push(
      el("div", { class: "vt-aggiorna" }, [
        el("label", { text: "Nota della revisione" }),
        notaInput,
        el("button", {
          type: "button",
          class: "vt-action",
          text: `Aggiorna "${variante.origine.nome || "elemento"}"`,
          onclick: () => doAggiorna(tool, title, variante, report, outputNodes, fields, notaInput, errorEl),
        }),
        el("p", { class: "vt-avviso", text: "Chiude le varianti aperte e riporta la pagina sull'elemento aggiornato." }),
      ]),
    );
  }
  if (puoSalvareNuovo) {
    const nomeInput = el("input", { type: "text", class: "vt-nome-input", value: `${variante.origine ? variante.origine.nome : (title || tool)} – variante ${variante.id}`, maxlength: "120" });
    const chiudiCheckbox = el("input", { type: "checkbox", id: "vt-chiudi-dopo" });
    body.push(
      el("div", { class: "vt-nuovo" }, [
        el("label", { text: "Nome del nuovo elemento" }),
        nomeInput,
        el("button", { type: "button", class: "vt-action", text: "Salva come nuovo elemento", onclick: () => doSalvaComeNuovo(tool, variante, report, outputNodes, current.id, nomeInput, errorEl, chiudiCheckbox) }),
        el("label", { class: "vt-chiudi-label" }, [chiudiCheckbox, document.createTextNode(" Chiudi le varianti dopo il salvataggio")]),
      ]),
    );
  } else {
    // No project selected at all: the picker's own message, project-agnostic.
    let progetti = [];
    try {
      progetti = await fetchProgetti();
    } catch (error) {
      progetti = [];
    }
    if (progetti.length > 0) {
      const select = el("select", { "aria-label": "Progetto" });
      select.append(el("option", { value: "", text: "Seleziona un progetto…" }));
      for (const progetto of progetti) select.append(el("option", { value: progetto.id, text: progetto.nome }));
      const nomeInput = el("input", { type: "text", class: "vt-nome-input", value: `${title || tool} – variante ${variante.id}`, maxlength: "120" });
      const chiudiCheckbox = el("input", { type: "checkbox", id: "vt-chiudi-dopo" });
      body.push(
        el("div", { class: "vt-nuovo" }, [
          select,
          nomeInput,
          el("button", {
            type: "button",
            class: "vt-action",
            text: "Salva come nuovo elemento",
            onclick: () => {
              if (!select.value) {
                errorEl.textContent = "Scegli un progetto.";
                errorEl.hidden = false;
                return;
              }
              setCurrentProgetto({ id: select.value, nome: select.options[select.selectedIndex].text });
              doSalvaComeNuovo(tool, variante, report, outputNodes, select.value, nomeInput, errorEl, chiudiCheckbox);
            },
          }),
          el("label", { class: "vt-chiudi-label" }, [chiudiCheckbox, document.createTextNode(" Chiudi le varianti dopo il salvataggio")]),
        ]),
      );
    }
  }
  body.push(
    el("div", { class: "vt-solo" }, [
      el("button", { type: "button", class: "vt-action vt-action--solo", text: "Usa solo nel modulo", onclick: () => useOnlyInForm(tool, variante, fields || []) }),
      el("p", { class: "vt-avviso", text: "Chiude le varianti aperte e torna al modulo con questi dati, senza salvare nulla." }),
    ]),
  );

  dialogEl = el("dialog", { class: "es-dialog vt-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
    el("h2", { id: titleId, text: `Tieni la variante ${variante.id}` }),
    errorEl,
    ...body,
    el("div", { class: "es-dialog-actions" }, [el("button", { type: "button", class: "es-dialog-cancel", text: "Annulla", onclick: close })]),
  ]);
  document.body.append(dialogEl);
  dialogEl.addEventListener("close", close);
  releaseTrap = trapFocus(dialogEl, { onEscape: close });
  dialogEl.showModal();
}
