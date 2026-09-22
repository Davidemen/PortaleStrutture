// #/varianti/<tool> ("Affianca", WORKBENCH_SPEC §19.3): one column per variant, a `<table>` with
// variants as columns and Modalità/Esito/Schema/Verifiche/Risultati/Dati rows. Full-width page,
// no Dati/Sintesi split -- same shell slot as #/registro and #/progetti (js/main.js
// `showVarianti`). Row builders live in js/varianti-confronto-righe.js (kept this module under
// the 400-line cap); this module owns the page shell, the run loop, the reference-column
// selector/toggles and the narrow-viewport (<1100px) one-column-at-a-time tab strip.
import { el, clear } from "./dom.js";
import { navigate } from "./router.js";
import { fetchSchema, runTool } from "./api.js";
import { describeFields } from "./schema.js";
import { describeOutput } from "./output-schema.js";
import { caricaVarianti, salvaVarianti, rinominaVariante, etichettaTab } from "./varianti-state.js";
import { differenzeCampi, deltaRelativo } from "./varianti-diff.js";
import { apriTieniDialog } from "./varianti-tieni.js";
import {
  buildModalitaRow, buildVerdictRow, buildSchemaRow, buildVerificheRows, buildRisultatiRows, buildDatiRows, sectionHead,
} from "./varianti-confronto-righe.js";

