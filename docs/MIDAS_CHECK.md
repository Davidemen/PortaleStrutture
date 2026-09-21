# MIDAS NX — live verification checklist

`docs/integrations/MIDAS.md` was written from MIDAS's official Python library (`midas-gen`) and its
API manual, **not** from a live MIDAS instance — none was available on the development machine. All
unit tests use `httpx.MockTransport` replaying the documented shapes. This checklist is what an
engineer with MIDAS Gen NX or Civil NX installed must run once, against a real model, before trusting
the import for a project. Commands are PowerShell (flags, not `VAR=value cmd` — that syntax is
POSIX-only and would silently fail on Windows).

Report back pass/fail for every numbered step, and for any failure the raw request/response JSON
(the key is never in the response — see step 8 — so it is always safe to paste as-is).

## 0. Find your Base URL and MAPI-Key

1. Open MIDAS Gen NX or Civil NX with the model you want to test.
2. Menu **Apps > API Settings**.
3. Toggle **Connect** to ON — the app must stay open and connected for every step below; if it's
   off you'll see `502 not_connected`.
4. **Base URL**: shown in the same panel, e.g. `https://moa-engineers.midasit.com:443/gen`
   (Gen NX) or `.../civil` (Civil NX). Regional installs may show `moa-engineers-gb`, `-in`, `-kr`,
   `-us`, or the China relay `moa-engineers.midasit.cn`. Copy it exactly — don't retype it.
5. **MAPI-Key** (personal API key): generate one if none exists yet, then copy it. Treat it like a
   password — paste it into a PowerShell variable, never into a command you'll paste elsewhere.

## 1. Start the server

```powershell
uv sync
uv run python -m strutture.web --port 8000
```

Leave this window running; do everything else in a second PowerShell window.

```powershell
$key = "<incolla qui la tua MAPI-Key>"
$baseUrl = "<incolla qui la tua Base URL, es. https://moa-engineers.midasit.com:443/gen>"
```

## 2. Connection + version

