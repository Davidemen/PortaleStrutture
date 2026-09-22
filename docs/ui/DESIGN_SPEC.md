# DESIGN_SPEC — StruttureMenni UI (static_next)

Implementation spec. Authority: `UI_BRIEF.md` (direction, scope, hard constraints) > `ENGINEER_NOTES.md` (vocabulary) > this file (mechanics).
All work lands in `src/strutture/web/static_next/`; `static/` is frozen. Contrast ratios below are computed (WCAG 2.x formula), not estimated.

## 0. Design review before writing (required by the task)
Cut because they read as generic SaaS, not as an engineer's calc sheet: card grid with shadows for the tool index (→ flat rules + `<details>`); skeleton-shimmer loading (→ button label "Calcolo…" + `aria-busy`); a theme toggle in a header bar (→ `prefers-color-scheme` only, zero chrome); stat tiles/KPI row above results (→ the marker-yellow rows ARE the emphasis); pill "chips" for groups; icon-only buttons.
**Accessory removed: the toast/snackbar layer** (brief left it as "toasts/none"). Nothing floats over the sheet. Copy/CSV confirm by swapping their own label to "Copiato" / "Scaricato" for 2 s; the single polite live region already announces it. Also dropped: P2 "recent tools".

## 1. Tokens — `css/tokens.css`
Light is the default; dark via `@media (prefers-color-scheme: dark)` overriding the same custom properties on `:root`. No `.dark` class, no toggle.

| Token | Light | on --paper | Dark | on --paper | Use |
|---|---|---|---|---|---|
| `--film` | `#EEF1F3` | — | `#0F1417` | — | app bg |
| `--paper` | `#FFFFFF` | — | `#161C21` | — | index/form/sheet bg |
| `--ink` | `#15202B` | 16.49 | `#E7ECEF` | 14.44 | text, primary button bg |
| `--graphite` | `#5B6773` | 5.78 | `#9AA7B2` | 6.99 | secondary text, clause margin, axis labels |
| `--rule` | `#828A91` | 3.50 (film 3.09) | `#646D74` | 3.26 (film 3.51) | **control borders only** (input/select/button) — ≥3:1 SC 1.4.11 |
| `--hairline` | `#C9D1D8` | 1.54 | `#2A333B` | 1.34 | decorative dividers between static content only |
| `--marker` | `#FFE45C` | ink on it 12.96 | `#6B5700` | ink on it 5.90 | governing-result fill + selected tool; never text colour |
| `--ok` | `#1F7A4D` | 5.32 | `#4AD07F` | 8.69 | |
| `--ko` | `#B42318` | 6.57 | `#F07068` | 5.91 | |
| `--warn` | `#8A5A00` | 5.93 | `#E0B252` | 8.72 | |
| `--ok-bg` | `#E6F2EA` | ok/on 4.62, ink/on 14.33 | `#12291D` | 7.81 / 12.97 | |
| `--ko-bg` | `#FCE9E7` | 5.62 / 14.10 | `#2E1614` | 5.82 / 14.22 | |
| `--warn-bg` | `#FBF0DA` | 5.24 / 14.59 | `#2C2312` | 7.86 / 13.01 | |
| `--series-1` | `#1B5FA8` | 6.46 | `#7FB3F0` | 7.86 | chart (solid) |
| `--series-2` | `#B4451A` | 5.52 | `#F0A070` | 8.16 | chart (dashed 6 3) |

