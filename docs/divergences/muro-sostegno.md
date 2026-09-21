# Divergences — `strutture.members.muro` (tool `muro-sostegno`, Tools 1-3)

Source: `Muro di sostegno DM2018.xlsx`, sheet `Tratto A` (golden case), sheets `Tratto B`.."Tratto E"
(free extra golden cases). `legacy_compat=True` reproduces the sheet exactly (bugs included);
`legacy_compat=False` (default) is the code-standard, fixed behaviour.

## Fixed after code review (two modes; golden/oracle — always `legacy_compat=True` — unchanged)

| Where | Sheet behaviour | Fixed behaviour | Clause | Numeric impact on golden case |
|---|---|---|---|---|
| `angoli_progetto.phi_d_rad`/`delta_d_rad` | `φ'd = radians(φ'k)/γφ'` — divides the ANGLE by the M2 partial factor. | `φ'd = atan(tan(φ'k)/γφ')`, `δd = atan(tan(δ)/γφ')` (NTC2018 Tab. 6.2.II — γφ' is a factor on tan φ', not on the angle). | NTC2018 Tab. 6.2.II | None on Tratto A's own golden assertions (STR_1/SISMA_1 checked there use γφ,terr=1, where `atan(tan(x)/1) == x` makes the two modes identical). GEO_1/GEO_2/EQU_1/EQU_2/SISMA_1/SISMA_2 (γφ,terr=1.25) do diverge under `legacy_compat=False`: φ'd increases (24.00°→24.79° for φ'k=30°) and Ka decreases — the sheet's own formula happens to be the more conservative of the two here, not the norm text. |
| `tool.py` sliding/overturning `Check.passed` | `passed = OS ≥ 1` / `OR ≥ 1` — the Tab. 6.5.I resistance factors γR are never applied. | `passed = OS ≥ γR,scorr` / `OR ≥ γR,rib`, with γR,scorr from `shared.ntc_combos.fattori_resistenza("scorrimento").r3` (1.1) and γR,rib = `ribaltamento_scorrimento.GAMMA_R_RIBALTAMENTO_R3` (1.15, NTC2018 Tab. 6.5.I ribaltamento/R3 — see note below on why this constant lives in `members/muro` and not in `shared.ntc_combos`) for the static combinations (STR/GEO/EQU, Approccio 2 = A1+M1+R3, NTC2018 §6.5.3.1.1), and γR=1.0 for both checks on SISMA_1/SISMA_2 (NTC2018 §7.11.6.2.1). `legacy_compat=True` keeps the sheet's threshold of 1.0 for every combination (identical to before). | NTC2018 §6.5.3.1.1, §7.11.6.2.1, Tab. 6.5.I | None on the golden case's `legacy_compat=True` checks (all still pass at threshold 1.0). Under `legacy_compat=False` STR_1's OR/OS margin against the new 1.15/1.1 thresholds is narrower than against the old threshold of 1 (still passes on Tratto A), and a wall design close to the old threshold of 1 can now fail that was previously reported as passing. |
| `tool.py` seismic sliding/overturning demand | `Rtot`/`Mrib` only include the Mononobe-Okabe earth+surcharge thrust; the wall's and backfill's own inertia forces are never formed, and `Wmuro`/`Wterr` are not scaled by (1±kv). | `Wmuro,d`/`Wterr,d` are scaled by `kv_factor = 1+kv` in `pesi_combo` (same signed kv as the thrust); `Fh = kh·(Wmuro,d+Wterr,d)` is added to `Rtot`, and its moment `kh·(Wmuro,d·z̄muro+Wterr,d·z̄terr)` to `Mrib` (new `GeometriaResult.z_muro_m`/`z_terr_m` vertical centroids), for SISMA_1/SISMA_2 only, under `legacy_compat=False` (EN1998-5 §7.3.2.2(2)P / NTC2018 §7.11.6.2.1). `legacy_compat=True` is unchanged (`kv_factor=1`, `Fh=0`). | EN1998-5 §7.3.2.2(2)P, NTC2018 §7.11.6.2.1 | None on the golden case's `legacy_compat=True` values (SISMA_1's `m_rib_kNm`/`n_tot_kN`/`os_scorrimento` in `test_golden.py` are untouched). Under `legacy_compat=False`, SISMA_1/SISMA_2 gain extra demand (`fh_kN>0`, larger `r_tot_kN`/`m_rib_kNm`) on top of the γR>1 threshold above — both changes only make the seismic checks stricter. |
| `armatura_paramento` stem bending moment | `MEd = SH.q·(H/2−sfond) + SH.terr·(braccio−sfond)` — reuses Tool 2's FULL-HEIGHT (H = hmuro+sfond) thrust resultants with reduced lever arms, which is not the moment of the pressure diagram actually acting on the stem. | `MEd = γQ·q·Ka·hs²/2·cosδ + γG,terr·γterr·Ka·hs³/6·cosδ` with `hs = H − sfond` (stem height only) and the stem's own natural lever arms (`hs/2`, `hs/3`) — `armatura_paramento.spinte_stelo`/`leva_sovraccarico_stelo_m`/`leva_terreno_stelo_m`, used under `legacy_compat=False` only (NTC2018 §6.5.3.1.1/§4.1.2). `legacy_compat=True` keeps the sheet's full-height/shifted-arm formula unchanged. | NTC2018 §6.5.3.1.1 / §4.1.2 | None on the golden case's `legacy_compat=True` value (`test_golden_armatura_paramento_row151` untouched). The sheet under-estimates `MEd` (and thus `As.nec`) by `γterr·Ka·sfond²·(3H−sfond)/6 + γQ·q·Ka·sfond²/2` relative to the fixed formula — always positive, so `legacy_compat=False` always increases the governing `As.nec` relative to the sheet's own (unfixed) value for the same combination. |
| `tool.py` report | Every `Check` is ribaltamento/scorrimento only; nothing tells the user the NTC2018 §6.5.3.1.1 bearing-capacity (capacità portante) limit state is not verified here, so an all-green check list can be misread as a complete §6.5.3 verification. | `run_muro_sostegno` always adds a `Report.warnings` entry stating the bearing-capacity check (γR=1.4 static/1.2 seismic, Tab. 6.5.I) is out of this tool's scope and that the eccentricity guard only rejects `|e|>B/2`, not the §6.4.2.1 limits. | NTC2018 §6.5.3.1.1, §6.4.2.1 | None (adds a warning string; no numeric output changes in either mode). |

