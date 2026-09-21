# Workbench — UI/UX overhaul spec

Decided with the user (2026-09-21): all four pain points apply (no live results, too much scrolling, no drawing of
the element, finding/switching tools); **live calculation like a spreadsheet**; **Workbench layout**; done **before
roadmap Phase 1**. This document EXTENDS `docs/ui/UI_BRIEF.md` (direction, copy rules, hard constraints) and
`docs/ui/DESIGN_SPEC.md` (tokens, components, §4/§4b hint contract, §5 module contracts). Where they conflict, this
wins. Everything stays schema-driven: **zero per-tool UI code**.

## 0. Principles
1. **Excel reflexes.** Change a number -> the answer moves. Never make the engineer look for the result.
2. **Answer first.** Verdict, governing utilisation, governing results and the sketch are visible without scrolling
   on a 1440×900 screen; everything else is one click away, collapsed.
3. **The sketch is a check.** A drawing that follows the inputs catches wrong units and swapped dimensions.
4. Quiet chrome, the results sheet stays the one bold place (brief). No new colours: tokens only.
5. WCAG 2.2 AA, keyboard-first, CSP `default-src 'self'`, no CDN, vanilla ES modules ≤ ~150 lines, DOM through
   `js/dom.js` (textContent only), Italian sentence-case copy, Windows + macOS browsers (Chrome/Edge/Safari/Firefox).

## 1. Layout (≥ 1100 px)
```
┌──────┬──────────────────────┬────────────────────────────────────────┐
│ rail │ DATI                 │ SINTESI (sticky)                       │
│  ⌂   │ ▾ Geometria  B 2,40… │ ✔ Tutte le verifiche soddisfatte       │
│  ★   │    B [ 2,40 ] m      │ η max 0,82 · Scorrimento SLV           │
│  ⏱   │    L [ 3,00 ] m      │ σ_max 182 kPa · A_s,x 12ø16 · …        │
│ ───  │ ▸ Materiali  C25/30… │ ┌ Pianta ─────────┐ ┌ Sezione ───────┐ │
│ cat. │ ▸ Azioni     N 850…  │ │   sketch        │ │   sketch       │ │
│ ···  │ ▸ Opzioni            │ └─────────────────┘ └────────────────┘ │
│      │ [esempio] [⟳ auto]   │ ▸ Verifiche (12)  ▸ Pressioni  ▸ Armature │
└──────┴──────────────────────┴────────────────────────────────────────┘
  56/240 px      400 px                       fluid
```
- **Rail** (shell): collapsed 56 px (icons + tooltips) / expanded 240 px (persisted `sm.ui.rail`). Items: Home,
  Preferiti, Recenti, then categories (top-level of `Tool.group`) each opening its tools. `Ctrl/Cmd+K` opens the palette.
- **Dati** column 400 px, own scroll. **Sintesi + results** column fluid, own scroll; the Sintesi block is sticky
  at the top of that column and collapses to one line (verdict · η max) after 200 px of scroll.
- 720–1099 px: rail collapsed, Dati 360 px, results fluid. **< 720 px:** one column; tabs *Dati | Risultati*; a
  sticky bottom bar always shows verdict + η max and jumps to Risultati. Sketch comes first in Risultati.
- Print (`print.css`) is untouched by this work.

## 2. Live calculation  (module `js/live.js`, owner: forms)
- Any input change -> client validation -> if valid, run after **300 ms** of quiet. One request in flight per tool:
  a newer change aborts the older request (`AbortController`); responses carry a sequence number and stale ones
  are dropped. `Enter` in a field or `Ctrl+Enter` anywhere runs immediately.
- While a request is in flight the Sintesi shows a 2 px progress hairline; nothing is blanked. **Invalid input keeps
  the last good results**, dimmed to 60 %, with the chip "dati non validi — risultati precedenti" and the field
  error inline. Server validation errors (`error_details`) behave the same.
