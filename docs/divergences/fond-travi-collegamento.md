# Divergences — `strutture.foundations.travi_collegamento` (tool `fond-trave-collegamento`)

## FIX — `check_t` compares Nt,Rd against the compression work ratio, not NEd

- **Cells**: `Travi collegamento NTC2018!C33 = IF(C32>C31,"OK","NO")` and
  `Travi colleg. EN 1998-1 e 5!C31 = IF(C30>C29,"OK","NO")`.
- **Sheet behaviour**: both sheets' tension check compares `Nt,Rd` against `T.L._c` (the
  *compression* work ratio, `C31`/`C29`, a dimensionless number typically 0-1), not against `NEd`
  (`C28`/`C26`) as the row label ("Nt,Rd > NEd") and every other check in the sheet imply — a
  copy-paste off-by-one-row error. Since a force in kN is essentially always greater than a
  dimensionless ratio near 0-1, this check is nearly always "OK" regardless of the real tension
  demand, i.e. it never actually fails in practice.
- **Fixed behaviour**: `trazione.trazione(..., legacy_compat=False)` compares `Nt,Rd` against
  `NEd`, matching the row label and the pattern of every other check on the sheet.
- **Clause**: NTC2018 §7.2.5 / EN1998-1 §5.8.2 (tension check intent).
- **Numeric impact on the golden case**: none — the golden case's `Nt,Rd=472.058 kN` (NTC) /
  `629.411 kN` (EN) exceeds both `NEd=122.31 kN` and `T.L._c≈0.05`, so both checks are "OK"
  either way. The divergence is only visible with a small reinforcement / high-demand
  combination (see `tests/foundations/travi_collegamento/test_trazione.py`,
  `test_trazione_fixed_catches_undersized_reinforcement` — `Nt,Rd=39.33 kN < NEd=339.75 kN`
  fails in fixed mode but stays "OK" under `legacy_compat=True`).

## FIX — EN sheet's spectrum-type *label* (`C7`) is inverted against EN1998-1 §3.2.2.2(2)P; its S-column selection (`C8`) is not

- **Cell**: `Travi colleg. EN 1998-1 e 5!C7 = IF(C6<=5.5,"TIPO1","TIPO2")`, one row above
  `C8 = VLOOKUP(C5,Tabelle!M131:O134,IF(C6<=5.5,3,2),FALSE)`.
- **Corrected analysis (previous version of this doc was wrong)**: an earlier pass of this
  divergence doc treated `C8`'s column selection as the bug and `C7`'s label as ground truth,
  and made `legacy_compat=False` align the S column with `C7`. That is backwards: EN1998-1
  §3.2.2.2(2)P states that when the governing earthquake has Ms **not greater than 5.5**, the
  **Type 2** spectrum (higher S) applies; Type 1 applies for Ms > 5.5. `C7`'s own label is
  exactly inverted relative to this rule (it says `"TIPO1"` when `Ms<=5.5`). `C8`'s column pick
  (column O/"S Tipo 2" when `Ms<=5.5`, column N/"S Tipo 1" when `Ms>5.5`) is **independently
  EN-correct** — it matches the norm's own threshold directly, regardless of what `C7` calls it.
  So the previous "fix" (aligning S with `C7`'s label) introduced a real EN1998-1 violation:
  verified with ground D, `Ms=5.0` — it gave `S=1.35` where the norm requires `S=1.8`, i.e. a
  ~25% understatement of `amax` and `NEd = amax·Nsd·α`.
- **Fixed behaviour**: `sismica_en.sismica_en(...)` computes the S value the same way in both
  modes (`s = S_Tipo2 if Ms<=5.5 else S_Tipo1`, matching `C8`/EN1998-1 §3.2.2.2(2)P exactly) —
  only the reported `tipo_spettro` label differs: `legacy_compat=True` reproduces the sheet's
  mislabeled `C7` (`"TIPO1"` when `Ms<=5.5`); `legacy_compat=False` reports the EN-correct label
  (`"TIPO2"` when `Ms<=5.5`).
- **Clause**: EN1998-1 §3.2.2.2(2)P (spectrum type selection by Ms).
- **Numeric impact on the golden case**: none — `S` and `amax_g` are identical under both flags
  (golden case: soil B, `Ms=5.6` → `S=1.2`, `amax_g=0.1812`, unchanged from before). Only the
  `tipo_spettro` label differs (`"TIPO2"` legacy vs `"TIPO1"` fixed for `Ms=5.6`); see
  `tests/foundations/travi_collegamento/test_sismica_en.py`,
  `test_sismica_en_legacy_and_fixed_give_same_s` and
  `test_sismica_en_ground_d_low_ms_uses_type2_spectrum` for the regression coverage.

## Da verificare — EN1998 stirrup minimum ratio uses fyk, not fyd

- **Cell**: `Travi colleg. EN 1998-1 e 5!C63 = 0.08*SQRT(VLOOKUP(class_c,...,3,FALSE)) /
  VLOOKUP(class_s,Tabelle!M45:P49,2,FALSE)`.
- The spec's own constants table names the divisor `fyd`, but column 2 of `Tabelle!M45:P49` is
  the raw characteristic yield `fyk` (column 3, `fyd = fyk/1.15`, is not used here) — this
  actually matches the real EC2 §9.2.2 eq. 9.5N formula `ρw,min = 0.08·sqrt(fck)/fyk` (fyk, not
  fyd), so the sheet is *not* wrong; the spec prose mislabelled the divisor. No divergence
  between `legacy_compat` modes: `staffe_minime_en.staffe_minime_en` always uses `fyk_MPa`
  (`MaterialiResult.fyk_MPa`, added for this reason). Kept here as a note in case the spec text
  is revised.

## Inherited — concrete `fck` fill-down (`shared.materials.concrete.fck`)

- `materiali()` forwards the tool's own `legacy_compat` to `shared.materials.concrete.fck`.
  `legacy_compat=True` reproduces the sheet's `fck=0.83*Rck` fill-down (24.9 MPa for C25/30, the
  golden case's cached value); `legacy_compat=False` uses the NTC2018 Tab. 4.1.I literal (25
  MPa). See `docs/divergences/materials.md` for the full analysis — not re-derived here since it
  is a `shared` module concern, not specific to this unit.

## Cosmetic (not a numeric divergence) — `check_λ` row label swapped

- Both sheets' slenderness row is labelled "λ > λlim" but the formula tests `λlim > λ`
  (`IF(λlim>λ,"OK","NO")`). The Python port matches the formula (`snellezza_ntc`/`snellezza_en`
  compare `lambda_lim > lambda_`), not the label text — values are unaffected, purely a label fix
  if the UI ever surfaces the row label literally.

## Da verificare — NTC vs EN α coefficient for soil category A

- NTC's `Tabelle!P118` gives `α_A=0.2` while EN's `Tabelle!P131` gives `α_A=0`. EN1998-5
  §5.4.1.2 point 5 states tie beams "are not necessary... for type A ground", consistent with
  `α=0` zeroing `NEd`; NTC's `α_A=0.2` does not zero it. This looks like an intentional
  difference between the two codes rather than a bug, so both values are kept as-is (see
  `test_sismica_ntc.py::test_sismica_ntc_soil_a_alpha_nonzero` and
  `test_sismica_en.py::test_sismica_en_soil_a_alpha_zero`) — flagged here per spec, not fixed.
