# MIDAS NX integration (Gen NX / Civil NX)

Goal: the engineer pulls **support reactions** (and the load-combination list) straight from the model
open in MIDAS Gen NX / Civil NX into our table inputs (`reazioni` of `fond-plinto-isolato`,
`fond-plinto-su-pali`), instead of exporting to Excel and pasting.

## 1. How the MIDAS API works (verified facts)
Source: MIDAS's official Python library `midas-gen` v1.6.6 (read from its code) + MIDAS API Online Manual.
NOT verified against a live MIDAS instance — none is available on the development machine; see §7.

- **Architecture.** REST over HTTPS to a MIDAS cloud relay, which forwards to the running desktop app over a
  WebSocket. The app must be open with a model and "Apps > API Settings > Connect" active. Our server can
  therefore run on any machine (Mac/Windows, same PC or not) — it only needs internet access and the key.
- **Base URL.** `https://moa-engineers.midasit.com:443/gen` (Gen NX) or `/civil` (Civil NX). Regional relays:
  `moa-engineers-gb` (Europe), `-in`, `-kr`, `-us` `.midasit.com`, and `moa-engineers.midasit.cn`. The exact URL is
  shown in the app under Apps > API Settings.
- **Auth.** Header `MAPI-Key: <personal key>` on every request. 401 = key invalid/expired (refresh in the app).
- **Probe.** `GET /config/ver` -> `{"VER": {"NAME": "…GEN…", …}}` (the library probes regional relays with it).
- **Units.** `GET /db/UNIT` -> `{"UNIT": {"1": {"FORCE": "KN", "DIST": "M", …}}}`. Forces: `N KN KGF TONF LBF KIPS`;
  lengths: `M CM MM FT IN`. The library CHANGES the model units with `PUT /db/UNIT` before reading tables — we never do.
- **Result tables.** `POST /post/table` with
  `{"Argument": {"TABLE_NAME": "SS_Table", "TABLE_TYPE": "REACTIONG", "STYLES": {"FORMAT": "Fixed", "PLACE": 5},
  "UNIT": {"FORCE": "KN", "DIST": "M"}, "NODE_ELEMS": {"KEYS": [1, 2]} | {"STRUCTURE_GROUP_NAME": "Plinti"},
  "LOAD_CASE_NAMES": ["G1(ST)", "SLU1(CB)"], "COMPONENTS": [...]}}`
  -> `{"SS_Table": {"HEAD": ["Index","Node","Load","FX","FY","FZ","MX","MY","MZ"], "DATA": [["1","12","SLU1","…"], …]}}`
  (all cells are strings; the response may echo `"FORCE"`/`"DIST"`). Errors come back as `{"message": "…"}`.
  `REACTIONG` = reactions in global axes (`REACTIONL` = local).
- **Load case names in tables** carry the analysis suffix: `NAME(ST)` static, `NAME(CB)` general combination,
  `NAME(CBC)` concrete-design, `NAME(CBS)` steel-design, `NAME(CBR)` SRC, `NAME(RS)` response spectrum, …
- **Load combinations.** `GET /db/LCOM-GEN` (general), `/db/LCOM-CONC`, `/db/LCOM-STEEL`, `/db/LCOM-SRC`,
  `/db/LCOM-STLCOMP`, `/db/LCOM-SEISMIC` -> `{"LCOM-GEN": {"1": {"NAME", "ACTIVE", "iTYPE", "DESC",
  "vCOMB": [{"ANAL": "ST", "LCNAME": "G1", "FACTOR": 1.3}]}}}`. `ACTIVE` is `ACTIVE|INACTIVE` for general/seismic and
  `STRENGTH|SERVICE|INACTIVE` for the design classes.
- **Supports.** `GET /db/cons` -> constrained nodes; `GET /db/node` -> coordinates; `GET /db/stld` -> static load cases.

## 2. Non-negotiable rules
1. **Read-only.** The client exposes only `GET` and `POST /post/table`. No `PUT`/`DELETE`/`/doc/*` — we never
   modify, save, analyse or re-unit the engineer's model. Enforced by an allow-list in the client + a test.
2. **The key is a secret.** Sources, in order: request header `X-Midas-Key` (per engineer, kept by the browser in
   `sessionStorage` only) > server environment `MIDAS_MAPI_KEY`. Never stored server-side, never logged, never
   echoed in any response or error, redacted in exception messages. `GET /api/midas/status` only says whether a
   server-side key exists.
3. **No SSRF.** A caller-supplied base URL must be `https`, port 443 (or none), host matching
   `^moa-engineers(-[a-z]{2})?\.midasit\.(com|cn)$`, path `/gen` or `/civil`. Anything else -> 400. The only escape
   hatch is the server env `MIDAS_ALLOWED_HOSTS` (comma-separated `host:port`, used by tests for a fake server).
4. **Units never guessed.** Ask for `KN`/`M` in the table request; if the response echoes other units, or echoes
   none and `/db/UNIT` says otherwise, convert with an explicit factor table. Unknown unit -> error, not a guess.