- **Changed values flash**: results are diffed against the previous render by output path; changed value cells get
  `data-changed` for 1.2 s (marker-yellow fade; none under `prefers-reduced-motion`). Scroll position, open groups
  and focus are preserved across renders — never re-mount the results tree when the structure is unchanged.
- Screen readers: the live region announces only when the **verdict or the governing check changes**
  ("Verifiche: 1 non soddisfatta — Scorrimento SLV, η 1,08"), not on every keystroke.
- **When live is off:** `live === false` from the tool metadata, OR any table input holds > 200 rows, OR the last run
  took > 800 ms, OR the header switch **Calcolo automatico** is off (`sm.ui.live`, default on). Then the primary button
  is "Calcola" and the Sintesi shows "Dati modificati — premi Calcola" when inputs are newer than results.
- Events: `strutture:inputs-changed {name, values, valid}` (forms -> live), `strutture:run-request {name, values,
  reason: "live"|"manual"|"example"}`, `strutture:run-result` gains `{seq, elapsedMs, reason}`,
  `strutture:results-stale {name}`.

## 3. Dati column (owner: forms)
- **Accordion sections** from the `group` hint. Header = title · **one-line summary of its values** when collapsed
  (`B 2,40 m · L 3,00 m · H 0,80 m`, symbols where available, max 3 values then "…") · error count badge. First
  section open by default, state persisted per tool (`sm.ui.openGroups`). "Espandi tutto / Comprimi tutto".
- **Compact rows**: label (symbol + short description) left, control right on ONE row at ≥ 400 px column width;
  unit as an input suffix inside the control; long descriptions move to a `?` disclosure under the row. Numeric
  inputs right-aligned, `inputmode="decimal"`, accept `,` and `.`, select-all on focus, ↑/↓ steps by the field's
  step (Shift ×10). Target: the retaining-wall form ≤ 1100 px tall with all sections collapsed but the first.
- Action bar (sticky bottom of the column): `Carica esempio` · `Calcola` (only when live is off) · `⋯` menu
  (Copia link, Azzera dati, Stampa relazione).
- Table inputs, the comune widget, the unit selector and the MIDAS import keep working unchanged; a table edit counts
  as an input change (live rules of §2 apply).

## 4. Sintesi + results (owner: results)
- **Sintesi block**: verdict in words; **η max** with the name and clause of the governing check and its utilisation bar;
  the ≤3 `highlight` outputs as large figures (symbol, value, unit); warnings count (opens the list). Tools with no
  checks show the highlights only.
- **Result groups are collapsible**, header = title · key-value preview (first 2 scalars) · failed-check badge.
  Default open: *Verifiche* and any group containing a failed check; the rest closed; "Passaggi di calcolo" always
  closed. State persisted per tool. Toolbar: **Solo non soddisfatte** (filters check rows), "Espandi tutto", jump
  links to groups. Click on a value copies it at full precision (toast "Copiato").
- Checks list sorted by utilisation, descending; failed first.
- Row tables and charts as today (paged, copy/CSV, chart above table) but inside their collapsible group.
- Target: retaining-wall results ≤ 1 screen at first render (everything beyond the Sintesi collapsed).

## 5. Sketch renderer (module `js/sketch.js` + `css/sketch.css`, owner: sketch)
Input: an output field with hint `widget: "sketch"` holding `Sketch` JSON — contract in
`src/strutture/shared/sketch.py` (read it: `viste[] -> forme[]` with `kind` = rect | polygon | circle | line | arrow |
dimension | label | bars | diagram; model metres, **y up**; semantic `stile`). One generic renderer:
- each `Vista` -> one `<figure>` with `<figcaption>` = `titolo`, SVG `viewBox` fitted to the bounding box of all
  shapes (incl. dimension offsets and labels) + 8 % padding, uniform scale, y flipped;
