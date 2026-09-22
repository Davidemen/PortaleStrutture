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
  Buttons in the Dati action bar: "↶ Annulla" and "↷ Ripristina" (icon + word; accessible
  names "Annulla modifica" / "Ripristina modifica", which contain the visible word). Implementation note: at
  1440px the row up to "⋯" already fills the width (`test_dati_action_bar_is_one_row`, a permanent test), so the
  two buttons sit on their own full-width line below the rest of the bar (`order: 5`, `flex-basis: 100%` in
  `forms.css`) instead of literally next to "Carica esempio"; still the first thing after the rest of the bar,
  same reading order. Disabled (`aria-disabled`,
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

## 23. "Dimensiona" — inverse sizing of one input (owner's request 2026-09-22)
Purpose: the engineer picks ONE numeric input (a dimension, a bar diameter or count, a thickness…) and asks for the
smallest value (or the largest, when the element gets safer as the value decreases) for which EVERY check passes
with utilisation η ≤ the target. The search runs on the server over the same `execute()` the run endpoint uses; the
UI never applies a result by itself. It works alongside §19 (varianti affiancate: a found value can be kept as a
variant) and §21 (applying the value is one undoable data change).

### 23.1 Owner's rule: rounding step and target are engineering choices (decided 2026-09-22)
The rounding step (`passo`) and the utilisation target (`obiettivo`) are chosen by the owner, never by the program.
Owner's decisions 17 and 18 (`docs/DECISIONI_DA_CONFERMARE.md`): both are SETTABLE office defaults, stored in
§26 "Impostazioni" and only PROPOSED by the dialog, which ALWAYS shows both; the search cannot start without them.
- `obiettivo`: prefilled with the §26 value `obiettivo_sfruttamento` (factory value 1,00, the code limit),
  editable per search, allowed range 0 < obiettivo ≤ 1,00 (above 1 a check fails by definition).
- `passo`: prefilled with the step §26.5 resolves for (tool, field): the per-field exception if one exists, else
  the step of the field's data type (§26.4), else — for integer fields only — 1 (the only meaningful step, still
  editable, e.g. 2 for symmetric layouts), else EMPTY and required. Factory settings hold no step at all, so until
  the office enters some, every non-integer field starts empty. Under the field the dialog says where the
  proposal comes from ("Passo d'ufficio per diametri di armatura" · "Passo d'ufficio per questo campo" · "Numero
  intero"), with a link to `#/impostazioni`.
- The body of the search request always carries the explicit `passo` and `obiettivo` shown in the dialog: the
  server never substitutes a setting, so a search is reproducible and a settings change never alters a search
  already open in a dialog, nor any saved element.
- The earlier per-model hint `json_schema_extra={"passo": …}` is dropped: steps live only in §26 (one place, set by
  the office, visible and resettable). The only per-model hint kept is `tipo_dato` (§26.4), which classifies a
  field and never carries a number.

### 23.2 How η is read from a Report (no contract change)
`Check` carries `passed` plus optional `value`/`limit` (`shared/report.py`). Most checks set `value=`/`limit=`;
today 20 of the 124 checks produced by the tools' examples do not (ca-pilastro-rettangolare 7, ca-pilastro-circolare
7, ca-trave-rettangolare 6: detailing rules such as bar spacing, minimum diameters, reinforcement percentages,
ductility, crack class — precisely the tools where "Dimensiona" is most wanted). The frozen list of
`test_copertura_rapporti.py` starts from exactly these 20. When the pair IS set, its orientation is not declared:
most checks are demand/capacity (`V_Ed ≤ V_Rd`, safe when the ratio is ≤ 1), some are capacity/demand or "minimum"
checks (`As = 3,93 ≥ As,min = 3,56`, ratio ≥ 1 when safe; `js/verdict.js` `effectiveUtilisation` already flips those
in the UI), and some are "ceiling" checks that the calculation also treats as a validity limit (`ρl ≤ ρl,max` in
ca-taglio-non-armato). Server rule, pure function in `shared/dimensiona/sfruttamento.py`:
- Raw ratio r = value/limit when both are finite, limit ≠ 0 and they have the same sign; otherwise the check has
  no ratio. The `detail` text is never parsed on the server (it is written for people).
- Orientation is learned per check NAME only from the `N_CAMPIONI` initial samples of §23.3 point 2 (probing, not
  hand tables), then stays fixed for bisection and confirmation: "diretto" when `passed ⇔ r ≤ 1` holds on every
  initial sample where the check has a ratio, "inverso" when `passed ⇔ r ≥ 1` holds; η = r or 1/r accordingly. A
  check whose initial samples contradict both (or that sits exactly on r = 1 in every sample) is demoted to
  outcome-only for that search. If a LATER evaluation (bisection, confirmation) contradicts the fixed orientation,
  the check keeps that orientation anyway, `affidabile = false`, and `motivi` gets "Orientamento della verifica
  <nome> incoerente".