## Note on scope: `shared.ntc_combos.FATTORI_RESISTENZA` has no "ribaltamento" row

`shared/ntc_combos/tables.py` is outside this task's edit scope (`src/strutture/members/muro/**`
only). `GAMMA_R_RIBALTAMENTO_R3 = 1.15` is therefore a local named constant in
`ribaltamento_scorrimento.py` instead of a new row in `shared.ntc_combos.FATTORI_RESISTENZA`
(`VerificaOpereDiSostegno` would need a `"ribaltamento"` literal added there). A maintainer of
`shared/ntc_combos` should consider adding that row so every consumer shares one source of truth;
flagged here rather than duplicating the shared module's edit.

**For Tools 1-3 (spinta, ribaltamento/scorrimento, pressioni sul terreno) no numeric divergence
between the sheet and NTC2018 beyond the ones above was confirmed** — see below for why the two
suspected bugs from the spec/architecture.md did not reproduce, and what the actual (harmless)
findings were once checked directly against the workbook with `openpyxl`.

## Corrections to the spec's own transcription (not sheet bugs — the spec mistranscribed the sheet)

| Where | Spec/architecture.md claim | Actual workbook value (checked with `openpyxl`, `data_only=True`) | Impact |
|---|---|---|---|
| `Muro!N47`/`N48` (γG,terr, rows GEO_1/GEO_2) | docs/specs/muro-sostegno.md §"Tool 1" table and docs/architecture.md §6 both state the sheet hardcodes `γG,terr=1.1` for both rows and that this should be "fixed" to `1.0` | `N47 = N48 = 1.0` already (confirmed by direct cell read; `1.1` is instead the real value of `N49`/`N50`, i.e. EQU_1/EQU_2) | **None.** `1.0` for both GEO rows exactly matches NTC2018 Tab. 6.2.I Approccio 2 (γG1 favorevole = sfavorevole = 1.0), so there is nothing to fix; `fattori_combo("GEO_1"/"GEO_2")` returns `1.0` in both `legacy_compat` modes (`src/strutture/members/muro/combinazioni.py`). GEO_1 and GEO_2 *are* identical for γG,muro/γφ,terr/γG,terr (as the spec observed), which is expected under Approccio 2, not a copy-paste bug. |
| `Muro!C58`/`C60` (γQ, rows GEO_1/EQU_1) | The spec's Tool 1 input description says "γQ(C, input: 1.5 static A1 / 0 others / 0.6 seismic)", implying γQ=0 for every non-STR_1 static row | `C58 (GEO_1) = 1.3`, `C60 (EQU_1) = 1.5` (both match NTC Tab. 6.2.I γQ sfavorevole for A2/EQU respectively); `C57/C59/C61 (STR_2/GEO_2/EQU_2) = 0` as the spec says | **None on the golden case** (Tratto A's cached OR/OS for GEO_1/EQU_1 already reflect the correct 1.3/1.5, confirmed against `tests/fixtures/muro_sostegno_oracle.json`). Recorded here because a literal reading of the spec text would have produced a wrong `_DEFINIZIONI` table (understating GEO_1/EQU_1 thrust) that passes the golden case for STR_1/SISMA.1 only and silently under-designs GEO_1/EQU_1. `fattori_combo` derives γQ from `strutture.shared.ntc_combos` per-row favorevole/sfavorevole selection instead, verified against the oracle for GEO_1 (case 0-7) and against direct cell reads for EQU_1. |