- styles -> CSS classes `sk-<stile>` (fills/strokes from tokens: calcestruzzo = light grey hatch-free fill + ink
  outline, terreno = dotted fill, armatura/palo = ink fill, carico/reazione = series-2/series-1 arrows, pressione =
  10 % tinted polygon + outline, quota = hairline with 45° ticks and centred text, evidenza = marker fill);
- `dimension`: extension lines, ticks, text centred above the line, always upright; `diagram`: polygon from the
  baseline with ordinates scaled to `altezza_relativa`; `bars`: true-diameter circles with a 2 px minimum;
  `label.simbolo` rendered with `<tspan>` subscripts (reuse `symbols.js`); text 11–12 px regardless of scale
  (`vector-effect`/inverse scaling), never below 10 px;
- accessible: `role="img"` + `aria-label` from `titolo` + `nota`; the sketch is decorative for numbers (all values
  are in the results), so no per-shape focus; must render ≤ 16 ms for 400 shapes; updates in place on live results
  (diff by view index; no flicker).
The Sintesi places the sketch views side by side (max 2 per row); tools without a `schizzo` output simply show none.

## 6. Navigation (owner: shell)
- **Home (`#/`)**: search field, *Preferiti*, *Recenti* (last 6), then one section per category with **tool cards**
  (title, `summary`, norm, ★ toggle). Empty Preferiti explains the ★.
- **Palette (`Ctrl/Cmd+K`, `/`)**: fuzzy search over title, summary, norm, group; ↑↓ Enter; recents first on empty query.
- Favourites/recents in `localStorage` (`sm.nav.fav`, `sm.nav.recent`). Shortcuts: `g h` home, `Ctrl+Enter` run,
  `[` / `]` previous/next section, `Alt+1/2` focus Dati/Risultati, `?` shows the shortcut sheet.
- `GET /api/tools` now returns `summary` and `live` per tool (backend done); `Tool.group` is already canonical.

## 7. Backend work for sketches (owners: sketch-authors)
Per tool: `schizzo.py` (pure, from validated inputs + computed results -> `Sketch`), output field
`schizzo: Sketch | None = campo_schizzo()`, attached in `run`; a failure while drawing must never fail the
calculation (catch, log, `schizzo=None`). Tests assert view titles, shape kinds/counts, key coordinates and
dimension texts for the example, and that geometry follows the inputs (change B -> the rectangle widens).
Also set `summary=` (one Italian sentence) on every Tool registration, and `live=False` on tools whose example
takes > 300 ms or whose main input is a big table (plinti).
First sketches: plinto isolato (pianta + sezione with base pressures), plinto su pali (pianta with piles + S&T
elevation), muro di sostegno (sezione with thrusts + base pressures), cedimenti (footing + layers + z_crit),
pavimento industriale (load footprint), trave e pilastri c.a. (section with bars), punzonamento (plan with
perimeters), mensola tozza (elevation with strut and tie), sezione H rimpiattata, colonna EC3 (section), neve
(roof with load), vento cpe (plan with zones).

