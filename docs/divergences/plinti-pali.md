# Divergences — `strutture.foundations.plinti_pali`

Source: `2xxxx_Plinti su pali_PL-FX_S&T Eurocode 2.xlsx`, sheet `Footing check` (`build/cellmaps/fond-plinti-pali/`).
EN 1992-1-1 (EC2) §6.5 (struts/ties/nodes), §9.8.1 (pile cap detailing), §6.4 (punching), §6.2.2 (shear).

All fixes are controlled by `legacy_compat` on `PlintoSuPaliInput` (`True` reproduces the sheet
exactly, `False` applies the fix); numeric impact is quoted on the golden case (Case 1, 4 piles 2x2,
`docs/specs/fond-plinti-pali.md` "Golden test case") unless noted.

| cell | sheet behaviour | fixed behaviour | clause | numeric impact on golden case |
|---|---|---|---|---|
| `Footing check!AF12` | Nmin,env self-weight divided by a hardcoded `1.4` (`AR24/$AR$18/1.4*0.9`), mismatched against the actual γG1 (`AR25`=1.3) the weight was built with | divides by the real `gamma_g1` instead | EC0/NTC2018 Tab. 2.6.I — favourable permanent action | Nmin,env 244.236 -> 258.758 kN (+14.5 kN): peso/palo=293.68 kN, `/1.4*0.9`=188.79 kN (legacy) vs `/1.3*0.9`=203.31 kN (fixed) |
| `Footing check!AR99` (`k`) | `k = 1+SQRT(200/d)`, never clamped at EC2's required ceiling of 2.0 | `shared.ec2_shear.k_size` (clamped) | EC2 §6.2.2(1) | None on the golden case (`d`=1102mm gives k=1.426 < 2.0 either way); diverges once `d` < ~89mm (see `test_taglio_punzonamento.py::test_k_si_clamps_a_2_con_altezza_utile_molto_piccola`) |
| `Footing check!AR100` (`rho`) | `As_real/(AX*d)`: divides the bottom reinforcement's per-meter density (`mm2/m`) by the FULL plinth width `AX` in mm, a unit mismatch that understates `rho` by a factor `AX/1000` (4x here) | divides by the 1-meter design-strip width the reinforcement was actually computed for (`As_real/(1000*d)`) | EC2 §6.2.2(1) (rho = Asl/(bw*d), bw = the width the reinforcement covers) | rho 0.0010263 -> 0.0041052 (x4); through `v_rd_c`'s cube-root term this raises the golden case's concrete-term `vRd,c` above `vRd,c,min` (0.4038 > 0.3372 MPa, no longer the minimum-governed branch) so `VRd,c` rises 1486.18 -> 1779.81 kN and the utilisation drops 0.2206 -> 0.1842 |
| `Footing check!AR90` ("As,tot_bottom", described in the spec as feeding `rho`) | A separate lever-arm sub-calc (`AR89*2`, part of the excluded "simplified method" block) that traces to nothing downstream — `AR100`'s actual formula (`AV28/(AR60*AR86)`) reads `AV28` (`flessione.inf_x.as_prov_mm2`) directly, never `AR90` | `taglio_punzonamento.py` builds `rho` from `flessione`'s own `as_prov_mm2`, confirmed against the sheet's real formula (see `AR100` row above) | — (tooling/spec correction, not a numeric divergence) | None: this only corrects which upstream quantity feeds `rho`, not its value |
| `Footing check!BG13` (`Lb`) | Hardcoded literal (600mm) labelled "=pile ø, support width" but never linked to the pile-diameter input (`AR107`) — goes stale if the pile diameter changes without updating this cell too | `Lb = diametro_pila_mm`, unconditionally (no sheet behaviour worth reproducing: the literal is simply wrong whenever it disagrees with `AR107`) | — | None on the golden case (both equal 600mm); diverges whenever a user changes the pile diameter (`test_oracle.py` keeps `Lb`/pile-diameter equal for this reason) |
| `Footing check!BL13/BL14` (tie X/Y forces) | Both orthogonal ties use the SAME angle `cos(atan(Ly/Lx))`, correct only for a square grid (`Lx=Ly`, where `cos=sin`) | X tie keeps `cos(alpha)`, Y tie uses `sin(alpha)` (`alpha = atan(Ly/Lx)`) | EC2 §6.5.3 (tie force = strut's thrust component along the tie's own axis) | None on the golden case (`Lx=Ly=2m` -> `cos(45°)=sin(45°)`); diverges on a non-square grid (`test_puntoni_tiranti.py::test_fix_tiranti_ortogonali_usa_seno_per_y_su_griglia_non_quadrata`) |
| `Footing check!BP:BX` (tension-pile strut/tie block) | Computed unconditionally for every case, using `Nmin,env` (pile in tension), but never surfaced anywhere in `Per Relazione` | `capacita_pali.capacita_trazione` is only computed (and only required as an input) when `Nmin,env < 0`; always reported when present | — | None: the golden case's `Nmin,env` (244.236 kN) is compressive, so no tension check applies either way |
| `AV42`/`AV50` (top reinforcement "assumed" vs "final" bar diameter) | Two separate cells: `AV42` ("diam_assumed", 20mm) sizes the effective depth `d` for `As_req_flexural`; `AV50` ("ø", 24mm) is a differently-sourced final bar diameter used for `As_real` — the sheet never links the two | `flessione.py`'s top block ("sup") uses ONE user-chosen diameter for both `d` and `As_real` (this block is explicitly excluded from `Per Relazione`, see below) | — | `as_req_flexural_mm2` (top) 483.25 -> 485.85 (+0.5%, using 24mm for `d` instead of 20mm); `mu_kNm`/`as_min_mm2`/`as_prov_mm2` (which do not depend on this split) are unaffected — see `test_golden_case.py::test_flessione` |