## Fixed (methodology, not a numeric divergence on the golden case)

| Where | Sheet behaviour | Fixed behaviour | Clause | Numeric impact on golden case |
|---|---|---|---|---|
| `Muro!I18` (Ss) | Tratto A hardcodes `I18` as a frozen manual input (`I*=1.5`); Tratto B recomputes it live from `Classe` via an `IF` formula (NTC Tab. 3.2.V, category C). Tratto A also carries two dead "what-if" cells `F18`/`F19` (categories E/D) that are never wired into the calculation (`F19` is additionally mislabeled as "ST"). | `parametri_sismici()` (`src/strutture/members/muro/parametri_sismici.py`) always computes Ss live from `categoria_sottosuolo`/`ag_g`/`f0` via `strutture.shared.ntc_site_seismic.fattore_amplificazione_ss` (already oracle-tested there) — driven by the `Classe` dropdown in every case, never a frozen input. `F18`/`F19` are not ported (dead cells, per docs/architecture.md §6 "DROP"). | NTC2018 Tab. 3.2.V | None — Tratto A's own category is "C" with `ag=0.136, F0=2.419`, and `Ss(C, 0.136, 2.419) = 1.5026`, clamped to `1.5`, exactly matching the frozen `I18=1.5`. The divergence would only be visible if `Classe`/`ag`/`F0` changed without `I18` being updated by hand — impossible in the tool since there is no frozen `I18` input at all. |
| `Muro!I19` (ST) | Raw numeric input (`I*=1`), no dropdown/table on the sheet. | `categoria_topografica` (`T1`.."T4") is a proper enum input; `parametri_sismici()` derives ST via `strutture.shared.ntc_site_seismic.fattore_topografico_st` (NTC Tab. 3.2.V ST values), instead of taking a raw number. | NTC2018 Tab. 3.2.V | None — `T1 → ST=1.0` matches Tratto A's `I19=1` exactly. |

## Da verificare

- **`Muro!I22` ("γE", unit label `[kN/m3]`)** — the sheet's row-21 label reads "Fattore importanza
  del sisma" but the unit column shows `[kN/m3]`, which is dimensionally wrong for a dimensionless
  multiplier applied to the seismic thrust (`E87=...*$I$22`). docs/architecture.md §6 marks this
  **DECIDE (D3)**: "establish true meaning before reuse". `gamma_e` is kept as a plain dimensionless
  input (`json_schema_extra={"unit": "-"}`) with the ambiguity noted in its `Field(description=...)`;
  no numeric behaviour depends on resolving this, so it is not treated as a divergence with two modes.
- **Rows 47-49 fill-down bug narrative (spec §7 item 1, architecture.md §6 "muro rows 47/48")** — as
  shown above, this did not reproduce against the actual workbook. Left here for visibility in case
  a different copy of the workbook (or a different `Tratto`) does exhibit the claimed `1.1` value;
  `tests/members/muro/test_combinazioni.py::test_fattori_combo_matches_workbook_cells` pins the
  correct values against direct `openpyxl` reads so any future regression would be caught immediately.
- **`Muro!K169` (`MAX(K161:L168)` spanning the empty column `L`)** — belongs to Tool 5
  (`armatura-fondazione-valle`), out of scope for this half of the package; left for the
  reinforcement-design agent.

---
# Tools 4-6 (armatura-paramento, armatura-fondazione-valle, armatura-fondazione-monte)

All formulas below were read directly from `Muro di sostegno DM2018.xlsx`, sheet `Tratto A`,
rows 133-187 with `openpyxl` (`data_only=False`, to get the formula text, not just the cached
number), then cross-checked by regenerating `tests/fixtures/muro_sostegno_oracle.json` and
`tests/fixtures/muro_sostegno_tratti_oracle.json` with a LibreOffice recalculation — per the spec
author's own note, "cross-check directly against the xlsx with openpyxl before trusting spec text".

## Fixed (two modes)

