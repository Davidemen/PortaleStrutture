# Divergences — `strutture.loads.neve`

Source: `neve.xlsx`, sheets `Neve` (`neve-carico-falda`) and `Neve accumulo` (`neve-accumulo`).
`legacy_compat=True` reproduces the sheet exactly (bugs included); `legacy_compat=False` (default)
is the code-standard, fixed behaviour. All numeric impacts below are re-verified against
`tests/fixtures/neve_carico_falda_oracle.json` / `neve_accumulo_oracle.json` (LibreOffice
recalculation) and the spec §8 golden case.

| cell | sheet behaviour | fixed behaviour | clause | numeric impact |
|---|---|---|---|---|
| `Tabelle!C3:C6` (Bug 1) | All four qsk2 formulas hardcode `Neve!$H$9`, so `Neve accumulo`'s qsk2 branch silently uses the *other* tool's altitude, not its own | `qsk_accumulo` takes the caller's own altitude as a parameter (`neve_sheet_as_m` only feeds legacy mode, mirroring the cross-sheet read as an explicit input per architecture.md §6/C7) | NTC2018 §3.4.2 | Golden case doesn't exercise it (qsk1 branch selected). Oracle case 2 (`as=150`, `Neve!H9=900`): legacy `qsk=3.51440` (uses 900 m) vs fixed `qsk=1.47498` if computed on its own 150 m — see `qsk.qsk_accumulo`. |
| `Neve accumulo!H8` (Bug 2) | `VLOOKUP(H6, Comuni!D:J, 4, FALSE)` looks up the *Provincia* string inside the *Comune* column | Keyed on the comune directly, like `Neve!H8` | — | On the real merged `comuni.csv`, zona is provincia-uniform (7845/8101 rows' provincia name resolves to *some* comune, always with the same zona as the original comune — 0 numeric mismatches found), so the bug is usually invisible; it crashes instead (`#N/A`/`KeyNotFound`) for the ~256 rows whose provincia name isn't itself a comune name (e.g. "Bagno di Romagna" → provincia "Forlì-Cesena", not a comune name) — see `tests/loads/neve/test_tool.py::test_bug_2_provincia_keyed_lookup_raises_in_legacy_for_multi_word_provincia`. Golden case (Bergamo→Bergamo) is a coincidental success, not a counter-example. |
| `Neve accumulo!H10` (Bug 3) | `IF(as<200, qsk2(as), qsk1)` — branch inverted vs `Neve!H10` | Same branch order as `Neve!H10`: `as<200 → qsk1`, else `qsk2(as)` | NTC2018 §3.4.2 | Golden case: `as=249≥200` → both modes pick `qsk1=1.5` (branch inversion invisible here). Oracle case 2 (`as=150<200`): legacy picks `qsk2` (contaminated by Bug 1) = 3.51440; fixed picks `qsk1=1.5`. |
| `Tabelle!A3:A6` range-VLOOKUP + Bug 5 (new finding, not separately listed in spec §7) | `Neve!H10`/`Neve accumulo!H10` VLOOKUP `Tabelle!A3:C6` with the `TRUE` (approximate) match flag. Combined with `Tabelle!A4`'s stray-paren "I (mediterranea))" (Bug 5), a caller's normalized `"I (mediterranea)"` (one char shorter) sorts *before* that key, so the nearest-lower match returns the **previous** row, `"I (alpina)"` — silently swapping the mediterranea zone's qsk2 coefficients for the alpine ones | `exact_lookup` on the normalized zona string (`qsk._resolve_zona_row`); `legacy_compat=True` reproduces the exact range-match quirk | NTC2018 §3.4.2 | Discovered while generating `tests/fixtures/neve_carico_falda_oracle.json` case 2 (Milano, `as=400`, zona="I (mediterranea)"): oracle gives `qsk=1.80964` (= alpina's `1.39·(1+(400/728)²)`), not mediterranea's `1.35·(1+(400/602)²)=1.94602`. Fixed mode gives the correct `1.94602`. |
| `Neve!H10` / `Neve accumulo!H10` boundary at as=200 m (new finding, engineering review) | `IF(as<200, qsk1, qsk2)` is strict on the lower side, so as=200 m exactly takes the qsk2 altitude formula instead of the qsk1 constant | `as<=200 → qsk1`, `as>200 → qsk2(as)` (NTC2018 §3.4.2 reads "per as<=200 m" for the constant) | NTC2018 §3.4.2 | At as=200 m the sheet's `IF(as<200,...)` reading is non-conservative in every zone: zona I alpina `1.39·(1+(200/728)²)=1.4949` (sheet) vs `1.50` (fixed); zona II `0.9970` (sheet) vs `1.00` (fixed); zona III `0.5982` (sheet) vs `0.60` (fixed). `legacy_compat=True` reproduces the sheet's strict `<200` boundary byte-for-byte (oracle/golden fixtures unaffected — neither exercises as=200 exactly); `legacy_compat=False` uses the corrected `<=200`/`>200` split. See `tests/loads/neve/test_qsk.py::test_qsk_falda_boundary_at_200m_uses_constant_in_every_zone_ntc_3_4_2`. |
| `Neve!H32/H54/H58` (Bug 6) | `AND(a>30, a<60)` is strict on both bounds, so a=30° exactly falls to the `a<30` branch's else → μ=0 (discontinuity; a=29.99° still gives 0.8) | `30 ≤ a < 60` — continuous ramp starting at 30° | NTC2018 §3.4.5.2, Tab. 3.4.II | Golden case doesn't hit the boundary (a=0/35/50). Oracle cases 4/5 (a=30° and a=60°) confirm both give μ=0 in legacy mode; fixed mode gives μ=0.8 at a=30° (only 30° differs — 60° evaluates to 0 in both modes since the ramp formula itself is 0 there). |
| `Neve!G29` (Bug 4) | Roof-type selector only drives a text banner (`K30`); both the 1-pitch (`D34`) and 2-pitch (`D60`/`H61`) branches are always computed regardless of selection | `run_carico_falda` gates the *output*: legacy mode returns both branches (matches the sheet); fixed mode nulls out the fields for the branch the user didn't select via `tipo_copertura` | — | No numeric change to the branch that *is* shown; changes which fields are `None` in `CaricoFaldaOutput`. See `tests/loads/neve/test_tool.py::test_bug_4_roof_type_gates_output_only_in_fixed_mode`. |
| `Neve accumulo!M38` (Bug 7) | Linear interpolation of m1 (`accumulo_m1.m1_interpolato`) is unbounded; extrapolating past `ls` (b2 > ls) can go negative or arbitrarily large, though it's only *used* (`H43`) when b2 < ls | Clamp the interpolated value to `[0, 4]` — 0 is the physically-motivated floor, 4 is `mu_w`'s own ceiling (`accumulo_mw.MW_MAX`) per Circ. 2019 §C3.4.5.6 / EN1991-1-3 §6.2(3); there is no independent upper limit narrower than that | Circ. 2019 §C3.4.5.6 | Golden case: b2=36.2 > ls=15 (extrapolation branch, unused) → legacy `M38=-3.67673` reproduced exactly (`docs/specs/neve.md` §8); `m1_final` still uses `m1_input=0.8` directly since b2≥ls in both modes. `tests/loads/neve/test_accumulo_m1.py` exercises the b2<ls branch directly (not reachable via the golden/oracle cases) with a contrived case exceeding `[0, 4]` to show the clamp taking effect. |

