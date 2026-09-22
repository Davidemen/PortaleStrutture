# Handoff — StruttureMenni (written 2026-09-22, 12:10 CEST)

Written for an agent starting clean. Read this, then `docs/BUILD_CONTRACT.md`, then the spec/architecture
documents named below. Do not re-derive: the state below is verified.

## 1. What this is
Italian structural-engineering calculation tools (NTC 2018 / Eurocodes), ported from 23 Excel workbooks into the
Python package `strutture` (31 tools) with a FastAPI + vanilla-JS web UI. Owner: Bastian (structural office, uses
MIDAS NX), reaches the app over a NetBird VPN at `http://100.112.1.85:8000`. Runs on macOS (developed here) and
Windows (not yet checked by the user — `docs/WINDOWS_CHECK.md`).

## 2. State at handoff
- Git: local only, branch `main`, latest commit `12ee445`. No remote (GitHub + CI deferred by the user).
- Suites (all green): `uv run pytest -q` → 4123 passed · `uv run pytest tests/e2e -m e2e -q` → 229 passed, 1 skipped
  (~3 min) · `node --test tests/e2e/*.mjs` → 34 · `uv run ruff check .` clean ·
  `uv run python -m strutture.shared.divergences.check --strict` → 0 errors.
- Live server (port 8000, localhost + VPN) was started from the previous session and dies with it. Start it with
  `uv run python scripts/serve_live.py --host 127.0.0.1,100.112.1.85 --port 8000` (background). **Tell the user
  before every restart. Never stop any process by name** (an agent's `pkill -f strutture.web` once killed the
  live server; that is why the launcher script exists). Verify: `curl -s http://127.0.0.1:8000/api/tools`.
- Served UI = `src/strutture/web/static/`. Staging copy = `src/strutture/web/static_next/` (git-ignored). All UI
  work happens in staging on a dev port (8012–8015, `--static-dir src/strutture/web/static_next --data-dir
  build/ui-dev-data`), is tested with `STRUTTURE_E2E_STATIC_DIR=src/strutture/web/static_next`, then promoted:
  `rm -rf build/static_prev_backup && mv src/strutture/web/static build/static_prev_backup && cp -R
  src/strutture/web/static_next src/strutture/web/static && sed -i '' 's#web/static_next/js/#web/static/js/#'
  tests/e2e/*.mjs`, full e2e on `static/`, commit `src/strutture/web/static tests/e2e`, announce, restart 8000.

## 3. In flight — check this first
**If the previous session is still alive (ask the user), it owns this section, `static_next/`, `tests/e2e/` and
port 8000 until it reports the builder done: do not touch those, do not start a server on 8000, and start from
§4 item 3 instead. Two sessions on the same files or port will collide.**

A Sonnet builder was working in `static_next/` + `tests/e2e/` on WORKBENCH_SPEC §15 ("Usa in…" typed links),
§16 (Excel mode retires per approved tool) and the element-restore control of the project page (§14.3) when this
handoff was written. It may have finished, died on a session limit, or been killed with the session.
1. `diff -rq src/strutture/web/static src/strutture/web/static_next`; `git status --short tests/e2e build/ui-review`.
2. If `tests/e2e/test_usa_in.py` and `tests/e2e/test_excel_ritirato.py` exist and the full e2e suite passes on
   staging, review the screenshots (`build/ui-review/usa-in-*.jpg`, `excel-ritirato.jpg`, `elementi-eliminati.jpg`),
   promote as in §2, commit, announce + restart. The previous builders' reports are in the session transcript only —
   judge by tests and screenshots.
3. If half done: finish per the specs, or reset (`rm -rf src/strutture/web/static_next && cp -R
   src/strutture/web/static src/strutture/web/static_next`, delete the partial test files) and relaunch one Sonnet
   builder with the §15/§16/restore brief (the brief is the spec text itself; the previous prompt also said: dev
   port, headless Python Playwright with `window.print` stubbed, TDD, files ≤ 400 lines, no Python edits,
   `Content-Type: application/json` with `{}` on the bodiless restore POST — the same-origin guard rejects it otherwise).

