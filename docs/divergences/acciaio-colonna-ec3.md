# Divergences — `strutture.members.acciaio_colonna_ec3` (acciaio-colonne-ec3!Column check)

Sheet: `Verifica instabilità e resistenza colonne ad H secondo EC3.xlsx`, sheet `Column check` (slug
`acciaio-colonne-ec3`). Golden case: spec §8 (`h=500, b=280, tw=8, tf=12, Q345, hot finished,
class 3, gammaM0=gammaM1=1`). Items 1-3 were pre-flagged (spec §7 / `docs/architecture.md` §6);
items 4-9 were found by direct cell-formula inspection (via `extract`/LibreOffice, not the spec)
while transcribing the sheet, and are new; items 10-17 were found in a later code review pass (not
by cell-formula inspection). All are **FIX** (code-standard `legacy_compat=False` implements the
corrected behaviour; `legacy_compat=True` reproduces the sheet exactly, verified against
`tests/fixtures/acciaio_colonna_ec3_oracle.json` where the fix is exercised by an oracle case, or
by hand-computed `@pytest.mark.unit` fixed-behaviour tests otherwise).

## 1. `H12`/`H13` — gammaM0/gammaM1 hardcoded to 1

Free user inputs, disconnected from `Materiali!E4:E5` (1.05/1.05). Non-conservative by ~5% on every
resistance/stability check if the user forgets to set them.

- **Fixed**: `materiale.risolvi_materiale` defaults to `structural_steel.partial_factors()`
  (gammaM0=1.05, gammaM1=1.05) when the input is left blank (`None`); still overridable, with a
  `Report.warnings` entry if the override differs from the standard value.
- **Clause**: EN1993-1-1 §6.1, Materiali!E4:E5.
- **Numeric impact on golden case**: none — the golden case's cached `gammaM0=gammaM1=1` is passed
  explicitly, so it is reproduced identically in both modes (the fix only changes the *default*
  used when the fields are left blank).

## 2. `H15` — fuk divided by gammaM0 instead of gammaM2

`fuk` is not read by any other formula in the sheet (a dead/cosmetic output), but its division is
wrong per EN1993-1-1 §6.2.3(1) (fracture resistance of tension sections uses gammaM2).

- **Fixed**: `Materiali.fud_MPa = fuk / gammaM2` (gammaM2=1.25 from `partial_factors()`).
- **Numeric impact**: none on any check (fuk is unused downstream); at gammaM0=1.05,
  fud=450/1.05=428.571 MPa (legacy) vs 450/1.25=360.0 MPa (fixed).

## 3. `Y25`/`Y26` — flexural-buckling alpha bypasses the buckling curve

alpha_yy/alpha_zz come from `IF(processing="hot finished", 0.34, 0.21)` / `IF(..., 0.49, 0.34)`,
duplicating (and able to diverge from) the curve-letter logic instead of being derived from it.

- **Fixed**: `buckling_curve.alpha_flessionali` derives a genuine Tab. 6.2 curve **per axis**
  (h/b and tf thresholds for rolled I/H sections: h/b>1.2 & tf<=40mm -> a/b; h/b>1.2 &
  40<tf<=100mm -> b/c; else b/c or d/d), then looks up alpha from the single shared
  `ALPHA_PER_CURVA` table — the same table already used (correctly) for the LTB curve `BC17`/`BC25`.
- **Clause**: EN1993-1-1 Tab. 6.1/6.2.
- **Numeric impact on golden case** (h/b=1.79>1.2, tf=12<=40mm -> curve a/b instead of the sheet's
  single "b" curve applied to both axes): chi_yy 0.588066 -> 0.655700, chi_zz 0.886636 -> 0.918017;
  utilizzo_yy (eq. 6.61) 0.230307 -> 0.222495.
- **Da verificare**: the sheet's "processing" dropdown (hot finished/cold formed) is Tab. 6.2's
  wording for *hollow* sections, but `BC17`'s h/b-threshold logic matches Tab. 6.3's *rolled vs
  welded I-section* LTB-curve rule instead. We keep `BC17` unchanged in both modes (not flagged as
  buggy) and only fixed the flexural-buckling alpha derivation; whether "cold formed" should map to
  Tab. 6.2's welded-I-section row for an open H/I section is not certain — not invented further.

## 4. `D33` — MRd,y divides by gammaM0 twice

