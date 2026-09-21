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
