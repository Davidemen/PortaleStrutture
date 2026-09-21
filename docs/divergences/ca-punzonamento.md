# Divergences — `strutture.members.ca_punzonamento`

Source: sheet `Shotblast_225N` (`build/cellmaps/ca-punzonamento/shotblast-225n.txt`), EN 1992-1-1
(EC2) §6.4 (punching shear) and §9.4.3 (minimum shear-reinforcement detailing). Golden case: spec §8
(Ved=225 kN, A=B=400 mm, H=500 mm, fck=35 MPa, β=1.15).

| cell(s) | sheet behaviour | fixed behaviour | clause | status | numeric impact on golden case |
|---|---|---|---|---|---|
| `D55` | dropdown list `"8,10,12,14,16,28,20,22"`, `28` a likely typo for `18` | `phi_staffa_mm` accepts `28` only under `legacy_compat=True`; rejects it (Italian message) otherwise, `18` is the valid commercial diameter | — | F | None — golden case uses φ=12 mm, unaffected either way |
| `H56` (fywd,ef) | `=250+0.25*d`, uncapped | `shared.ec2_shear.fywd_ef`: `min(250+0.25*d, fywd)` (EC2 eq. 6.52) | EC2 eq. 6.52 | F | None at d=430 mm (357.5 MPa < fyd=391.3 MPa for B450C, cap not active); becomes relevant for d≳560 mm |
| `D41:D62` (u0,out … VRrd block) | always computed, even when `uEd,i<uRd,i` (reinforcement not needed); several intermediate values then go negative and lose meaning (`k'd=-51.7`, `n(rows)=-1`, `n(f)=-12`) | `PunzonamentoOutput.armatura` is `None` when `legacy_compat=False` and the perimeter-critico check already passes | — | F | Golden case does not need reinforcement: `armatura` group present (with the sheet's own negative-valued fields) under `legacy_compat=True`, `None` under `legacy_compat=False` |
| `AS` column (`A_a` formula, steps 5/7) | `A*B + 4*MIN(A,B)*a + π*a²` unconditionally, even for a circular column (`A=lato_a_mm=0`): the `π*a²` term is kept but the `π*(D/2)*a` cross term and `π*(D/2)²` base are silently dropped | `shared.ec2_shear.control_perimeter` — shape-aware rounded-rectangle/circle area | EC2 §6.4.2 | F (circular case) / V (rectangular, `A≠B` case — see `docs/divergences/ec2-shared.md`, kept ambiguous since the sheet's `4*MIN(A,B)*a` only matches the standard `2*(A+B)*a` term when `A=B`) | None in the golden case (`A=B=400`, `pterreno=0`, so the diverging term is multiplied by zero anyway). Verified with an oracle case (circular column ⌀500 mm, `pterreno=0.02 MPa`): legacy `A_a`=1.506e6 mm² vs code-standard 2.235e6 mm² (+48%), propagating to `uEd,i` 0.0898 → 0.0939 MPa (+4.6%) |
| `D35`/`D37` (ρl cap) | ρl used in `uRd,i` is never capped at 2% (EC2§6.4.4(1)), only flagged by the informational `F35` message | `shared.ec2_shear.v_rd_c` always caps ρl at 2% before the cube-root term, in both `legacy_compat` modes — this tool routes every resistance formula through `shared.ec2_shear` per its task instructions, so it cannot literally reproduce an out-of-clause sheet input even under `legacy_compat=True` | EC2 §6.4.4(1) | F (norm-compliant, both modes) | None in the golden case (ρl=0.00365 ≪ 2%). Verified with an oracle case (ρl=0.0231, px=py=50 mm, φ=25 mm): concrete term 0.8728 MPa (uncapped) vs 0.8318 MPa (capped, both modes here), −4.9% |
| `uRd,max[D17]` | `0.2*0.85*fck/1.5`, an unrelated simplified coefficient | `shared.ec2_shear.v_rd_max`: `coeff_vrd_max*ν*fcd`, `ν=0.6*(1-fck/250)` — `coeff_vrd_max` is now `PunzonamentoInput`'s own explicit advanced input (`Literal[0.4, 0.5]`, default `0.4` = `V_RD_MAX_COEFF_A1_2014`), not a silent shared default | EC2 §6.4.5(3) | V — see `docs/divergences/ec2-shared.md` "Da confermare dall'ingegnere"; the correct EC2/NA coefficient in front of `ν*fcd` is a nationally-determined parameter two reviewers disagree on, so it is exposed as a user choice instead of guessed; `legacy_compat=True` keeps the sheet's `0.2*0.85/1.5` regardless of `coeff_vrd_max` | None on the golden case: `uEd,0=0.376 MPa` is far below `3.967 MPa` (sheet), `4.094 MPa` (coeff=0.4 default) and `5.117 MPa` (coeff=0.5) |

## Not ported (cosmetic / dead formulas, spec §7.2-3)

- `E14` (`=IF(D14="a=d",...)`) is dead/orphaned logic (`D14` is itself a numeric formula, never one of
  the compared text labels) — not reproduced, no output field corresponds to it.
- `E55` unit label `"mm2"` on the stirrup diameter cell is cosmetic (the area itself, `H55`, is computed
  correctly) — `phi_staffa_mm` carries `unit: "mm"` in this port.

## Da verificare

None beyond the `uRd,max` and `A_a` (rectangular, `A≠B`) rows above, both already tracked as
ambiguous in `docs/divergences/ec2-shared.md` (the shared module they come from has no sheet cell or
golden case of its own, so its divergence notes live there; this file only adds the numeric impact on
`ca-punzonamento`'s own golden case).

## Da confermare dall'ingegnere

- **`coeff_vrd_max` (`PunzonamentoInput`, code-standard mode only)**: 0.4 (`V_RD_MAX_COEFF_A1_2014`,
  EN 1992-1-1:2004/A1:2014 §6.4.5(3), current default) vs 0.5 (`V_RD_MAX_COEFF_2004_NA_IT`,
  EN 1992-1-1:2004 §6.4.5(3) + Appendice Nazionale italiana 2013). See
  `docs/divergences/ec2-shared.md` "Da confermare dall'ingegnere" for the full rationale (two
  reviewers disagreed, the user's own workbooks disagree too).

## Findings review (2026-09-21)

| finding | outcome |
|---|---|
| `effective_depth()`/`k_size()` can raise a bare `ValueError` (crashes the tool) when `H`, `copriferro` and the bar diameters combine into `d_mm<=0` | **Fixed** — `compose.run` now checks `d_mm<=0` right after `effective_depth()` and raises `CalcError("altezza utile d non positiva…")` in both `legacy_compat` modes, before it ever reaches `k_size`. No numeric impact on the golden/oracle cases (their `d_mm` is comfortably positive); new regression test `test_non_positive_effective_depth_raises_calc_error_instead_of_crashing`. |
| `asw_min_mm2` (eq. 9.11) computed but never compared against `area_staffa_mm2` in the `_armatura` checks tuple | **Fixed** — added `Check(name="asw_min", clause="EN 1992-1-1 §9.4.3(2) eq. (9.11)", value=area_staffa_mm2, limit=asw_min_mm2, unit="mm2")` to `_armatura`'s checks, in both `legacy_compat` modes (the sheet has no such check either, so there is nothing to preserve under `legacy_compat=True`; this is a pure addition, all existing checks/values unchanged). New tests confirm the check both passes (golden-style φ8 case) and fails (larger `st_mm` pushing `Asw,min` past the fixed stirrup area). No impact on golden/oracle numeric outputs — only a new `Check` entry. |
| `perimeter_length_mm`/`area_within_perimeter_mm2` always use the full closed perimeter, never truncated at a free edge for `posizione in {"bordo", "angolo"}` (EC2 Fig. 6.15) | **Rejected, no code change.** The sheet (and this port) implement EC2's *simplified β-factor* method for eccentric/edge/corner columns: EN 1992-1-1 §6.4.3(3)-(4) and Fig. 6.21N give recommended `β` values (1.15 interior / 1.4 edge / 1.5 corner — `tables.POSIZIONE_BETA`) applied to the **full, untruncated** control perimeter `u1`, as an explicit *alternative* to computing `β` "exactly" from a reduced/truncated perimeter (Fig. 6.15, `u1*`) when the eccentricity is known precisely. The two methods are mutually exclusive per the code — combining a truncated perimeter (as the finding requests) with the simplified `β` table would double-penalise edge/corner columns, which is not what EC2 intends and is not what the source sheet (`Shotblast_225N`, dropdown H13:K13, `docs/specs/ca-punzonamento.md` step 2) does either. Truncating the perimeter is only correct if paired with a computed (not tabulated) `β`, which is a materially different, out-of-scope method (would also need eccentricity `e` as a new input) — not something to silently graft onto the existing `posizione`+β model. Left as-is; flagged here for the engineer to confirm before ever adding an "exact eccentricity" mode. |