`D33 = G31*W/1e6/H12`, where `G31` (`fy'`) is itself `fyk/gammaM0` (already embeds one division,
per item 1). `D43` (MRd,z) and `AD35`/`AD36` (used everywhere else, incl. the Annex A interaction
and the simplified checks) do **not** double-divide — `D33` alone is the outlier.

- **Fixed**: `flessione.mrd_y_kNm` drops the extra division (mirrors `mrd_z_kNm`/`AD35`).
- **Clause**: EN1993-1-1 §6.2.5.
- **Numeric impact**: none at gammaM0=1 (golden case); at gammaM0=1.05, MRd,y=590.881 kNm (legacy,
  wrongly reduced) vs 620.425 kNm (fixed).

## 5. `J26`/`J36` — shear checks compare the wrong axis's demand

`J26` ("web" check) tests `G26 > J23` (Vz,sd, the *wings'* shear) instead of `J22` (Vy,sd, the
web's own shear); `J36` ("wing" check) tests `G36 > J22` instead of `J23`. The adjacent ratio-text
cells `K26`/`K36` (same rows) use the *correct*, non-swapped reference, and the spec's own §3
output table documents the intended (non-swapped) pairing — both corroborate the boolean checks are
the outlier.

- **Fixed**: `taglio.costruisci_taglio` compares each capacity against its own axis's demand.
- **Clause**: EN1993-1-1 §6.2.6(2).
- **Numeric impact on golden case**: none (both shears are far below both capacities either way);
  the swap matters only when one axis's demand approaches its capacity while the other's doesn't.

## 6. `AN53` — Cmz's diagram-type-2 branch reuses Iyy instead of Izz

`AN53` (Cmz, transverse-load diagram) is `AI53` (Cmy) mirrored for the z-z axis, but the mirror
kept `P5` (Iyy) instead of switching to `P6` (Izz) — a copy-paste slip.

- **Fixed**: `annex_a_cm.cmz` uses Izz for the type-2 branch in fixed mode.
- **Clause**: EN1993-1-1 Annex A / Table B.3.
- **Numeric impact**: not exercised by the golden case (diagram type 1); for the oracle case with
  diagram type 2 (dmax_zz=30mm, Mz,sd=15kNm), Cmz = 4.6957 (legacy) vs 1.3363 (fixed) — large,
  because Iyy/Izz differ by more than 10x for this section.

## 7. `U37` — chi_LT omits phi_LT^2 from the sqrt radicand

`U37 = 1/(W36 + sqrt(S34^2 - AF44*S34^2))` — the radicand is `lambda_LT^2*(1-beta)`, not the
standard EN1993-1-1 §6.3.2.2 `phi_LT^2 - beta*lambda_LT^2` (the `phi_LT^2` term is missing).

- **Fixed**: `instabilita_flesso_torsionale.fattore_chi_lt` uses the standard formula.
- **Clause**: EN1993-1-1 §6.3.2.2.
- **Numeric impact on golden case**: none (chi_LT is capped at 1 either way, lambda_LT=0.226 is
  small). Impact appears once chi_LT is not capped — see `tests/fixtures/acciaio_colonna_ec3_oracle.json`
  case index 4 (lt=8000mm): chi_LT = 0.537235 (legacy) vs 0.527587 (fixed, more conservative).

## 8. `Y47` — eq. 6.61's third term has an extra /gammaM1

`Y47 = ... + X43*J21/Q40/H13` — missing the parentheses around `Q40/H13` that its own first two
terms use, and that `Y50`'s (eq. 6.62) third term `X45*J21/(Q40/H13)` **does** have. `Y47`'s term
therefore evaluates to `kyz*Mz,sd/(Mpl,z*gammaM1)` instead of `kyz*Mz,sd/(Mpl,z/gammaM1)`.

- **Fixed**: `interazione._utilizzo` mirrors `Y50`'s grouping for both equations.
- **Clause**: EN1993-1-1 §6.3.3 eq. 6.61.
- **Numeric impact**: none at gammaM1=1 (golden case, invisible like items 1/2/4). At gammaM1=1.05,
  see `acciaio_colonna_ec3_oracle.json` case index 1: utilizzo_yy = 1.33888 (legacy, verified
  against the real recalculated sheet) vs a materially smaller value once the extra gammaM1 is
  dropped (fixed mode also changes items 1 and 3 simultaneously for that same case, so the isolated
  effect of this item alone is covered by `tests/members/acciaio_colonna_ec3/test_interazione.py`).

## 9. `V54` — linear interaction's axial term is mis-scaled by ~1000x

`V54`'s axial term is `J19/(H10*H14)` — i.e. `Nsd/(A*fyd)` with `A*fyd` **in Newtons** (no `/1000`,
unlike `H46`/`Q41`, which correctly give `Npl` in kN) — making it ~1000x smaller than the intended
`n = Nsd/Npl,Rd`, effectively dropping the axial-load contribution from this one check.

