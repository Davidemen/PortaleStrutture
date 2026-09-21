# Fable design review — 2026-09-21 (staging build, before go-live)

Verdict: **ready after the P0/P1 fixes**, on one condition — regenerated contact sheets (light, dark, print page 1)
show no P0 in any tool and no empty Sintesi. Keep: verdict / η max / bar / highlight typography (STIX symbols,
tabular Barlow), the quiet film-paper-rule chrome, sigla chips, the nine pictograms and the collapsed active state,
quota ticks and line weights, the report order sketch -> dati (simbolo | descrizione | valore | unità).
Remove: the header "Cerca strumento… ⌘K" field (search already lives in the rail, on Home and on ⌘K; it breaks the
390 px header).

## UI / renderer findings (for the staging UI fixer; paths under src/strutture/web/static_next/)
1. [P0] Stirrups are closed `armatura` shapes and `.sk-armatura{fill:var(--ink)}` blacks out the core (TRV, PIR, PIC, TCO). css/sketch.css: `rect.sk-armatura,polygon.sk-armatura,circle.sk-armatura{fill:none;stroke:var(--ink);stroke-width:1.25}`; only `bars` circles stay filled.
2. [P0] `stile="pressione"` labels inherit `fill-opacity:.12` and are invisible (PLI σ, MUR p, NEV q_s, print). `.sk-svg text{fill:var(--ink);fill-opacity:1}`.
4. [P0] PUN: the marker-filled perimeter hides everything: `.sk-evidenza` closed shapes `fill-opacity:.3` (the Python side reorders the shapes).
6. [P0] Report cartiglio: `.print-cartiglio-meta{grid-template-columns:repeat(3,max-content)}` scrambles the dt/dd pairs -> `max-content 1fr max-content 1fr` in a 1pt ruled box; fields progetto, committente, elemento, relazione n., rev., progettista, "pag. x di y", "StruttureMenni v…".
7. [P0] Report sketch prints without fills, dots or arrowheads: SVG ids (`sk-terreno-0`, `sk-arrow-*-0`) are duplicated by the hidden screen copy, and print `--film` is white. `renderSketch(holder, value, {idPrefix:"p"})` in relazione.js; print.css `.sk-calcestruzzo{fill:#e6e6e6}`, `print-color-adjust:exact`.
8. [P0] η name shows raw keys: verdict.js fallback replaces `_` with spaces and capitalises (the backend renames the checks).
9. [P1] `buildDimension`: vertical quota text centred on its line runs into the solid (PLI, TCO, NAC, MUR): when |dy|>|dx| anchor on the outer side (`text-anchor:end|start`, x=∓GAP_PX, `dominant-baseline:middle`) and reserve its width in sketch-fit.js.
10. [P1] `diagramPolygon`: if the view's smaller side < 0.3·larger, scale ordinates to 0.3·larger.
17. [P1] Bars unreadable: `BAR_MIN_PX=5`; `.sk-nota` negative margin strikes the frame -> `margin:var(--s1) 0 0`.
18. [P1] Sintesi: two views stacked in the 55 % column make it 640 px tall beside an empty left half: `.r-si-layout:has(.sk-figure:nth-child(2)){grid-template-columns:1fr}`, `.r-si-main` as a band (verdict+η left, figures right), `.r-si-sketch{grid-template-columns:repeat(2,1fr)}`, max-height 260px.
19. [P1] Highlights without a symbol print their description in STIX italic; "–" units; ALL-CAPS strings: descriptions in Barlow `--t-s` graphite with a 2-line clamp; hide unit "-"; sentence case.
20. [P1] `.r-action` and `.home-card-open` render in Arial: layout.css `button,input,select,textarea{font:inherit}`.
21. [P1] Checks/units: "OS=1.263", ">=", "kN/m3", "cm2/m": `.r-check` columns `1.25rem minmax(12rem,1.4fr) minmax(9rem,13rem) 1fr 8rem`, 2-line clamp; format.js `formatDetail()` (decimal comma, ≤ ≥) and `formatUnit()` (² ³ ⁴) used everywhere.
22. [P1] Dati accordion: collapsed rows ≈ 85 px; summaries read "AX4 m": `.f-section{padding-top:0}`, `.f-section-toggle{min-height:2.5rem}`, `.f-section-summary-token{gap:.25em}`, symbols via symbols.js, symbol tokens only.
23. [P1] Rail: expanded, an open Recenti with 4-line rows pushes the categories off-screen and the active tool is yellow twice; the flyout floats mid-screen: hide `.rail-row-norm` in the rail, Recenti closed when a tool is open, marker only in the category; `.rail-flyout{top:var(--header-h);bottom:0;left:56px;border:0;border-right:1px solid var(--ink)}`.
24. [P1] Report body: a lone view sits at half width with the note beside it; values left-aligned; `.r-group{break-inside:avoid}` blanks a third of page 1: `.print-schizzo-views:has(.sk-figure:only-child){grid-template-columns:1fr}`, max-height 95mm, nota below; th left, `td.r-num{text-align:right}`; input groups `break-inside:auto`; closing "Il progettista" signature line.
25. [P2] Dark: `.sk-calcestruzzo{fill:var(--film)}` is darker than paper and reads as a void -> `color-mix(in srgb,var(--ink) 12%,var(--paper))`. Mobile: `#bottom-bar` marker-yellow "Calcolo completato" misuses the marker -> paper + ink top rule, show the first highlight.

## Also on the UI fix list (found by the orchestrator)
- The active category's sigla badge covers its pictogram in the collapsed rail (move it to the corner).
- "Espandi tutto / Comprimi tutto" are two large buttons above the form (make them compact text buttons).
- Odd gap in the "a g" subscript in form labels.
- Tools with no checks / highlights / sketch show an EMPTY Sintesi (e.g. sisma-spettro): show the chart there when the tool has one, otherwise collapse the block.
- `acciaio-resistenza-incendio` cannot run from the UI: "tempi_min: Input should be a valid tuple" — the generic form has no input for a list of numbers. Add an array-of-scalars field (comma/space/newline separated, decimal comma accepted, shown as chips or a plain text field) driven by the JSON schema (`type: array`, `items` number/string).
- Remove the header search field.

## Sketch content findings (sent to the Python sketch authors)
3 MUR pressure diagram mirrored · 5 PLP elevation (piles, tie level, labels) · 10 NEV snow as vertical load on a horizontal baseline · 11 MEN proportions · 12 MUR labels and surcharge · 13 EDO/NEW/TG soil width, quotas, 2:1 spread · 14 PLI plan with column/axes/eccentricity, no M arrow · 15 PAV footprints · 16 CPE zones A/B/C, real minus · 17 SHR/COL quotas · 8 Italian check names · 19 symbols for highlighted outputs.