```powershell
curl.exe -s http://127.0.0.1:8000/api/midas/status
```
Expect `{"server_key":false,"base_url":null,"product":null}` (no server-wide key configured — normal;
the key is per-engineer, sent with every request instead).

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/verify -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{}"
```
If autodetection doesn't find your relay, pass the Base URL explicitly:
```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/verify -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{`"base_url`":`"$baseUrl`"}"
```
Compare against MIDAS itself:
- `name`/`version` match **Help > About**.
- `product` is `gen` or `civil` as appropriate.
- `units.force`/`units.dist` match what **Tools > Unit System** shows for the model right now.

## 3. Combinations

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/combinations -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{`"base_url`":`"$baseUrl`"}" | Out-File combinations.json -Encoding utf8
notepad combinations.json
```
Compare against MIDAS's own **Results > Load Combinations** tables (General, Concrete Design, Steel
Design, SRC, Steel Composite, Seismic):
- every combination MIDAS shows appears exactly once, under the right `classification`;
- `table_name` is `NAME` followed by the analysis suffix in parentheses — our code assumes `(CB)`
  for General and Seismic, `(CBC)` Concrete, `(CBS)` Steel and Steel Composite, `(CBR)` SRC (see
  `src/strutture/integrations/midas/combinations.py`). **This is the single biggest unverified
  assumption in the whole integration** — if step 4 below returns zero rows for a combination that
  clearly has results in MIDAS, this suffix is the first thing to check (look at the `Load` column
  of MIDAS's own reaction table for the exact string MIDAS uses);
- `famiglia_suggerita` is a reasonable NTC 2018 guess (SLU_STR / SLU_EQU / SLV_STR / SLV_EQU /
  SLE_RARA / SLE_FREQ / SLE_QP) — wrong guesses are harmless, the UI lets you override them.

## 4. Reactions on a small model — the main check

Pick 2-3 nodes and 2-3 load combinations you can also read by eye in MIDAS's own
**Results > Reactions > Reaction Table** (set its display units to kN / m first, Tools > Unit
System, so the comparison in this step is apples-to-apples).

```powershell
$body = '{"base_url":"' + $baseUrl + '","nodi":[12,13],"combinazioni":[{"table_name":"SLU1(CB)","famiglia":"SLU_STR"}]}'
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/reactions -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d $body
```
(Replace node ids and `table_name` with values from step 3's `combinations.json`.)

For every row, compare against MIDAS's own reaction table, row by row:
- **Values**: `fx_kN`/`fy_kN`/`fz_kN`/`mx_kNm`/`my_kNm`/`mz_kNm` match to 5 significant digits (we
  request `STYLES.PLACE=5`).
- **Signs** — check this explicitly, it is the easiest way an import silently corrupts a
  foundation check: pick a gravity-only combination and confirm `fz_kN`'s sign matches MIDAS's
  convention for a downward load reacted upward (MIDAS's global-axis sign convention; some
  installs flip it per project template).
- **Units**: our values are always kN / kNm regardless of what MIDAS's UI currently displays — if
  you temporarily switch MIDAS's display to kgf or tonf, convert one row by hand and confirm it
  still matches.
- `combo` equals the load-combination name with the suffix stripped (`SLU1(CB)` -> `SLU1`).
- `famiglia` equals whatever you passed in `combinazioni`.

## 5. Non-SI model

Switch the model's unit system (**Tools > Unit System**) to something non-SI (e.g. kgf/cm or
tonf/m), repeat step 4, and confirm `fz_kN` etc. are still correct kN values. This exercises the
`/db/UNIT` fallback in `reactions.py` (rule 4 of `docs/integrations/MIDAS.md` §2): the request always
asks MIDAS for `KN`/`M`, but if a table response doesn't echo the units it actually used, we ask
`/db/UNIT` instead of assuming the request was honoured. If this step shows wrong values, capture
the raw `SS_Table` response (does it include `FORCE`/`DIST` keys or not?) — that is the fastest way
to diagnose it.

## 6. Model with construction stages

If the model has staged construction analysis, repeat step 4 against a staged load case / combination
and confirm the import doesn't crash. If MIDAS's `Load` column for a staged result uses a naming
scheme other than `NAME(SUFFIX)`, note the exact string here — `_strip_suffix` in `reactions.py` may
need a new pattern.

## 7. Large import

On a model with many nodes and combinations, request reactions for 100+ combinations across all
supports and time it:
```powershell
Measure-Command { curl.exe -s -X POST http://127.0.0.1:8000/api/midas/reactions -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d $bigBody }
```
Expect the request to be chunked at 50 combinations per call to MIDAS (`CHUNK_SIZE` in
`reactions.py`) — if MIDAS exposes a connection/request log, you should see several calls, not one.
If the total rows returned would exceed 20 000, `avvisi` must contain an explicit truncation message
and `n_righe` must be exactly 20 000.

## 8. Key refresh

In MIDAS, **Apps > API Settings**, regenerate the MAPI-Key. Then retry the OLD key:
```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/verify -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{}"
```
Expect HTTP 401 with `{"ok":false,"kind":"auth",...}`, and — check this by eye — the old key string
does **not** appear anywhere in the response body. Then set `$key` to the new value and confirm
step 2 succeeds again.

## What "wrong" looks like

| Symptom | Likely cause |
|---|---|
| `400 forbidden_url` | Base URL mistyped, or not the `moa-engineers...midasit.(com\|cn)` relay — copy it from Apps > API Settings, don't retype |
| `401 auth` | Key expired or rotated — regenerate (step 8) |
| `502 not_connected` | MIDAS isn't running, or **Apps > API Settings > Connect** is off |
| `504 timeout` | Slow network, or MIDAS busy recalculating — retry |
| `502 bad_response` | MIDAS returned a shape our parser doesn't recognise — this checklist exists to catch exactly this; report the raw JSON body (safe to share, never contains the key) |