- **Fixed**: `interazione_semplificata.v54_lineare` uses `H46`'s `n` (already computed correctly and
  used everywhere else, incl. `I56`).
- **Clause**: EN1993-1-1 §6.2.9.1.
- **Numeric impact on golden case**: V54 = 0.185370 (legacy) vs 0.232381 (fixed) — both still well
  under 1 (check unaffected), but a ~25% relative change in the reported utilisation.

## 10. `G31`/`G41` high-shear trigger reads the wrong axis's shear (upgraded from "Da verificare")

Re-reviewed and confirmed as a real bug, the same pattern already fixed for `J26`/`J36` (item 5):
`D33`'s (MRd,y) reduction trigger reads `Vz,sd` (wings) against the *web* capacity `Vpl,Rd,web`,
while the reduction factor itself uses `Vy,sd`/`Vpl,Rd,web` — mirrored for `D43`/MRd,z. EN1993-1-1
§6.2.8(2)-(3) requires the SAME VEd and Vpl,Rd in both the trigger and rho = (2VEd/Vpl,Rd-1)^2.

- **Fixed**: `flessione.costruisci_flessione` uses one shear per axis in fixed mode
  (`fy_ridotta_MPa(vy_sd_kN, vy_sd_kN, vpl_rd_anima_kN, ...)` / `(vz_sd_kN, vz_sd_kN, vpl_rd_ali_kN, ...)`);
  legacy reproduces the swap.
- **Clause**: EN1993-1-1 §6.2.8(3).
- **Numeric impact on golden case**: none (Vy,sd=29.2 kN and Vz,sd=0.002 kN are both far below
  0.5*Vpl,Rd on either axis in both modes — no reduction is triggered either way). The swap matters
  once one axis's demand exceeds 0.5*Vpl,Rd,web while the other axis's own shear does not (see
  `tests/members/acciaio_colonna_ec3/test_flessione.py`).

## 11. `W23`/`W24`/`S34`/`AI35` — non-dimensional slendernesses use fyd instead of fyk