## Confermato (non è una divergenza)

- `Neve accumulo!H36`'s bounds on μw, `0.8 <= mu_w <= 4` (`accumulo_mw.MW_MIN`/`MW_MAX`), are
  correct and confirmed against **Circ. 2019 §C3.4.5.6** (mirroring **EN1991-1-3 §6.2(3)**). Both
  bounds are part of the sheet's own `H36` formula (`docs/specs/neve.md` step 8: `K35<4 ?
  (K35>0.8 ? K35 : 0.8) : 4`), so they are applied identically in legacy and code-standard mode —
  not a `legacy_compat` divergence. Previously flagged "unverified" pending an authoritative
  source check; the clause is now cited directly in `accumulo_mw.py`. See
  `tests/loads/neve/test_accumulo_mw.py`, which adds direct unit coverage for both bounds
  (previously only exercised indirectly through `accumulo_m1` tests).

## Da verificare

- **Resolved** (reviewed finding, CRITICAL): the previous `[0, 2]` upper clamp bound for the
  fixed-mode m1 interpolation (Bug 7) has no basis in Circ. 2019 §C3.4.5.6 or EN1991-1-3
  §6.2(3)/Annex B.3 — the only documented limit on the drift shape coefficient is `0.8 <= mu_w <=
  4`. The cap has been raised to `4` (`accumulo_m1.M1_INTERP_MAX`, matching `accumulo_mw.MW_MAX`);
  the `2.0` figure was an unverified guess from architecture.md §6's parenthetical and is no longer
  used. See `tests/loads/neve/test_accumulo_m1.py::test_no_spurious_2_0_cap_legitimate_values_above_2_pass_through`.
