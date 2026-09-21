# Build contract (read fully before writing code)

Goal: port the Excel workbooks to a modular, tested Python package `strutture` (src layout, Python ≥3.12, pydantic v2) with a generic web UI. Specs: `docs/specs/<unit>.md`. Architecture: `docs/architecture.md`.

## Modularity (hard rule)
- One **small module per calculation step** (≤ ~150 lines, functions ≤ 40 lines, pure, no I/O, no globals mutated). A tool's `run` only composes steps.
- Package per tool group: `src/strutture/loads/<group>/` with e.g. `models.py` (pydantic I/O), `<step>.py` files, `tables.py` (constants/lookup data), `tool.py` (`TOOLS` tuple). Same shape for tests: `tests/loads/<group>/test_<step>.py`.
- Shared logic lives in `src/strutture/shared/`. Tools never import from another tool package; if two tools need the same thing it belongs in `shared/`.
- You may only create/edit files inside the directories assigned in your task. Never edit `pyproject.toml`, `src/strutture/shared/{report,tool,numeric,tables}.py`, `extract/`, or another agent's directories — if you need a change there, say so in your final `notes`.

## Tool contract (already implemented — read `src/strutture/shared/tool.py` and `report.py`)
- Inputs/outputs are **frozen pydantic models** (`model_config = ConfigDict(frozen=True)`); every field has `Field(description=<Italian label>, json_schema_extra={"unit": "kN/m²"})`, bounds (`gt`, `ge`, `le`) and `Literal[...]` for dropdown enums. The web UI builds its forms from this JSON schema, so descriptions/units/enums are the UI.
- Every input model has `legacy_compat: bool = False`. `False` = code-standard behaviour (bugs fixed). `True` = reproduce the spreadsheet exactly, bugs included.
- `run(inputs) -> Report` via `success(data, inputs, checks=..., warnings=...)`; raise `CalcError("messaggio in italiano")` for inputs outside the method's validity range. Pass/fail verifications go in `checks` with the clause number. Never return strings like "OK"/"NO" as data.
- Register by exposing `TOOLS: tuple[Tool, ...]` in `tool.py`; discovery is automatic (`strutture.shared.tool.discover`).
- Use `shared.tables.exact_lookup / band_lookup / interp_lookup` instead of ad-hoc dict/loop lookups; `shared.numeric.clamp / lerp`.
- Immutability everywhere: tuples/frozensets/frozen models, no in-place mutation. Type-annotate every signature. No `print` (use `logging`). No magic numbers: name code constants with the clause they come from.

## Tests (TDD: write the failing test first)
1. **Golden** (`@pytest.mark.golden`): the spec's §8 cached input→output case, with `legacy_compat=True`, `pytest.approx(rel=1e-6)`.
2. **Oracle** (`@pytest.mark.oracle`): write `tests/fixtures/gen_<tool>.py` that calls `extract.fixtures.generate(slug, sheet_name, cases, read, target)` for **6–10 input sets** that exercise every branch (each enum value, both sides of every threshold), run it once (`uv run python tests/fixtures/gen_<tool>.py`; each LibreOffice recalculation takes 10–40 s), commit the JSON to `tests/fixtures/<tool>_oracle.json`, and test `legacy_compat=True` against it. Tests read only the JSON. Cell addresses for inputs/outputs are in the spec tables. If a sheet cell is a dropdown, pass the exact string from the `# validation` line of the cell map.
3. **Fixed behaviour** (`@pytest.mark.unit`): for every divergence, a hand-computed expectation with `legacy_compat=False`, plus boundary/validation tests (invalid enum, out-of-range, thresholds).
- Run only your own tests while iterating: `uv run pytest tests/<your dir> -q`. Before finishing: `uv run pytest tests/<your dir> --cov=strutture.<your package> --cov-report=term-missing -q` — must be ≥ 80 % and fully green, then `uv run ruff check <your dirs>`.

## Member tools (waves 3–5) — additions
- Packages live in `src/strutture/members/<pkg>/`, tests in `tests/members/<pkg>/` (pytest runs with `--import-mode=importlib`, so test file basenames may repeat across directories).
- **One composed Tool per sheet-level workflow.** A sheet that verifies one element (a beam, a column, a wall) becomes ONE tool whose `run` composes the step modules and returns every intermediate group + all `checks`, so the user fills one form. Steps stay separate small modules (pure functions with frozen result models) — that is the modularity. Register an extra sub-step Tool only when it is useful on its own. Group outputs in nested frozen models (`geometria`, `materiali`, `flessione`, `taglio`, …); the web UI renders nested objects and tuples of rows.
- Inputs stay FLAT (the generic form renders flat fields only), ordered as in the sheet from top to bottom; only outputs are nested.
- Shared modules available (read the file before using): `shared/units.py` (the ONLY place for conversion factors — name fields with units: `b_mm`, `ned_kN`, `fcd_MPa`), `shared/numeric.py` (`clamp`, `lerp`, `bisect` for goal-seek, `fixpoint` for Excel iterative circular references), `shared/tables.py`, `shared/ntc_site_seismic` (muro), plus whatever your task lists as upstream API.
- **Norm vintage.** Several sheets cite NTC 2008. Code-standard mode (`legacy_compat=False`) targets NTC 2018 + Circolare 7/2019 (and EN 1992/1993/1997/1998 where the sheet uses them). Where a 2018 formula/limit differs numerically from the sheet, implement 2018, keep the sheet under `legacy_compat=True`, and add a divergence row. If you are not certain of the 2018 text, keep the sheet behaviour in both modes and list it under "Da verificare" — never invent a clause.
- Extra golden cases: sheets that exist in several copies with different inputs (e.g. muro `Tratto B`–`E`) are free golden cases — `extract.fixtures.generate(slug, "<sheet name>", cases=[{}], read=[...])` with an empty override returns that sheet's computed values.
- Text outputs like "OK"/"NO"/"Mrd > Med -> OK" in the sheet become `Check(passed=...)`; compare against them in oracle tests by mapping the sheet's string to a bool.