`lambda_bar = sqrt(A*fyd/Ncr)` and `lambda_bar_LT = sqrt(Wy*fyd/Mcr)` use fyd = fyk/gammaM0.
EN1993-1-1 eq. (6.50) and eq. (6.56) are defined on the CHARACTERISTIC fy (NRk=A*fy); gammaM0 must
not appear. Invisible while gammaM0=1 (item 1's own bugged default); at gammaM0=1.05 lambda_bar and
lambda_bar_LT come out sqrt(1/1.05)=2.4% too small, so chi/chi_LT are overstated — non-conservative.

- **Fixed**: `instabilita_flessionale.costruisci_instabilita_flessionale` and
  `instabilita_flesso_torsionale.costruisci_ltb` use `materiali.fyk_MPa` for the lambda_bar/lambda_LT
  calculation in fixed mode; legacy reproduces fyd.
- **Clause**: EN1993-1-1 §6.3.1.2 eq. (6.50), §6.3.2.2 eq. (6.56).
- **Numeric impact on golden case**: none (gammaM0=1 explicit override). At gammaM0=1.05, lambda_yy
  increases by a factor sqrt(1.05)=1.0247, reducing chi_yy accordingly (more conservative fix).

## 12. `Y47`/`Y50` — eq. 6.61/6.62 apply gammaM0 and gammaM1 in series

`npl_kN`/`mpl_y_kNm`/`mpl_z_kNm` (§6.3.3 denominators) are built from fyd=fyk/gammaM0, and
`Y47`/`Y50` then divide by gammaM1 again — every term of both interaction equations ends up
divided by gammaM0*gammaM1 instead of gammaM1 alone. EN1993-1-1 §6.3.3 eq. (6.61)/(6.62) require
NRk=A*fyk and Mi,Rk=Wi*fyk divided by gammaM1 ONLY.

- **Fixed**: `sezione.costruisci_sezione` now also computes `npl_rk_kN`/`mpl_y_rk_kNm`/`mpl_z_rk_kNm`
  (same section-modulus selection, fyk instead of fyd); `interazione.costruisci_interazione` feeds
  these into `_utilizzo` in fixed mode instead of the fyd-based `npl_kN`/`mpl_y_kNm`/`mpl_z_kNm`;
  legacy is unchanged.
- **Clause**: EN1993-1-1 §6.3.3 eq. (6.61)/(6.62).
- **Numeric impact**: none at gammaM0=gammaM1=1 (golden case). At gammaM0=gammaM1=1.05 the fixed
  denominators are 1.05x larger (characteristic vs. design-strength-halved), reducing the reported
  utilisation relative to a hypothetical fix that only addressed item 8's grouping bug in isolation.

## 13. `AL72` (Czy) divides by `wz**5` instead of `wy**5`

EN1993-1-1 Annex A Table A.1 pairs Czy's `Cmy`/`lambda_max` term with `wy**5` (matching the
`(wy-1)` prefactor the code already uses); the sheet's `AL72` reuses `wz**5` from the analogous
`Cyz` term — a copy-paste slip when `Czy` was derived from `Cyz`. For a typical rolled I/H,
wy≈1.14 vs wz capped at 1.5 (wy^5≈1.9 vs wz^5≈7.6): the subtracted term is ~4x too small, so Czy
(and hence kzy, feeding My,Ed's term in eq. 6.62) is over-estimated.

- **Fixed**: `annex_a_kij.czy` uses `wy**5` in fixed mode; legacy reproduces `wz**5`.
- **Clause**: EN1993-1-1 Annex A, Table A.1 (Czy).
- **Numeric impact**: not exercised at gammaM0=gammaM1=1 with the golden case's near-zero Mz,sd
  (d_lt/e_lt terms vanish); see `tests/members/acciaio_colonna_ec3/test_annex_a_kij.py` for an
  isolated regression with nonzero moments.

## 14. `I56` divides by Mpl,Rd instead of the axial-reduced MN,Rd

`I56` (eq. 6.41) computes `(My,Ed/Mpl,y,Rd)^2 + (Mz,Ed/Mpl,z,Rd)^max(5n,1)` using the UNREDUCED
plastic moments, while the same function has already computed the axial-reduced `MN,y,Rd`/`MN,z,Rd`
(`J53`/`J54`) for the linear check (`V54`). EN1993-1-1 §6.2.9.1(6) eq. (6.41) requires MN,Rd in the
denominator; since MN,Rd <= Mpl,Rd, the sheet's `I56` under-reports utilisation without bound.

- **Fixed**: `interazione_semplificata.i56_potenza` is fed `mn_rd_y`/`mn_rd_z` in fixed mode instead
  of `mpl_y_kNm`/`mpl_z_kNm`; legacy reproduces the unreduced denominators.
- **Clause**: EN1993-1-1 §6.2.9.1(6) eq. (6.41).
- **Numeric impact on golden case**: small (n=0.047 is low, so MN,Rd is close to Mpl,Rd here); the
  effect grows with n — see `tests/members/acciaio_colonna_ec3/test_interazione_semplificata.py`
  for a case at n=0.8 where the gap is material.

## 15. `H50` (`a_zz`) uses a flange-area-style ratio and the y-y interpolation formula for z-z

`fattore_area_anima` computes `a_zz = MIN((A-2*h*tw)/A, 0.5)` — a web-area-derived fraction, not
EN1993-1-1 §6.2.9.1(5)'s single `a = MIN((A-2*b*tf)/A, 0.5)` used for BOTH axes — and `mn_rd_kNm`
then applies the y-y interpolation `Mpl,z*(1-n)/(1-0.5*a_zz)` to the z-z axis too, instead of the
clause's actual z-z expression (`Mpl,z,Rd` for `n<=a`, `Mpl,z,Rd*[1-((n-a)/(1-a))^2]` for `n>a`).
The sheet's substitute is conservative over the tested range, but not the clause's formula, and it
also feeds `V54`.

- **Fixed**: fixed mode uses the flange-based `a` (already computed as `a_yy`) for both axes and
  implements §6.2.9.1(5)'s literal z-z expression (`interazione_semplificata.mn_rd_z_kNm_fixed`);
  legacy reproduces `H50`'s web-area ratio and the y-y-style interpolation for both `J53`/`J54`.
- **Clause**: EN1993-1-1 §6.2.9.1(5).
- **Numeric impact**: not material on the golden case's low-utilisation load (n=0.047, well inside
  `n<=a` for both formulas); grows with `n` — see `test_interazione_semplificata.py` (n=0.5,
  a=0.35: legacy 0.67*Mpl,z vs fixed 0.95*Mpl,z).

