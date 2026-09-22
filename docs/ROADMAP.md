# Roadmap — improvements after the 30-tool port

Status 2026-09-21. Decisions below marked **[U]** were taken by the user; **[A]** are my assumptions —
correct them before the phase starts.

## Ground rules (apply to every phase)
- **No user management [U].** No login, no accounts, no roles. Where a name is useful (sign-off, cartiglio) it is a
  free-text *sigla* typed by the engineer; anyone who can reach the app can read and edit everything.
- **Storage: one SQLite database on the server [U]**, stdlib `sqlite3` behind a repository interface (no ORM, no new
  dependency). Location `STRUTTURE_DATA_DIR` (default `var/`), never inside the package, never in git.
- **Hosting: both [U]** — a central instance that everybody uses from the browser, AND local installs on an
  engineer's PC with their own database. No synchronisation between instances; a project moves between them by
  **Esporta / Importa progetto** (one JSON file).
- **Relazione: PDF from the browser first [U]**; DOCX later from the same data.
- MIDAS integration stays **read-only**. Everything runs on **Windows and macOS**. Modular code, TDD, Excel-mode
  oracle tests stay green. Builders/reviewers are Sonnet/Opus agents, architecture steps Fable.
- **Version control: local git from now [U]** (first commit done), one commit per work package. Private GitHub +
  Actions **deferred [U]** — see "Marked down".

## Phase 0 — finish MIDAS reactions import *(in progress)*
Security fixes from the review (cross-origin protection for all API POSTs, bounded requests, MIDAS calls off the
event loop) -> swap the staging UI in -> **you verify against a real model** with `docs/VERIFICA_MIDAS.md`.
Manual entry / paste / CSV remain exactly as they are.

## Phase 1 — Trust layer *(first; everything else builds on confirmed results)*
1. **Divergence register as data.** Today ~150 rows live in free-form markdown. Move them to one structured file per
   unit (`src/strutture/data/divergences/<unit>.json`: stable `id`, tools, cell, sheet behaviour, fixed behaviour,
   clause, numeric impact, kind = *errore del foglio | aggiornamento normativo | scelta ingegneristica | da verificare*,
   affected outputs). The markdown documents are generated from it. Every `legacy_compat` branch in code names the
   `id` it implements; a test fails on orphans in either direction.
2. **Sign-off** (SQLite): per divergence `stato` (da confermare / approvato / respinto), `sigla`, date, note, history.
   UI page **Registro correzioni**: filter by tool / kind / status, approve or reject in bulk, open the clause text.
   Every result sheet and printed relazione shows "N correzioni da confermare".
   **Rejected = flagged, then fixed in code [U]:** a rejected item shows a red banner on every affected result
   ("correzione respinta — risultato standard non approvato per questo punto") and lands in a developer to-do list;
   reverting that fix is a small code task, after which the divergence disappears. No per-correction run-time
   switches.
3. **Confronta con Excel.** `POST /api/tools/{name}/compare` runs both modes and returns, per output, standard
   value, Excel value, Δ %, and the divergence ids responsible. UI: a toggle on the results sheet adding the
   "Excel" and "Δ %" columns, differing rows marked, each linked to its register entry and its approve/reject
   buttons — sign-off happens where the numbers are.
Effort ≈ 1.5–2 M agent tokens. Output: you can work through the corrections tool by tool in an afternoon each.

## Phase 2 — Relazione di calcolo with formulas (PDF)
1. **Formula trace.** Each calculation step can emit `Passo(simbolo, descrizione, formula, sostituzione, valore,
   unità, clausola)`; formulas are written once in a small notation (`V_Rd,c = [C_Rd,c·k·(100·ρ_l·f_ck)^(1/3) +
   k_1·σ_cp]·b_w·d`) and rendered as MathML (native in Chrome/Edge/Safari — no CDN, no JS math library; the STIX Two
   Math font is self-hosted). The substituted line is generated from the same expression and the actual values.
2. **Adoption order [A]:** plinti isolati/su pali, punzonamento, trave, pilastri, muro, then loads, then the rest —
   tool by tool, each with a snapshot test of its trace. Tools without a trace keep today's results-only print.
3. **Print layout:** cartiglio (progetto, elemento, sigla, data, versione, norma, modalità, provenienza MIDAS),
   dati by section, passi by group, tabelle (paged) and charts, riepilogo verifiche, note on unconfirmed corrections.
   One element, or the whole project in one document (needs Phase 3).
Effort ≈ 3–4 M (it touches every tool; can be spread over several sessions).

## Phase 3 — Projects and saved elements
Schema: `progetto` (codice, nome, committente, note), `elemento` (tool, nome "Plinto P1", inputs, result summary,
tool version, mode, revision), append-only `revisione`, `importazione` (MIDAS provenance). **Optimistic locking**
(`revision` number -> 409 "modificato da un altro utente, ricarica") because several engineers edit without accounts.
UI: project picker in the header, **Salva in progetto**, element list with status (verificato / non verificato / dati
modificati dopo il calcolo), duplicate, rename, history, **Relazione di progetto**, **Esporta / Importa progetto**
(the only bridge between the central and the local instances). `scripts/backup_db` + restore instructions.
Effort ≈ 1.5 M.

