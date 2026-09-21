# `strutture.shared.ec2_shear` / `strutture.shared.ec2_strut_tie` — notes for consumers

These are pure shared math modules, not sheet-bound tools, so they have no `legacy_compat` flag and no
golden/oracle fixtures of their own. This note records the divergences between the code-standard EC2
formulas implemented here and the sheet formulas mined from `docs/specs/ca-punzonamento.md` and
`docs/specs/fond-plinti-pali.md`, for the consuming tools (`members/ca_punzonamento`,
`foundations/plinti_pali`) to decide how to reproduce the sheet under `legacy_compat=True`.

| Function | Sheet behaviour (cell) | Code-standard (this module) | Clause | Status |
|---|---|---|---|---|
| `ec2_shear.fywd_ef` | `H56 = 250+0.25d`, no cap | `min(250+0.25d, fywd)` | EC2 eq. 6.52 | F (matches architecture-batch2.md §7 `punzonamento H56`) |
| `ec2_shear.control_perimeter` (`rett`) | `A_a = A*B + 4*MIN(A,B)*a + π*a²` (ca-punzonamento step 5/7) | `A*B + 2*(A+B)*a + π*a²` (standard rounded-rectangle area) | EC2 §6.4.2 | V — sheet formula only matches the standard one when `A == B`; not fixed here since the sheet cell belongs to `ca_punzonamento`, kept as its own copy under `legacy_compat=True` |
| `ec2_shear.v_rd_max` | `uRd,max[D17] = 0.2*0.85*fck/1.5` (simplified, unrelated coefficient) | `coefficient * nu * fcd`, `nu = 0.6*(1-fck/250)`, `coefficient` a keyword defaulting to **`V_RD_MAX_COEFF_A1_2014` (0.4)** — EN 1992-1-1:2004/A1:2014 §6.4.5(3), the amendment that lowered the original 2004 recommended value; the other named, equally valid constant is `V_RD_MAX_COEFF_2004_NA_IT` (0.5, EN 1992-1-1:2004 §6.4.5(3) Note + Appendice Nazionale italiana 2013). `alpha_cc` a keyword defaulting to `shared.materials.concrete.ALPHA_CC` (`0.85`, NTC2018 §4.1.2.1.1.1) | EC2 §6.4.5(3) | F — resolved 2026-09-21 (orchestrator decision, superseding the earlier 2026-09-21 note below that had wrongly defaulted `coefficient` to 0.5 and broken `pavimento_industriale`'s `test_vrd_max_fixed_uses_en_04_coefficient`): the coefficient is a nationally-determined parameter that two reviewers legitimately disagree on, so it is never silently defaulted by a consuming tool again — `ca_punzonamento`, `plinti_pali` and `pavimento_industriale` each expose it as their own explicit, named `coeff_vrd_max: Literal[0.4, 0.5] = 0.4` advanced input, threaded into `v_rd_max(..., coefficient=coeff_vrd_max)` in `legacy_compat=False` mode only; each sheet's own `legacy_compat=True` coefficient/`alpha_cc` combination (`ca_punzonamento`'s `0.2*0.85/1.5`; `plinti_pali`'s `0.5`/`alpha_cc=1.0`; `pavimento_industriale`'s NTC2018 `0.5`) is unaffected and stays bit-identical |
| `ec2_shear.v_rd_c` (punching, `av_over_2d` branch) | n/a — code-only bug, not a sheet divergence | Was `concrete_term * av_over_2d`, dropping the `vmin` floor and any `sigma_cp`; now `max(concrete_term, v_min_MPa) * av_over_2d + k1*sigma_cp` per eq. (6.50), with `v_min_MPa`/`k1_sigma_cp_MPa` populated in the result | EC2 §6.4.4(2) eq. 6.50 | F — resolved 2026-09-21 (code-review finding, `shared_ec2`). This branch is used unconditionally by `ca_punzonamento.perimeter_scan`/`governing_capacity` and `plinti_pali.taglio_punzonamento.punzonamento_palo` regardless of `legacy_compat` (there was no legacy/code-standard split at this call site — the old, floor-less formula was mistakenly believed to already match EC2 for every input); verified the fix keeps all existing golden/oracle fixtures green (concrete term already exceeds vmin in every current fixture case) |
| `ec2_strut_tie.sigma_rd_max` | `fond-plinti-pali.md` §…: CCC `1.18*(1-fck/250)/0.85*fcd`, CCT(1 dir) `(1-fck/250)*fcd`, CCT(2 dirs) `0.88*(1-fck/250)*fcd` | `k1=1.0` (CCC), `k2=0.85` (CCT), `k3=0.75` (CTT), all `* nu' * fcd` — the standard EC2 §6.5.4(4) coefficients | EC2 §6.5.4(4) | V — sheet uses non-standard, apparently confinement-enhanced coefficients; `plinti_pali` decides its own `legacy_compat=True` node formulas independently, this module only exposes the EN-standard ones with overridable `k1`/`k2`/`k3` |

No `docs/divergences/` row is claimed as "fixed" against a specific cached golden output here, because
these modules have no sheet cell of their own — the numeric impact of each row above should be assessed
by the tool that wires this module in (`ca_punzonamento`, `plinti_pali`) against its own golden case.

## Da confermare dall'ingegnere

- **`ec2_shear.v_rd_max`'s coefficient `c` in `vRd,max = c*ν*fcd` (EC2 §6.4.5(3)).** Two engineering
  reviewers disagreed, and the user's own spreadsheets disagree too (the punching workbook uses `0.4`,
  the pile-cap workbook uses `0.5` with `αcc=1.0`):
  - **Option A — `V_RD_MAX_COEFF_A1_2014 = 0.4`** (EN 1992-1-1:2004/A1:2014 §6.4.5(3)): the amendment
    lowered the originally recommended value; more conservative; matches the user's newer punching
    sheet. **Current shared default**, and the default of every `coeff_vrd_max` input.
  - **Option B — `V_RD_MAX_COEFF_2004_NA_IT = 0.5`** (EN 1992-1-1:2004 §6.4.5(3) Note): the original
    2004 recommended value, adopted by the Italian National Annex (2013); matches the user's pile-cap
    workbook (with `αcc=1.0` there, not `0.85`).
  - Resolved for now by making the choice explicit rather than silent: `ca_punzonamento`,
    `plinti_pali` and `pavimento_industriale` each expose `coeff_vrd_max: Literal[0.4, 0.5] = 0.4` as
    an advanced input, so the engineer picks per project instead of the tool guessing. Confirm which
    value should be the actual office standard (and whether it should vary by structure type, given
    the pile-cap workbook's own `0.5`/`αcc=1.0` combination looks like a deliberate, self-consistent
    choice rather than an oversight).