**Changed vs the brief** (reasons in §Token changes of the summary): `--rule` split into `--rule`/`--hairline` and darkened/lightened; status tints frozen as explicit hexes instead of `color-mix()` (the live app's mixes fail AA at 3.96/3.97/4.35); series colours added.
Focus: `--focus: var(--ink)`; `:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: inherit }` — one rule, valid on `--paper`, `--film` and `--marker` (12.96 light / 5.90 dark). Never `outline: none`.
Type scale (rem): `--t-xs .8125 / --t-s .9375 / --t-m 1.0625 / --t-l 1.3125 / --t-xl 1.75`; line-height `--lh-tight 1.25` (headings, values) `--lh 1.45` (prose). All values/tables `font-variant-numeric: tabular-nums lining-nums`.
Spacing (4 px base): `--s1 .25rem --s2 .5rem --s3 .75rem --s4 1rem --s5 1.5rem --s6 2rem --s7 3rem`. Radii: `--radius: 3px` on controls only; panels/sheets radius 0, separated by `--hairline` + space. Shadows: none. Motion: `@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}` ships in the first commit.
Sizing: `--control-h: 2.75rem` (44 px, fixes 11–14 sub-44 px tap targets at 390 px); `--field-max: 22rem`; `--index-w: 240px`; `--form-w: 380px`.

**Fonts — self-host, `static_next/fonts/`, `woff2` only, `font-display: swap`.** Source = official OFL releases (`@fontsource/*@5` npm tarballs, or the upstream GitHub releases); copy each licence next to the files.
- **Barlow** 400, 500, 600 — subsets `latin`, `latin-ext` (`@fontsource/barlow`, upstream `jpt/barlow`) → `--font-ui`.
- **Barlow Semi Condensed** 400, 600 — `latin`, `latin-ext` (`@fontsource/barlow-semi-condensed`) → `--font-label` (field labels, table headers, index).
- **STIX Two Text** 400 normal + 400 italic — subsets `latin`, `greek` (`@fontsource/stix-two-text`, upstream `stipub/stixfonts`) → `--font-sym`.
- Licences: `fonts/OFL-Barlow.txt`, `fonts/OFL-BarlowSemiCondensed.txt`, `fonts/OFL-STIXTwoText.txt`.
- **Barlow has no Greek.** Declare an extra `@font-face` family `SymGreek` = STIX Two Text regular with `unicode-range: U+0370-03FF, U+1F00-1FFF, U+2126, U+00B5;` and put it **first** in `--font-ui`/`--font-label` stacks, so `γ`, `μ`, `φ`, `η` render from STIX inside otherwise-Barlow labels instead of falling back to a system font.
- 13 files total, ~180 KB. No CDN, no `@import`, no inline `<style>`.

## 2. Layout — `css/layout.css`, `js/layout.js`
Breakpoints: `≥1100px` three columns `[--index-w | --form-w | 1fr]`; `720–1099px` two columns `[--index-w | 1fr]`, results **below** the form in the same column; `<720px` one column.
Regions (fixed ids, shell-owned): `#tool-index`, `#form-pane`, `#results-pane`, inside `#app`. `#app` is `display:grid`, `min-height:100dvh`; each pane scrolls independently at ≥1100px (`overflow-y:auto; overscroll-behavior:contain`).
Sticky: at ≥1100px `#tool-index` and the form's `#form-actions` (Calcola / Carica esempio bar) are `position:sticky; top:0` / `bottom:0`; in `#results-pane` the verdict block `.r-verdict` is `position:sticky; top:0; background:var(--paper)` with a `--hairline` bottom rule. Nothing sticky below 1100 px except the mobile pane switch.
`<720px`: `#tool-index` collapses into a `<details class="app-picker">` whose `<summary>` reads `Strumenti` + the current tool title; opening it renders the same index DOM (one implementation, moved with `append`, not duplicated). Below it a two-button tablist `[Dati | Risultati]` (`role="tablist"`, `aria-selected`, `aria-controls`) switches panes via `hidden` on `#form-pane`/`#results-pane`; `data-pane="dati|risultati"` on `#app`. Both panes stay in the DOM.
200 % zoom / 320 px: single column, no horizontal page scroll; only `.r-table-scroll` scrolls horizontally.
**Focus after Calcola** (shell): success → `#results-head` (`tabindex="-1"`, the `<h2>` of the sheet) `.focus({preventScroll:false})`, and on `<720px` first switch to `risultati`; failure with field errors → first `[aria-invalid="true"]` control; failure without field mapping → `#error-summary` (`tabindex="-1"`). Selecting a tool focuses `#tool-title`. `scroll-margin-top: var(--s5)` on both targets.
**Routing** — `js/router.js`, hash only: `#/<tool-name>?<field>=<value>&…`. Read on **boot before first render** (fixes the measured deep-link regression), on `hashchange`, and on back/forward. Unknown tool → `#tool-index` stays, `#form-pane` shows `Strumento sconosciuto: <name>` + list link, no silent no-op. Query params = shared inputs (P1); writing them is opt-in (the "Copia link" action in `#form-actions`), submitting a form only does `history.replaceState` of `#/<tool>`.
Headings: persistent `<h1>StruttureMenni</h1>` (visually `--t-s`, `--graphite`), per-tool `<h2 id="tool-title">`, sheet `<h2 id="results-head">`, groups `<h3>`. Never a page without an `h1`.

## 3. Components and states
Every interactive element: default / hover (`--film` wash or 1-step border darkening, no transform) / `:focus-visible` (§1) / `[disabled]` (`opacity:.55; cursor:not-allowed`, still announced) / error (`aria-invalid="true"`, `--ko` border + `--ko-bg` tint) / loading (`aria-busy="true"`, label swap) / empty (prose invitation, never an illustration).

- **Tool index + search.** `<input type="search" id="tool-search" placeholder="Cerca strumento o norma">`; filters on `title + norm + group`, case/accent-insensitive (`String.prototype.normalize("NFD").replace(/\p{Diacritic}/gu,"")`), substring match, so `3.3` and `§3.4` hit. Groups = `tool.group.split(" / ")` → level-1 `<details open>` + level-2 `<h3>`; open group remembered in `sm.ui.openGroups`. Tools are `<button type=button class="ti-item" data-tool=…>`, min-height `--control-h`. Selected: `background:var(--marker); color:var(--ink)` + `aria-current="true"`. Empty search: "Nessuno strumento per «x»."
- **Form section.** `<section class="f-section"><h3>` from the `group` hint, order = first appearance; `Avanzate` always last, rendered as `<details class="f-section f-advanced">` closed. No `group` → one unnamed section.
- **Field.** `<div class="f-field" data-field=NAME data-kind=…>` → `<label for=field-NAME>` (`--font-label`; unit in a `<span class="f-unit">[kN/m²]</span>`, symbol via `symbolNode`) → control (`id=field-NAME`, `name=NAME`, `max-width:--field-max`, `height:--control-h`) → `<p class="f-help">` (schema `description` when it differs from the label) → `<p class="f-error" id="field-NAME-error" hidden>`. `aria-describedby` lists help + error ids; error sets `aria-invalid="true"`. Number: `inputmode="decimal"`, `step` from schema, `[min]/[max]` present for semantics but the form is **`novalidate`** — all range checks run in JS and render into `.f-error` in Italian (fixes: native tooltips currently bypass the app's error copy). Select: native, first option `—` only when the field is optional. Checkbox: native control ≥24 px hit area via label padding (no `appearance:none`). Comune: existing `comune-widget.js` datalist pattern, unchanged. Conditional fields use the `condition` hint (§4): hidden in place with `hidden`, never reordered, and excluded from the submitted payload.
- **Error summary + inline error.** `<div id="error-summary" role="alert" tabindex="-1">`: "N campi da correggere" + `<ul>` of `<a href="#field-NAME">label: message</a>`. Server errors arrive as `"loc: messaggio"` strings (`shared/tool.py::_message`); `parseServerErrors()` splits on the first `": "`, matches `loc` (and dotted first segment) against known field names → inline; unmatched → summary only (e.g. the model-level "specificare esattamente uno tra comune e zona", which additionally attaches to **both** named fields when their names appear in the message).
- **Verdict block** `.r-verdict`. Load tools have no checks: render the one-line *sintesi* built from the highlighted outputs (`q_s = 1,20 kN/m² — zona II, a_s = 350 m`) so the slot is never empty. Verify tools: `✓ Tutte le verifiche soddisfatte` / `✗ N verifiche non soddisfatte` — icon (inline SVG) + word + colour, never colour alone.
- **Check row + utilisation bar.** Grid `[name | clause | detail | bar]`. Bar = two `<div>`s, width set with `el.style.setProperty("--util", ratio)` (CSSOM, CSP-safe), fill `--ok` ≤1 / `--ko` >1, ticks at 1.0; `role="img"` + `aria-label="sfruttamento 0,82"`. Ratio from `check.value/check.limit` when present, else parsed from `detail` (`/(-?\d+(?:[.,]\d+)?)\s*(?:≤|<=|\/)\s*(-?\d+(?:[.,]\d+)?)/`); unparseable → no bar, row still complete.
- **Results group.** Nested output models → `<section class="r-group"><h3>` = the model's Italian `description`/title (never the class name, never `Sisma!I31`). Rows: `<div class="r-row" data-highlight>` grid `[symbol | label | value | unit | clause]`, right-aligned numeric column, `--hairline` between rows. Highlighted rows go **first**, `background:var(--marker)`, ≤3; everything else demoted into a `Passaggi di calcolo` group. Nulls hidden; a null with a documented reason prints the reason text, not `—`. Unit cell always exists (`-` when the schema says so). Clause = the tool `norm` or a per-field clause, `--graphite`, `--t-xs`, in the right margin (below 720 px it moves under the label).
- **Symbol rendering** — `symbolNode(sym)` returns a `DocumentFragment` of `<i class="r-sym">` + `<sub>` built with `createElement`/`textContent`, never `innerHTML`. Tokenizer: split at the **first** `_`; the subscript ends at the first `(`, ` ` or end; trailing `(z)`, `(T)` stay on the baseline; `T*_C` → base `T*`. Greek passes through as Unicode (rendered by STIX, §1).
- **Value formatting** — `js/format.js`, `Intl.NumberFormat("it-IT")` only. Default `maximumSignificantDigits: 4`; integers (schema `type: integer`, or `Number.isInteger`) exact with `maximumFractionDigits: 0`; `|v| < 1e-4 || |v| >= 1e6` → scientific, mantissa 4 sig + `·10` + `<sup>`; `0` → `0`; booleans → `sì`/`no`; strings verbatim. Every formatted numeric node carries `title` = full precision (`String(value)`). Copy/CSV use full precision with decimal **comma**.
- **Row table** — `.r-table-scroll{overflow-x:auto}` (fixes the measured 379–425 px table clipped in a 285 px wrapper) with `tabindex="0"` + `aria-label` so it is keyboard-scrollable; `<caption>`, `<th scope=col>` sticky (`position:sticky; top:0`), header = `symbol` + `description` + `[unit]`. Actions above: `Copia tabella` (TSV, decimal comma → pastes into Excel it-IT) and `Scarica CSV` (`;` separator, decimal comma, UTF-8 BOM, filename `<tool>-<field>.csv`) via `Blob` + `URL.createObjectURL`. Both swap their own label for 2 s; no toast.
- **Line chart** — see §5 `chart.js`. Inline SVG, `viewBox` + `preserveAspectRatio`, `stroke-width="2"` presentation attribute, `stroke="currentColor"` with `currentColor` set per series class. Series 1 solid, series 2 dashed `6 3` (CVD + b/w print). One quantity per axis, `y` never mixes kinds; direct end-of-line labels, plus a legend when ≥2 series. Crosshair + tooltip follow pointer and arrow keys (`role="application"` avoided: the `<table>` is the accessible alternative, chart is `aria-hidden="true"` + `<figcaption>`). Optional vertical guides (`guides` hint) labelled `T_B`, `T_C`, `T_D`. Max 400 plotted points (decimate, never drop endpoints). No animation.
- **Print "relazione"** — `css/print.css`, `@media print` only: `#tool-index`, search, pane switch, buttons, chart tooltip hidden; single column; `--paper`/`--ink` forced to white/black, `--marker` becomes a 1.5 px left rule + bold (yellow fills print grey); `break-inside: avoid` on `.r-group`, `.r-check`, `figure`; tables repeat `<thead>`; `@page { margin: 18mm 15mm }`. Order: **cartiglio** (progetto + committente — free text, persisted `sm.cartiglio`, editable in the print dialog panel — element, tool title, `norm`, date, app version, mode `standard` | `foglio Excel`) → full input echo grouped as §1 of ENGINEER_NOTES → symbol/value/unit/clause rows → table → chart → checks. **Never print without the mode line.**
- **Empty / loading.** `#results-pane` empty: "Compila i dati: il calcolo parte da solo. Oppure carica l'esempio." with live
  calculation on, "Compila i dati e premi Calcola. Oppure carica l'esempio." when it is off (header toggle, persisted;
  the placeholder follows the toggle while the pane is empty — owner's finding 2026-09-22). Loading: submit button `disabled`, `textContent = "Calcolo…"`, `form[aria-busy=true]`; restored in `finally`.
- **Live regions.** Exactly two, declared statically in `index.html` (fixes: 0 today): `#results-pane` has `aria-live="polite" aria-atomic="false"`; `#error-summary` and `#run-error` have `role="alert"`. Nothing else is live.

## 4. Backend hint contract (final)
All optional, all via pydantic `json_schema_extra`; the UI must render correctly when every one is absent.

| Key | Where | Type | UI effect | Absent → |
|---|---|---|---|---|
| `unit` | in/out field | `str` (`"-"` = adimensionale) | unit column / label suffix | empty unit cell |
| `widget` | in field | `"comune"` | datalist widget | plain text input |
| `group` | in field | `str` | form section, order = first appearance | one unnamed section |
| `advanced` | in field | `true` | moved into the closed `Avanzate` fold | stays inline (**and `ADVANCED_FIELD_NAMES` is deleted** — no field name in JS) |
| `condition` | in field | `{"field": str, "equals": [any]}` | show/hide in place, excluded from payload when hidden | always visible |
| `symbol` | in/out field | `str`, `_` = subscript, Greek Unicode | symbol column, mathematical italic | symbol cell empty |
| `highlight` | out field | `true`, ≤3 per tool | marker row, hoisted to the top, feeds the load-tool sintesi | no highlight, natural order |
| `legacy_only` | out field | `true` | hidden unless the run's `inputs_echo.legacy_compat` is true; otherwise grouped under `Solo modalità Excel` | always shown |
| `chart` | out tuple-of-rows | `{x, y[], x_label, y_label, guides?: [{field, label}]}` | line chart above the table | table only |

`Tool.example: dict[str, Any] | None = None` (frozen dataclass field, defaults `None`). `GET /api/tools/{name}/schema` returns `{"name","title","group","norm","example","input","output"}` — one request is enough to boot a deep link. `GET /api/tools` unchanged. `Check` gains `value: float | None = None`, `limit: float | None = None`, `unit: str = ""` (non-breaking; the UI still falls back to parsing `detail`). No hint key is ever required, and no UI module may branch on a tool name.

## 4b. Addendum (batch 2) — table inputs and located errors
Decided by the batch-2 architecture (`docs/architecture-batch2.md` §2 — read that section; it is normative for this addendum).
- **Table input widget (package `forms`, new module `js/table-input.js` + styles in `css/forms.css`).** Any input property of JSON type `array` whose `items` resolve to an object (hint `widget: "table"`, but render the same editor when the hint is absent) becomes a row editor: header cells = column `symbol` + `description` + `[unit]`; one `<input>`/`<select>` per cell typed from the column schema; add / duplicate / delete / move row (hidden when `table.fixed_rows`); Tab/Enter/arrow grid navigation; `minItems`/`maxItems` enforced with an Italian message. "Incolla da Excel" (`table.paste`, default true): textarea/clipboard accepting TSV or `;`-CSV, decimal comma or point, blank lines skipped, thousands separators rejected with a message naming the cell, header row auto-detected and mapped through each column's `aliases` (case/accents/units in brackets ignored), otherwise positional; choice "sostituisci / aggiungi". `table.csv`: "Carica CSV" (FileReader, UTF-8 with or without BOM, same parser) and "Scarica modello CSV" (header only). Above `table.preview_rows` (default 50) rows the editor collapses to "N righe caricate" with first/last rows previewed; such tables are NOT written to localStorage or the share link. The submitted value is an array of row objects with typed values (numbers as numbers, empty optional cell = null).
- **Unit selector (user decision D1).** A model-level hint `unit_selector: "<field>"` names an enum input (e.g. `sistema_unita`); fields carrying `unit_options: {"SI": "m", "tecnico": "cm"}` show the unit matching the selector's current value and update live when it changes (labels, table headers, placeholders). Values are never converted client-side. Absent hints -> the plain `unit`.
- **Located errors.** `Report.error_details = [{loc: [...], message}]` now accompanies the `errors` strings (backend done). Map `loc = ["campo"]` to the field, `loc = ["tabella", i, "colonna"]` to the cell of 0-based row `i` (mark with `aria-invalid`, message in the row's error line, summary entry "Stratigrafia, riga 3, Modulo: …" using `table.key` for the row label when present), `loc = []` to the summary only. Fall back to parsing the `"campo: messaggio"` strings when `error_details` is empty.
- **Many-rows results (package `results`).** Output tuples with the hint `rows_page: N` render paged (N rows per page, "Scarica CSV" always exports all rows); groups named `inviluppo` / `governante` are ordinary groups/tables — no special casing by name.
- **E2E.** No real table tool exists until batch 2 is built: the suite registers a demo tool with a table input (soil layers) through `create_app(tools={**discover(), "demo-tabella": …})` served in-process, and covers: paste TSV with header aliases and decimal commas, add/delete row, cell-level server error, CSV template download, collapse above `preview_rows`.

## 5. Module contracts — `src/strutture/web/static_next/js/`
Every module is an ES module ≤150 lines, no default exports. Events are `CustomEvent`s dispatched on `document`, all namespaced `strutture:`. Types below are shape sketches, not TS.

**Shell**
- `dom.js` — unchanged: `el(tag, attrs, children) -> Element`, `clear(node) -> void`. `attrs.text` sets `textContent`; `on*` adds listeners.
- `api.js` — `fetchTools() -> Promise<Tool[]>`, `fetchSchema(name) -> Promise<{name,title,group,norm,example,input,output}>`, `runTool(name, inputs) -> Promise<{status, report}>`, `searchComuni(q) -> Promise<string[]>`.
- `json-schema.js` — `resolveRef(root, "#/$defs/X") -> object`, `resolveProperty(root, raw) -> object` (unwraps `$ref`/`anyOf`, adds `nullable`), `hintsOf(prop) -> {unit,widget,group,advanced,condition,symbol,highlight,legacy_only,chart}` (missing keys `undefined`).
- `storage.js` — `readJSON(key, fallback) -> any`, `writeJSON(key, value) -> boolean` (false on quota/parse failure, never throws), `remove(key)`. Namespace `sm.`; keys `sm.inputs.<tool>`, `sm.cartiglio`, `sm.ui.openGroups`, `sm.ui.pane`.
- `router.js` — `readRoute() -> {tool: string|null, params: Record<string,string>}`, `navigate(tool, params = {}, {replace = false}) -> void`, `onRoute(cb) -> unsubscribe`. Fires `cb` once on `start()`; `start() -> void` called by `main.js` before first paint.
- `tool-index.js` — `renderIndex(root, tools, {onSelect}) -> {setActive(name), filter(query)}`.
- `layout.js` — `setPane("dati"|"risultati") -> void`, `focusResults() -> void`, `focusFirstError() -> void`, `isNarrow() -> boolean`.
- `main.js` — wiring only: boot → `fetchTools` → index → `router.start()`; on route → `fetchSchema` → dispatch `strutture:tool-schema`; on `strutture:run-request` → `strutture:run-start` → `runTool` → `strutture:run-result`; on `strutture:results-rendered` → pane + focus.

**Events** (`detail` shapes)
`strutture:tool-schema` `{name, title, norm, example, input, output, params}` · `strutture:run-request` `{name, values}` (forms → shell) · `strutture:run-start` `{name}` · `strutture:run-result` `{name, status, values, report}` · `strutture:run-network-error` `{name, message}` · `strutture:results-rendered` `{name, ok, hasChart}` (results → shell).

**Forms**
- `schema.js` — `describeFields(inputSchema) -> Field[]`; `Field = {name, kind: "number"|"text"|"enum"|"boolean", label, help, unit, symbol, widget, group, advanced, condition, required, nullable, default, enumValues, minimum, maximum, exclusiveMin, exclusiveMax, step}`. Extends today's version; drops nothing.
- `fields.js` — `buildField(field) -> HTMLElement` (the `.f-field` wrapper), `readValue(form, field) -> any`, `setFieldError(form, name, message|null) -> void`.
- `forms.js` — `renderForm(root, {fields, example, initialValues}) -> FormApi`; `FormApi = {values(), setValues(obj), setFieldErrors(byField: Record<string,string>), clearErrors(), setBusy(bool), applyConditions()}`. Emits `strutture:run-request`. Actions: `Calcola` (submit), `Carica esempio` (hidden when `example == null`), `Copia link`.
- `validate.js` — `validateValues(fields, values) -> Record<string,string>` (Italian messages incl. the range copy from the brief), `parseServerErrors(errors: string[], fieldNames: string[]) -> {byField, general: string[]}`.
- `form-state.js` — `save(tool, values)`, `load(tool) -> object|null`, `toParams(values, fields) -> Record<string,string>`, `fromParams(params, fields) -> object`. Precedence on load: hash params > localStorage > schema defaults.
- `comune-widget.js` — unchanged: `buildComuneInput(field, id) -> HTMLInputElement`.

**Results**
- `output-schema.js` — `describeOutput(outputSchema) -> Node[]` where `Node = {kind:"scalar"|"group"|"rows", name, path, label, symbol, unit, highlight, legacy_only, chart, children?, columns?}`; resolves `$ref`/`$defs` via `json-schema.js`.
- `format.js` — `formatNumber(value, {significant = 4, integer = false}) -> string`, `formatValue(value, node) -> {text, title}`, `valueNode(value, node) -> DocumentFragment` (handles the `·10ⁿ` case), `toCsv(rows, columns) -> string`, `toTsv(rows, columns) -> string`.
- `symbols.js` — `symbolNode(symbol: string) -> DocumentFragment`, `symbolText(symbol) -> string` (for `title`/CSV headers).
- `verdict.js` — `renderVerdict(root, {checks, highlights, ok}) -> void`, `utilisation(check) -> number|null`.
- `table.js` — `renderRows(root, node, rows) -> void` (scroll wrapper, sticky head, copy/CSV buttons).
- `results.js` — `renderReport(root, {report, outputNodes, tool}) -> {hasChart}`; listens to `strutture:run-result` / `run-start`, dispatches `strutture:results-rendered`.
- `print.js` — `buildRelazione(root, {tool, inputsEcho, fields, report, mode}) -> void`, `cartiglioFields() -> {progetto, committente}` (persisted).

**Charts**
- `chart.js` — `renderChart(container, {rows, chart, series, labels, guides}) -> SVGElement|null` (returns `null` and renders nothing when `chart` is absent or `<2` valid points). `series = [{key, label, className}]`.
- `chart-axis.js` — `niceTicks(min, max, count = 5) -> number[]`, `scale(domain, range) -> (v) => number`.

**Shared CSS classes / data attributes** (owner in brackets; no other package may define them)
`app-*`, `pane-*`, `ti-*` [shell] · `f-*` [forms] · `r-*` [results] · `c-*` [charts].
Attributes: `data-tool` (index item + `#app`), `data-pane` on `#app`, `data-field` on `.f-field`, `data-kind`, `data-state="error|busy"`, `data-highlight` on `.r-row`, `data-series` on chart paths.
Fixed ids the shell guarantees and others may query: `#app #tool-index #tool-search #form-pane #form-root #form-actions #results-pane #results-root #results-head #error-summary #run-error #tool-title`.

## 6. Work packages (disjoint file ownership)
Every package works only inside its own files; anything shared is already fixed in §5.

**A. shell** — `static_next/index.html`, `css/tokens.css`, `css/layout.css`, `fonts/**`, `js/{main,router,api,dom,json-schema,storage,tool-index,layout}.js`.
Responsibilities: page skeleton with the three regions + live regions, tokens/fonts/layout, index with search + collapsible 2-level groups, hash routing incl. boot + unknown-tool fallback, pane switch, focus management, run orchestration.
Acceptance: reload on `#/vento-pressione` renders the form (>0 fields) without a click; `#/nope` shows the unknown-tool message; search for `3.3` filters the list; at 390 px every index item and control is ≥44 px tall; `document.querySelectorAll('[aria-live],[role=alert]').length === 3`; after Calcola `document.activeElement.id === "results-head"`; zero requests to any host other than `location.origin`; zero CSP violations.

**B. forms** — `css/forms.css`, `js/{schema,fields,forms,validate,form-state,comune-widget}.js`.
Responsibilities: schema → sections → fields, conditional fields, `novalidate` + Italian client validation, server-error mapping to fields, example prefill, localStorage + hash params, busy state.
Acceptance: `neve-carico-falda` shows 9 fields for `tipo_copertura = "una falda"` and 11 for `"due falde"` (hidden ones excluded from the POST body); an out-of-range altitude shows the message at the field with `aria-invalid="true"` and no native tooltip; the `comune`/`zona` model error appears in `#error-summary` **and** on both fields; "Carica esempio" fills every required field; reload restores the last inputs; `ADVANCED_FIELD_NAMES` does not exist in the tree (`grep -r legacy_compat static_next/js` → 0 hits).

**C. results** — `css/results.css`, `css/print.css`, `js/{results,output-schema,format,symbols,verdict,table,print}.js`.
Responsibilities: schema-driven sheet, highlights, groups, nulls, it-IT formatting, symbols, verdict + utilisation, row table with copy/CSV, print relazione.
Acceptance: `vento-pressione` shows `p(H) = 1,523 kN/m²` with `title="1.5230430659834242"` and exactly one marker row group (≤3 rows); no output label equals a raw key; no `Sisma!` string in the DOM; zero `—` rows; at 390 px the table scrolls horizontally with 0 clipped cells; `print` emulation shows the cartiglio with the mode line and hides `#tool-index`; CSV downloads with `;` and decimal comma.

**D. charts** — `css/chart.css`, `js/{chart,chart-axis}.js`.
Responsibilities: inline-SVG line chart per the `chart` hint, guides, legend/direct labels, crosshair + tooltip, reduced motion, CVD-safe palette, decimation.
Acceptance: `sisma-spettro` renders one `<svg>` with 2 `<path data-series>` and the table still present; `vento-pressione` renders 1 series; a tool without the hint renders no `<svg>`; no inline `style` attribute anywhere in the SVG; plotted point count ≤400 with first/last preserved.

**E. backend-hints** — `src/strutture/shared/tool.py`, `src/strutture/shared/report.py`, `src/strutture/web/routes/tools.py`, `src/strutture/loads/**`, `pyproject.toml`, `tests/web/test_schema_hints.py`.
Responsibilities: `Tool.example`, `Check.value/limit/unit`, schema endpoint shape, apply `docs/ui/hints_loads.json` to the 9 load models (groups, labels, symbols, units, ≤3 highlights, charts, `advanced`, `condition`, `legacy_only`), register or explicitly defer `sisma-completo`, add the `e2e` pytest marker + `pytest-playwright` dev dep.
Acceptance: `python docs/ui/check_hints.py` prints OK against the live schemas; `GET /api/tools/neve-carico-falda/schema` has `example`, and every input property has `group`; each tool has ≤3 `highlight`s; `sisma-spettro.punti` carries `chart`; existing golden/oracle tests still pass; no numeric behaviour changed.

**F. e2e** — `tests/e2e/**` (`conftest.py` + flow files).
Responsibilities: the plan in §7; fixture boots uvicorn with `STRUTTURE_WEB_STATIC_DIR=src/strutture/web/static_next` on a free port and yields the base URL.

## 7. E2E plan — pytest-playwright, `@pytest.mark.e2e`
1. `test_desktop_run` 1440×900 — pick `vento-pressione` from the index, fill, Calcola; assert the verdict line, the marker rows ≤3, `1,523` present and `1.5230430659834242` only in `title`.
2. `test_deep_link_boot` — `goto("#/sisma-spettro")` cold, then `reload()`; both times form fields > 0 and the tool is `aria-current`.
3. `test_keyboard_only` — Tab from the search field to Calcola, submit with Enter, assert `document.activeElement.id == "results-head"` and that every focused element had a visible `outline-width != 0px`.
4. `test_validation_flow` — out-of-range altitude → `.f-error` visible next to `#field-as_m`, `aria-invalid=true`, `#error-summary` link jumps to the field, entered values preserved; then the `comune`+`zona` model error maps to both fields.
5. `test_example_and_persistence` — "Carica esempio" → Calcola → reload → fields restored from localStorage; `#/tool?as_m=350` wins over localStorage.
6. `test_mobile_flow` 390×844 — picker `<details>`, choose a tool, Calcola switches to `Risultati`, focus on `#results-head`; assert `scrollWidth <= clientWidth` on `<body>` and `.r-table-scroll` scrollable with 0 clipped cells; all tap targets ≥44 px.
7. `test_chart_present` — `sisma-spettro` has 2 `path[data-series]` + the 81-row table; `vento-cpe-rettangolare` has no `<svg>` chart.
8. `test_print_media` — `emulate_media(media="print")`: cartiglio visible with tool, `norm`, date, mode; `#tool-index` and all buttons hidden; `.r-group` has `break-inside: avoid`.
9. `test_copy_csv` — "Scarica CSV" triggers a download whose body starts with the symbol header row, uses `;`, and contains a decimal comma.
10. `test_no_console_errors_no_csp` — walk all registered tools; assert 0 `console.error`/`pageerror`, 0 `securitypolicyviolation` (captured via `page.on("console")` + a listener registered before load), and 0 requests outside `location.origin`.
Each flow also asserts `axe`-free basics inline: every control has an accessible name, one `h1`, heading order never skips.

## 8. Risks
Contrast numbers above assume the exact hexes; any hue tweak must be re-computed with the same formula before merge. Chart + sticky verdict at 200 % zoom on 1280 px is the tightest layout case. `sisma-completo` (17 scalars + 81 rows) is the worst case for the ≤3-highlight rule and for print pagination.