## Phase 4 — Engineering gaps
1. **Sezioni in c.a. — dominio M-N, generic section engine [U]:** polygonal concrete outline (rectangle, circle, T, L,
   walls as presets + free vertices via the table widget) + bar table; fibre/strip integration with NTC 2018
   §4.1.2.1.2 constitutive laws (parabola-rectangle and stress-block, steel elastic-plastic, optional hardening);
   N–M domain about either axis with chart, `M_Rd(N_Ed)`, and — same engine, neutral axis at any angle — the biaxial
   N–Mx–My check. Feeds `M_Rd` into the column tools automatically (Phase 5) and covers beams with axial force.
   No Excel oracle exists: verification = closed forms (pure compression/tension, rectangular section in pure
   bending = the existing beam tool, balanced point), published worked examples, convexity/symmetry properties,
   mesh-convergence tests, and an Opus engineering review. **L effort, highest verification burden.**
2. **Capacità portante [A]:** EN 1997-1 Annex D / Brinch-Hansen, drained and undrained, shape/depth/inclination
   factors, effective area B'×L' from eccentricities, NTC 2018 §6.4.2.1 (A1+M1+R3, γR = 2.3) and the seismic case;
   new shared module; replaces the typed-in resistance in `fond-plinto-isolato` (still overridable) and removes the
   "not computed" warning of `muro-sostegno`.
3. Later: EN 1993-1-5 class-4 effective widths; free pile coordinates in pile caps.
Effort ≈ 2.5–3 M.

## Phase 5 — Connected tools
Schema-driven links: an output declares `provides: "amax_g"`, an input declares `accepts: "amax_g"`; a registry test
guarantees every `accepts` has a provider. UI: **Usa in…** on a result row opens the consuming tool prefilled, with
provenance shown; inside a project the link is stored and the consumer is marked *dati a monte modificati* when the
source changes. First links: sisma -> muro / travi di collegamento (a_max), sezioni M-N -> pilastri (M_Rd), plinto su
pali -> punzonamento, trave -> fessurazione (σ_s), MIDAS reactions -> plinti (exists). Effort ≈ 1 M.

## Phase 6 — MIDAS phase 2 *(only after you have verified reactions live)*
Beam/column end forces (`BEAMFORCE` table) into **batch verification** of many elements × combinations, reusing the
many-rows result pattern of the footing tool (per-row results, envelope, governing row); section and reinforcement
assigned per element group in a table; every import stored with model name, time and units in the project.
Effort ≈ 2 M.

## Phase 7 — Housekeeping
- **Local install [U: both]:** `Avvia StruttureMenni.bat` / `.command` (checks uv, syncs, starts the server on
  localhost, opens the browser) + a short guide for running the central instance as a Windows service.
- ~~Move `muro` onto `shared.footing_pressure` and `ca_mensole` onto `shared.ec2_strut_tie`~~ — NOT done (2026-09-22):
  both would replace the sheet's own formulas (the wall's per-metre triangular diagram with B* = 3(B/2−|e|); the corbel's
  P_Rc = 0,4·b·d·f_cd·c/(1+(l/0,9d)²) of unknown provenance, register `ca-mensole/costanti-formule-tirante-puntone`) with
  different models and change results: an engineering decision for the sign-off, not housekeeping; highlights for the seismic
  step tools; split the few modules over 150 lines; tidy `pyproject.toml`.
- **Excel mode stays in the code** as the regression oracle; once all corrections of a tool are approved its switch
  is hidden from the UI (not deleted).

## Marked down (decided, not scheduled)
| Item | Decision | What is needed to start |
|---|---|---|
| Private GitHub repo + Actions on Windows & macOS | **chosen, deferred [U]** | your go-ahead + a repository; the suite is already portable (`docs/VERIFICA_WINDOWS.md`), the workflow file is a 30-line job |
| Seismic hazard grid (ag, F0, T*C from coordinates) | **deferred [U]** | a trusted copy of NTC Allegato B (e.g. the CSLP "Spettri-NTC" workbook) + 5 sites with known values for validation; coordinates per comune for a by-name lookup |
| DOCX relazione | after the PDF | Phase 2 data model; a DOCX renderer with native Word equations |
| Login / permissions | **excluded [U]** | — |
| Tool validation signed inside the app (option, 2026-09-22) | **optional [U]**: today the one-off pre-release gate is the hand-filled table in `docs/VALIDAZIONE_STRUMENTI.md` (kept by `scripts/validazione_strumenti.py`); if the owner wants to tick and sign it while validating, the cheapest route is one register entry per tool of a new type `validazione` (generated by a script, signed like any other entry in `#/registro`: approved = validated, sigla + date in the database; Excel mode stays available until it is approved; the markdown then generated from the database). Side effect to accept: the register mixes corrections and validations (entry counts and `docs/divergences/` pages change). ~2 agent hours. | the owner's go-ahead, after trying the markdown table for a while |

## Order and dependencies
`0 -> 1 -> 2` is the critical path to results you can sign and print. `3` can run in parallel with `2`. `4.1` before the
pilastri link in `5`. `6` waits for your live MIDAS check. `7` any time. Total ≈ 12–15 M agent tokens at the
rates measured so far.

## Open points I will ask about when each phase starts
- Phase 2: the office cartiglio (fields, logo, numbering of the relazione).
- Phase 4.2: which geotechnical parameters you normally receive (characteristic φ'k, c'k, cu,k from the geologist?)
  and whether approach 2 (A1+M1+R3) is the only one you use.
- Phase 6: which element types come first (beams or columns) and how reinforcement is assigned to groups.
