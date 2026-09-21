# Divergences — `strutture.foundations.pavimento_industriale` (tool `fond-pavimento-industriale`)

Source: `10x_Pavimento industriale CNR_DT211-2014.xlsx`, sheet `carichi_distribuiti_concentrati`
(cell addresses below are the sheet's real addresses, from `build/cellmaps/pavimento-industriale/
carichi-distribuiti-concentrati.txt` — a few differ by one row from the prose spec's approximate
numbering, e.g. `M_SLU` for concentrated loads is actually row 17, not row 6; the *formulas* match
the spec exactly and are all confirmed against the cached example).

## FIX — inconsistent strength basis for the ULS stress check, distributed load

- **Cells**: `G22 = G21/$C$12` (fcfk, characteristic) vs `H22 = H21/$C$13` (fcfd, design).
- **Sheet behaviour**: the same sup/inf check pair divides by two different concrete strengths —
  the top fibre (`G22`) is checked against `fcfk` while the bottom fibre (`H22`), and every other
  check on the sheet (crack, punching, rebar), is checked against the *design* value `fcfd`.
- **Fixed behaviour**: `distribuiti_verifiche.verifiche_distribuito(..., legacy_compat=False)` uses
  `fcfd` for both. `legacy_compat=True` reproduces `fcfk` for the sup check.
- **Clause**: CNR-DT211/2014 (no clause number stamped on the sheet).
- **Numeric impact on the golden case**: none — `σc,max,sup=1.1638 MPa` clears both `fcfk=2.18973`
  and `fcfd=1.45982`, so the check passes either way. The divergence is only visible when the ULS
  stress lands between `fcfd` and `fcfk` (see `tests/foundations/pavimento_industriale/
  test_distribuiti_verifiche.py::test_fixed_stress_check_fails_when_sheet_bug_would_pass`: at
  `σc,max,sup=1.629 MPa`, `legacy_compat=True` passes, `legacy_compat=False` fails).

## FIX — punching-shear control perimeter `u1` uses `h` instead of `d` at the slab edge/corner

- **Cells**: `M33 = 2*MIN(M10,M11)+MAX(M10,M11)+2*$C$27(h)*PI()` (bordo), `N33 = N10+N11+$C$27(h)*PI()`
  (spigolo); `L33 = 2*(L10+L11)+4*$C$29(d)*PI()` (centro) already uses `d`.
- **Sheet behaviour**: the interior (`centro`) 2d-offset control perimeter correctly uses the
  effective depth `d=170mm`, but the edge (`bordo`) and corner (`spigolo`) perimeters use the total
  thickness `h=200mm` instead. EC2 §6.4.2 always uses `d` for the 2d-offset perimeter.
- **Fixed behaviour**: `concentrati_punzonamento.punzonamento(..., legacy_compat=False)` uses `d`
  for every position. `legacy_compat=True` reproduces `h` for bordo/spigolo (centro is identical in
  both modes — the sheet doesn't have the bug there).
- **Clause**: EC2 §6.4.2 (2d-offset control perimeter).
- **Numeric impact on the golden case** (bordo, `bx=500mm`, `by=100mm`): `u1` shrinks from
  `1956.64mm` (sheet, `h`) to `1768.14mm` (fixed, `d`), so `vEd1` rises from `0.097857MPa` to
  `0.108238MPa` — both still well below `VRd,c=0.494975MPa`, so the check's pass/fail verdict is
  unchanged on this golden case (using `h` instead of `d` oversizes `u1` by ~11% here and
  understates `vEd1`; a heavier/thinner-slab combination could flip the verdict).

## FIX — punching `VRd,max` coefficient mislabelled as EC2, actually NTC2018

- **Cells**: `L30:N30 = 0.5*$C$35(v)*$C$8(fcd)` (and `R30:T30`, second block).
- **Sheet behaviour**: `VRd,max = 0.5*ν1*fcd`. The code previously kept this `0.5` unconditionally
  and stamped the check `"EC2 §6.4.5"`, but EN 1992-1-1's §6.4.5(3) coefficient is a nationally-
  determined parameter two engineering reviewers disagreed on (see "Da confermare dall'ingegnere"
  below and `docs/divergences/ec2-shared.md`) — `0.5` is (also) the NTC2018 §4.1.2.3.5.2 value, not
  necessarily "the" EC2 one.
- **Fixed behaviour**: `concentrati_punzonamento.punzonamento(..., legacy_compat=False)` now takes
  the coefficient from `PavimentoIndustrialeInput.coeff_vrd_max` (`Literal[0.4, 0.5]`, an explicit
  advanced input, default `0.4` = `V_RD_MAX_COEFF_A1_2014`) and stamps the check `"EC2 §6.4.5(3)"`,
  with the value used recorded in the check's `detail`. `legacy_compat=True` keeps the sheet's `0.5`
  (`VRD_MAX_COEFFICIENT_NTC`, unaffected by `coeff_vrd_max`) and stamps the check
  `"NTC2018 §4.1.2.3.5.2"` — numerically identical to the sheet in every case (golden case
  unchanged: `VRd,max=3.825 MPa`).
- **Clause**: EC2 §6.4.5(3) (code-standard) vs NTC2018 §4.1.2.3.5.2 (legacy sheet value).
- **Numeric impact on the golden case** (code-standard branch only, default `coeff_vrd_max=0.4`):
  `VRd,max` drops from `3.825 MPa` (legacy, `0.5`) to `3.060 MPa` (fixed, default `0.4`) — 20% lower
  (25% higher if the engineer instead picks `coeff_vrd_max=0.5`, back to the legacy value); both
  still clear the golden case's `vEd0` values (max `0.170956 MPa`), so the pass/fail verdict is
  unchanged here, but a heavier point load closer to the limit could flip depending on the choice.

## Da confermare dall'ingegnere

- **`coeff_vrd_max` (`PavimentoIndustrialeInput`, code-standard mode only)**: 0.4
  (`V_RD_MAX_COEFF_A1_2014`, EN 1992-1-1:2004/A1:2014 §6.4.5(3), current default) vs 0.5
  (`V_RD_MAX_COEFF_2004_NA_IT`, EN 1992-1-1:2004 §6.4.5(3) + Appendice Nazionale italiana 2013 —
  also this sheet's own `legacy_compat=True` NTC2018 value). See `docs/divergences/ec2-shared.md`
  "Da confermare dall'ingegnere": two reviewers disagreed, and the user's own workbooks disagree too
  (this punching workbook uses `0.4`, the pile-cap workbook uses `0.5` with `αcc=1.0`).

## Da verificare — joint-check label/threshold mismatch (not fixed)

- **Cell**: `F39` label text is "a/b<1.2" but `I39 = IF(G39<1.5,"OK","ATTENZIONE")` tests `1.5`,
  identical to row 47's own label ("a/b<1.5") and formula.
- Kept as `1.5` in **both** `legacy_compat` modes: the architecture review treats this as a stale
  label (the formula, matching row 47 exactly, is very likely the intended one), not a confirmed
  formula bug — no clause found to justify inventing a `1.2` threshold. See
  `docs/architecture-batch2.md` §7 `pavimento I39`.

## Fixed by construction (no legacy_compat branch possible) — `$L$6` absolute-reference bug

- **Cells**: `M8 = M5*$L$6` and `N8 = N5*$L$6` (should read `$M$6`/`$N$6`): the ULS-load formula for
  the `bordo`/`spigolo` position columns reads the **centro** column's `γ` cell via an absolute
  reference, not its own column's `γ`. Harmless in the cached example only because `γ` (and `ψ1`,
  which is *not* affected — `L9/M9/N9` correctly use their own row 7) are equal across all three
  position columns.
- **Fix**: the `carichi` table (architecture-batch2.md §2) gives every row its own `gamma`/`psi1`
  column (`carico_row.CaricoRow`); a `pav-carichi-concentrati` row can no longer read another row's
  coefficient — there is no cell reference left to get wrong. This applies in **both**
  `legacy_compat` modes (there is nothing to reproduce: the table input shape itself prevents the
  bug), so it is not gated by `legacy_compat`.

## Construction simplification (not a sheet bug) — one mesh definition instead of per-block/position inputs

The sheet repeats the welded-mesh diameter/spacing input (`ø`/`S`) three times: once for the
distributed-load check (`G31/H31`, `G32/H32`) and once per position column for **each** of the two
concentrated-load blocks (`L45:N45`/`L46:N46`, `R45:T45`/`R46:T46`) — up to 8 near-identical
scalar inputs in the cached example (all `ø=8mm`, `S=200mm`). `PavimentoIndustrialeInput` exposes a
single `phi_rete_mm`/`passo_rete_mm` pair (`armatura.py`), reused by the distributed check and every
`carichi` row, since it is physically the same slab mesh throughout in every cached example. This is
a UI/input-count simplification, not a fixed bug — flagged here per BUILD_CONTRACT "report needs in
notes" in case an engineer needs genuinely different mesh in different zones of the same slab (out
of scope for this tool; would need a per-row mesh column in `carichi` plus a second mesh scalar for
the distributed check).

## Not implemented — `pav-giunti`'s "GIUNTI DI CONSTRUZIONE" section has no formula

Rows 46 (`GIUNTI DI COSTRUZIONE`) carries only a label, no formula or cached output in the sheet —
nothing to port (`build/cellmaps/pavimento-industriale/carichi-distribuiti-concentrati.txt` row 46).

## Not registered as a separate tool — `pav-eisenman` lookup

Per this package's task (`docs/architecture-batch2.md` §1 lists a second tool
`pavimento-eisenmann-coefficiente`, "unwired table, useful alone"), the explicit instruction for
this unit was **one** composed tool. The Eisenmann table (dead data on the main sheet, spec
"pav-eisenman") is embedded as immutable data with its linear-interpolation rule in `eisenmann.py`
(`EISENMANN_TABLE`, `eisenmann_coefficiente`), fully unit-tested, but not wired into
`fond-pavimento-industriale` (nothing on `carichi_distribuiti_concentrati` references it) and not
exposed as its own registered `Tool`. Promote it to a second `Tool` later if an engineer needs the
lookup standalone — the function is already there.

## Reported need (not actioned — outside this package's directories)

`shared/units.py` has no `daN_to_kN`/similar helper for the distributed-load inputs (`G4`/`G6`,
daN/m²); `distribuiti_carico.py` uses a package-local constant (`tables.DAN_PER_KN_M2 = 100.0`)
instead. Promote to `shared/units.py` if a second consumer appears (BUILD_CONTRACT: "shared/units.py
is the ONLY place for conversion factors" — this package cannot edit `shared/**`).