## 8. Work packages (disjoint files; staging dir `src/strutture/web/static_next/`)
| Package | Owns |
|---|---|
| shell-nav | `index.html`, `css/layout.css`, `css/tokens.css` (additions only), `css/nav.css`, `js/main.js`, `js/router.js`, `js/layout.js`, `js/storage.js`, `js/api.js`, `js/tool-index.js` -> rail, new `js/home.js`, `js/palette.js`, `js/nav-state.js`, `js/shortcuts.js` |
| forms-live | `css/forms.css`, `js/forms*.js`, `js/fields.js`, `js/schema.js`, `js/validate.js`, `js/form-state.js`, new `js/live.js`, `js/form-sections-summary.js`, `js/number-input.js` (table-input*, comune-widget, midas-* untouched except the single `inputs-changed` hook) |
| results-workbench | `css/results.css`, `js/results*.js`, `js/verdict.js`, `js/output-schema.js`, `js/format.js`, `js/table.js`, new `js/sintesi.js`, `js/results-diff.js`, `js/results-toolbar.js` |
| sketch | new `js/sketch.js`, `js/sketch-shapes.js`, `js/sketch-fit.js`, `css/sketch.css` + a harness page with fixture JSON covering every shape kind |
| sketch-authors ×2 | Python `schizzo.py` + tests + `summary`/`live` per tool (foundations+geotechnics / RC+steel+loads) |
| integrator | everything in staging + `tests/e2e/` (only agent allowed to use the Playwright MCP browser) |
Cross-package contract additions: events of §2; `results.js` exposes `renderReport(root, {report, outputNodes,
tool, previous})`; the Sintesi root is `#sintesi` (shell provides the empty container inside `#results-pane`);
sketch API `renderSketch(container, sketch, {previous}) -> void`; rail/home read tools via `api.fetchTools()`.

## 9. Acceptance (e2e, desktop 1440×900 + mobile 390×844)
Typing in a field updates a highlighted result within 1 s without pressing anything and flashes it; an invalid value
keeps the previous results dimmed with the chip; a stale response never overwrites a newer one (test with delayed
routes); retaining wall: form ≤ 1100 px and results ≤ 900 px at first render; the footing sketch widens when B
grows; `Ctrl+K` -> type "punz" -> Enter opens the punching tool; favourites persist across reload; the bottom
bar on mobile shows the verdict; live is off for a 300-row table and "Calcola" appears; zero console errors / CSP
violations; keyboard-only run of a whole tool; all existing e2e tests still pass.

## 10. Report export — always complete (user rule, 2026-09-21)
**An exported report never depends on what happens to be open on screen.** "Stampa relazione", the browser's own
print command (Ctrl/Cmd+P) and any future export all produce the SAME complete document:
- it is built FROM THE DATA (report + input/output schema) into a print-only container at print time
  (`beforeprint` and the button), not by printing the interactive results tree; the interactive UI is hidden in print;
- **document order (user rule):** cartiglio -> **Schizzo** (every sketch view, large: full text width, one view per
  row when there are more than two; the sketch carries the main input dimensions as quotas) -> **Dati di ingresso**
  -> Sintesi (verdict, η max, governing results) -> Verifiche -> result groups -> tables -> charts -> avvisi;
- **Dati di ingresso are printed in full, as a table per input section: simbolo | descrizione | valore | unità** —
  every dimension and every other input the engineer typed, every default actually used, the advanced options and
  the calculation mode; table inputs (soil layers, reactions, load cases, plates) are listed row by row with their
  column units (same 2 000-row rule as result tables); a value is never printed without its unit;
- everything expanded: every input section with every value actually used (defaults and advanced options
  included, the calculation mode stated), every result group including "Passaggi di calcolo", EVERY check (no
  "failed + top 5" fold, no "Solo non soddisfatte" filter), all sketch views, all charts, warnings in full;
- tables unpaged: all rows up to 2 000; beyond that the envelope and the governing rows plus the note "Tabella
  completa di N righe disponibile in CSV" (a 20 000-row table is ~400 pages);
- nothing interactive or transient: no buttons, chips, flash highlights, dimming, toasts, tooltips-only content
  (full descriptions are printed, not left in `title` attributes);
- **stale results are never exported**: if the inputs were changed or are invalid since the last successful run,
  the export first recalculates; if that fails it refuses with "I risultati non corrispondono ai dati correnti —
  correggi i dati o ricalcola prima di stampare";
- the screen state (open groups, filters, scroll) is untouched by printing.
Acceptance (e2e, print media emulation): with every group collapsed, the checks folded, the "Solo non soddisfatte"
filter on and a table on page 2, the printed document still contains every group title, every check, every table
row (count equals the data), the sketch views BEFORE the inputs, and a Dati di ingresso table whose row count equals
the number of input fields of the tool with every numeric value followed by its unit; stale results refuse to print.

