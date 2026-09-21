# UI/UX brief — StruttureMenni

**Subject.** Structural-engineering calculation tools (NTC 2018 / Eurocodes) ported from an engineer's Excel sheets.
**Audience.** Italian structural engineers at a desk (wide screen, keyboard) and occasionally on a phone/tablet over VPN on site. They know the norm; they do not know our field names.
**Job of the UI.** Enter the data of one element fast, read the verdict at a glance, trust it (symbol, value, unit, clause), and take it away (print/PDF into a *relazione di calcolo*, copy a table).

## What is wrong today (measured on the live app, 2026-09-20)
1. Results show raw keys and raw floats: `a_r 1.0007337802921321`, `p_h_kNm2 1.5230430659834242`. Every output field ALREADY has an Italian `description` (100 %) and most have `unit` in the JSON schema — the renderer ignores them.
2. No hierarchy in results: the governing value and the pass/fail verdict are buried among 20 equal rows; `null` values render as "—" rows.
3. Form and results are stacked: "Pressione del vento" is 1800 px tall; you compute, then scroll to find the answer. Wide screens are wasted.
4. Mobile: the tool list occupies ~45 % of the first screen (8 tools now, ~30 soon) before the form starts.
5. Labels leak implementation: "…(parametrico, cfr. Tabelle!M1)", "alternativa al comune", keys like `legacy_compat` with no label. Group headings are tracked ALL-CAPS.
6. Validation errors appear as one list far from the fields; inputs are lost on reload; no example to start from; no way to print or export; row tables (spectrum: 81 rows, wind profile) have no chart.
7. Long flat forms are coming (columns ~25 fields, retaining wall ~30): they need sections.

## Design direction — "foglio di calcolo dell'ingegnere"
Grounded in the engineer's own paper world: the calculation sheet (symbol = value unit, clause in the margin), the drawing title block (*cartiglio*), DIN-style drafting lettering, and the yellow highlighter engineers drag over the governing result.

**Spend the boldness in ONE place: the results sheet.** It is typeset like a page of a relazione di calcolo — symbol in mathematical italic, value in tabular figures, unit, clause reference in the margin, the governing results struck with highlighter yellow, the verdict stated in words with a utilisation bar. Everything else (index, form) is quiet and disciplined.

### Tokens
| Role | Light | Dark | Note |
|---|---|---|---|
| `--film` app background | `#EEF1F3` | `#0F1417` | cool drafting-film grey, not cream |
| `--paper` sheets/panels | `#FFFFFF` | `#161C21` | |
| `--ink` text, primary button | `#15202B` | `#E7ECEF` | blue-black china ink, not tinted near-black |
| `--graphite` secondary text | `#5B6773` | `#9AA7B2` | |
| `--rule` hairlines, borders | `#C9D1D8` | `#2A333B` | |
| `--marker` highlighter | `#FFE45C` | `#6B5700` (bg) | ONLY behind governing results and the selected tool; never for text |
| `--ok` / `--ko` / `--warn` | `#1F7A4D` / `#B42318` / `#8A5A00` | `#4AD07F` / `#F07068` / `#E0B252` | status only, always with icon + word |
Designer must verify contrast (WCAG AA) for every text/background pair and may adjust steps, not hues.

**Type.** Two self-hosted OFL families (no CDN — CSP is `default-src 'self'`, and the app runs offline on a VPN):
- **Barlow / Barlow Semi Condensed** — UI, labels, values (`font-variant-numeric: tabular-nums`). DIN-drafting vernacular; the semi-condensed cut keeps long Italian labels on one line.
- **STIX Two Text Italic** — mathematical symbols only (`f_ck`, `γ_c`, `λ_lim`, `V_Rd`), with real subscripts.
Scale (rem): 0.8125 / 0.9375 / 1.0625 / 1.3125 / 1.75. Sentence case everywhere. No ALL-CAPS labels, no monospace for data, no "→" on buttons, no eyebrow labels, no identical rounded cards with soft shadows: separate with rules and space; radius 3 px on controls only.

**Layout.**
```
≥1100 px                                         <1100 px                 <720 px
┌────────┬──────────────┬───────────────────┐   ┌────────┬───────────┐   ┌───────────────┐
│ index  │ form         │ results sheet     │   │ index  │ form      │   │ [Strumenti ▾] │
│ search │ sections     │ verdict (sticky)  │   │        │ results   │   │ Dati│Risultati│
│ groups │ [Calcola]    │ groups, table,    │   │        │ (below)   │   │ (one at a time)│
│ 240px  │ 380px sticky │ chart   (fluid)   │   └────────┴───────────┘   └───────────────┘
└────────┴──────────────┴───────────────────┘
```
Left-aligned throughout. After "Calcola" on narrow screens switch to "Risultati" and move focus to the verdict.