export async function renderVariantiConfronto(root, { tool, owner }) {
  if (root._smOwner !== owner) return;
  clear(root);
  let set = caricaVarianti(tool);
  if (!set) {
    root.append(
      el("h2", { text: "Confronto varianti" }),
      el("p", { text: "Nessuna variante aperta per questo strumento." }),
      el("a", { href: `#/${tool}`, text: "Torna al calcolo" }),
    );
    return;
  }

  let schema;
  try {
    schema = await fetchSchema(tool);
  } catch (error) {
    if (root._smOwner !== owner) return;
    root.append(el("p", { text: "Impossibile caricare lo strumento." }));
    return;
  }
  if (root._smOwner !== owner) return;

  const fields = describeFields(schema.input || {});
  const outputNodes = describeOutput(schema.output || {});
  let mostraTuttiRisultati = false;
  let mostraTuttiDati = false;
  let riferimentoId = set.varianti[0].id;
  // §19.3 "<1100px: one column at a time, same tab strip as above" -- which column stays visible
  // in the narrow layout; a screen-reader/keyboard user never loses the others (CSS `display:
  // none` only applies inside that one `@media` query, so this is purely a narrow-viewport
  // affordance, never a data-loss risk at any width).
  let activeColIndex = Math.max(0, set.varianti.findIndex((v) => v.id === set.attiva));
  const reportsById = new Map(); // id -> {report, error}

  root.append(
    el("h2", { text: `Confronto varianti — ${schema.title || tool}` }),
    el("a", { href: `#/${tool}`, class: "vc-torna", text: "← Torna al calcolo" }),
  );
  const narrowTabs = el("div", { class: "vc-narrow-tabs", role: "tablist", "aria-label": "Variante visibile" });
  root.append(narrowTabs);
  const table = el("table", { class: "vc-table", tabindex: "0", "aria-label": "Confronto varianti" });
  root.append(el("div", { class: "r-table-scroll" }, [table]));

  function renderNarrowTabs() {
    clear(narrowTabs);
    set.varianti.forEach((variante, index) => {
      narrowTabs.append(el("button", {
        type: "button", role: "tab", class: "vc-narrow-tab", "aria-selected": String(index === activeColIndex), text: variante.nome,
        onclick: () => { activeColIndex = index; render(); },
      }));
    });
  }

  // Marks every data cell of `tr` (skipping the row's own `<th>`) with `vc-col-hidden-narrow`
  // when it is not the active column -- the ONLY thing the <1100px media query in css/varianti.css
  // acts on, so a row builder never needs its own narrow-layout logic.
  function markNarrowVisibility(tr) {
    Array.from(tr.children)
      .slice(1)
      .forEach((cell, index) => cell.classList.toggle("vc-col-hidden-narrow", index !== activeColIndex));
  }

  function reportOf(id) {
    return (reportsById.get(id) || {}).report || null;
  }

  async function runOne(variante, colEl) {
    colEl.setAttribute("aria-busy", "true");
    try {
      const { status, report } = await runTool(tool, variante.inputs);
      // `runTool` never throws on 4xx/5xx (api.js's own `readJson` contract) -- a non-2xx body is
      // the Italian error envelope (`{errors: [...]}`), never a real report, so this column must
      // show "! Errore" with the first message, exactly like every other error path in the app,
      // not silently render it as if the calculation had produced this as its result.
      if (status >= 200 && status < 300) {
        reportsById.set(variante.id, { report, error: null });
      } else {
        const message = (report && report.errors && report.errors[0]) || "Impossibile eseguire il calcolo.";
        reportsById.set(variante.id, { report: null, error: message });
      }
    } catch (error) {
      reportsById.set(variante.id, { report: null, error: "Impossibile contattare il server." });
    }
    colEl.setAttribute("aria-busy", "false");
  }

  function buildRefSelector() {
    const select = el("select", { "aria-label": "Confronta con" });
    for (const variante of set.varianti) {
      select.append(el("option", { value: variante.id, text: etichettaTab(variante), selected: variante.id === riferimentoId }));
    }
    select.addEventListener("change", () => {
      riferimentoId = select.value;
      render();
    });
    return el("div", { class: "vc-ref" }, [el("label", { text: "Confronta con " }), select]);
  }

  function deltaCell(value, refValue) {
    if (typeof value !== "number" || typeof refValue !== "number") return el("span", { text: "—" });
    const delta = deltaRelativo(value, refValue);
    if (!delta) return el("span", { text: "—" });
    return el("span", { class: `vc-delta vc-delta--${delta.simbolo === "▲" ? "up" : delta.simbolo === "▼" ? "down" : "eq"}`, text: delta.testo });
  }

  function buildHeadRow() {
    const tr = el("tr");
    tr.append(el("th", { scope: "col", text: "" }));
    for (const variante of set.varianti) {
      const nameInput = el("input", { type: "text", class: "vc-name-input", value: variante.nome, maxlength: "40", "aria-label": `Nome variante ${variante.id}` });
      nameInput.addEventListener("change", () => {
        // `rinominaVariante` (the SAME pure transition js/varianti-bar.js's own tab menu uses),
        // never a hand-rolled map here -- otherwise this table's own copy of `set` drifts from
        // what a following "Tieni questa" reads (the closed-over `variante`, captured before the
        // rename), and the dialog opens on the OLD name.
        set = rinominaVariante(set, variante.id, nameInput.value);
        salvaVarianti(tool, set);
        render();
      });
      const originTxt = variante.origine ? `da ${variante.origine.nome || "elemento"}, rev. ${variante.origine.revisione}` : "";
      const teniBtn = el("button", {
        type: "button", class: "vc-tieni", text: "Tieni questa",
        // Never on a column that errored or has not finished its own first run yet -- "Tieni
        // questa" builds its payload straight from THIS report (js/varianti-tieni.js's own
        // `payloadFor`), so with none there is nothing correct to keep.
        disabled: !reportOf(variante.id),
        onclick: () => apriTieniDialog({ tool, title: schema.title, variante, report: reportOf(variante.id), outputNodes, fields, tuttiId: set.varianti.map((v) => v.id) }),
      });
      const th = el("th", { scope: "col", class: "vc-col-head" }, [
        nameInput,
        originTxt ? el("p", { class: "vc-origin", text: originTxt }) : document.createTextNode(""),
        teniBtn,
      ]);
      tr.append(th);
    }
    return tr;
  }

  function buildCtx() {
    return { set, fields, outputNodes, riferimentoId, mostraTuttiRisultati, mostraTuttiDati, reportOf, reportsById, deltaCell };
  }

  function render() {
    clear(table);
    const ctx = buildCtx();
    const conta = differenzeCampi(fields, set.varianti, set.varianti.findIndex((v) => v.id === riferimentoId)).filter((v) => v.diverso).length;
    const totale = fields.length;
    table.append(el("caption", { class: "vc-caption" }, [el("span", { text: `Variante ${set.varianti.findIndex((v) => v.id === set.attiva) + 1} di ${set.varianti.length}` })]));
    const thead = el("thead", {}, [buildHeadRow()]);
    const tbody = el("tbody", {}, [
      buildModalitaRow(ctx),
      buildVerdictRow(ctx),
      buildSchemaRow(ctx),
      sectionHead(ctx, "Verifiche"),
      ...buildVerificheRows(ctx),
      sectionHead(ctx, "Risultati"),
      ...buildRisultatiRows(ctx),
      sectionHead(ctx, `Dati diversi: ${conta} di ${totale}`),
      ...buildDatiRows(ctx),
    ]);
    table.append(thead, tbody);
    renderNarrowTabs();
    for (const tr of tbody.children) markNarrowVisibility(tr);
    markNarrowVisibility(thead.children[0]);
  }

  root.insertBefore(buildRefSelector(), table.parentElement);
  const toggleRisultati = el("button", { type: "button", class: "vc-toggle", text: mostraTuttiRisultati ? "Nascondi risultati" : "Mostra tutti i risultati", onclick: () => {
    mostraTuttiRisultati = !mostraTuttiRisultati;
    toggleRisultati.textContent = mostraTuttiRisultati ? "Nascondi risultati" : "Mostra tutti i risultati";
    render();
  } });
  const toggleDati = el("button", { type: "button", class: "vc-toggle", text: mostraTuttiDati ? "Nascondi dati uguali" : "Mostra tutti i dati", onclick: () => {
    mostraTuttiDati = !mostraTuttiDati;
    toggleDati.textContent = mostraTuttiDati ? "Nascondi dati uguali" : "Mostra tutti i dati";
    render();
  } });
  root.insertBefore(el("div", { class: "vc-toggles" }, [toggleRisultati, toggleDati]), table.parentElement);

  // Registered BEFORE the run loop below (§19.3: Esc must work WHILE the columns are still
  // running), bound to `owner` rather than removed on first use -- a page reached through
  // "Torna al calcolo"/the rail never runs this handler again since `root._smOwner` moved on, but
  // an unconditional one-shot `removeEventListener` would instead leave THIS handler dead while
  // still on this very page (e.g. after an unrelated Esc closed some other widget) and never
  // catch a later Esc meant for this page. `document.activeElement`'s own open `<dialog>` (Tieni/
  // conflitto) already stops Esc from reaching here (native dialog behaviour), so no extra guard.
  document.addEventListener("keydown", function onKeydown(event) {
    if (root._smOwner !== owner) {
      document.removeEventListener("keydown", onKeydown);
      return;
    }
    if (event.key !== "Escape" || document.querySelector("dialog[open]")) return;
    document.removeEventListener("keydown", onKeydown);
    navigate(tool);
  });

  render();
  for (const variante of set.varianti) {
    if (root._smOwner !== owner) return;
    const colIndex = set.varianti.findIndex((v) => v.id === variante.id) + 1;
    const colEl = table.querySelector(`thead tr th:nth-child(${colIndex + 1})`) || table;
    await runOne(variante, colEl);
    if (root._smOwner !== owner) return;
    render();
  }
}