## 11. Report personalisation overlay (user rule, 2026-09-21)
"Stampa relazione" (button, `⋯` menu, Ctrl/Cmd+P) opens a **full-window overlay** before anything is generated.
The default is always the COMPLETE report of §10; the overlay is where the engineer changes that on purpose.
```
┌ Relazione di calcolo ─────────────────────────────────────────────── [Annulla] [Stampa / Salva PDF] ┐
│ OPZIONI (380 px, scroll)                      │ ANTEPRIMA (live, paged A4, scroll, zoom fit-width)   │
│ Cartiglio   progetto · committente · elemento │ ┌──────────────┐ ┌──────────────┐                    │
│             relazione n. · revisione · sigla  │ │ cartiglio    │ │ verifiche    │   pagina 1 di 6     │
│             data · note                       │ │ schizzo      │ │ …            │                    │
│ Contenuto   ◉ Completa  ○ Sintetica  ○ Person.│ │ dati         │ │              │                    │
│   ☑ Schizzo  ☑ Dati di ingresso  ☑ Sintesi    │ └──────────────┘ └──────────────┘                    │
│   ☑ Verifiche (tutte | solo non soddisfatte)  │                                                     │
│   ☑ Risultati: ☑ gruppo 1 ☑ gruppo 2 …        │                                                     │
│   ☑ Passaggi di calcolo  ☑ Tabelle  ☑ Grafici │                                                     │
│   ☑ Avvisi  ☑ Nota sulle correzioni           │                                                     │
│ Tabelle     righe: tutte | prime N | governanti│                                                     │
│ Pagina      A4 verticale | orizzontale · corpo │                                                     │
│             testo normale | compatto · numeri  │                                                     │
│             di pagina · intestazione ripetuta  │                                                     │
└───────────────────────────────────────────────┴─────────────────────────────────────────────────────┘
```
- **Presets.** *Completa* (default; everything of §10), *Sintetica* (cartiglio, schizzo, dati di ingresso, sintesi,
  verifiche), *Personalizzata* (any change to a checkbox switches to it). The sketch and the input data can be
  unticked only in *Personalizzata*.
- **Transparency.** When anything is omitted the report says so under the cartiglio: "Contenuto ridotto
  dall'utente — omessi: Passaggi di calcolo, Tabelle". A reduced report is never mistaken for the complete one.
- **Cartiglio** fields: progetto, committente, elemento (default = tool title), relazione n., revisione, sigla,
  data (default today, editable), note. Persisted (`sm.cartiglio`, per browser; per project once Phase 3 exists);
  contents choices persisted per tool (`sm.relazione.<tool>`); "Ripristina predefiniti".
- **Preview.** The right pane renders the actual report DOM (the same `js/relazione.js` output) scaled to fit,
  split into A4 pages with CSS (`break-*` rules + a page frame per sheet on screen); it updates within 300 ms of
  an option change; very large tables render the first page of rows in the preview with "… N righe in stampa".
- **Behaviour.** Opening it runs the stale-results rule of §10 first (recalculate or refuse). Focus is trapped,
  Esc / Annulla closes and returns focus to the trigger, the underlying page does not scroll, the overlay is a
  labelled dialog (`role="dialog"`, `aria-modal`). "Stampa / Salva PDF" prints exactly the previewed document
  (the overlay chrome is hidden in print). Browser print (Ctrl/Cmd+P) opens the overlay instead of printing the
  raw page; `beforeprint` without the overlay (menu print, OS shortcut that cannot be intercepted) falls back to
  the complete report with the saved cartiglio.