**Copy.** Interface voice, Italian, plain verbs: "Calcola", "Carica esempio", "Stampa relazione", "Copia tabella", "Scarica CSV". Errors say what is wrong and how to fix it next to the field ("Altitudine: massimo 1500 m — oltre serve uno studio specifico del sito (§3.3.2)"). Empty results pane invites action: "Compila i dati e premi Calcola. Oppure carica l'esempio." `legacy_compat` is shown as "Riproduci il foglio Excel originale (errori inclusi)" under "Avanzate".

## Scope
**P0 — must**
- Results from the OUTPUT JSON schema: label = `description`, unit, optional symbol; nested models = titled groups; tuples of rows = tables; hide nulls; it-IT number formatting (4 significant digits by default, integers exact, full precision in `title` and when copying).
- Verdict block: "Tutte le verifiche soddisfatte" / "N verifiche non soddisfatte", each check with clause, detail and (when `value`/`limit` are parseable from the check) a utilisation bar; warnings and errors above results.
- Two-pane desktop layout, mobile tool picker + Dati/Risultati switch, tool index with search and collapsible groups, deep link `#/tool-name`.
- Form sections from the schema hint `group`; field errors placed at the field (map pydantic `loc`), summary linked to fields; keep inputs on error; loading state on "Calcola"; Enter submits.
- Accessibility: WCAG 2.2 AA, visible focus, `aria-live` results, labels/ids, reduced motion, keyboard-only flow, works at 200 % zoom.
**P1 — should**
- "Carica esempio" (tool `example` inputs), remember last inputs per tool (localStorage), share link with inputs in the URL hash.
- "Stampa relazione": print stylesheet that renders a clean calc-report page with a cartiglio (tool, norm, date, mode) + inputs + results + checks; no chrome.
- Copy table / download CSV for row tuples.
- Line chart for row tuples with a `chart` hint (spectrum Se, Sd vs T; wind p vs z; fire fy vs t): inline SVG, 2 px lines, crosshair + tooltip, legend for ≥2 series + direct labels, one axis only, table stays as the accessible alternative, palette validated for CVD in light and dark.
**P2 — could**: standard vs legacy side by side; recent tools.

## Schema-hint contract (backend -> UI), all via pydantic `json_schema_extra`
`unit` (exists) · `widget: "comune"` (exists) · `group: "Geometria"` (input sections, order = first appearance) · `symbol: "f_ck"` (underscore = subscript, Greek as Unicode) · `highlight: true` (governing results, ≤3 per tool) · on a tuple-of-rows field `chart: {"x": "t_s", "y": ["se_g","sd_g"], "x_label": "T [s]", "y_label": "S [g]"}`. `Tool.example: dict | None` = the golden-case inputs, exposed by `GET /api/tools/{name}/schema` as `example`. The UI must work when any hint is missing.

## Hard constraints
- Vanilla ES modules, no build step, no framework, no CDN, no inline `<script>`/`<style>`/`style=""` attributes (CSP `default-src 'self'`): use classes, CSS custom properties, and CSSOM (`el.style.setProperty`) only; SVG presentation attributes are fine.
- Schema-driven: ZERO per-tool UI code. Everything inserted into the DOM goes through `textContent` (existing `js/dom.js`).
- Modular: one ES module per concern (≤ ~150 lines), CSS split by owner (`tokens.css`, `layout.css`, `forms.css`, `results.css`, `chart.css`, `print.css`).
- **Staging.** Work in `src/strutture/web/static_next/` (start as a copy of `static/`); the live UI in `static/` is in use over VPN and must not change. Dev server: `STRUTTURE_WEB_STATIC_DIR=src/strutture/web/static_next STRUTTURE_WEB_PORT=8001 uv run python -m strutture.web`. The orchestrator swaps directories after review.
- Only ONE agent at a time may drive the browser (single shared Playwright instance). Prefer accessibility snapshots and `browser_evaluate` measurements to screenshots (≤ 6 JPEG screenshots per agent, `scale: css`).
- Tool schemas for reference: `build/ui-audit/tool_schemas.json` (regenerate with `discover()` if stale). Do not read Python tool packages to learn field names.