## 16. `L30`/`L31` (epsilon/eta) and `AD27` (limite_hw_t)/`K32` use fyd, and the check direction is inverted

`epsilon = sqrt(235/fyd)` and `eta = IF(fyd>460,1,1.2)` are keyed on the design strength; EN1993-1-1
Tab. 5.2 and EN1993-1-5 §5.1 define both on the nominal/characteristic fy. Separately, `AD27`
(`limite_hw_t`) multiplies by eta where EN1993-1-5 §5.1(2) divides (`72*eps*eta` vs `72*eps/eta`),
and `K32`'s boolean tests `hw/t <= limite` where the clause requires the check ABOVE the threshold
(`hw/t > limite`) — both the scale and the direction of the flag are wrong. With gammaM0=1.05,
epsilon comes out 2.4% too large (non-conservative on Vbw,Rd via lambda_w); for an S460 member the
eta branch also flips the wrong way (fyd=438<460 -> eta=1.2 instead of 1.0, a 20% overestimate of
the Vb,Rd cap).

- **Fixed**: `taglio_instabilita.epsilon`/`eta` use `materiali.fyk_MPa` in fixed mode;
  `limite_hw_t` implements `72*eps/eta`; `richiede_verifica_taglio` implements `hw_t > limite`.
  Legacy reproduces all three (fyd-based eps/eta, `72*eps*eta`, `hw_t <= limite`).
- **Clause**: EN1993-1-1 Tab. 5.2, EN1993-1-5 §5.1(2).
- **Numeric impact on golden case**: `richiede_verifica` flips in fixed mode for this section's
  geometry (see `test_taglio_instabilita.py`); `Vb,Rd` itself is unaffected because `tool.py`
  always includes `tgl_instab.verifica` in the check list regardless of the flag.

## 17. `Y16` "class 4" is accepted but treated as class 3 (no effective-width calculation)

`ClasseSezione` accepts `"class 4"`, but `npl_kN`/`momento_plastico_resistente_kNm`/the
lambda_bar/lambda_LT calculations all use the gross section for class >= 3 — no EN1993-1-5 §4.4
effective-width/effective-modulus calculation exists anywhere in this module or the sheet.
Implementing §4.4 (plate slenderness, buckling factors per element) was not specified anywhere in
the spec and would mean inventing a clause; per BUILD_CONTRACT.md, we do not invent it.

- **Fixed**: `sezione.verifica_classe_supportata` raises `CalcError` for class 4 in fixed mode
  instead of silently checking against the (non-conservative, unbounded) gross section; legacy
  mode reproduces the sheet's implicit class-3 treatment.
- **Clause**: EN1993-1-5 §4.4 (not implemented — explicit refusal instead).
- **Numeric impact**: none on the golden case (class 3). Any fixed-mode run with `classe_sezione =
  "class 4"` now raises instead of silently under-reporting the reduction.

## Da verificare

- **Buckling-curve label for "cold formed" I/H sections** — see item 3 above.
- **Shear-buckling `cw` formula** (`C67 = 0.83/lambda_w`, `taglio_instabilita.py`): the sheet always
  uses the single "intermediate" row of EN1993-1-5 Table 5.1, regardless of whether `lambda_w` is
  below `0.83/eta` or at/above `1.08` (where different formulas apply). Reproduced identically in
  both modes (not flagged as a bug, and out of scope to invent the missing branches; the
  §5.1(2) applicability check itself — item 16 — is orthogonal and now fixed).
- **`AI30-AI83` Cij correction terms divide by `lambda_zz` (W24), not `chi_zz` (W32)**: reproduced
  identically in both modes per the module docstring in `annex_a_kij.py` — not confirmed as a bug
  distinct from item 13 (which only concerns the `wz**5`/`wy**5` swap), and out of scope to
  re-derive Annex A's Cij terms from first principles without a normative reference confirming the
  intended denominator.
- **No root-radius `r` input**: the task template mentioned "h, b, tw, tf, r" as typical section
  inputs, but neither the spec (`docs/specs/acciaio.md` §2) nor the cellmap
  (`build/cellmaps/acciaio-colonne-ec3/column-check.txt`) has an `r` cell — none was added.