- **Mobile (< 720 px):** options first, "Anteprima" as a second step (segmented control), same actions.
- **Contract.** `js/relazione.js` exports `buildRelazione(container, data, options)` with
  `options = {preset, sezioni: {schizzo, dati, sintesi, verifiche: "tutte"|"non_soddisfatte"|false, gruppi:
  {<path>: bool}, passaggi, tabelle, grafici, avvisi, nota_correzioni}, tabelle: {righe: "tutte"|"prime"|
  "governanti", n}, pagina: {orientamento, corpo: "normale"|"compatto", numeri, intestazione}, cartiglio: {…}}`;
  missing keys = complete. New modules: `js/relazione-overlay.js`, `js/relazione-options.js` (pure: defaults,
  presets, persistence, the "omessi" sentence), `js/relazione-preview.js`, `css/relazione-overlay.css`.
- Acceptance: defaults produce the §10 document byte-for-byte; unticking a section removes it from preview and
  print and adds it to the "omessi" line; options persist across reload; keyboard-only operation; Esc restores
  focus; print output contains no overlay chrome; works at 390 px.

## 12. Navigation rail, redesigned (user feedback 2026-09-21: "icons are all the same; collapsed it is almost
impossible to navigate")
**Diagnosis.** The collapsed rail lists all 30 tools as identical dots and all recents as identical clocks:
thirty indistinguishable targets. Thirty pictograms at 24 px would not be recognisable either. The collapsed rail
must show FEW, DISTINCT destinations and reach the tools through flyouts.

**Collapsed rail (56 px) = activity bar.** Top to bottom, one 44×44 target each, icon + tooltip (name + shortcut):
Home · Cerca (opens the palette, ⌘K/Ctrl K) · Preferiti · Recenti · ─ · the FIVE categories (Carichi,
Calcestruzzo armato, Acciaio, Geotecnica, Fondazioni) · ─ · at the bottom: expand/collapse. No individual tools.
- A category / Preferiti / Recenti button opens a **flyout** (280 px panel to the right of the rail, over the
  content, `role="dialog"` non-modal; opens on click or Enter/Space/→, NOT on hover; closes on Esc, outside click,
  selection or ←): title, then its tools grouped by sub-group ("Neve", "Sisma", "Vento"), each row = **sigla
  chip** + title (2 lines max) + norm in small type + ★ toggle; ↑↓ move, Enter opens, type-ahead jumps by title.
- The active tool's category button is marked (ink left rule + marker background) and shows the tool's
  **sigla** as a small badge, so the collapsed rail always says where you are.
