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
register fields (`id, titolo, tipo, strumenti, cella, foglio, corretto, clausola, impatto, uscite, ramo
(codice|condiviso|nessuno), motivo_senza_ramo, riprodotta_da`) + `stato (da_confermare|approvato|respinto), sigla, nota, data`; `GET /api/divergences/riepilogo`
-> `{per_strumento:{tool:{da_confermare,approvato,respinto}}}`; `GET /api/divergences/{unita}/{slug}` (+ `storia`);
`PUT /api/divergences/{unita}/{slug}/signoff {stato,sigla,nota}` (sigla required unless `da_confermare`; 422 carries
the Italian message); `POST /api/divergences/signoff-multiplo {ids,stato,sigla,nota}`;
`POST /api/tools/{name}/compare <inputs>` -> `{ok, disponibile, standard:Report, excel:Report|null, confronto:
{confrontabile, differenze:[{percorso,standard,excel,delta,delta_rel,divergenze:[id]}], totale_differenze,
verifiche:[{nome,standard:{passed,value}|null,excel:{…}|null}], divergenze_coinvolte:[id],
attribuzione:{correzioni_valutate, completa, non_valutabili:[id]}}|null}`. Attribution is exact for the current
inputs: the server re-runs the tool with ONE correction at a time in Excel behaviour (3 s budget). When
`attribuzione.completa` is false the panel adds "Attribuzione parziale: non tutte le correzioni sono state provate.";
`non_valutabili` are listed as "Correzioni che non si possono isolare: …" (links).

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
  Excel-mode line from `ramo`: "codice" -> "Riprodotta in modalità Excel"; "condiviso" -> "Riprodotta in modalità
  Excel insieme a <links to `riprodotta_da`>" (no ids: just "Riprodotta in modalità Excel") + the motivo as a muted
  note; "nessuno" -> "NON riprodotta in modalità Excel: <motivo>" (warn ink + icon: such an entry never appears in
  "Confronta con Excel"). A filter chip "Non riprodotte in Excel" next to the tipo select. Sign-off form: three radios, sigla (required
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

## 14. Progetti (phase 3 UI, 2026-09-22)
Purpose: an engineer keeps the elements of a job together, reopens them with their inputs, sees at a glance which
are verified, and prints one report for the whole job. No accounts: everyone sees every project. Backend done:
`docs/architecture-phase3.md`; API `GET/POST /api/progetti`, `GET/PUT/DELETE /api/progetti/{id}` (+ `POST …/
ripristina`), `GET/POST /api/progetti/{id}/elementi`, `GET/PUT/DELETE /api/elementi/{id}`, `POST /api/elementi/{id}/
duplica {nome}`, `GET /api/elementi/{id}/revisioni`, `GET /api/progetti/{id}/esporta`, `POST /api/progetti/importa`.
Element body: `{strumento, nome, inputs, sintesi, stato, modalita, provenienza, sigla, nota}` (+ `revisione` on
PUT/DELETE: optimistic locking — 409 = "Modificato da un altro utente: ricarica e riprova"). `stato` ∈ verificato |
non_verificato | dati_modificati. Italian error messages come in the standard envelope (`errors[0]`).

### 14.1 Where it lives
- Rail: fixed entry "Progetti" below "Registro correzioni" (pictogram: the folder path already in §12's table).
- Header, left of "Calcolo automatico": the **project picker** — a select "Progetto: <nome>" listing active projects
  plus "Nessun progetto" and "Nuovo progetto…" (inline mini-form: codice, nome, committente). The choice is kept per
  browser (`localStorage`). Nothing else in the app changes when no project is selected.
- Tool page, Dati action bar (next to "Carica esempio"): **"Salva in progetto"**. With no project selected it opens
  the picker first. Dialog: nome elemento (default "<tool title> n"), sigla (optional, ≤ 8), nota (optional).
  `inputs` = exactly the payload the run sends (`visibleValues`, tables included); `sintesi` = from the LAST
  successful run: `{ok, eta_max, verifica_governante, evidenze: [{simbolo|label, valore, unita}] (≤ 3 highlights)}`;
  `stato`: verificato (last run ok, every check passed) · non_verificato (run ok, a check failed) · dati_modificati
  (inputs changed since the last run, or no run yet); `modalita` from `legacy_compat`. After saving, the header shows
  "Elemento: <nome> · <progetto>" and the button becomes **"Salva"** (PUT with the last `revisione`) + a small
  **"Salva come nuovo"**. 409: dialog with "Ricarica" (reload the element, discarding local edits) and "Salva come
  copia". Opening `#/<tool>?elemento=<id>` loads the element's inputs into the form (tables too), runs it (live) and
  shows the same header state.

### 14.2 Page `#/progetti`
Ruled list (no cards): codice, nome, committente, n. elementi, aggiornato; row actions Apri, Rinomina (inline),
Elimina (soft; confirm), and a "Mostra eliminati" toggle that reveals deleted rows with Ripristina. Top: "Nuovo
progetto" and **Importa** (file input, `.json`; shows the imported project's name and any elements whose tool is
unknown, flagged in the list as "strumento non disponibile"). Empty state: one sentence + the button.

### 14.3 Page `#/progetti/<id>`
Head: codice · nome · committente · note (editable inline, PUT with revisione), **Esporta** (downloads the JSON),
**Relazione di progetto**. Element list, ruled rows: sigla chip (tool), nome, stato as icon + word (✓ Verificato ·
✕ Non verificato · ○ Dati modificati — never colour alone), η max (2 decimals), verifica governante, aggiornato;
actions per row: Apri (→ `#/<tool>?elemento=<id>`), Duplica (name prompt), Rinomina, Storia (disclosure: every
revision with data · sigla · nota; "Carica questa revisione" opens the tool with THOSE inputs without saving),
Elimina / Ripristina. Sort by aggiornato desc; filter by tool (select of siglas present).
**Relazione di progetto** = the personalisation overlay (§11) once for the whole set, then ONE print document:
project cartiglio (codice, nome, committente, data, n. elementi), then every element in list order as its own
section with a sub-cartiglio (nome, sigla, tool title, stato, aggiornato) followed by exactly what §10 prints for
a single tool — built from a FRESH run (`?relazione=1` when "Sviluppo dei calcoli" is on) of the element's stored
inputs; a run that fails prints its Italian error instead of results; an unknown tool prints "Strumento non
disponibile in questa versione". Progress line while the runs complete ("Elemento 3 di 12…"); stale never printed.

### 14.4 Files, staging, tests
Work in `src/strutture/web/static_next/` (identical to `static/` today). New modules ≤ 400 lines each:
`js/progetti-api.js`, `js/progetti.js` (list page), `js/progetto.js` (project page), `js/progetto-elementi.js`,
`js/progetto-storia.js`, `js/progetto-relazione.js`, `js/elemento-salva.js` (dialog + header state + 409 flow),
`js/progetto-picker.js` (header), `css/progetti.css`; small edits to `router.js`, `tool-index.js` (rail entry),
`main.js`, the Dati action bar, `relazione-print.js`. CSP unchanged (no inline style/script). Tests:
`tests/e2e/test_progetti.py` (create project via UI, save an element from a tool, reopen it with its tables, 409
dialog via two saves with a stale revision (drive the second through `page.request` PUT), duplicate, history,
soft delete + restore, export → import round trip via `page.request`, project report contains every element and the
per-element sections, unknown-tool element flagged); the e2e server already uses `InMemoryProjectRepository`.

## 15. "Usa in…" — typed links between tools (phase 5 UI, 2026-09-22)
Backend done: fields carry `provides: "<chiave>"` / `accepts: "<chiave>"` in their UI hints (already in the
`/schema` payloads); `GET /api/tools/collegamenti` -> `{chiavi: {chiave: {fornitori: [{strumento, percorso, ingresso}],
consumatori: [{strumento, campo}]}}, per_strumento: {tool: {fornisce: [chiave], accetta: {campo: chiave}, usa_in: [tool]}}}`.
A key's value is copied as it is (the key names the unit); the registry test already guarantees compatibility.
- Results toolbar: a button **"Usa in…"** (only when `per_strumento[tool].usa_in` is non-empty and a successful run
  exists). It opens a small menu listing the consumer tools (sigla chip + title). Choosing one navigates to
  `#/<consumer>?da=<tool>&<chiave>=<valore>&…` with every key the current run provides (`inputs_echo` for forwarded
  inputs, `data` paths for outputs — resolve the paths client-side from the registry).
- Consumer page: on load, fields whose `accepts` key is in the query are prefilled and marked with a provenance chip
  "da <sigla fornitore>" next to the label (tooltip: "Valore preso da <tool title>: <chiave> = <valore>"); the run
  starts live as usual. Editing a prefilled field clears its chip. A note under the tool title: "Dati ricevuti da
  <tool>: N campi" with a link back (`#/<fornitore>`), dismissible.
- Inside a project (§14): when the consumer element is saved, `provenienza` records `{"collegamenti": [{chiave,
  strumento, elemento_id?}]}`; nothing else in this phase (the "dati a monte modificati" marking is a later step).
- Tests: `tests/e2e/test_usa_in.py` — run sisma-parametri-sito's example, "Usa in…" lists muro-sostegno and
  fond-trave-collegamento, choosing muro-sostegno prefills ag_g/f0/categorie with chips, editing ag_g clears its chip;
  a tool without consumers shows no button. Files: `js/usa-in.js`, `js/provenienza.js`, `css/usa-in.css`; small edits
  to `results-toolbar.js`, `router.js`, `forms.js`. Staging + full suite green as in §13.4.

## 16. Excel mode retires per approved tool (phase 7, 2026-09-22)
Data: `GET /api/divergences/riepilogo` -> `{per_strumento: {tool: {da_confermare, approvato, respinto}}}` (already
fetched by the rail badge and refreshed after every sign-off). A tool is **approvato** when it has register entries,
`da_confermare == 0` and `respinto == 0`.
- For an approved tool the input `legacy_compat` ("Riproduci il foglio Excel originale") is not rendered in the Dati
  column (its value is always false), the "Confronta con Excel" toolbar button is hidden, and the tool header's
  correction link reads "Correzioni approvate" (muted, still a link to the register filtered on the tool).
- A share link or a saved element that carries `legacy_compat: true` for an approved tool loads with the switch
  forced off and a dismissible note: "Modalità Excel non più disponibile: tutte le correzioni di questo strumento sono
  state approvate." Nothing else changes; a later rejection (respinto > 0) brings the switch back.
- Tests (`tests/e2e/test_excel_ritirato.py`): approve every entry of one tool through the API (`signoff-multiplo`),
  reload the tool: no switch, no compare button, header text; reject one entry: both come back.

## 17. Avvisi that point at a parameter (user feedback 2026-09-22)
`Report.avvisi_campi: {warning text: input field name}` — a tool sets it for every warning that is about ONE input
(`success(..., avvisi_campi=…)`; `execute()` adds the Excel-mode trace warning -> `legacy_compat`). The results
panel "Dettaglio avvisi" renders such a warning as a text button; clicking it opens the field's accordion section
(and "Avanzate" when needed), scrolls the field into view, focuses its control and flashes it once
(`js/campo-salto.js`). Without an entry the UI falls back to the first input whose `symbol` appears as a whole
word in the text; a warning with no field stays plain text. Also from the same feedback: the sticky Sintesi
collapse has hysteresis (collapse past 200 px, expand back under 40 px) and gives the removed height back as
bottom padding on the results pane (`--sm-collapse-spacer`) so the scroll range never shrinks — no flicker, no
jump; the Dati action bar wraps its live-status text instead of overlapping the save widget.

## 18. Editable dimensions in the sketch (owner's request 2026-09-22)
A dimension in the Sintesi sketch whose text reads `<symbol> = <value> <unit>` and matches a NUMBER input field by
symbol AND unit (or that the Python sketch names explicitly with `Quota.campo`, when the drawing prints another
symbol or unit than the field carries — geo cedimenti `B`/`Δz`, trave di collegamento in m vs mm) is rendered
as a button: dotted underline, `role="button"`, `tabindex="0"`, tooltip "Modifica b = 15,00 m (Invio)". Click or
Enter/Space opens a popover next to it (`form.sk-edit`, `role="dialog"`, `position: fixed`, one text input with
`inputmode="decimal"`, the field's unit, Applica/Annulla). Enter applies, Esc or a click outside cancels and
focus returns to the dimension. Applying writes the Dati control and dispatches a native `input` event, so
js/forms.js's own `handleChange` runs unchanged (validation, persistence, live run, redraw) and the field flashes
(`.f-field--flash`); a non-number is refused in place ("Inserire un numero"). The printed relazione renders the
same sketch WITHOUT the fields, so nothing is editable on paper. Computed dimensions (wall base `B`, `2d`) never
match and stay plain. Modules: `js/schizzo-modifica.js` (matching + popover), `sketch.js`/`sketch-shapes.js`
(`campi` option → `data-campo` on the text group), `results.js` (passes `tool.fields`, mounts the editor on
`#sintesi`). Tests: `tests/e2e/test_schizzo_modifica.py`, `tests/e2e/schizzo_modifica.test.mjs`.
Same rule for every text-bearing shape (owner's example, the wall section): labels (`Etichetta.simbolo = testo`),
load arrows (`Freccia.testo`) and diagram texts (`Diagramma.etichette`) — the muro's `q = 2 kN/m²` diagram text edits
`q_kN_m2`. Unit strings are compared after `²→2`, `³→3`. On the automatic path the SHOWN number must equal the
field's current value at the displayed precision (`valoreCampoCorrente`): a result label that shares an input's symbol
and unit (`S_stat = 30 kN`) is never linked. `Etichetta.campo`/`Freccia.campo` exist like `Quota.campo`; a computed
total may point at the input it is driven by (the wall's `H` → `h_muro_m`; the popover names the field, so the edit
is unambiguous). Composite dimensions with several inputs (`B` = mancia + paramento + tacco) stay plain.
Permanent rule (`tests/shared/test_sketch_campi.py`, mirrors the JS matching over every tool's example sketch): a text
carrying the symbol of a numeric input must be linked (automatically or via `campo`), `campo` must name an existing
numeric input, and a COMPUTED text must not borrow an input's symbol (punching `a` → `a_gov`, settlement layer
thickness `Δz` → `s`, since `Δz` is the discretisation step input).

## 19. Varianti affiancate (owner's request 2026-09-22)
Purpose: the engineer tries two to four versions of the same element ("plinto 1,80 m" vs "2,00 m" vs "2,00 m,
cls C30/37"), sees them side by side with checks, utilisation and verdict, keeps one and saves it. No new
engineering: every column is an ordinary run of the same tool.

### 19.1 Where variants live (decided)
A **client-side working set, per tool, in `sessionStorage`** (`sm.varianti.<tool>`: survives a reload and a
visit to another tool, dies with the browser tab), NOT in SQLite. Reasons, after reading `storage/` and
`routes/progetti.py`: (a) variants must work without a project (§14.1: nothing changes when none is selected);
(b) saving each attempt as an element would fill the project table (§20) and the project report (§14.3) with
discarded attempts; (c) what is kept is already covered by elements + revisions: the chosen variant becomes a
normal element (POST) or the next revision of the element it started from (PUT with `revisione`), and the
revision history keeps the previous inputs. **No SQLite schema change, no new endpoint.** Stored shape (immutable
updates only, one JSON object): `{attiva: "B", varianti: [{id: "A", nome: "A", inputs, origine: {elemento_id,
revisione, nome} | null}]}` — ids are the letters A–D, `nome` is editable (≤ 40 chars, default the letter).
Results are never stored: every column is recomputed (`POST /api/tools/{name}/run`) when shown.

### 19.2 Behaviour in the tool page
- **Crea variante** (Dati action bar, next to "Carica esempio"; icon "⧉" + word). The first press turns the current
  form into variant A and a copy of it into variant B, and B becomes active; later presses copy the ACTIVE
  variant. Maximum **4** (`MAX_VARIANTI`); at 4 the button is disabled with the tooltip "Massimo 4 varianti".
  When the form was opened from an element (`?elemento=<id>`), A carries `origine` (id, revisione, nome).
- **Variant strip** above the form (under the §15/§16 notices): `role="tablist"`, one tab per variant ("A",
  "B · cls C30", …) + **Affianca** (opens §19.3) + **Chiudi varianti** (confirm: "Le varianti non salvate
  saranno scartate"). ←/→ move between tabs, Enter/Space activates; activating a tab writes that variant's inputs
  into the form through `api.setValues()` (live run as usual). Every valid form change updates the active
  variant's `inputs` (same hook as `form-state.save`). Per-tab menu: Rinomina, Duplica, Elimina (not on the last
  remaining one). With variants open the header shows "Variante B di 3".
- A tool change leaves the set in `sessionStorage`; coming back restores the strip and the active variant.
  Opening an element, "Carica questa revisione" or a "Usa in…" link while a set exists asks first: "Chiudere le
  varianti aperte?" (Chiudi e carica / Annulla).

### 19.3 Page `#/varianti/<tool>` ("Affianca")
One column per variant (≥ 1440 px: 4 columns fit; 1100–1439 px: columns keep a 320 px minimum and the grid
scrolls horizontally inside `.r-table-scroll`; < 1100 px: one column at a time with the same tablist on top).
A `<table>` with variants as columns (`<th scope=col>` sticky) and rows aligned across columns (`<th scope=row>`):
1. Head: variant name (editable inline), origin ("da P1, rev. 4" when `origine`), **Tieni questa**.
2. Verdict: icon + word as in the Sintesi (`✓ Verificato` · `✕ Non verificato` · `! Errore` + the first Italian
   error), η max (2 decimals) with the `verdict.js` bar, verifica governante.
3. The small sketch (`sketch.js`, same fit as the Sintesi, no §18 editing, `aria-hidden` + figcaption).
4. **Verifiche**: one row per check name in the union of all columns (ordered by `sortChecks` on the reference
   column); cell = η + ✓/✕ + word; a check absent from a column shows "—".
5. **Risultati**: the highlighted outputs (the selection `elemento-sintesi.js` uses for `evidenze`), then, behind
   "Mostra tutti i risultati", every scalar output.
6. **Dati**: by default ONLY the inputs that differ between at least two variants ("Dati diversi: 3 di 24");
   "Mostra tutti i dati" reveals the rest. Table inputs compare as a whole ("tabella: 2 righe diverse su 5").
Differences are always **icon + word**, never colour alone. The reference column is A (switchable: select
"Confronta con"). An input cell different from the reference carries "≠ diverso"; a result or η cell carries
"▲ +12,5 %" / "▼ −3,0 %" relative to the reference (1 decimal; "= uguale" when equal at displayed precision); a
verdict different from the reference carries "≠ esito diverso". The page never ranks variants or picks a "best".
Runs: sequential, one per variant, `aria-busy` on the column while its run is in flight; a run error fills its own
column and leaves the others intact. Keyboard: the table is Tab-reachable (`tabindex="0"`, `aria-label="Confronto
varianti"`), every button reachable; Esc or **Torna al calcolo** returns to `#/<tool>` with the active variant
unchanged. Print (`@media print`): the table as it is, no buttons, with the §10 mode line per column — a working
sheet, not the relazione (the relazione stays per element).

### 19.4 Keeping one ("Tieni questa")
A dialog with three outcomes, all through existing code paths:
- Project selected and `origine` set: **Aggiorna "<nome elemento>"** = PUT `/api/elementi/{id}` with the variant's
  inputs, `sintesi`/`stato` from its run (same builder as §14.1), `revisione` from `origine`, and the revision
  `nota` prefilled "Variante B scelta fra A, B, C" (editable). 409 → the existing conflict dialog of §14.1
  ("Ricarica" / "Salva come copia").
- Project selected: **Salva come nuovo elemento** = POST `/api/progetti/{id}/elementi` (the §14.1 dialog, nome
  prefilled "<nome dell'origine o titolo dello strumento> – variante B").
- Always: **Usa solo nel modulo** = the variant's inputs go into the form, nothing is saved.
After Aggiorna or Usa solo nel modulo the set is closed (the dialog says so beforehand) and the tool page shows
the kept inputs. After Salva come nuovo the dialog offers "Chiudi le varianti" or "Tieni aperte" (so several
variants can be saved in turn); there is no bulk "save all" in this phase.

### 19.5 Files, backend, CSP, tests
New modules (each ≤ 400 lines): `js/varianti-state.js` (pure: create/copy/rename/delete/activate over an immutable
set, `sessionStorage` through `storage.js`, `MAX_VARIANTI`), `js/varianti-diff.js` (pure: input diff incl. tables,
relative deltas, union of checks; node-testable), `js/varianti-bar.js` (strip + "Crea variante"),
`js/varianti-confronto.js` (page, runs, table), `js/varianti-tieni.js` (§19.4 dialog), `js/elemento-conflitto.js`
(the 409 dialog extracted from `elemento-salva.js`, 373 lines today, so both callers share it),
`css/varianti.css`. Touched: `router.js` (`#/varianti/<tool>`), `forms.js` (mount the strip, update the active
variant on change), `elemento-salva.js` (use `elemento-conflitto.js`; export its payload builder),
`elemento-sintesi.js` (build `sintesi`/`stato` from a given report, not only from `getReportState()`),
`shortcuts.js` (the sheet lists ←/→ on the strip). Backend: none. CSP (rule 4): nothing inline, column widths by
class, the delta arrows are text, `el.style.setProperty` only for sticky offsets. Tests:
`tests/e2e/test_varianti.py` (from an example create 3 variants, change one input in B, Affianca shows 3 columns
with "≠ diverso" on that input only and "Dati diversi: 1 di N", η delta with ▲/▼ text; reload keeps the set; at
4 the button is disabled; Tieni questa → Salva come nuovo creates one element; from `?elemento=` → Aggiorna does a
PUT and the history gains a revision with the prefilled nota; a stale `revisione` (second PUT through
`page.request`) → 409 dialog; a run error in one column leaves the others), `tests/e2e/varianti_diff.test.mjs`
(pure diff: scalars, tables, missing checks, equal at displayed precision → "= uguale").

Decisioni ingegneristiche aperte: nessuna.

## 20. Tabella di progetto (owner's request 2026-09-22)
The element list of `#/progetti/<id>` (§14.3) becomes a real table: every element of the project, sortable,
filterable, keyboard-driven, opened with a click. It READS what was saved and never recomputes (the project
report of §14.3 remains the place where every element is recalculated).

### 20.1 What is saved today, what is missing
`Elemento.sintesi` (free JSON in `storage/models.py`, TEXT column in `elemento` and `elemento_revisione`) holds
`{ok, eta_max?, verifica_governante?, evidenze}` from the last successful run (`js/elemento-sintesi.js`); the
element also has `stato` and `aggiornato`. So η max, esito (`stato`) and the date of the last revision
(`aggiornato`, written by the save that created the current `revisione`) are already there. **Missing: the
warnings** (and the error text of a failed run). Decision: extend the summary **computed at save time** (the moment
`sintesi` is built today; stored with the element AND its revision) — no SQLite migration, no API change, the
column is already JSON: `sintesi.avvisi = {n: <count>, primo: "<text of the first warning>"}` and, when `ok` is
false, `sintesi.errore = "<first Italian error>"`. The Excel-mode trace warning that `execute()` appends is not
counted (the mode is shown by `modalita`). **"Avviso più grave" is not definable today**: `Report.warnings` is a
plain tuple of strings with no level (`shared/report.py`), so the table shows the count and the FIRST warning in
the tool's own order. A gravity level would change the shared contract (rule 15) and every tool: a question for
the owner (below), not part of this section.
Also at save: when live calculation is on and a run is pending or in flight, "Salva" waits for it (`live.js`
`whenSettled()`, at most the debounce + one run), so the saved summary belongs to the saved inputs and
`dati_modificati` remains only when that run could not complete. Elements saved before this change lack `avvisi`:
their cell shows "n.d." with the tooltip "Riepilogo salvato con una versione precedente: apri e salva l'elemento
per aggiornarlo". Optional backend hardening (small, same change): `_ElementoBody.sintesi` stays a `dict` but
rejects a non-numeric `eta_max` and a non-integer `avvisi.n` with the standard Italian 400 envelope.

### 20.2 Table
Columns (`<table>`, `<caption>` "Elementi del progetto", sticky `<th scope=col>`): **Strumento** (sigla chip, tool
title in the tooltip), **Nome** (link `#/<tool>?elemento=<id>`, the element's sigla after it), **η max** (2
decimals + the `verdict.js` bar; "—" when absent), **Esito** (icon + word: `✓ Verificato` · `✕ Non verificato` ·
`○ Dati modificati` · `! Errore di calcolo`), **Avvisi** ("2 · <first warning cut to one line>", full text in the
tooltip; "Nessuno"; "n.d."), **Ultima revisione** (date and time, "rev. 4" muted). The §14.3 row actions
(Duplica, Rinomina, Storia, Elimina/Ripristina) move into a per-row **Azioni** menu button in the last column. When
`stato = dati_modificati`, η max and Avvisi are muted and prefixed "(prec.)": they belong to earlier inputs. A
click anywhere on a row outside Azioni follows the Nome link; Ctrl/Cmd+click and middle-click on the link open a
new tab as usual.
- **Sort**: each header is a `<button>` inside its `<th>`, `aria-sort` on the `<th>`; the first click sorts
  ascending (η max: descending first), the second reverses. Missing values always last; stable, secondary key
  Nome. Default: Ultima revisione, descending (as §14.3 today).
- **Filter** (one row above the table): "Cerca" text (nome, sigla, tool title; case- and accent-insensitive),
  select Strumento (siglas present), select Esito, checkbox "Solo con avvisi"; counter "8 di 23 elementi";
  "Azzera filtri" while any filter is active; empty result: one sentence + "Azzera filtri".
- Sort and filters live in the hash query (`#/progetti/<id>?ordina=eta&verso=desc&strumento=PLI&esito=
  non_verificato&avvisi=1&q=plinto`), so Back/Forward and shared links reproduce the view.
- **Keyboard**: Tab reaches the filters, the header buttons, then the table body; in the body ↑/↓ move a roving
  focus across rows (focus sits on the Nome link), Home/End first/last, Enter opens, the context-menu key or
  Shift+F10 opens Azioni. Footer: "23 elementi · 17 ✓ verificati · 4 ✕ non verificati · 2 ○ dati modificati ·
  η max del progetto 0,94 (P3)".
- Print (`@media print`): the filtered, sorted table without buttons under the project cartiglio — a quick status
  sheet, distinct from "Relazione di progetto".

### 20.3 Files, backend, CSP, tests
New: `js/progetto-tabella.js` (render, header buttons, roving focus, query sync), `js/progetto-tabella-dati.js`
(pure: row model from elements, sort, filter, footer counts; node-testable), additions to `css/progetti.css`.
Touched: `progetto-elementi.js` (row actions become the Azioni menu; list rendering moves to the table),
`progetto.js` (mount), `elemento-sintesi.js` (`avvisi`, `errore`), `elemento-salva.js` (await `whenSettled()`),
`live.js` (export `whenSettled()`). Backend: none required; the optional validation of §20.1 goes in
`web/routes/progetti.py` with a unit test under `tests/web/`. CSP: nothing inline; the η bar width through
`el.style.setProperty`, as `verdict.js` already does. Tests: `tests/e2e/test_progetto_tabella.py` (three elements
of different tools saved through the UI, one with warnings and one failing a check: η, esito words and "1 ·
<text>" shown; sorting by η puts missing values last; filters by esito and "Solo con avvisi"; the query survives a
reload and Back; ↓ ↓ Enter opens the right element; an element POSTed through `page.request` without `avvisi`
shows "n.d."; opening the page sends no `/run` request — asserted with `page.on("request")`),
`tests/e2e/progetto_tabella.test.mjs` (pure sort/filter/footer).

Decisioni ingegneristiche aperte: nessuna di calcolo. One contract question for the owner: should warnings get a
gravity level, so that "avviso più grave" means something? (It changes `shared/report.py`, rule 15.)

## 21. Annulla e ripristina sui dati del modulo (owner's request 2026-09-22)
Excel reflex (§0.1): a wrong edit is undone with Ctrl+Z. Scope: the VALUES of the Dati form of the current tool
(every field, conditional ones included, and table inputs). Out of scope: project/element records, register
sign-offs, relazione overlay settings.

### 21.1 Behaviour
- Keys: **Ctrl+Z / Cmd+Z** annulla; **Ctrl+Shift+Z / Cmd+Shift+Z** and **Ctrl+Y** (Windows habit) ripristina.
  Buttons in the Dati action bar, after "Carica esempio": "↶ Annulla" and "↷ Ripristina" (icon + word; accessible
  names "Annulla modifica" / "Ripristina modifica", which contain the visible word). Disabled (`aria-disabled`,
  still focusable, DESIGN_SPEC §3 disabled style) when there is nothing to undo/redo; the tooltip names the step
  ("Annulla: Altezza muro 3,00 → 3,50 m"). After each undo/redo a polite live region says "Annullato: Altezza
  muro" / "Ripristinato: …", the field flashes (`.f-field--flash`, as §17/§18) and its accordion section opens if
  collapsed (reuse `campo-salto.js`).
- **Native undo first**: when the focused element is a text control whose value differs from the current snapshot
  (uncommitted typing), the key is left to the browser (character-level undo inside the box). Otherwise the app
  handles it and calls `preventDefault()`. The keys do nothing while a dialog or popover is open (§11 overlay, §18
  popover, §14 dialogs).
- **Granularity**: one step per CONFIRMED field change. Consecutive `input` events on the same control are one
  step, closed by its `change` event, by focus leaving it, or by an edit in another control. A select, checkbox or
  unit-selector change is one step. Table inputs: one step per committed cell edit; a paste (`table-paste.js`), a
  row insert or a row delete is one step. The snapshot is the full value object of every field (`allValues`,
  hidden conditional fields included, so undoing a switch brings back what was typed under it).
- Applying a snapshot uses `api.setValues()` and then dispatches ONE `change` on the form, so `handleChange` runs
  as for a manual edit (validation, `form-state.save`, live run, redraw, `dati_modificati` on a loaded element). A
  new edit after an undo discards the redo branch. Limit: **100 steps** (`MAX_PASSI_ANNULLA`); the oldest step is
  dropped silently.
- **§18 sketch edits are ordinary steps (unified history).** The popover's "Applica" writes the control and
  dispatches `input` + `change`, so the edit is one step and Ctrl+Z restores the previous value (the sketch follows
  through the live run). The popover's own "Annulla"/Esc keeps its meaning: discard an edit never applied (no step).
- **Carica esempio** is one undoable step (label "Carica esempio"): the engineer can get their own data back.
- **Boundaries that reset the history** (both stacks emptied, the loaded state is the new base): opening an element
  (`?elemento=`), "Ricarica" in the 409 dialog, "Carica questa revisione" (`?anteprima=1`), a "Usa in…" arrival
  (§15), "Tieni questa" (§19). Reason: undoing past a load would put another element's inputs under the loaded
  element's header, one "Salva" away from overwriting it.
- **Tool change**: each tool keeps its own history in memory for the life of the tab (a `Map` keyed by tool,
  immutable stacks). Coming back to a tool whose current values equal the history's present resumes it; otherwise
  (values changed elsewhere) it starts empty. Nothing is persisted: a reload starts with an empty history.
- **Variants (§19)**: one history per variant (key `<tool>#<variante>`); switching tab is not a step.
- **§15 provenance chips** are not restored by undo (a prefilled value brought back by Ctrl+Z shows no chip):
  declared limitation, keeps §15's "editing clears the chip" rule simple.

### 21.2 Files, backend, CSP, tests
New: `js/annulla.js` (pure: `{passato, presente, futuro}`, `registra`, `annulla`, `ripristina`, coalescing by
control, `MAX_PASSI_ANNULLA`, step labels; every function returns a new object; node-testable), `js/annulla-ui.js`
(buttons, keys with the native-first rule, live region, wiring to the form API, per-tool/per-variant `Map`).
Touched: `forms.js` (mount; expose `allValues()`; report `change`/focus-out commits and the example load),
`fields.js` (read hidden fields too, if `visibleValues` cannot be reused), `table-input-events.js` /
`table-paste.js` (one commit per cell edit, paste, row operation), `schizzo-modifica.js` (dispatch `change` after
`input`), `elemento-salva.js` and `provenienza.js` (reset at the boundaries above), `shortcuts.js` (the sheet lists
the three combinations; its global keydown leaves Z/Y to `annulla-ui.js`). Backend: none. CSP: nothing inline;
icons are text glyphs or existing `icons.js` SVGs. Tests: `tests/e2e/test_annulla.py` (type 3,5 in a field + Tab →
one Ctrl+Z restores the old value and the live result follows; typing "123" is one step; while typing inside the
box Ctrl+Z is native and the app history is untouched; a select change, a table cell edit and a table paste are one
step each; Ctrl+Shift+Z and Ctrl+Y redo; a new edit clears redo; undoing "Carica esempio" brings back the user's
data; undoing a §18 sketch edit restores the field and the dimension text; opening `?elemento=` empties the history
(buttons disabled); switching tool and back keeps it; the buttons work by mouse and name the step in the tooltip;
`Meta+Z` path for macOS), `tests/e2e/annulla.test.mjs` (pure stacks: coalescing, limit 100, redo cleared, returned
objects never the same instance as the input).

Decisioni ingegneristiche aperte: nessuna.

## 22. `sketch-fit.js` split (module cap, 2026-09-22)
`js/sketch-fit.js` has 459 lines, over the 400-line cap (CLAUDE.md rule 12). It holds three independent parts;
split along them, code moved verbatim (no behaviour change), no re-export shims:
- `js/sketch-geometry.js` (~130 lines): `MIN_EXTENT` (now exported), `PADDING`, `isFiniteNumber`,
  `isFinitePoint`, `toScreen`, `dimensionOffset`, `diagramPolygon`, `boundsPoints`, `extend`, `boundsOfShapes`,
  `sizeOf`, `referenceSide`, `round6` (today's lines 1–135 minus the fit constants).
- `js/sketch-dimensions.js` (~115 lines): the "M2" block — `MIN_DIMENSION_OFFSET_PX`, `DIMENSION_STACK_PX`,
  `PARALLEL_TOLERANCE`, `MAX_DIMENSION_OFFSET_SHARE`, `direction`, `parallelAndOverlapping`, `DIAGRAM_LABEL_PX`,
  `leftNormal`, `diagramClearance`, `resolveDimensionOffsets`, `applyDimensionOffsets` (today's lines 342–452);
  imports `MIN_EXTENT` from `sketch-geometry.js` and `TEXT_PX`/`LABEL_GAP_PX` from `sketch-text.js`.
- `js/sketch-fit.js` (~220 lines): `STRUCTURAL_KINDS`, `ANNOTATION_KINDS`, `MIN_ELEMENT_SHARE`,
  `CENTER_BUDGET_SHARE`, `clampNear`, `centerAround`, the margin-aware scale helpers, `fitVista`, `uniformScale`;
  imports from the two modules above and `longestTextPx` from `sketch-text.js`.
Importers: `sketch-shapes.js` takes `toScreen`, `dimensionOffset`, `diagramPolygon` from `sketch-geometry.js`;
`sketch.js` takes `fitVista`, `uniformScale` from `sketch-fit.js` and `applyDimensionOffsets` from
`sketch-dimensions.js`. Safety net written BEFORE the move: `tests/e2e/sketch_fit.test.mjs`, a characterisation
test running `fitVista` and `applyDimensionOffsets` on every tool example's sketch views (dumped once to
`tests/fixtures/sketch_viste.json` by a small script in `scripts/`) against outputs recorded from the current
file; it must pass unchanged after the split. Also `tests/web/test_js_module_size.py`: every file in `static/js`
(and `static_next/js` when present) ≤ 400 lines (today `results.js` sits exactly at 400). The full e2e suite
(`test_sketch_quality.py`, `test_schizzo_modifica.py` included) runs on `static_next` before promotion (rule 3).

Decisioni ingegneristiche aperte: nessuna.