## Da confermare dall'ingegnere

- **`coeff_vrd_max` (`PlintoSuPaliInput`, code-standard mode only, both `taglio`'s companion eq. 6.5
  check and `punzonamento_colonna`)**: 0.4 (`V_RD_MAX_COEFF_A1_2014`, EN 1992-1-1:2004/A1:2014
  §6.4.5(3), current default) vs 0.5 (`V_RD_MAX_COEFF_2004_NA_IT`, EN 1992-1-1:2004 §6.4.5(3) +
  Appendice Nazionale italiana 2013 — also this pile-cap workbook's own `legacy_compat=True` value,
  paired with `alpha_cc=1.0`). See `docs/divergences/ec2-shared.md` "Da confermare dall'ingegnere":
  two reviewers disagreed, and the user's own workbooks disagree too.

## Da verificare (kept in both modes, no fix applied)

- **Top ("sup") reinforcement is a simplified, best-effort port.** `Footing check!AV33:BA51` mixes
  the "assumed"/"final" diameter split above with a beam-span logic that otherwise matches the
  bottom block exactly (same `_mu_beam` helper, verified against `AV38/AZ38/AV43/AZ43` in
  `test_golden_case.py`). Per `docs/specs/fond-plinti-pali.md` §"Per Relazione" itself, this block
  is **not surfaced in the report** — kept here only because the task asked for "bending check as
  the sheet does" — so the single-diameter simplification was judged an acceptable trade-off rather
  than reverse-engineering an unreported, internally-inconsistent block further.
- **Non-`2x2` strut-and-tie geometry (`2x1`/`1x2`/`1x1`) is a generalisation, not a sheet
  reproduction.** The sheet's own "Case 2"/"Case 3"/"Case 4" branches were traced from their
  formulas (`Footing check!BF9`, `BL13/BL14`, `BG19`) and are believed correct, but the golden test
  case and all 3 oracle fixtures use the "2x2" schema exclusively (its own workbook has no populated
  2-pile/1-pile example): `puntoni_tiranti.py`'s `_fila_singola`/`_appoggio_diretto` branches carry
  unit tests (`test_puntoni_tiranti.py`) built from the traced formulas, but are "da verificare"
  against a real 2-pile/1-pile cached case.

## Not ported: excluded blocks

- **Top reinforcement** and the **"simplified method" tension-rod block** (`Footing check!BP:BX`
  minus the `capacita_pali` gate above, and rows 55-93's lever-arm sub-calc) are, per
  `docs/specs/fond-plinti-pali.md`, explicitly not surfaced in `Per Relazione`. Top reinforcement is
  still computed (`flessione.sup_x`/`sup_y`, "Da verificare" above); the lever-arm sub-calc
  (`AR90`/`AR91`/rows 66-93) is not ported at all — nothing downstream needs it once `AR100`'s real
  formula is traced (see the `AR90` row above).
- **Diagnostic out-of-plane ratio `Y`/`AA` column** (`Footing check!Y6:Y15000`, spec Tool-1 step 5):
  used only for a display ratio, never feeding any other cell — not ported.

## Addition beyond the sheet (per the task)

- **Punching of the corner (governing) pile** (`punzonamento_palo`, EC2 §6.4.2, control perimeter at
  `2d` from the pile face) — the sheet only gates on pile spacing
  (`interasse_x/y_sufficiente`, `Footing check!AQ108/109`) and never checks an individual pile's own
  punching cone. Uses the same `rho`/`k` as the beam shear check (§6.2.2), since the sheet defines no
  pile-local reinforcement ratio; flagged "Da verificare" as an engineering approximation, not a
  sheet cell.
- **Pile axial capacity check** (`capacita_compressione`/`capacita_trazione`) against a user-given
  admissible pile resistance — the sheet has no such input or check at all (its `BP:BX` block
  computes a *tie/strut* force under the tension-pile case, not a geotechnical/structural pile
  capacity comparison).

## Code-review engineering fixes (2026-09-21, gated on `legacy_compat=False`; legacy stays bit-identical)

These were not in the original architecture bug list; found during code review and fixed with the
sheet's own (buggy) behaviour kept exactly under `legacy_compat=True` (verified by the unchanged
golden/oracle tests).