**Expanded rail (240 px).** Same items with text; categories are accordions (only the active one open by
default); each tool row starts with its sigla chip instead of a dot, so rows are scannable; Preferiti and Recenti
(max 5) list tools the same way.
**Sigla.** `GET /api/tools` now returns `sigla` (2–3 capital letters, unique, e.g. PLI plinto isolato, PLP plinto su
pali, MUR muro, TRV trave, PUN punzonamento — backend done, `src/strutture/web/presentation.py`). The chip is a
28×20 px rounded-2 outline in tabular capitals; it is also shown on Home cards, in the palette rows and next to
the tool title. Missing sigla -> first two letters of the title.
**Pictograms.** One inline-SVG icon per destination, drawn in the drafting vernacular of the app (24×24 viewBox,
`fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"`; built with
createElementNS from the path data below — no icon font, no external file, CSP-safe), in `js/icons.js`:
| key | meaning | path data (`d`), extra shapes |
|---|---|---|
| home | house | `M4 11 12 4l8 7M6 10v10h12V10` |
| cerca | magnifier | circle cx10.5 cy10.5 r5.5 + `M15 15l5 5` |
| preferiti | star | `M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.9 6.8 19.6l1-5.8L3.5 9.7l5.9-.8z` |
| recenti | clock | circle cx12 cy12 r8 + `M12 7.5V12l3 2` |
| carichi | distributed load on a beam | `M4 5h16M6 5v6M10 5v6M14 5v6M18 5v6M4.8 9.5 6 11l1.2-1.5M8.8 9.5 10 11l1.2-1.5M12.8 9.5 14 11l1.2-1.5M16.8 9.5 18 11l1.2-1.5M3 14h18M5 14l-2 4h4zM19 14l-2 4h4z` |
| calcestruzzo-armato | RC section with bars | `M6 4h12v16H6z` + filled circles r1.1 at (9,17) (12,17) (15,17) (9,7) (15,7) |
| acciaio | I section | `M6 4h12v3h-4.5v10H18v3H6v-3h4.5V7H6z` |
| geotecnica | ground with soil layers | `M3 8h18M5 8l-2 3M9 8l-2 3M13 8l-2 3M17 8l-2 3M21 8l-2 3M3 14h18M3 19h18` (the last two dashed `2 2`) |
| fondazioni | footing under a column | `M10 3h4v9h-4zM4 12h16v5H4zM3 20h18` |
| registro | checklist (Phase 1) | `M5 6l1.5 1.5L9 5M5 12l1.5 1.5L9 11M5 18l1.5 1.5L9 17M12 6h7M12 12h7M12 18h7` |
| progetti | folder (Phase 3) | `M3 7h6l2 2h10v10H3z` |
| espandi / comprimi | chevrons | `M9 6l6 6-6 6` / `M15 6l-6 6 6 6` |
Icons inherit `currentColor` (graphite, ink when active); `aria-hidden="true"`, the button carries the label.
**Acceptance.** Collapsed: exactly 9 destination buttons + the toggle, every icon's path data differs, each has an
accessible name and a tooltip; keyboard: Tab to a category, Enter opens the flyout with focus on the first tool, ↓↓
Enter navigates and closes it, Esc returns focus to the button; the active category is marked and shows the active
tool's sigla; every tool is reachable in ≤ 2 actions from the collapsed rail; sigle unique; 44 px targets; works at
720–1099 px where the rail is forced collapsed; no layout shift of the content when a flyout opens.

## 13. Registro correzioni + Confronta con Excel (phase 1B UI, 2026-09-21)
Purpose: the engineer sees every place where the tool departs from the original spreadsheet, decides on each one
(sign-off, no accounts: a typed `sigla`), and can see for the CURRENT inputs what those departures change.
API (already live): `GET /api/divergences?strumento=&tipo=&stato=&q=` -> `{divergenze:[entry], totali}`; entry =
register fields (`id, titolo, tipo, strumenti, cella, foglio, corretto, clausola, impatto, uscite, ramo,
motivo_senza_ramo`) + `stato (da_confermare|approvato|respinto), sigla, nota, data`; `GET /api/divergences/riepilogo`
-> `{per_strumento:{tool:{da_confermare,approvato,respinto}}}`; `GET /api/divergences/{unita}/{slug}` (+ `storia`);
`PUT /api/divergences/{unita}/{slug}/signoff {stato,sigla,nota}` (sigla required unless `da_confermare`; 422 carries
the Italian message); `POST /api/divergences/signoff-multiplo {ids,stato,sigla,nota}`;
`POST /api/tools/{name}/compare <inputs>` -> `{ok, disponibile, standard:Report, excel:Report|null, confronto:
{confrontabile, differenze:[{percorso,standard,excel,delta,delta_rel,divergenze:[id]}], totale_differenze,
verifiche:[{nome,standard:{passed,value}|null,excel:{…}|null}], divergenze_coinvolte:[id]}|null}`.

### 13.1 Page `#/registro` (optional query: `strumento`, `stato`, `tipo`, `q`, `id`)
- Rail: one fixed entry "Registro correzioni" below Recenti, own pictogram (a ruled ledger page with a tick — distinct
  from every category pictogram), a count chip with the number still `da_confermare` (hidden at 0).
- Main area, full width (no Dati/Sintesi split). Title + ONE sentence: "Ogni punto in cui lo strumento si discosta dal
  foglio Excel originale. Il progettista conferma o respinge ogni correzione."