| Where | Sheet behaviour | Fixed behaviour | Clause | Numeric impact on golden case |
|---|---|---|---|---|
| `Muro!I151`/`K169`/`M187` (bar diameter/callout) | `Ø = 10·CEILING(2·√(As.nec·passo/π), 0.2)` — a *continuous* diameter rounded to a 0.2 mm drafting step, not clamped to a commercially available bar. On Tool 5's golden case this yields `Ø=4 mm`, which is not on the standard EN10080 series (`shared.rebar_catalog.STANDARD_DIAMETERS_MM` starts at 6 mm) — no rebar supplier stocks 4 mm bars. | `legacy_compat=False` picks the smallest standard diameter (from `shared.rebar_catalog.STANDARD_DIAMETERS_MM`/`bar_area`) whose area covers As.nec over one bar spacing, and formats the callout via `shared.rebar_catalog.bar_callout` (`src/strutture/members/muro/rebar_selection.py`). | Commercial availability (EN10080 series); no NTC clause mandates a specific diameter | Tool 4 (`1φ8/20`) and Tool 6 (`1φ10/20`) are unaffected — their sheet diameters already sit on the standard series. Tool 5's golden case changes from `"1φ4/20"` (legacy) to `"1ø6/20"` (fixed): area increases from 12.57 mm²/bar to 28.27 mm²/bar (both ≥ As.nec=0.387 cm²/m over the 0.2 m spacing), a conservative change. |
| Governing `As.nec` (rows 151/169/187) | `As.nec = MAX(...)` over the 8 per-combination rows, with no floor: if every combination's row happens to be negative (self-weight/geometry more favourable than the thrust on every combination — an edge case, not exercised by any `Tratto` sheet), the sheet reports a negative "required" steel area. | `rebar_selection.governante_cm2_m` floors the *reported* governing value at 0 (both modes): a negative "requirement" is not meaningful to hand to a drafter, so it is reported as "no tension reinforcement required by this check" instead. The unclamped per-combination rows (`ArmaturaParamentoCombo.as_nec_cm2_m` etc.) are left exactly as the sheet computes them (oracle-tested), only the aggregated design value is floored. | — (design-value sanity floor, not a code clause) | None on any `Tratto` sheet's golden case — every governing combination (`SISMA_1` throughout) is comfortably positive. |

## Da verificare

- **`Muro!F179`/`F185` (`p**`, heel-root interpolated pressure) branch condition** — the sheet's
  formula is `IF(B*=0, ..., IF(B* > -(Bfond-Bmonte), (B*-(Bfond-Bmonte))·pvalle/B*, 0))`. Since
  `B* ≥ 0` and `Bmonte < Bfond` always (Bfond = Bvalle+smuro,base+Bmonte), the middle branch's
  condition is true for every physically possible geometry — the sheet's own inner `IF` is
  effectively unconditional, and can return a *negative* `p**` when `B* < Bfond-Bmonte` (confirmed
  against the LibreOffice oracle, case 1: `B*=0.0425 m`, `Bfond-Bmonte=0.75 m` → `p**=-71015 kPa`).
  This reads as an unintentional formula (a physically meaningless negative "pressure" propagates
  into `MEd.p`/`As.nec` for that combination's row), but no spec/architecture.md note flags it and
  it never governs on any `Tratto` sheet (only feeds a non-governing row in the extreme
  `phi_deg=25, beta_deg=22` synthetic oracle case). Reproduced identically in both `legacy_compat`
  modes (`armatura_fondazione_monte.pressione_interpolata_kPa`) pending confirmation from the
  original spreadsheet author on the intended geotechnical meaning — do not "fix" this without
  re-deriving the intended heel-pressure model from first principles.
- **`fyk`/`fyd` as a `RebarGrade` dropdown instead of a raw MPa input** — the sheet's `I136` (fyk)
  is a free-form numeric input (example value 450 MPa) rather than a grade dropdown; this tool
  instead exposes `grado_acciaio: RebarGrade` and derives `fyd` via
  `shared.materials.rebar.rebar_properties` (per docs/BUILD_CONTRACT.md's preference for `Literal`
  enums over free-form numeric inputs representing a finite catalog of choices). Not a numeric
  divergence: `rebar_properties("B450C").fyd_MPa = 391.304...`, identical to the sheet's own
  `I137=I136/1.15` for `I136=450` in every case. The sheet has no concrete-class field at all in
  this section (the simplified 0.9d flexure formula only needs `fyd`, never `fcd`), so no concrete
  class input was added either — flagged here rather than silently dropped, in case a future
  reviewer expects an `fcd`-based check (e.g. minimum reinforcement) that the sheet itself does not
  perform (Tool 4's own heading states "minimum steel not checked here"; Tools 5/6 have no such
  check either).
