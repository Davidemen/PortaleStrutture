# Windows check

The project is developed and tested on macOS; it is written to run unchanged on Windows 10/11.
This list is what to run on the Windows machine. Every command is identical in PowerShell, cmd and zsh
(flags instead of `VAR=value command`, which only POSIX shells understand).

LibreOffice is **not** needed: it is only used on the development machine to generate test
fixtures, which are stored as JSON in `tests/fixtures/`.

## 1. Install
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # installs uv (once)
cd <folder>\StruttureMenni
uv sync                                                                              # Python + dependencies
```

## 2. Tests
```powershell
uv run pytest -q                       # calculation tools, API, shared modules — must be all green
uv run ruff check src tests            # optional: lint
```
Browser tests:
```powershell
uv run playwright install chromium     # once, ~150 MB
uv run pytest tests/e2e -m e2e -q      # 230 tests (about 3 minutes)
```

## 3. Run the app
```powershell
uv run python -m strutture.web                                  # http://127.0.0.1:8000  (31 tools)
uv run python scripts/avvia.py                                  # same, and opens the browser once the server answers
# or double-click "Avvia StruttureMenni.bat" in Explorer (check: a console opens, then the browser; closing the console stops the server)
uv run python -m strutture.web --port 8080                      # other port
uv run python -m strutture.web --host 127.0.0.1,100.112.1.85    # localhost + a VPN address
```
- First start: Windows Defender Firewall asks whether Python may accept connections. Allow it on
  *private* networks if colleagues must reach it over the VPN; localhost works either way.
- The address after `--host` must be an address of THIS machine (`ipconfig`); binding to the VPN
  address fails if the VPN is down.
- Stop with Ctrl+C.

## 4. What to look at
| Check | Expected |
|---|---|
| `uv run pytest -q` | **4123 passed** (macOS reference, 2026-09-22), 0 failures — the browser tests are deselected by default |
| `uv run pytest tests/e2e -m e2e -q` | **229 passed, 1 skipped** |
| `node --test tests/e2e/list_input_parse.test.mjs` | **34 passed** (optional, needs Node ≥ 20; `node --test tests/e2e/*.mjs`) |
| Accented text (à è ù § φ γ) in labels, errors and results | rendered correctly — every file is read as UTF-8 explicitly |
| Comune search ("Forlì", "Castro") | suggestions appear; homonyms show the province |
| A tool with a table result (spectrum, wind profile) → "Scarica CSV" | opens in Excel with `;` separators and decimal commas |
| "Stampa relazione" | clean print preview in Edge/Chrome |
| Decimal input | the browser accepts `,` or `.` according to the Windows regional settings; results always use the Italian format |

## 5. If something fails
Send the full output of the failing command. Known platform-sensitive spots, in order of likelihood:
1. a test helper that starts the web server as a subprocess (port already in use → change `--port`);
2. path length > 260 characters if the project sits in a deeply nested folder (move it closer to `C:\`);
3. antivirus scanning `.venv` slowing the first `uv sync` / test run.

## Portability rules the code follows (see `docs/BUILD_CONTRACT.md` → Portability)
`pathlib` everywhere · `encoding="utf-8"` on every text read/write · no shell syntax, `shell=True`,
`os.fork`, POSIX signals · generated file names ASCII/lowercase without `: * ? " < > |` ·
listening sockets use `SO_EXCLUSIVEADDRUSE` on Windows and `SO_REUSEADDR` elsewhere.