5. Timeouts (connect 5 s, read 60 s), one retry on transport errors only, Italian user-facing messages,
   everything portable to Windows + macOS.

## 3. Package `strutture.integrations.midas` (pure, no FastAPI imports)
| Module | Responsibility |
|---|---|
| `settings.py` | `MidasSettings` (frozen): base_url, product, allowed hosts; `from_env()`; `validate_base_url()` (rule 3) |
| `client.py` | `MidasClient(base_url, key, transport=None)` on `httpx`; `get(path)`, `post_table(argument)`; method/path allow-list; error mapping -> `MidasError(kind: auth\|not_connected\|timeout\|bad_response\|forbidden_url, message_it)`; key redaction |
| `units.py` | factor tables force->kN, length->m; `to_kn`, `to_m`, `moment_factor` |
| `version.py` | `probe(client) -> VersionInfo{product, name, version}`; `autodetect_base_url(key, product)` over the regional relays |
| `combinations.py` | read all six LCOM endpoints -> `tuple[Combination{name, table_name ("SLU1(CB)"), classification, active, description, n_terms}]` |
| `famiglia.py` | `suggest_famiglia(combination) -> Famiglia \| None` from name patterns (`SLU`, `STR`, `EQU`, `SLV`, `SISM`, `SLE`, `RARA`, `CAR`, `FREQ`, `QP`, `PERM`) then `ACTIVE` (`STRENGTH` -> SLU_STR, `SERVICE` -> SLE_RARA); pure, table-driven, user can override per combination in the UI |
| `supports.py` | `/db/cons` + `/db/node` -> `tuple[SupportNode{nodo, x_m, y_m, z_m, vincoli}]` |
| `reactions.py` | build the `REACTIONG` argument; parse `SS_Table` by HEADER NAME (never by position), strip the analysis suffix into `combo`, convert units, attach `famiglia`; returns `tuple[strutture.shared.load_table.ReactionRow, …]` + warnings; chunk requests over combinations (≤ 50 per call) to stay under the 20 000-row table limit and report truncation explicitly |

## 4. HTTP API (`src/strutture/web/routes/midas.py`), all under the existing rate limit and envelope
| Route | Body / params | Returns |
|---|---|---|
| `GET /api/midas/status` | — | `{server_key: bool, base_url: str\|null, product: "gen"\|"civil"\|null}` |
| `POST /api/midas/verify` | `{base_url?, product?}` (+ header key) | `{ok, product, name, version, base_url, units: {force, dist}}`; with no `base_url` -> autodetect |
| `POST /api/midas/combinations` | `{base_url?}` | `{combinations: [{name, table_name, classification, active, description, famiglia_suggerita}]}` |
| `POST /api/midas/supports` | `{base_url?}` | `{supports: [{nodo, x_m, y_m, z_m}]}` |
| `POST /api/midas/reactions` | `{base_url?, nodi?: [int], gruppo?: str, combinazioni: [{table_name, famiglia}]}` | `{righe: [ReactionRow…], n_righe, avvisi: [str]}` |
Errors: `{ok: false, errors: [str], kind}` with 400 (bad url/body), 401 (auth), 502 (MIDAS unreachable / not connected), 504 (timeout).

## 5. UI
`shared.load_table.reazioni_table_field` adds the hint `table.source = "midas-reactions"`. For such tables the
table widget shows **"Importa da MIDAS"** next to "Incolla da Excel": a dialog (native `<dialog>`, focus-trapped)
with (1) connection — product, base URL (prefilled from status / autodetect), key field (`type=password`,
`autocomplete=off`, sessionStorage only, hidden when the server has a key) and "Verifica connessione";
(2) combinations — searchable checkbox list grouped by classification, each with an editable `famiglia`
select prefilled with the suggestion, "solo attive" filter; (3) supports — all constrained nodes (default),
a structure group name, or explicit node ids; (4) "Importa" -> fills the table (sostituisci / aggiungi) and
reports `n_righe` + warnings. No per-tool code: everything is driven by the hint.

## 6. Tests
- Unit: URL validation (rule 3, incl. `http://`, IP literals, `moa-engineers.midasit.com.evil.org`, userinfo tricks),
  method allow-list (rule 1), key redaction in every error path and in logs (caplog), unit conversion, header-name
  parsing with shuffled/extra columns, suffix stripping, famiglia rules, chunking + truncation warning.
- Contract: `httpx.MockTransport` replaying the documented shapes of §1 (fixtures in `tests/fixtures/midas_*.json`).
- API: FastAPI `TestClient` with an injected fake client factory; status never leaks the key.
- E2E: a fake MIDAS relay (in-process ASGI app on a free port, allowed through `MIDAS_ALLOWED_HOSTS`) -> dialog ->
  table filled -> tool runs.

## 7. What the engineer must verify with a real MIDAS (docs/MIDAS_CHECK.md)
Connection + version, a reactions import on a small model compared with MIDAS's own Reaction table (values, signs,
units), a model set to non-SI units, a model with construction stages, large imports (rows/time), key refresh.
