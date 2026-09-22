// Pure undo/redo stack for the Dati form's values -- WORKBENCH_SPEC §21. No DOM access here on
// purpose (node-testable with plain `node --test`): every function takes a `storia` object
// `{passato, presente, futuro}` and returns a NEW one, never mutates its argument or the arrays it
// holds. `js/annulla-ui.js` is the only caller and owns everything DOM/event related (coalescing by
// control, labels built from field descriptors, wiring to the form API).
export const MAX_PASSI_ANNULLA = 100;

// A fresh history for a just-mounted tool (or variant): nothing to undo or redo yet.
export function creaStoria(valori) {
  return { passato: [], presente: valori, futuro: [] };
}

export function puoAnnullare(storia) {
  return storia.passato.length > 0;
}

export function puoRipristinare(storia) {
  return storia.futuro.length > 0;
}

// Records one CONFIRMED step: `passo` is `{etichetta, testo, campo, valori}` -- `valori` is the
// full new value object (the state AFTER the edit); `etichetta`/`testo` describe the step for the
// live region / tooltip; `campo` is the single field name it touched, or `null` for a multi-field
// step (Carica esempio, Azzera dati). The OLD `presente` becomes the snapshot this step restores.
// Redo is cleared (a new edit after an undo discards the redo branch). Oldest step silently
// dropped past `MAX_PASSI_ANNULLA` (owner's limit, §21.1).
export function registra(storia, passo) {
  const voce = { etichetta: passo.etichetta, testo: passo.testo, campo: passo.campo ?? null, valori: storia.presente };
  const passato = [...storia.passato, voce];
  const trimmed = passato.length > MAX_PASSI_ANNULLA ? passato.slice(passato.length - MAX_PASSI_ANNULLA) : passato;
  return { passato: trimmed, presente: passo.valori, futuro: [] };
}

export function annulla(storia) {
  if (!puoAnnullare(storia)) return storia;
  const voce = storia.passato[storia.passato.length - 1];
  const passato = storia.passato.slice(0, -1);
  const futuro = [{ etichetta: voce.etichetta, testo: voce.testo, campo: voce.campo, valori: storia.presente }, ...storia.futuro];
  return { passato, presente: voce.valori, futuro };
}

export function ripristina(storia) {
  if (!puoRipristinare(storia)) return storia;
  const [voce, ...futuro] = storia.futuro;
  const passato = [...storia.passato, { etichetta: voce.etichetta, testo: voce.testo, campo: voce.campo, valori: storia.presente }];
  return { passato, presente: voce.valori, futuro };
}

// The step an "Annulla"/"Ripristina" press would apply right now, or null -- for the tooltip/live
// region text, without either caller having to reach into `passato`/`futuro` directly.
export function passoAnnulla(storia) {
  return puoAnnullare(storia) ? storia.passato[storia.passato.length - 1] : null;
}

export function passoRipristina(storia) {
  return puoRipristinare(storia) ? storia.futuro[0] : null;
}