| location | sheet/original behaviour | fixed behaviour | clause | numeric impact |
|---|---|---|---|---|
| `taglio_punzonamento.py` `taglio`/`flessione.py` `_progetta` | `d_mm <= 0` raised a bare `ValueError`, not caught by `shared.tool.execute`'s `except CalcError` — crashes the run instead of a graceful `Report` failure | raises `CalcError` | tool contract (`shared/tool.py`) | None on the golden case (`d>0`); a run with e.g. `h_plinto_m=0.1, copriferro_cm=30` now fails gracefully instead of crashing |
| `taglio_punzonamento.py` `taglio` (av reduction) | `beta = av/(2d)` with no floor: the tool's own default `av=120mm`, `d=1102mm` gives `beta=0.054` | `av` clamped to `[0.5d, 2d]` before forming `beta` (`beta` in `[0.25, 1.0]`) | EC2 §6.2.2(6) | with `av=120mm` on the golden case's loads/geometry (`d`=1102mm): `VEd,red` 83.7 kN -> 384.3 kN (+4.6x, no longer non-conservative); golden case itself uses `av=470mm` (already > 0.5d), so `ved_ridotto_kN` is unchanged there |
| `taglio_punzonamento.py` `taglio` (companion check) | EC2 eq. 6.5 (`VEd <= 0.5*b*d*ν*fcd`, unreduced) was never checked | computed as `ved_max_kN`, enters `verificato` | EC2 eq. 6.5 | golden case: `ved_max_kN` >> `ved_kN`, does not govern; new field, no change to previously-tested values |
| `taglio_punzonamento.py` `punzonamento_colonna` (`alpha_cc`) | hard-coded `alpha_cc=1.0` | `shared.materials.concrete.ALPHA_CC` (0.85) | NTC2018 §4.1.2.1.1.1 | golden case (with `coeff_vrd_max` also held at the sheet's own 0.5 to isolate this effect): `vRd,max` 17220.1 -> 14637.1 kN (-15%, no longer non-conservative). With the `coeff_vrd_max` default below (0.4) applied too: 17220.1 -> 11709.7 kN (-32%) |
| `taglio_punzonamento.py` `punzonamento_colonna`/`taglio` (`coeff_vrd_max`, both instances of `vRd,max = c*ν*fcd`) | sheet's own coefficient `c=0.5` used unconditionally (also in code-standard mode) | `c` is now `PlintoSuPaliInput.coeff_vrd_max` (`Literal[0.4, 0.5]`, default `0.4` = `V_RD_MAX_COEFF_A1_2014`), a user choice applied in `legacy_compat=False` mode only; `legacy_compat=True` keeps the sheet's own `c=0.5`/`alpha_cc=1.0` combination unconditionally | EC2 §6.4.5(3) — see `docs/divergences/ec2-shared.md` "Da confermare dall'ingegnere" | golden case, code-standard mode: `punzonamento_colonna.vrd_max_kN` 14637.1 (old silent 0.5 default) -> 11709.7 kN (new 0.4 default, -20%); `taglio.ved_max_kN` scales identically (same formula) |
| `taglio_punzonamento.py` `punzonamento_colonna` (`beta`) | `beta=1` assumed (no eccentricity effect) | `beta = 1 + 1.8*sqrt((ex/bx)^2+(ey/by)^2)` (EC2 eq. 6.39, simplified interior-column approximation; ex/ey from the governing combo's `Mx,final`/`My,final` over `NSd`) | EC2 §6.4.3(2)/(6)/eq. 6.39 | golden case (`Mx=241.6`, `My=741.5 kNm` on `NSd=3074.7 kN`, `bx=by=700mm`): `beta`≈1.65, `VEd`≈5080 kN vs `NSd`=3074.7 kN (utilisation was optimistic by ~65%) |
| `taglio_punzonamento.py` `punzonamento_palo` (control perimeter) | Full closed 2d circle regardless of pile spacing/cap edge, `u`≈16000mm on the golden 4x4m cap — the check is physically meaningless and always passes | perimeter capped to the non-overlapping distance `a = min(2d, spacing/2 - r_pile, cap-edge margin - r_pile)` (isotropic simplification: conservative, never overstates `u`); when `a < 2d`, `v_rd_c`'s `av_over_2d` enhancement (§6.4.4(2)) is used | EC2 §6.4.2(5)/§6.4.4(2) | golden case (`lx=ly=2m`, `ax=by=4m`, `Ø_palo=600mm`, `d=1102mm`): `a` 2204mm -> 700mm, `u` 15733mm -> 6283mm, `VRd,c` drops proportionally (utilisation rises from the previously meaningless ~0.11) |
| `puntoni_tiranti.py` node coefficients | sheet's own non-standard `K1_CCC=1.18/0.85`, `K2_CCT=1.0`/`0.88` applied unconditionally | `shared.ec2_strut_tie.sigma_rd_max` EN 1992-1-1 §6.5.4(4) defaults (k1=1.0 CCC, k2=0.85 CCT, k3=0.75 CTT); the 2x2 bottom node (two tie directions anchored) is classified CTT, the 2x1/1x2 node (one tie direction) CCT | EC2 §6.5.4(4) | golden case (2x2): `sigma_Rd,max` 13.915 -> 11.859 MPa (-14.8%, no longer non-conservative) |
| `puntoni_tiranti.py` strut angle floor | `theta = max(25°, atan(h_wt2/lxy))`, mis-attributed to EC2 §6.5.2(2) (which sets no angle floor); substitutes a flatter-than-real geometry, understating `Fus`/`Fut` | always uses the true `atan(h_wt2/lxy)`; raises `CalcError` outside a 20°-70° sanity band (**Da verificare**: this band is not itself an EC2 clause, see below) instead of silently clamping | — | example `lx=ly=4m`, `H=1.2m` (golden case's `Fus`/materials, wider spacing): real `theta`=21.43° vs the floor's 25°, `Fus` 2120.3 -> 2452.8 kN (+15.7%, no longer non-conservative); golden case itself (`lx=ly=2m`, `theta`=38.13°, above the floor) is unaffected either way |
| `puntoni_tiranti.py` `_schema_2x2` orthogonal ties | `fut_x`/`fut_y` used the strut's FULL inclined force, missing the `cos(theta)` projection onto the horizontal plane that only the diagonal tie XY had | `fut_x`/`fut_y` also carry `cos(theta)` | EC2 §6.5.3 (node equilibrium: tie forces must sum to the strut's horizontal thrust) | golden case: `fut_x`/`fut_y` 615.73 -> 484.36 kN (the legacy value was conservative here, `1/cos(38.13°)`≈1.27x too high) |

**Da verificare** (kept as an explicit guard, not tied to a specific EC2 clause): the 20°-70° strut-
angle sanity band above is an engineering safety net against a geometrically nonsensical mechanism
(near-horizontal or near-vertical strut), not itself an EC2 formula; it should be confirmed against a
strut-and-tie design reference before being treated as normative.

**Finding addressed at its "at minimum" level, `shared/pile_group/reactions.py` left unchanged**: the
code-review finding about `rigid_cap_axial` returning 0 for a moment about a zero-second-moment axis
is not itself a bug — it already matches the module's own documented physics (a rigid cap with every
pile on one line truly cannot resist a transverse moment by differential pile axial force). Editing
the shared function's signature/behaviour was judged unnecessary and out of proportion (it is only
ever consumed by `plinti_pali`, but changing a shared module's return contract for one caller's UX
need is not a "fix"). Implemented the finding's own documented fallback instead: `plinti_pali.tool.run`
now raises a warning (`_warnings` in `tool.py`) when a moment about such an axis is non-negligible on
a "2x1"/"1x2" schema, so the user is told the cap needs pile-head fixity or a second pile line —
`test_tool.py::test_avverte_quando_mx_non_e_resistibile_su_schema_2x1`/`..._my_..._1x2`.

## Cell-mapping note (tooling, not a spreadsheet divergence)

`Footing check!AR90` ("As,tot_bottom") is described in `docs/specs/fond-plinti-pali.md` as feeding
`rho` (`AR100`) via a "parallel lever-arm tension-tie sub-calc"; tracing the actual formula
(`AR100 = AV28/(AR60*AR86)`) shows it reads `AV28` (this port's `flessione.inf_x.as_prov_mm2`)
directly — `AR90` is unused downstream except by the equally-unused `AR92` "Section check" cell.
Reported for whoever next reads that spec section.