- Totals strip = the state filter: three buttons `aria-pressed` "Da confermare N · Approvate N · Respinte N".
  Filter row: search (`q`, debounced 250 ms), tool select (sigla + title), tipo select (Italian labels: Errore del
  foglio / Aggiornamento normativo / Scelta ingegneristica / Da verificare). Filters live in the hash query (shareable).
- A ruled LIST grouped by unità (group heading = unit + counts), not cards. Collapsed row: state mark (icon + word,
  never colour alone: ○ Da confermare, ✓ Approvata, ✕ Respinta), titolo, tipo (plain text, sentence case), sigla
  chips of the tools (link to the tool), clausola. `#/registro?id=<id>` opens and scrolls to that row.
- Expanded row (`button aria-expanded`): two columns "Il foglio" | "Lo strumento" (`foglio` / `corretto`), then
  cella, impatto, the outputs affected (label from the tool's output schema when resolvable, else the path);
  `ramo="nessuno"` -> "Non riproducibile in modalità Excel: <motivo>". Sign-off form: three radios, sigla (required
  unless Da confermare), nota, "Salva decisione"; last decision line "AB · 21/09/2026 · nota"; "Storia" disclosure
  (from the detail endpoint). The row updates only after the server confirms; errors inline, in Italian.
- Bulk: a checkbox per row + "Decidi per le N selezionate…" -> the same small form -> `signoff-multiplo`.

### 13.2 Per-tool indicators (data: `riepilogo`, fetched once, refreshed after a sign-off)
- Tool header, after the title: link "N correzioni da confermare" (warn ink + icon) -> `#/registro?strumento=<tool>
  &stato=da_confermare`; with none pending but entries present: muted "Correzioni confermate".
- Any `respinto` entry for the tool: a banner above Dati (danger ink rule, icon + text): "Una correzione di questo
  strumento è stata respinta: la modalità standard la applica comunque. Apri il registro." (link, filtered).

### 13.3 "Confronta con Excel" (results toolbar toggle, `aria-pressed`; only when the input schema has `legacy_compat`)
- On: POST `compare` with the current VALID inputs through the same debounce/queue as live calculation (non-live
  tools: on "Calcola"). Panel "Confronto con il foglio Excel" directly under the Sintesi; off: panel removed.
- Summary sentence: "N valori diversi · M verifiche cambiano esito · K correzioni coinvolte", or "Nessuna differenza:
  per questi dati le due modalità coincidono.", or (not `confrontabile`) which mode failed and its error text.
- Checks that change outcome first (name, both verdicts as icon + word, both values). Then a table: Grandezza (symbol
  + label via the output schema by path; `righe[2]` -> "riga 3") | Standard | Excel | Δ | Δ % | Correzione (links
  `#/registro?id=…`, "—" when unattributed). Numbers via format.js, units via `formatUnit`. When
  `totale_differenze` exceeds the list: "Mostrate le prime 200 di N." Footnote when any row is unattributed:
  "Le differenze senza correzione indicata dipendono da una correzione a monte."
- Stale while recomputing (same treatment as results). NOT part of the printed report (out of scope here).

### 13.4 Staging, files, tests
Work in `src/strutture/web/static_next/` (identical to `static/` today). New modules, each ≤ 400 lines:
`js/registro.js` (page), `js/registro-row.js`, `js/registro-signoff.js`, `js/registro-api.js`, `js/confronto.js`,
`js/confronto-api.js`, `css/registro.css`, `css/confronto.css`; small edits to the router, rail and results toolbar.
CSP: no inline style/script. Tests: `tests/e2e/test_registro.py`, `tests/e2e/test_confronto_excel.py` (the e2e
server must use a temporary sign-off store — never the real `var/` database), full e2e suite green on
`STRUTTURE_E2E_STATIC_DIR=src/strutture/web/static_next`.