## 4. Outstanding work, in order
1. §15 + §16 + element restore UI (above). After that every phase the user asked for is built.
2. Blocked on the user (do not start; remind them): Windows check (`docs/WINDOWS_CHECK.md`, incl. the
   `Avvia StruttureMenni.bat` launcher); MIDAS live check against their NX (`docs/MIDAS_CHECK.md`); sign-off of the
   corrections register (209 entries "da confermare", page `#/registro`); the engineering decisions in §5; then
   the deferred items in `docs/ROADMAP.md`: GitHub + Actions, hazard grid, DOCX export, MIDAS phase 2.
3. Small backend follow-ups (optional): more typed links (`src/strutture/shared/collegamenti.py`; pile cap →
   punching needs mm-unit outputs first); `avvisi_campi` for the warnings of tools other than muro, plinti_isolati,
   ca_travi, vento (BUILD_CONTRACT "Warnings about one input").
4. Known P2 leftovers: `neve-carico-falda` draws a pitched roof line at α = 0°; the corbel sketch is schematic;
   highlight symbols like `M_Ed/M_Rd` subscript oddly.

## 5. Decisions the engineer of record must confirm (tell the user; do not decide for them)
Bearing capacity: γR 2,3 footing (Tab. 6.4.I), 1,4 static / 1,2 seismic wall (Tab. 6.5.I, §7.11.6.2.1); seismic
capacity uses the static Annex D formula with no inertial soil reduction (verdict flagged "da confermare");
footing self-weight factored 1,35 (Tab. 6.2.I A1 gives 1,3); the typed admissible-resistance check is still shown
beside the new one. Wall: seismic bearing capacity uses characteristic soil parameters (γM = 1, §7.11.1) while the
sheet's seismic sliding uses M2 — inconsistent, register `muro-sostegno/capacita-portante-sismica-parametri-
caratteristici`. M-N section tool: biaxial exponent EN 1992-1-1 §5.8.9(4); e0 = max(h/30, 20 mm); Es = 210 000 MPa;
Nmax = fcd·(Ac−As)+fyd·As; T/L/wall sections take bars only as a table. Beam: new input V_g (gravity shear in
capacity design, default 0 with a warning). Pile cap: β with column sides and the 1 m-strip flexure design kept
as documented simplifications (register). Punching: β applied before the soil-pressure deduction (conservative).
vRd,max coefficient 0,4 (default) vs 0,5 (register `ec2-shared/coefficiente-vrd-max-scelta-ingegneristica`).
Two shared-module refactors deliberately NOT done (ROADMAP Phase 7 note). Open unit/reference doubts: wind cr at
TR = 50, cedimenti "500" O' 40 m vs 4 m, embedment unit (register `da_verificare` entries).

## 6. Where things are
- Rules for builders: `docs/BUILD_CONTRACT.md`. Architecture: `docs/architecture.md`, `-batch2.md` (§9 user
  decisions D1–D5), `-phase2.md` (formulas), `-phase3.md` (projects), `-phase4.md` (M-N engine, bearing capacity).
  Roadmap: `docs/ROADMAP.md`. Design: `docs/ui/DESIGN_SPEC.md`, `docs/ui/WORKBENCH_SPEC.md` §0–17,
  `docs/ui/REVIEW_FABLE_2026-09-21.md`. MIDAS: `docs/integrations/MIDAS.md`.
- Core: `src/strutture/shared/{tool,report,sketch}.py` (Tool contract, Report envelope incl. `avvisi_campi`,
  sketch COMPOSITION RULES), `shared/relazione/` (formula notation + harness), `shared/divergences/` (register:
  `legacy("<unita>/<slug>", flag)`, `check --strict`, `render`), `shared/collegamenti.py` (typed links),
  `shared/sezione_ca/`, `shared/capacita_portante/`, `storage/` (SQLite: sign-offs, projects), `integrations/midas/`.
- Tools: `loads/`, `members/`, `geotechnics/`, `foundations/` — each package: models, steps, tool.py, schizzo.py,
  relazione*.py; register data `src/strutture/data/divergences/*.json` (format: `json.dumps(…, ensure_ascii=False,
  indent=1)`, no trailing newline; `docs/divergences/*.md` are GENERATED).
- Web: `src/strutture/web/{app,config,serve,presentation,confronto}.py`, `routes/{tools,comuni,midas,divergences,
  progetti}.py`, `middleware/`; UI modules under `static/js`, `static/css`.
- Tests: `tests/<package>` mirrors src; `tests/e2e` (helpers `_actions.py`, in-memory stores in `_server.py`);
  review helpers `build/ui-review/{make_sheet,shot_sintesi}.py` (need a server on 8000).
- Memory of the previous agent: `/Users/coccobas/.claude/projects/-Users-coccobas-Development-StruttureMenni/
  memory/` (`execution-plan-all-phases.md` is the running log; `MEMORY.md` the index).

## 7. Conventions and lessons (each cost time once)
- Excel mode: `legacy_compat=True` reproduces the sheet (bugs included); standard mode fixes bugs; every such branch
  is `legacy("<id>", flag)` linked to a register entry (`ramo` codice | condiviso | nessuno); tool examples never
  contain `legacy_compat`; `check --strict` stays at 0 errors (permanent test).
- Formulas: every tool has `relazione*.py`; the harness evaluates each printed formula against the tool's number, so a
  calculation change without a trace change fails there — intended. The Opus proof-read of the RENDERED formula
  text found ten real calculation defects across three waves: run it for any new calculation.
- User rule "flag it, fix in code": a defect found in a calculation is fixed in standard mode with a register entry
  (legacy keeps the sheet), never papered over in the trace.
- Checks: short names (≤ ~25 chars) and short details (≤ ~150 px), or `test_wall_results_height_budget` (900 px)
  fails; check names in Italian, no underscores.
- Sketches: lints in `tests/shared/test_sketch_layout.py` model arrow text at the TAIL and vertical-dimension text
  OUTWARD, exactly as the renderer draws them; 8-text budget per view; "Schema non in scala" notes.
- e2e: `get_by_role("button", name="Calcola", exact=True)` (a field help button's label contains "calcola");
  debug pytest-playwright timing with a temporary test file under `tests/e2e` (same fixtures), not a standalone
  script; the Playwright MCP browser gets wedged by native print dialogs — use headless Python Playwright with
  `window.print` stubbed.
- UI: strict CSP (no inline style/script, never `innerHTML`; CSSOM `el.style.setProperty` is fine); no CDN;
  Italian, sentence case, no ALL-CAPS labels, icon + word never colour alone; report exports are always complete and
  built from a fresh run (user rule).
- Agents: the user's policy — no Fable subagents (Sonnet builders, Opus reviewers; Fable only for architecture/UX if
  needed), token-aware; builders must be told "do the work yourself, never delegate" and "never stop processes by
  name"; requirements go in the repo specs + the initial prompt (mid-run messages are distrusted); session limits
  killed workflows twice — commit each finished package immediately and run at most ~5 heavy agents at once.
- Git: local commits are approved by the user; conventional-commit messages; follow the attribution rule of your own
  session reminder.

## 8. First 15 minutes for the next agent
1. `git status --short`; `diff -rq src/strutture/web/static src/strutture/web/static_next` (see §3).
2. Start the live server (§2) and tell the user it is up.
3. `uv run pytest -q` and `uv run python -m strutture.shared.divergences.check --strict` to confirm the baseline.
4. Continue at §4 item 1.
