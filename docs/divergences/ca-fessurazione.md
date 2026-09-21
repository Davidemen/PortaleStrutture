# Divergences — `strutture.members.ca_fessurazione`

Source: `Verifica fessurazione - SLEF (X).xlsx`, sheets `Limitazione delle tensioni`,
`Apertura delle fessure`, `Apertura delle fessure SEMP` (`build/cellmaps/ca-fessurazione/`).
NTC2018 §4.1.2.2.4/§4.1.2.2.5, Circ. NTC2018 2019 §C4.1.2.2.4.5.

| cell | sheet behaviour | fixed behaviour | clause | numeric impact on golden case |
|---|---|---|---|---|
| `Apertura delle fessure!E18/E19` (Ecm, fctm) | `=VLOOKUP(E4,'[1]MATERIALE CLS'!A3:P14,...)` — points at an **external workbook link that is dead** (unavailable at parse time) | Both cells' source, the local `MATERIALE CLS` table, is replaced project-wide by `strutture.shared.materials.concrete.concrete_properties`; `AperturaFessureInput.classe_calcestruzzo` (already an input, `E4`) is passed straight through, so no new input is needed | NTC2018 §11.2.10.1 / Tab. 4.1.I | None: `concrete_properties("C28/35", legacy_compat=True)` reproduces the sheet's cached `Ecm=32588.1 MPa`, `fctm=2.83499 MPa` exactly — C28/35 is not one of the two rows (`C30/37`, `C35/45`) where the `MATERIALE CLS` sheet's own fck fill-down is broken (see `docs/divergences/materials.md`). |
| `Apertura delle fessure!E6` dropdown, `V7`/`W7` | Third dropdown option `"caso di trazione eccentrica (o per singole parti di sezione)"` drives `k2=W7=(W9+W10)/2/W9`, which divides by two empty cells → `#DIV/0!`; this row also sits outside the `V5:W6` range the working `VLOOKUP` in `E40` actually reads, so it is dead/unreachable even before the div-by-zero | Dropped from `TipoSollecitazione` entirely — only `"caso di flessione"` and `"caso di trazione semplice"` are valid `tipo_sollecitazione` values | Circ. 2019 §C4.1.9 | None: golden case uses `"caso di flessione"`. Per `docs/architecture.md` §6 ("Dead cells across units ... ca-fessurazione `W7` ... DROP — do not port"). |
| `Apertura delle fessure SEMP!D21/D43/D66` (σs,lim FRE), `D22/D44/D67` (σs,lim QPE) | Free-typed numbers (280/240 MPa, identical in all three sections) with **no backing formula**; spec speculates they come from "EC2 Table 7.2N ... at a given bar diameter" but that table is not present in this sheet | Replaced the raw limit inputs with a `diametro_mm_i` input per section and derive σs,lim via `strutture.shared.rebar_catalog.sigma_limit_by_diameter` (Tab. C4.1.II): FRE against the `w3` curve, QPE against the `w2` curve | NTC2018 §4.1.2.2.4 / Tab. C4.1.II | None: `diametro_mm=16` reproduces the sheet's cached 280/240 MPa exactly in both `legacy_compat` modes (16 mm is an exact row in both the w3 and w2 tables), for all three sections. |
| `Apertura delle fessure SEMP!B20/B65` | `=+'Limitazione delle tensioni'!B12` / `!B28` — both source cells are blank, so Excel coerces the link to the literal number `0` instead of an empty string (`B42`, sourced from the populated `B20`, correctly renders "Zona centrale") | `sezioni.SEZIONI` hardcodes `""` for the blank subtitles instead of `"0"` | — (cosmetic, no clause) | None: display-only, no numeric field is affected. |
| `Apertura delle fessure!E14` (Δsm, §C4.1.10 branch) | `=0.75*(E23-E25)` — `0.75` is `1.3/1.7` rounded down to 2 decimals | `spaziatura_fessure.delta_sm_c4_1_10_mm(..., legacy_compat=False)` uses `1.3/1.7` (`FATTORE_DELTA_SM_C4_1_10`), so `wk = 1.7*εsm*Δsm` reproduces `sr,max = 1.3*(h-x)` exactly | EN1992-1-1 eq. 7.14 / Circ. 2019 §C4.1.10 | ~2% larger `wk` on the golden case's `interferro_mm=300` variant (`Δsm`: 130.62 mm → 133.18 mm) — the sheet's `0.75` was non-conservative. Resolves the "Da verificare" item below. |
| `Apertura delle fessure SEMP!D21/22/43/44/66/67` (σs,lim FRE/QPE) | Hardcoded to the `w3`(FRE)/`w2`(QPE) curves of Tab. C4.1.II — only the NTC2018 Tab. 4.1.IV row for "condizioni ordinarie + armatura poco sensibile" | New `condizioni_ambientali`/`sensibilita_armatura` inputs (default `"ordinarie"`/`"poco sensibile"`, matching the sheet's implicit row) resolve the applicable class via `strutture.shared.durability_cover.crack_width_limit` (`classe_apertura_normativa.classe_normativa_fre/qpe`); the `None` (decompression-required) cells of Tab. 4.1.IV raise `CalcError` since this tool only checks crack width, not decompression | NTC2018 Tab. 4.1.IV | None on the default/golden inputs (same `w3`/`w2` classes). For other exposure/sensitivity combinations the limit can drop up to ~40% (e.g. Ø16mm: 280 MPa sheet value vs 200 MPa for `w1`, "molto aggressive"/"sensibile"). |

Both `legacy_compat`-gated divergences above (dead external link, dropped dead branch, table
vs. free input) collapse to the same numeric result as the sheet for the tools' own golden
cases; `tests/members/ca_fessurazione/test_fixed_behaviour.py` exercises the cases where
`legacy_compat=False` actually changes the result (off-`w3`/`w2`-table diameters, invalid
`tipo_sollecitazione` values).

## Da verificare

- **`Apertura delle fessure!E14` (Δsm, §C4.1.10 branch)** — RESOLVED (see table above):
  EN1992-1-1 eq. 7.14 / Circ. 2019 §C4.1.10 give `sr,max = 1.3*(h-x)` once bar spacing exceeds
  `5*(c+ø/2)`, which is exactly `1.3/1.7` once `wk = 1.7*εsm*Δsm,eff` is applied; the sheet's
  `0.75` is that same constant rounded down to 2 decimals, not a distinct formula. Kept under
  `legacy_compat=True`; `legacy_compat=False` now uses `1.3/1.7`.
- **`Apertura delle fessure!B39` label** (`=D7` "durata carico") is cosmetically wrong — the
  cell it labels (`E39`, k1) is actually driven by `E5` "tipo barre", not `E7`/`D7`. This is
  moot for the ported tool: our generic UI builds field labels from
  `AperturaFessureInput.tipo_barre`'s own `Field(description=...)`, which states its true
  dependency directly, so the sheet's mislabelling has no analogue to reproduce or fix.