- Outcome-only checks (no ratio, or orientation undecidable) still take part: a sample is admissible only if every
  check passes AND every check with η has η ≤ obiettivo. The search therefore bisects on a boolean outcome and works
  with outcome-only checks too; the response lists them in `verifiche_solo_esito` and the UI says so ("Considerate
  solo come esito, senza obiettivo: …"). Whether that is acceptable is decision 19.
- Outcome-only checks in a sizing are accepted (owner's decision 19, 2026-09-22): no contract change for them.
- **Target on minimum/detailing checks — setting `obiettivo_su_verifiche_minimo` (§26, decision 19-bis still
  open, factory value `false`).** The server reads it from the §26 repository at request time and echoes it in the
  response. With `false`: the target applies only to "diretto" checks (value ≤ limit); "inverso" checks (value ≥
  limit: minimum reinforcement, minimum cover…) count as pass/fail only and are listed in
  `verifiche_senza_obiettivo` — an `obiettivo < 1` turning `As ≥ As,min` into `As ≥ 1,25·As,min` is a margin the
  program must not invent. A "diretto" ceiling/detailing check (`ρl ≤ ρl,max`) cannot be told apart from a
  resistance check without a `verso`/category contract, so with `false` and `obiettivo < 1` the response is always
  `affidabile = false` with the `motivo` "Obiettivo applicato anche a eventuali limiti massimi di dettaglio:
  controllare". With `true`: the target applies to every check with η (both orientations), `verifiche_senza_obiettivo`
  is empty and that `motivo` is not added.
- Contract proposal, NOT done (rule 15, needs the owner's go-ahead): an optional `Check.verso: "max" | "min"`
  ("value must stay below / above limit") would make the orientation explicit and remove the learning step. Until
  then a permanent test (`tests/shared/dimensiona/test_copertura_rapporti.py`) runs every tool's example and
  compares the set of checks without `value`/`limit` to a frozen list, so a new outcome-only check is noticed.

### 23.3 Search algorithm (monotonicity NOT assumed)
Pure functions in `src/strutture/shared/dimensiona/` (each module ≤ 150 lines, functions ≤ 40), `Decimal` for the
grid so that 0,05 steps never drift:
1. **Grid** (`griglia.py`): the multiples of `passo` inside [da, a]; at most `MAX_GRADINI = 10 000` steps, else 422.
   Integer fields: integer multiples only.
2. **Sampling**: `N_CAMPIONI = 17` grid points evenly spread, both ends included (fewer when the grid is smaller).
   Each evaluation = `execute(tool, {**inputs, campo: v})` in the request's mode (`legacy_compat` as sent; forced
   off for an approved tool, §16 and §23.4). For each
   sample the `warnings` are compared to the base run's (§23.4 `inputs`): a warning that was not there before is
   remembered against that grid value. Outcome per sample: `ammissibile`, `non_ammissibile`, or `errore` (`ok=false`:
   the value is outside the method's validity range; the Italian error is kept). An `errore` sample counts as a
   BOUNDARY, never as `ammissibile`: it separates whatever lies on each side, exactly like an admissibility change.
3. **Direction** (`verso.py`): `verso: "auto"` by default, or `"minimo"`/`"massimo"` forced by the user.
   - Auto reads the admissibility pattern of the samples, with `errore` treated as a boundary (not ignored): N…N
     A…A → search the minimum; A…A N…N → the maximum; all A → see below; all N → `esito = "nessun_valore"` with the
     best sample (lowest η_max) reported; more than one change (of admissibility OR into/out of `errore`) → not
     monotone, see 5. When the response lands exactly on the boundary between an `errore` band and an `A` band, that
     boundary is refined by bisection (`errore` treated as `N` for the interval only), `esito = "limite_validita"`,
     `affidabile = false`, motivo "Il valore trovato è il limite di validità del metodo (<messaggio d'errore>), non
     il limite delle verifiche". `estremo_sufficiente` (below) is only returned when the sample AT the extreme is
     `ammissibile`, never when it is `errore`.
   - All A (and the extreme sample admissible): the η_max trend over the samples decides which end is the answer
     and `esito = "estremo_sufficiente"` ("Già il valore <da|a> soddisfa le verifiche: allargare l'intervallo"). If
     every check in play is outcome-only (no η at all), or η_max is constant or changes direction between samples,
     the trend does not exist: the program does not guess an end — `esito = "estremo_sufficiente"`, `valore = null`,
     motivo "Tutto l'intervallo soddisfa le verifiche: scegliere Valore minimo o Valore massimo".
   - Forced `verso`: with `"minimo"` forced, if `da` is admissible, `esito = "estremo_sufficiente"` at `da`; if no
     sample is admissible, `esito = "nessun_valore"`; otherwise bisect between the last N and first A in that
     direction; a sequence that contradicts the forced direction (e.g. A…A N…N with `"minimo"` forced) falls into
     the not-monotone case 5. Symmetric for `"massimo"` (`a`, N…N A…A).
4. **Bisection** (`ricerca.py`) on grid indices between the bracketing samples (last N, first A in the search
   direction) until they are adjacent; the answer is the admissible grid value. If a bisection point itself returns
   `errore` (a validity gap invisible to the initial sampling), the bisection stops there: the adjacent grid values
   are evaluated outward on both sides up to `MAX_VALUTAZIONI` looking for the nearest non-`errore` point; the
   answer is the last `A` found near that gap, `affidabile = false`, and `motivi` gets "Fra <v1> e <v2> il metodo
   non è applicabile: <messaggio>". An `errore` point never counts as `A`. Then a **confirmation**: the next
   `N_CONFERMA = 3` grid values beyond the answer (towards "safer") are evaluated; any non-admissible one, or any
   new warning appearing at the answer or at a confirmation point (see point 2), sets `affidabile = false` and adds
   the warning text to `motivi`.
5. **Not monotone** (several admissibility changes, confirmation failed, or an `errore` sample inside the bracket):
   every admissible window found by sampling is refined at its near edge, the answer is the best edge in the
   requested direction, `affidabile = false` and `motivi` lists the windows ("Ammissibile per b in [0,30; 0,45] e
   [0,60; 1,00]: l'andamento non è monotono, controllare"). Always declared, never hidden: sampling cannot see
   windows narrower than one sampling interval, and the response says so ("Campionamento: 17 punti su 181 valori").
6. **Limits**: `MAX_VALUTAZIONI = 80` tool runs and `TEMPO_MAX_S = 10` s (wall clock, checked between runs); when
   hit, `esito = "interrotta"`, the best bracket found so far and `affidabile = false`. Runs are off the event loop
   (`run_in_threadpool`); at most `MAX_RICERCHE_CONTEMPORANEE = 2` searches per process (semaphore). Semaphore and
   clock live in `app.state.dimensiona` (built in `create_app`, replaceable in tests); `TEMPO_MAX_S` and
   `MAX_VALUTAZIONI` are parameters passed to the pure search functions, not module constants, so a test does not
   have to wait 10 s to see "interrotta". A third concurrent search gets 429 "Un'altra ricerca è in corso: riprovare
   fra qualche secondo." The global rate limit counts one request. The dialog's "Annulla" only aborts the browser's
   request (`AbortController`); the server-side search still runs to completion or to its own limits and keeps the
   semaphore until then — a search restarted immediately after Annulla can still get 429.
7. **Grid and validation edge cases**: an empty grid (`passo` has no multiple strictly between `da` and `a`) is 422
   "Nessun multiplo del passo fra da e a"; a non-integer `passo` on an integer field is 422 "Il passo deve essere
   intero"; `gt`/`lt` schema bounds are exclusive (`da`/`a` must be strictly inside), `ge`/`le` are inclusive — the
   422 in §23.4 for "range outside the field's schema bounds" is checked accordingly (`da > exclusiveMinimum`,
   `a < exclusiveMaximum`). A field that is `null` in the base `inputs` (an alternative input group, e.g.
   `asl_mm2` vs `n_barre`+`diametro`) is accepted for `campo`: the trial value is substituted for it and the other
   alternative fields are left as sent, with the tool's own validation errors surfacing as `errore` samples.
   `report` in the response is `null` when `valore` is `null` (`nessun_valore`, or `estremo_sufficiente` with
   `valore = null`).

### 23.4 API
New router `src/strutture/web/routes/dimensiona.py` (keeps `routes/tools.py` small), mounted under `/api/tools`:
`POST /api/tools/{name}/dimensiona`, body
`{inputs: {…the run payload…}, campo, da, a, passo, obiettivo, verso?: "auto"|"minimo"|"massimo"}`.
`build_dimensiona_router(tools, signoffs, impostazioni, register=None)` (the §26 repository, read once per
request for `obiettivo_su_verifiche_minimo`) is wired in `web/app.py` next to `build_tools_router`;
"approved" (for the "forced off" legacy_compat rule of §16/§23.3 point 2) is computed with the same
`riepilogo_per_strumento` of §25.2 (approvato = register entries present, `da_confermare == 0` and `respinto == 0`).
An element saved in Excel mode for a tool that later becomes approved recalculates in standard mode, as §16.
Response 200: `{ok: true, campo, verso, esito:
"trovato"|"estremo_sufficiente"|"nessun_valore"|"interrotta"|"limite_validita",
valore: number|null, affidabile, motivi: [str], governante: {nome, eta}|null, verifiche_solo_esito: [str],
verifiche_senza_obiettivo: [str], campioni: [{valore, esito, eta_max, messaggio?, avvisi_nuovi: [str]}], valutazioni,
durata_s, modalita, correzioni: {da_confermare, respinto}, obiettivo, passo, obiettivo_su_minimi: bool,
report: <run envelope at `valore`>}`.
`verifiche_senza_obiettivo` lists the checks the target was NOT applied to under the §23.2 rule ("inverso" checks
when `obiettivo_su_minimi` is false); `obiettivo`/`passo` echo the body; `modalita`/`correzioni` are read the same way as §25.2 so the UI can show the same
"⚠ riproduce il foglio Excel" / "◐ Provvisorio" caveats as a saved element (§23.5).
Errors (standard envelope, Italian `errors[0]`, `error_details.loc` naming the body key): 404 unknown tool; 422
unknown or non-numeric `campo` (tables, enums, booleans and `legacy_compat` are refused: "Il campo … non è
numerico"), missing or non-positive `passo` ("Indicare il passo di arrotondamento"), `obiettivo` outside (0; 1],
`da ≥ a`, range outside the field's schema bounds (§23.3 point 7: exclusive bounds enforced strictly), empty grid,
non-integer `passo` on an integer field, too many steps, invalid base `inputs` (the run's own messages); 429 as
above; 500 envelope on an unexpected exception (logged with the tool name, never the inputs). Frozen pydantic models
for body and response in `shared/dimensiona/modelli.py`.

### 23.5 UI
- Entry points: a results toolbar button **"⌖ Dimensiona…"** (icon + word) when the last run succeeded, and a
  "Dimensiona" link in §18's sketch popover for the field being edited. Keyboard: `g d` opens the dialog on the
  focused (or last focused) numeric field, chosen outside text fields only — `shortcuts.js` ignores every key while
  the target is editable (`isEditableTarget`), so `g d` cannot fire from inside a field. A `focusin` listener on the
  Dati form remembers the last numeric field that had focus; `g d` opens the dialog preselected on that field (or
  the first numeric field if none had focus yet); the shortcut sheet lists it.
- Da / A prefill, per side: `da` = the field's `minimum` when it is inclusive (`ge`); otherwise
  `max(minimum, current × 0,5)` if a `minimum`/`exclusiveMinimum` exists, else empty. Symmetrically `a` = `maximum`
  when inclusive (`le`); otherwise `min(maximum, current × 2)` if a bound exists, else empty. If the current value is
  ≤ 0, both sides start empty and required (×0,5/×2 of a non-positive number is not a useful proposal). Both remain
  always visible and editable; the field is never prefilled with an exclusive bound itself (h `gt=0`: Da starts at
  `min(current × 0,5, …)`, never 0).
- Dialog (`role="dialog"`, non-modal side panel so the Dati stay readable, `aria-labelledby` on the title): Campo
  (select of numeric inputs grouped like the Dati sections, symbol + label + unit; focus starts here on open), Da /
  A (above), **Passo** (prefilled per 23.1 from §26, else empty and required; changing Campo re-resolves it unless
  the user already typed one), **Obiettivo di sfruttamento** (prefilled from §26), a read-only line "Obiettivo
  anche sulle verifiche di minimo: no|sì (Impostazioni)" linking to `#/impostazioni`, Verso (Automatico ·
  Valore minimo · Valore massimo), "Cerca" (Enter inside the dialog; `Ctrl+Enter` inside the dialog is handled by
  the dialog's own handler, which calls `preventDefault()` + `stopPropagation()` so the global "Calcola" shortcut of
  §6 does not also fire), disabled with `aria-disabled` + `aria-describedby` pointing at the reason text (still
  reachable by Tab) until Passo is valid. While running: "Ricerca in corso…" announced in an `aria-live="polite"`
  region, and "Annulla" (Esc while running = abort via `AbortController`; the search on the server is not
  cancelled, see §23.3 point 6). Esc at rest closes the dialog and returns focus to whichever control opened it.
  Below 720 px width (§9) the panel becomes a full-width sheet under the Dati instead of a side panel.
- Result block: `<symbol> = <valore> <unit>` in large type, η max and governing check, then the reliability line as
  icon + word: "✓ Affidabile" or "⚠ Da controllare" + every `motivo`; outcome-only checks listed separately from
  `verifiche_senza_obiettivo` (§23.4). With `modalita = "excel"`: "⚠ Valore trovato riproducendo il foglio Excel,
  errori inclusi" and `affidabile = false`; with pending register corrections on the tool (§25.2 rule): "◐
  Provvisorio" with the same text and register link as §25.2. The same `aria-live` region announces the result once
  ready: "<simbolo> = <valore> <unit>, affidabile" or "…, da controllare". Disclosure "Campioni" = accessible table
  (valore · esito · η max · avvisi nuovi). Buttons **"Applica"** (writes the Dati control and dispatches `input`
  then `change`, as §18 after §21, so it is exactly one undo step in §21 labelled "Dimensiona: <simbolo> <vecchio> →
  <nuovo>"; the field flashes) and **"Studia la sensibilità"** (opens §24 with the same field and range). "Nessun
  valore", "interrotta" and "limite_validita" show the best sample and no Applica.
- Modules: `js/dimensiona.js` (dialog, ≤ 400 lines), `js/dimensiona-api.js`, `js/dimensiona-esito.js`,
  `css/dimensiona.css`; small edits to `results-toolbar.js`, `shortcuts.js`, `schizzo-modifica.js`. Settings are
  read through `js/impostazioni-api.js` (§26.7: `leggiImpostazioni()` cached per page load and dropped on the
  `impostazioni:salvate` event, `passiStrumento(tool)`). CSP (rule 4):
  no inline style or script, no `innerHTML`, geometry via classes or `style.setProperty`.

### 23.6 Acceptance
- Unit (`tests/shared/dimensiona/`): `test_griglia.py` (Decimal multiples, integer fields, MAX_GRADINI, empty grid,
  non-integer passo on an integer field), `test_sfruttamento.py` (direct, inverse, contradictory → outcome-only,
  sign mismatch, limit 0, target not applied to a minimum/detailing check), `test_ricerca.py` with synthetic
  `valuta` callables: monotone increasing and decreasing, all admissible (with and without an η trend), none, two
  windows (→ `affidabile=false`, both windows in `motivi`), an `errore` band at a sampling point, an `errore` at a
  bisection point (§23.3 point 4), forced `verso` in and against the sequence, a new warning appearing at the
  answer, orientation contradicted after being fixed, evaluation and time limits; `test_copertura_rapporti.py`
  (23.2).
- Golden: on `muro-sostegno`'s example (has both demand/capacity and minimum checks), searching a stated field
  `campo=<nome>` over an explicit `da=<x>, a=<y>, passo=<p>` with `obiettivo=1,00` returns `esito = "trovato"` with a
  grid value v such that v is admissible and v − passo is not (checked by two direct `execute` calls); target 0,80
  gives a value v' ≥ v. `ca-taglio-non-armato` (a single minimum/ceiling check, no demand/capacity action) is kept
  only as a `estremo_sufficiente` case, not as the main golden example.
- API (`tests/web/test_dimensiona_api.py`): 404, each 422 message (including empty grid and non-integer passo),
  429 with a held semaphore (via the injectable `app.state.dimensiona`), response shape including `modalita` and
  `correzioni`.
- E2E (`tests/e2e/test_dimensiona.py`): open a tool, "Dimensiona…", Cerca disabled until Passo is filled with the
  reason reachable by Tab, result shown with the reliability word, Applica updates the field and the live run,
  focus a numeric field then `g d` preselects it, Esc cancels and returns focus, `Ctrl+Enter` inside the dialog
  starts the search and does not also trigger the global "Calcola"; repeated at 390×844 for the mobile layout;
  `tests/e2e/dimensiona.test.mjs` for the pure formatting helpers (Da/A prefill rule).

### 23.7 Engineering decisions
Decided by the owner on 2026-09-22: target and steps are settable office defaults (17, 18 → §26); outcome-only
checks are acceptable in a sizing (19). Still open: whether the target also applies to minimum/detailing checks
(19-bis) — a §26 setting, factory value "no", with the §23.2 caveat. The API test adds: `obiettivo_su_minimi`
echoed from a settings repository set both ways, and with `true` an "inverso" check limits the answer at the target.
The E2E test adds: with §26 holding a step for the field's type and a target 0,90, the dialog opens prefilled with
both and the provenance line (run on a temporary data-dir fixture, as §26.8).

## 24. Studio di sensibilità (owner's request 2026-09-22)
Purpose: see how every check reacts to one input over a range, before or after §23.

### 24.1 Behaviour and API
`POST /api/tools/{name}/sensibilita` (same router and same pure modules as §23: η reading of §23.2, same semaphore
and time limit), body `{inputs, campo, da, a, punti}` with `2 ≤ punti ≤ MAX_PUNTI = 41`, evenly spaced, ends
included, no rounding step (a study, not a choice); `TEMPO_MAX_S = 10`. Pure function `shared/dimensiona/serie.py`.
Response: `{ok, campo, valori: [number], verifiche: [{nome, clausola, eta: [number|null], esito: [bool|null]}],
errori: [{valore, messaggio}], verifiche_solo_esito: [str], modalita, correzioni: {da_confermare, respinto},
completa: bool}` — `completa=false` when the time limit cut the series (the points evaluated so far are returned).
`modalita`/`correzioni` are read the same way as §23.4/§25.2, for the same caveats in the UI. 422s as §23.4 (`punti`
out of range: "Indicare fra 2 e 41 punti"); no `obiettivo` in the body: the target line is drawn client-side from
the dialog value (prefilled from §26 `obiettivo_sfruttamento`, same rule as 23.1).

### 24.2 UI
- Entry: results toolbar **"∿ Sensibilità…"**, `g s` (outside text fields, same preselection rule as `g d` in
  §23.5), or "Studia la sensibilità" from §23. Dialog (`role="dialog"`, `aria-labelledby`, focus on Campo at open,
  Esc at rest closes and returns focus, full-width sheet below 720 px, `aria-live="polite"` announcing "Ricerca in
  corso…" and then the result — all as §23.5): Campo, Da / A, Punti (proposed 21), Obiettivo (prefilled from
  §26, only draws the line), "Calcola" (Enter inside the dialog; `Ctrl+Enter` inside the dialog is handled locally with
  `stopPropagation()` so it does not also trigger the global "Calcola").
- Chart: `renderChart` from `js/chart.js`, rows `[{x: valore, s1: η, …, s5: η}]`, `chart = {x: "x", x_label:
  "<symbol> [<unit>]", y_label: "η"}`. Series = the 5 most critical checks over the range (failed somewhere first,
  then by max η); checkboxes under the chart swap which checks are drawn (at most 5 at a time; with 5 already
  checked, the remaining checkboxes get `aria-disabled` and their label says "massimo 5 verifiche"). Guides: a
  vertical guide "attuale" at the field's current value (existing `guides`) and a HORIZONTAL target line "obiettivo
  1,00". The y domain is `[0, min(max η in the series, ETA_MAX_GRAFICO = 3)]`: a point above `ETA_MAX_GRAFICO` is
  drawn clipped to the top edge with a "▲" marker (the accessible table below always shows the true value), so a
  field with a small denominator cannot flatten the useful part of the curve. Today `chart.js` draws only vertical
  guides and `css/chart.css` styles only 2 series: small edits, both JS files stay far under 400 lines —
  `renderChart(…, {hGuides: [{value, label}]})` drawn by a new `buildHGuide` in `chart-axis.js` and included in the
  (now capped) y domain; `c-series-3..5` added to `chart.css`, each with its own dash pattern and end marker so
  series are told apart without colour. Points with an error or without η are gaps (`toFinite` → null, already
  handled).
- Accessible equivalent, always rendered (DESIGN_SPEC §3): a table with caption, one row per point: valore · η of each
  drawn check (2 decimals, true value even above `ETA_MAX_GRAFICO`, "—" when none) · "Esito" as icon + word (✓ Tutte
  passano / ✕ N non passano) · outcome-only checks as ✓/✕ columns · a row button "Usa questo valore" (writes the Dati
  control and dispatches `input` then `change`, as §18 after §21, one undo step §21). Error points show the Italian
  message in the row. The chart wrapper keeps its arrow-key crosshair.
- Modules: `js/sensibilita.js` (dialog and orchestration), `js/sensibilita-grafico.js` (pure rows/series/guides
  mapping), `js/sensibilita-tabella.js`, `css/sensibilita.css`; edits to `chart.js`, `chart-axis.js`, `chart.css`,
  `results-toolbar.js`, `shortcuts.js`. CSP as §23.5.

### 24.3 Acceptance and open decisions
Unit: `tests/shared/dimensiona/test_serie.py` (spacing, limits, errors kept, partial series). API:
`tests/web/test_sensibilita_api.py`. JS: `tests/e2e/sensibilita.test.mjs` (top-5 selection, row mapping, target in
the y domain, horizontal guide present). E2E `tests/e2e/test_sensibilita.py`: study a tool's example, the chart has a
target line and ≤ 5 series, the table has `punti` rows, "Usa questo valore" updates the field, keyboard only (`g s`,
Tab, Enter). Open engineering decisions: none new (the target line reuses decision 17).

## 25. Stato del progetto — "da ricalcolare", "provvisorio", counts (owner's request 2026-09-22)
Purpose: on the project page (§14.3, and the table of §20) each element says whether its data are still current and
whether its results rest on register corrections the owner has not signed yet.

### 25.1 "Da ricalcolare": what must be saved (today it is not)
§15 saves `provenienza = {collegamenti: [{chiave, strumento}]}` (`js/provenienza.js` `activeProvenienza`): neither the
provider element nor the copied value, so an upstream change cannot be detected. Worse, `activeProvenienza(tool)`
returns `{}` whenever the current session was not opened with `?da=…` (`session.provider` unset) — see
`provenienza.js` lines 140-143 — and `elemento-salva.js` sends that empty object on EVERY save, unconditionally
(`currentPayload`). So today, reopening a saved element with `?elemento=<id>` and saving again for any reason (a
renamed note, an unrelated field) silently wipes ALL of its `collegamenti`: the "da ricalcolare" marker becomes
permanently impossible for that element, exactly when it should still work. New shape of each item (additive; old
elements keep working and simply show no marker):
`{chiave, strumento, percorso, ingresso, valore, elemento_id?, revisione_fornitore?}` — `percorso`/`ingresso` as in
`shared/collegamenti.py`'s `Fornitore`, `valore` the exact value copied into the consumer field.
- **Reconstruction on open**: opening `?elemento=<id>` makes `provenienza.js` rebuild its session from the saved
  `provenienza.collegamenti`: each item whose consumer field still holds exactly `valore` gets its "da <sigla>" chip
  restored (same rendering as a fresh "Usa in…"); an item whose field was hand-edited since the save is dropped, as
  today. `activeProvenienza(tool)` then returns the union of the still-valid restored items and any new ones added in
  this session. **No save ever clears the provenance of an item the user did not touch.** The same reconstruction
  feeds "Aggiorna dai dati a monte" below.
- `elemento_id` and `revisione_fornitore` are added only when the on-screen provider EXACTLY matches a saved
  element: no unsaved changes ("dati modificati" state of §14.1) and the same `modalita`. `js/usa-in.js` reads that
  state before adding `&da_elemento=<id>&da_revisione=<n>` to the query; when it does not match, the link is saved
  WITHOUT `elemento_id` ("origine non salvata" in the tooltip, never marked) — the value-based comparison below
  would otherwise flag an origin whose revision never changes even though the copied value does not match what
  that revision actually produces.
- Editing a prefilled field clears its chip and drops its item (as today), so a hand-typed value is never "stale".
Rule (pure, `shared/stato_progetto/origini.py`): an element is **da ricalcolare** when, for at least one item with
`elemento_id`, the provider element is deleted ("origine eliminata"), or the value at `percorso` of a FRESH run of
the provider's CURRENT stored inputs (`execute`, the provider's current `modalita`) differs from `valore` (numbers:
relative difference > 1e-9; enums: not equal) — **regardless of whether `revisione` changed**: a code fix after a
rejected register entry, a register entry applied or withdrawn, or a shared table changed all change the provider's
output at a fixed revision, and the consumer must be marked too (`causa: "valore_cambiato"`). The comparison result
is cached per `(elemento_id, revisione, impronta)`, where `impronta` combines the register signoffs' fingerprint and
the installed package/commit fingerprint, so the cache itself is invalidated by exactly the same changes that must
be detected — `revisione` alone is kept in the cache key only to make the "Aggiorna" message readable, not as the
trigger. A provider run that fails gives "origine non calcolabile" (marked, message kept); a rename or a note alone
never marks anything, because the value at `percorso` is unchanged. The marker clears when the consumer is saved
again with current values (new "Usa in…" or the row action below).
**Propagation along the chain (owner's decision 22, 2026-09-22: yes — to be built).** Without it, if A changes, B
is marked, but B's saved inputs do not change until the owner acts on it; when C uses B, a fresh run of B's stored
inputs still returns the OLD value, so C would never be marked although it rests on a stale B. Symmetrically, a
standard-mode element with no pending corrections that consumes a value from a provvisorio or Excel-mode provider
would look fully "definitivo". Rule (pure, `shared/stato_progetto/propagazione.py`, ≤ 150 lines, functions ≤ 40):
- Graph: one node per element, one edge consumer → provider for each provenance item WITH `elemento_id` (items
  without it, "origine non salvata", never propagate; their tooltip says so). A provider may live in another
  project: it is read with `get_elemento` and evaluated exactly like a local one (its own §25.1/§25.2 state),
  counting towards `MAX_RICALCOLI_ORIGINI`; only elements of the requested project appear in `elementi`/`conteggi`.
- Own states: the §25.1 comparison and the §25.2 provvisorio rule are computed at most once per `elemento_id` per
  request (memoised; they are the expensive part, provider runs).
- Propagated states, defined per element X as a bounded reachability, so the result never depends on the order of
  the elements: breadth-first from X along provider edges, with a visited set, up to `PROFONDITA_MAX_ORIGINI = 10`
  edges.
  - **da ricalcolare per origine**: X is marked with `causa: "origine_da_ricalcolare"` when some reached provider
    is da ricalcolare by its OWN state; one motivo per direct provider on such a path, naming it (`elemento_id`,
    `strumento`, name) with the farthest-upstream own motivo as `messaggio` ("da SPS via MUR: ag 0,150 → 0,180 g").
  - **provvisorio per origine**: new flag `provvisorio_origine` with `motivi_origine: [{elemento_id, strumento,
    causa: "origine_provvisoria"|"origine_excel"}]` when some reached provider is provvisorio by its own state or is
    saved in Excel mode. Shown and counted separately: it never changes X's own `provvisorio`/`correzioni`.
  - **Depth limit**: when the BFS still has unvisited providers at depth `PROFONDITA_MAX_ORIGINI`, X gets one motivo
    `causa: "controllo_rinviato"` ("Catena di origini più lunga di 10 passaggi: controllo interrotto"), not marked
    by it, counted as the run cap of §25.3.
- **Cycles**: "Usa in…" cannot prevent them (two elements may copy values from each other at different times). The
  visited set makes every BFS terminate; in addition the strongly connected components of the graph (Tarjan,
  iterative, order-independent) with more than one node or a self-edge give each member one motivo `causa:
  "ciclo_origini"` ("Le origini formano un ciclo: <sigla> → … → <sigla>"), not marked by it, counted in
  `conteggi.cicli_origini`. Marking through a cycle still follows the reachability rule above.
- Tests (§25.5) prove order independence (every permutation of the element list gives the same result) and
  termination on cycles of length 1, 2 and 5.
The row action for `origine_da_ricalcolare` is "Apri l'origine <sigla>" (opens the provider element, which has its
own "Aggiorna dai dati a monte"): the consumer's values are refreshed only once the provider has been updated and
saved, at which point the consumer's own `valore_cambiato` rule takes over.
"Aggiorna dai dati a monte" (row action, §25.4) reads the CURRENT values through `GET /api/progetti/{id}/stato`
(the same `valore_attuale` already carried in each `motivo`), fills the linked fields, and `provenienza.js` updates
each item's `valore`/`revisione_fornitore` to the provider's current value/revision (read again via `GET` on the
provider element) so the next "Salva" stores a provenance that matches what was actually applied.

### 25.2 "Provvisorio"
From the same data as `GET /api/divergences/riepilogo`: the per-tool count is factored into a pure function
`riepilogo_per_strumento(divergences, signoffs)` in `shared/divergences/`, reused by the existing route (no
behaviour change). `Divergence.ramo` is `"nessuno"` for 62 of the 209 register entries today: those are corrections
applied in BOTH modes (or not reproduced in Excel at all), so an Excel-mode element is not automatically clear of
pending corrections either. An element is **provvisorio** when its tool has register entries that affect its mode
and are not approved:
- standard mode: every entry with `stato` `da_confermare`/`respinto` counts (a rejected entry stays applied in
  standard mode until an agent adapts the code, see DECISIONI "Come si conferma");
- Excel mode: only entries with `ramo == "nessuno"` count (applied in both modes).
`riepilogo_per_strumento` returns, alongside the existing per-`stato` counts, the same counts restricted to
`ramo == "nessuno"` so the Excel-mode rule above can be computed. Entries with `tipo == "da_verificare"` (30 today)
are open doubts, not applied corrections: they are counted SEPARATELY and never make an element provvisorio; the
tooltip names them "N dubbi da verificare" rather than listing them as corrections applied. Granularity is the
tool, as in the register: the program does not know which entries a given run traversed; the tooltip says "Il
calcolo applica correzioni del registro non ancora approvate (N da confermare, M respinte)", plus "N dubbi da
verificare" when non-zero, and links to the register filtered on the tool. A rejected entry counts towards
provvisorio (owner's decision 21, 2026-09-22): the rule lives in a single place (`shared/stato_progetto/
provvisorio.py`, constant `RESPINTO_RENDE_PROVVISORIO = True`), and the tooltip always reports the two counts
(`da_confermare`, `respinto`) separately.
**The printed relazione is unchanged** (single tool §10 and project §14.3), including "provvisorio per origine":
the owner decided on 2026-09-22 (decision 20) that "provvisorio" does not appear on paper. It stays on screen only
(project page, §20 table, §23 dialog).

### 25.3 API
`GET /api/progetti/{id}/stato` (new router `routes/progetti_stato.py`; `routes/progetti.py` is already 358 lines) →
`{elementi: {<id>: {da_ricalcolare: bool, motivi: [{chiave, strumento, elemento_id, causa:
"valore_cambiato"|"origine_eliminata"|"origine_non_calcolabile"|"origine_da_ricalcolare"|"ciclo_origini"|
"controllo_rinviato", valore_salvato|null, valore_attuale|null, messaggio?}], provvisorio: bool,
provvisorio_origine: bool, motivi_origine: [{elemento_id, strumento, causa: "origine_provvisoria"|"origine_excel"}],
correzioni: {da_confermare, respinto, ramo_nessuno, da_verificare}}}, conteggi: {elementi, verificati,
non_verificati, dati_modificati, da_ricalcolare, provvisori, provvisori_per_origine, controllo_rinviato,
cicli_origini}}`. `build_progetti_stato_router(progetti, tools, signoffs, register=None)` needs the project,
tool and register/signoff repositories together (same dependency shape as `build_dimensiona_router`, §23.4), wired
in `web/app.py`. 404 unknown or deleted project (Italian envelope). Provider runs are off the event loop, cached in
memory per `(elemento_id, revisione, impronta)` per §25.1, at most `MAX_RICALCOLI_ORIGINI = 50` per request (beyond:
`causa: "controllo_rinviato"`, not marked, counted). The page fetches the state after the element list, again after
every save/duplicate/delete/restore on the page and after a register sign-off (the rail badge's refresh event
already exists).
Modules: `src/strutture/shared/stato_progetto/{origini.py, provvisorio.py, propagazione.py, conteggi.py}` (pure,
≤ 150 lines each). The route builds the graph and hands `propagazione.py` a callable for the own state of one
element, so the propagation is tested without the web layer.

### 25.4 UI
- Element row (§14.3 list and the state column of the §20 table): next to the stato, chips as icon + word, never
  colour alone: **"↻ Da ricalcolare"** (tooltip: each motivo, e.g. "ag da SPS: 0,150 → 0,180 g") and
  **"◐ Provvisorio"** (tooltip + register link, 25.2) and **"◐ Provvisorio per origine"** (tooltip: "Usa valori
  di <sigla>, che applica correzioni non approvate" / "…, che riproduce il foglio Excel", each provider a link to its
  element). "↻ Da ricalcolare" caused only by `origine_da_ricalcolare` has the row action "Apri l'origine <sigla>"
  (§25.1). Row action **"Aggiorna dai dati a monte"** (only when da ricalcolare by the element's own values) opens `#/<tool>?elemento=<id>&aggiorna_origini=1`: the page calls `GET /api/progetti/{id}/stato`,
  reads `valore_attuale` from the element's motivi and fills the linked fields, with §15's "da <sigla>" chips and
  the old value in the chip tooltip; the fill happens AFTER §21's history reset on `?elemento=` load and is itself
  one undoable step "Aggiorna dai dati a monte"; nothing is saved until "Salva", which then stores the refreshed
  `valore`/`revisione_fornitore` per §25.1.
- Project head: one line of counts, each a button that filters the list/table (Tab + Enter; Esc clears the filter):
  "12 elementi · ✓ 9 verificati · ✕ 1 non verificato · ○ 2 dati modificati · ↻ 3 da ricalcolare · ◐ 5 provvisori ·
  ◐ 2 provvisori per origine". "Controllo rinviato" and "⟲ N cicli di origini" appear only when non-zero.
- Modules: `js/progetto-stato.js` (fetch, chips, counts; ≤ 400 lines), `css/progetto-stato.css`; small edits to
  `progetto.js`, `progetto-elementi.js` (and the §20 table module), `usa-in.js`, `provenienza.js`. The provenance
  payload (`collegamenti` with `elemento_id`/`revisione_fornitore`, and the §25.1 reconstruction-on-open) is built
  and owned entirely by `provenienza.js`; `elemento-salva.js` (already 373 of its 400 lines, and also touched by
  §21) only calls `activeProvenienza(tool)` as it does today — no new logic added there. If a further need arises
  that would push it over 400 lines, the 409-conflict dialog is split out first into a new `js/elemento-conflitto.js`.
  CSP as §23.5.

### 25.5 Acceptance
Unit (`tests/shared/stato_progetto/`): unchanged revision, unchanged value → not marked; new revision, same value →
not marked; SAME revision, output changed by a code/register change → marked `causa: "valore_cambiato"` (25.1);
changed value, deleted provider, failing provider run → marked with the right `causa`; old-shape provenienza → no
marker; reopening and resaving an element without touching a linked field keeps its `collegamenti` (25.1); "Usa
in…" from an unsaved/modified provider saves without `elemento_id`; provvisorio for standard mode
(da_confermare/respinto) and Excel mode (`ramo == "nessuno"` entries only); `da_verificare` entries counted
separately, never provvisorio; counts. Propagation (`test_propagazione.py`): chain A → B → C with A changed
marks B `valore_cambiato` and C `origine_da_ricalcolare`; a provvisorio or Excel-mode A makes B and C
`provvisorio_origine` without touching their own `provvisorio`; items without `elemento_id` never propagate; a
self-edge, a 2-cycle and a 5-cycle terminate and give each member one `ciclo_origini`; a chain longer than
`PROFONDITA_MAX_ORIGINI` gives `controllo_rinviato` and is not marked; same result for every permutation of the element list; a provider in
another project is followed. API (`tests/web/test_progetti_stato_api.py`, in-memory repository): 404,
shape, cache hit on unchanged revision AND unchanged impronta, `MAX_RICALCOLI_ORIGINI`. E2E
(`tests/e2e/test_progetto_stato.py`): save sisma-parametri-sito as an element, "Usa in…" muro-sostegno from it and
save; change ag_g in the provider and save → the wall shows "↻ Da ricalcolare" and the head count is 1; reopen the
wall, rename it only, Salva → the provenance and "↻ Da ricalcolare" survive; "Aggiorna dai dati a monte" + Salva
clears it; sign off every register entry of the wall via `signoff-multiplo` with sigla "E2E" on a fresh temporary
data-dir fixture (so other tests' "da confermare" expectations are not disturbed), reload the project page →
"◐ Provvisorio" disappears; the printed project relazione contains no "Provvisorio". Chain: "Usa in…" a third
element from the saved wall and save; change the provider again → the third element shows "↻ Da ricalcolare" with
"Apri l'origine", and a provider saved in Excel mode makes both consumers "◐ Provvisorio per origine".

### 25.6 Engineering decisions
Decided by the owner on 2026-09-22: "provvisorio" is not printed in any relazione (20); a rejected entry makes an
element provvisorio (21); "da ricalcolare" and "provvisorio" propagate along the usage chain (22, §25.1, to be
built). None open. The comparison tolerance (1e-9 relative) and `PROFONDITA_MAX_ORIGINI` are guards against numeric
noise and runaway graphs, not engineering thresholds.

## 26. Impostazioni — office defaults (owner's decisions 17, 18, 19-bis, 2026-09-22)
Purpose: one page where the office sets the defaults that §23/§24 PROPOSE, instead of the program choosing them.
There are no users (roadmap decision): one set of settings for the whole installation, stored in the server's SQLite
database next to projects and register sign-offs, so every workstation sees the same values. A setting is only ever
a proposal: every dialog that uses one still shows the value and lets the engineer change it for that operation.

### 26.1 Content (initial) and factory values
| Setting | Key | Factory value | Limits |
|---|---|---|---|
| Obiettivo di sfruttamento (decision 17) | `obiettivo_sfruttamento` | 1,00 | 0 < x ≤ 1,00, at most 2 decimals |
| Obiettivo anche sulle verifiche di minimo e di dettaglio (decision 19-bis, still open) | `obiettivo_su_verifiche_minimo` | `false` ("no") | boolean |
| Passo di arrotondamento per tipo di dato (decision 18) | `passi_per_tipo: {<tipo>: number\|null}` | every type `null` (no step) | see 26.3 |
| Eccezioni per campo (decision 18) | `passi_per_campo: [{strumento, campo, passo: number\|null}]` | empty | at most `MAX_ECCEZIONI = 200`, unique (strumento, campo) |
The factory steps are EMPTY on purpose: the office enters them, the program invents none. New settings added later
follow the same pattern: a key with a factory value, limits in the model, one row on the page, a test.

### 26.2 Model (`src/strutture/shared/impostazioni/modelli.py`, frozen pydantic v2)
- `TipoDato = Literal["lunghezza_m", "lunghezza_cm", "lunghezza_mm", "diametro_armatura", "passo_armatura",
  "copriferro", "spessore", "intero"]` (26.4).
- `PassoCampo(strumento: str, campo: str, passo: float | None)` — `passo = None` means "no step for this field",
  which masks the type step (the dialog then asks every time).
- `Impostazioni(obiettivo_sfruttamento: float = 1.0, obiettivo_su_verifiche_minimo: bool = False, passi_per_tipo:
  dict[TipoDato, float | None] = {every type: None}, passi_per_campo: tuple[PassoCampo, ...] = ())`,
  `extra="forbid"`; `FABBRICA = Impostazioni()` is the single definition of the factory values.
- Field validation in the model (Italian messages, `loc` naming the key): obiettivo `gt=0, le=1`, "L'obiettivo di
  sfruttamento deve essere maggiore di 0 e al massimo 1,00", at most 2 decimals; every step `gt=0`,
  `le=PASSO_MAX = 1000` (in the type's unit), at most 4 decimals, checked on the decimal string of the number (no
  binary-float drift, same `Decimal` convention as §23.3); the `intero` step and any exception on an integer field
  must be an integer ≥ 1 ("Il passo deve essere intero"); duplicate (strumento, campo) refused.
- Validation that needs the tool registry lives in `shared/impostazioni/validazione.py` (pure, receives the tools'
  input schemas): `strumento` must exist ("Strumento sconosciuto: …"), `campo` must be a numeric input of it (same
  "numeric" definition as §23.4: tables, enums, booleans and `legacy_compat` refused).
- `ImpostazioniSalvate(valori: Impostazioni, revisione: int, sigla: str, aggiornato_il: str)`; revisione 0 with an
  empty sigla = factory values never saved.

### 26.3 Units of the steps
A step is expressed in the unit of its data type (26.4): `lunghezza_m` in m, `lunghezza_cm` in cm, `lunghezza_mm`,
`diametro_armatura`, `passo_armatura`, `copriferro` and `spessore` in mm, `intero` without unit. Types that group
fields in different units (a `copriferro_cm` field next to `c_mm` fields) convert the step into the field's unit with
the factors of `shared/units.py` (the only place for conversion factors) when resolving (26.5); a converted step that
does not survive the 4-decimal rule is refused at save time with the field named ("Il passo di 0,5 mm non è
esprimibile in cm per fond-plinto-isolato.copriferro_cm"). An exception is always in the FIELD's own unit, shown
next to the input.

### 26.4 Data types of the fields (`shared/impostazioni/tipi_dato.py`, pure)
Read from the input schemas that `GET /api/tools/{name}/schema` already serves (unit, symbol, group, JSON type;
survey of 2026-09-22 over the 28 tools: 117 inputs in mm, 50 in m, 3 in cm, 24 integers). `tipo_dato(nome,
schema_campo) -> TipoDato | None`, first matching rule wins:
0. Explicit hint `json_schema_extra={"tipo_dato": "<tipo>"}` in the tool's own `models.py` (not the shared
   contract; pydantic copies it into the field schema). None exists today; it is added only where the rules below
   misclassify a field.
1. JSON type `integer` (or `anyOf` with `integer`) → `intero` (bar counts, number of legs, sections…).
2. Unit not in {m, cm, mm} → `None`: no type step (angles, forces, stresses, coefficients, times…); only a
   per-field exception can give such a field a step.
3. Name contains `copriferro`, or is `c_mm`/`cf_mm` (all described as "Copriferro") → `copriferro`.
4. Symbol starts with `⌀`, `φ` or `Φ`, or the field has no symbol and its name contains `diametro` →
   `diametro_armatura` (so `ca-punzonamento.diametro_mm` "D", `ca-sezione-dominio-mn.diametro_mm` "D" and
   `fond-plinto-su-pali.diametro_pila_mm` "Ø_palo" — section and pile diameters — stay lengths).
5. Name contains `passo` or `interferro` → `passo_armatura`.
6. Symbol starts with `t_` or equals `h_f`, or the name contains `spessore` → `spessore`.
7. Otherwise by unit: m → `lunghezza_m`, cm → `lunghezza_cm`, mm → `lunghezza_mm`.
A frozen table test (`tests/shared/impostazioni/test_tipi_dato_copertura.py`) lists the type of EVERY numeric input
of every tool, so a new field or a rule change is noticed and reviewed; spacings the rules cannot recognise by name
(e.g. `ca-punzonamento.st_mm`, `px_mm`) remain `lunghezza_mm` in that table until a builder, reading the field's
description, adds a `tipo_dato` hint. Italian labels (page and messages): Lunghezze in m · Lunghezze in cm ·
Lunghezze in mm · Diametri di armatura · Passi di armatura · Copriferri · Spessori · Numeri interi.

### 26.5 Resolution for §23 (`shared/impostazioni/risolvi.py`, pure)
`passo_proposto(impostazioni, strumento, campo, schema_campo) -> PassoProposto(passo: float | None, origine:
"campo" | "tipo" | "intero" | None, tipo: TipoDato | None)`, in this order:
1. an exception for (strumento, campo) → its `passo` (also when `None`: the office wants no proposal there),
   `origine = "campo"`;
2. the step of the field's type, converted per 26.3 → `origine = "tipo"`;
3. integer field with no step set → 1, `origine = "intero"` (§23.1: the only meaningful step, not an engineering
   choice);
4. otherwise `None`: the dialog's Passo starts empty and required.
An exception whose tool or field no longer exists (a tool renamed after the save) is ignored by the resolution and
reported in `GET /api/impostazioni` `avvisi` ("Eccezione ignorata: il campo … non esiste più"); it is removed only
when the office saves the page.

### 26.6 Storage (`src/strutture/storage/`, same pattern as projects)
- Migration 3 in `migrations.py`: `impostazioni (id INTEGER PRIMARY KEY CHECK (id = 1), valori TEXT NOT NULL,
  revisione INTEGER NOT NULL, sigla TEXT NOT NULL, aggiornato_il TEXT NOT NULL)` (one row) and
  `impostazioni_storia (revisione INTEGER PRIMARY KEY, valori TEXT NOT NULL, sigla TEXT NOT NULL, aggiornato_il TEXT
  NOT NULL)` (append-only). No row = `FABBRICA` at revisione 0. `valori` is the model's JSON (`ensure_ascii=False`).
- `ImpostazioniRepository` Protocol in `interfaces.py`: `leggi() -> ImpostazioniSalvate`, `salva(valori,
  revisione_attesa, sigla) -> ImpostazioniSalvate`, `storia(limite=50) -> tuple[ImpostazioniSalvate, ...]`.
  `salva` checks `revisione_attesa` against the stored one INSIDE the same `write_session` transaction and raises
  the existing `ConflictError` on mismatch (optimistic lock, as `progetti_sqlite.py`), then writes the row with
  revisione + 1 and appends the same values to the history. Implementations `impostazioni_sqlite.py`
  (`open_impostazioni_repository(data_dir)`) and `impostazioni_memory.py` (tests, e2e in-memory server).
- Reading is defensive (file content is external data): a stored `valori` that no longer validates (hand-edited
  database, a type removed in a later version) is logged with the revision number, replaced in memory by `FABBRICA`
  merged with every key that still validates, and reported in `avvisi` ("Impostazioni salvate non leggibili in
  parte: usati i valori di fabbrica per …"); never silently. Nothing is written until the office saves.
- Settings are part of `var/strutture.db`, so the existing backup covers them; the project export/import
  (`scambio.py`) does not carry them (they belong to the office, not to a project).

### 26.7 API (`src/strutture/web/routes/impostazioni.py`, `build_impostazioni_router(repository, tools)`)
Wired in `web/app.py` next to the other routers; the existing middleware (rate limit, security headers, same-origin
check on writes) applies unchanged. Standard envelope for errors, Italian `errors[0]`, `error_details.loc` naming
the body key (e.g. `["passi_per_campo", 3, "passo"]`).
- `GET /api/impostazioni` → `{ok, impostazioni, revisione, sigla, aggiornato_il, fabbrica: <FABBRICA>, avvisi:
  [str]}` (`fabbrica` feeds "Ripristina predefiniti" without a second definition in JavaScript).
- `PUT /api/impostazioni` body `{impostazioni, revisione, sigla}` → 200 as GET with the new revision; 409 when
  `revisione` is stale, same envelope as the projects' conflict (`attuale` = the stored settings, message "Le
  impostazioni sono state modificate nel frattempo (revisione N, sigla X): ricaricare e riprovare"); 422 for every
  26.2 rule and a missing sigla (same 1-12 characters rule and message style as the register sign-off).
- `GET /api/impostazioni/tipi` → `{tipi: [{tipo, etichetta, unita, campi: [{strumento, campo, simbolo, etichetta,
  unita}]}], senza_tipo: [same item shape]}` from 26.4 over all tools (cached per process: schemas are static).
- `GET /api/impostazioni/passi?strumento=<name>` → `{strumento, obiettivo_sfruttamento,
  obiettivo_su_verifiche_minimo, passi: {<campo>: {passo, origine, tipo}}}` for every numeric input of the tool
  (26.5); 404 unknown tool. This is what §23/§24 read; the resolution logic exists only on the server.
- `GET /api/impostazioni/storia` → the last 50 revisions (`revisione, sigla, aggiornato_il, valori`).
- 500 envelope on an unexpected exception, logged with the route, never the body.

### 26.8 Page `#/impostazioni`
- Reach: a fixed rail entry "Impostazioni" below "Registro correzioni" (§13.1), own pictogram (a gear with a ruler
  tick, distinct from every category and from the register ledger), label always present next to the icon when the
  rail is expanded and as tooltip + `aria-label` when collapsed (§12); a palette entry "Impostazioni" (keywords:
  passo, arrotondamento, obiettivo, sfruttamento, predefiniti); the shortcut `g i` (outside text fields, as `g h`),
  listed in the shortcut sheet. `main.js` routes `impostazioni` like `registro` (full-width main area, no
  Dati/Sintesi split, `data-view="impostazioni"`).
- Title + one sentence: "Valori d'ufficio proposti dal programma. Ogni finestra li mostra e si possono cambiare
  caso per caso." Last change line: "Revisione N · modificata il <data> da <sigla>" (or "Valori di fabbrica, mai
  modificati").
- Section **"Dimensiona e sensibilità"**: "Obiettivo di sfruttamento" (numeric input through `number-input.js`,
  Italian comma, 2 decimals, hint "fabbrica 1,00"); checkbox "Applica l'obiettivo anche alle verifiche di minimo e
  di dettaglio" with the note "Decisione ancora aperta (19-bis): valore di fabbrica no".
- Section **"Passi di arrotondamento per tipo di dato"**: an accessible table with caption, one row per type: tipo ·
  unità · passo (input, empty = "nessun passo") · a disclosure "N campi" listing the fields of that type (strumento
  sigla · simbolo · etichetta), from `/tipi`. Under the table: "Campi senza tipo (angoli, forze, tensioni…): solo
  eccezioni per campo" with its own disclosure.
- Section **"Eccezioni per campo"**: table rows strumento (select: sigla + title) · campo (select of that tool's
  numeric inputs, symbol + label + unit, grouped like the Dati) · passo in the field's unit (empty = "nessun passo:
  chiedi ogni volta") · button "✕ Rimuovi" (icon + word); button "+ Aggiungi eccezione" adds a row and focuses its
  strumento select. Duplicates are flagged in place before saving.
- Footer: "Sigla" (required, 1-12 characters), **"Salva"** (Enter inside the sigla field submits), **"Annulla
  modifiche"** (back to the last loaded values), **"Ripristina predefiniti"**: a confirmation dialog (`role=
  "alertdialog"`, focus trapped, Esc = no) "Ripristinare i valori di fabbrica? Obiettivo 1,00, obiettivo sulle
  verifiche di minimo no, nessun passo, nessuna eccezione. Diventano effettivi solo con Salva." → fills the form
  with `fabbrica`; nothing is written until Salva, which stores them as a new revision (history kept).
- State: "○ Modifiche non salvate" (icon + word) while the form differs from the loaded values; leaving the page
  (router navigation or `beforeunload`) with unsaved changes asks for confirmation. Save success is announced in an
  `aria-live="polite"` region ("Impostazioni salvate: revisione N") and dispatches `impostazioni:salvate` on
  `window` so open §23/§24 helpers drop their cache. 422: the message next to each offending input
  (`aria-invalid`, `aria-describedby`), a summary at the top listing them as links, focus on the summary. 409: a
  dialog with the server message and **"Ricarica"** (loads the stored values, discarding local edits after a second
  confirmation) or "Chiudi" (keeps the local edits so they can be copied by hand).
- Disclosure "Storia delle modifiche": table revisione · data · sigla · what changed (a readable diff of the two
  JSONs: "Obiettivo 1,00 → 0,90", "Diametri di armatura: — → 2 mm", "Eccezione aggiunta: PIR ⌀ 2 mm").
- `avvisi` from GET are shown at the top as warnings (icon + word "⚠ Attenzione").
- Every control reachable by Tab in reading order; no action needs a pointer; below 720 px the tables become stacked
  cards with the same controls.
- Modules: `js/impostazioni.js` (page and orchestration, ≤ 400 lines), `js/impostazioni-api.js` (fetch helpers:
  `leggiImpostazioni`, `salvaImpostazioni`, `leggiTipi`, `passiStrumento`, cache + `impostazioni:salvate`),
  `js/impostazioni-passi.js` (type table and exception rows), `js/impostazioni-modello.js` (pure: form ↔ payload,
  dirty detection, readable diff), `css/impostazioni.css`; small edits to `main.js`, `tool-index.js` (rail entry),
  `palette.js`, `shortcuts.js`, `icons.js`, and the §23/§24 dialogs (prefill). CSP (rule 4): no inline style or
  script, no `innerHTML`, geometry via classes or `style.setProperty`. Built in `static_next/` and promoted per
  CLAUDE.md rule 3.

### 26.9 How §23 and §24 use them
Opening "Dimensiona" or "Sensibilità" calls `passiStrumento(tool)` (one request per dialog opening, cached until
`impostazioni:salvate`): Obiettivo ← `obiettivo_sfruttamento`; Passo ← `passi[campo].passo` with the provenance
line of §23.1; the read-only "Obiettivo anche sulle verifiche di minimo" line ← `obiettivo_su_verifiche_minimo`.
If the request fails the dialog still opens with Obiettivo 1,00 (factory value, from `fabbrica` if already cached,
else the constant exported by `impostazioni-modello.js`), Passo empty and a visible note "Impostazioni non
disponibili: valori di fabbrica" — never a silent fallback. The search/series requests carry the explicit values
(§23.1); only `obiettivo_su_verifiche_minimo` is read by the server itself (§23.2). Saved elements, variants (§19)
and relazioni never store or print settings: they store the values actually used.

### 26.10 Acceptance
- Unit (`tests/shared/impostazioni/`): `test_modelli.py` (factory values; each limit and message; 2 and 4 decimals
  on the decimal string; integer step; duplicate exceptions; `extra="forbid"`), `test_validazione.py` (unknown
  tool, unknown field, non-numeric field, integer field with a fractional exception), `test_tipi_dato.py` (each rule
  0-7 with a synthetic schema, including the three "D"/"Ø_palo" diameters staying lengths),
  `test_tipi_dato_copertura.py` (frozen table, 26.4), `test_risolvi.py` (precedence campo > tipo > intero > none;
  `None` exception masks the type step; cm/mm conversion of a `copriferro` step; vanished field ignored with avviso).
- Storage (`tests/storage/test_impostazioni_sqlite.py`, and the same cases on the memory repository): empty database
  → `FABBRICA` at revisione 0; save increments the revision and appends history; stale revision → `ConflictError`
  and nothing written; corrupted `valori` → factory merge + avviso, nothing written; migration 3 applied once over a
  database that already has migrations 1-2 and its data intact.
- API (`tests/web/test_impostazioni_api.py`): GET factory shape (with `fabbrica`); PUT ok and revision +1; 409 shape
  with `attuale`; every 422 message with its `loc` (obiettivo 0, 1,01, 0,905; step 0, negative, 5 decimals, 1001;
  fractional integer step; unknown tool; unknown or non-numeric field; duplicate; missing sigla; more than
  `MAX_ECCEZIONI`); `/tipi` covers every numeric input exactly once; `/passi` 404 and precedence; `/storia` order;
  §23 `obiettivo_su_minimi` echoes the stored setting.
- JS (`tests/e2e/impostazioni.test.mjs`): form ↔ payload round trip, dirty detection, readable diff, comma parsing.
- E2E (`tests/e2e/test_impostazioni.py`, on a fresh temporary data-dir fixture so the settings never leak into other
  tests, which expect factory values): the page is reached from the rail, from the palette and with `g i`; factory
  values shown (1,00, every step empty, checkbox off, no exceptions); set obiettivo 0,90, a step for "Diametri di
  armatura" and an exception on one field, Salva with a sigla → reload shows them and "Revisione 1"; open
  `ca-pilastro-rettangolare`, "Dimensiona…" on the bar diameter → Passo and Obiettivo prefilled with the provenance
  line, the excepted field prefilled with its own step; a field with no step still starts empty; "Ripristina
  predefiniti" + Salva → factory values at revisione 2 and the history lists both changes; two pages saving from the
  same revision → the second gets the 409 dialog and "Ricarica" shows the first page's values; a 422 (obiettivo
  1,5) shows the message next to the input and in the summary; leaving with unsaved changes asks for confirmation;
  the whole flow keyboard-only; repeated at 390×844. `Calcola` locators follow CLAUDE.md rule 10.

### 26.11 Engineering decisions
Decided by the owner on 2026-09-22: target and steps are settable (17, 18), with factory target 1,00 and no factory
step. Open: 19-bis, exposed as the setting `obiettivo_su_verifiche_minimo` with factory value "no" — the owner may
change it on the page at any time; the decision stays listed in `docs/DECISIONI_DA_CONFERMARE.md` until a
definitive value is chosen. No change to `pyproject.toml` or to the shared contract (`shared/{tool,report,numeric,
tables}.py`) is needed for §26.