## Batch 2 (geotechnics, foundations, new member tools) — additions
- Architecture: `docs/architecture-batch2.md` — §1 module map (your package row + the shared modules you consume), §2 table inputs, §6 tests, §7 bug list, **§9 user decisions (normative)**.
- Packages: `src/strutture/geotechnics/<pkg>/`, `src/strutture/foundations/<pkg>/`, `src/strutture/members/<pkg>/`, shared physics in `src/strutture/shared/<module>/`; tests mirror the path under `tests/`.
- **Table inputs** only through `strutture.shared.tabular` (`RowModel`, `table_field`, `row_errors`): one field `tuple[Row, ...]`, rows frozen/flat/scalar, cross-row rules in a `model_validator(mode="after")` raising Italian messages that name the 1-based row. Never accept free-form nested input.
- **Many-rows results:** `righe` (all rows, key columns echoed, hint `rows_page`), `inviluppo` (quantity × famiglia -> value + governing row/combo), `governante` (the governing row expanded); `checks` on the envelope only, with `value` / `limit` / `unit` filled.
- **UI hints are part of the job** (`docs/ui/DESIGN_SPEC.md` §4 + §4b, vocabulary in `docs/ui/ENGINEER_NOTES.md`): every input has `group`, Italian `description`, `unit` (or `unit_options` per §9-D1) and `symbol` where one exists; `advanced: true` on `legacy_compat` and rarely-changed coefficients; `condition` for fields that apply only to some option; ≤3 `highlight` outputs; `chart` on plottable row tuples; `Tool(..., example=<golden inputs>)` must validate and run ok in the DEFAULT mode (do not put `legacy_compat` in it — the API strips it anyway; ≤ 30 table rows). Add a test asserting all of this.
- Performance: a 20 000-row table must run in < 5 s — vectorise with plain Python comprehensions over tuples (no pandas/numpy dependency), no per-row model re-validation inside loops.

## Portability — everything must run on Windows AND macOS (user requirement)
- Files: always `pathlib.Path`; never hard-code `/` separators, `/tmp`, `~` expansion by hand, or absolute paths. Temp files via `tempfile` / pytest `tmp_path`. Generated file names: ASCII, lowercase, no `: * ? " < > |`, no names differing only by case, no trailing dot/space, avoid reserved names (`con`, `nul`, `aux`, `prn`, `com1`…), keep repo-relative paths < 180 chars.
- Text I/O: ALWAYS pass `encoding="utf-8"` to `open` / `read_text` / `write_text` (Windows defaults to cp1252 and breaks on à/è/§/φ); CSV with `newline=""`. JSON fixtures are UTF-8.
- Processes: `subprocess.run([...list...], check=…)` only — never `shell=True`, never shell syntax (`VAR=x cmd`, `&&`, `&`, pipes) in code or in test helpers; no `os.fork`, `signal.SIGKILL/SIGHUP`, `fcntl`, `resource`, `pwd`. Start helper servers with `subprocess.Popen([sys.executable, "-m", "strutture.web", "--port", …])` and stop them with `.terminate()`.
- Commands in docs and messages: `uv run python -m strutture.web --host … --port …` (flags, not env-var prefixes) so they paste into PowerShell, cmd and zsh unchanged.
- Numbers/locale: never rely on the OS locale for parsing/formatting; line endings are irrelevant to logic (`splitlines()`, not `split("\n")` on file content).
- Front-end: nothing OS-specific; fonts are self-hosted; test in Chromium (the e2e suite runs on both OSes).

## Divergences
For each spreadsheet bug you fix (see your spec §7 and `docs/architecture.md` §6), add a row to `docs/divergences/<unit>.md`: cell | sheet behaviour | fixed behaviour | clause | numeric impact on the golden case. If you are not sure the sheet is wrong, keep the sheet behaviour in both modes and list it under "Da verificare".

## Token discipline
Read your spec and only the architecture sections named in your task (use `grep -n`/`sed -n` to pull sections). Do not open other specs, the workbooks, or whole CSVs (`head`, `awk`, `grep` only). Do not explore the repo.
