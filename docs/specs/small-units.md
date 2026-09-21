# Small Units — Implementation Spec

Three tiny workbooks, one calc each: (1) steel material properties at elevated temperature,
(2) shear check of an unreinforced-web RC section (per-metre strip), (3) section properties of a
plated H-profile.

---

## Tool 1: `fuoco-materiali` — steel reduction factors at temperature θ

### Purpose
EN 1993-1-2:2005 Table 3.1: reduce fyk, Ea by ky,θ/kp,θ/kE,θ at a given steel temperature θ (e.g.
critical temperature from fire resistance check). Workbook has one sheet per θ example
(550/600/700 °C found; 650 °C presumably exists too) — **all four are the same calc**; make θ an
input, don't hardcode per-temperature sheets.

**This entire tool is redundant with the existing shared module** `strutture.shared.fire_reduction`
(`reduction_factors(theta_C) -> ReductionFactors(ky_theta, kp_theta, kE_theta)`, backed by the
verbatim `TABLE_3_1` in `tables.py`, interpolated via `strutture.shared.tables.interp_lookup`).
Re-implement this tool as a thin wrapper: call `reduction_factors(theta_C)`, then
`fy_theta = fyk*ky_theta`, `fp_theta = fyk*kp_theta`, `Ea_theta = Ea*kE_theta`. Do not re-derive
Table 3.1 or re-implement interpolation.

### Inputs
| cell | symbol | meaning | unit | type/range | cached example (550°C sheet) |
|---|---|---|---|---|---|
| C20 | fyk | characteristic yield strength at 20°C | MPa | float >0 | 355 |
| C21 | Ea | elastic modulus at 20°C | MPa | float >0 | 210000 |
| C22 | θ (Tcritic) | steel temperature | °C | float, [20,1200] | 550 / 600 / 700 |

### Outputs
| cell | symbol | meaning | unit |
|---|---|---|---|
| C23 | fp,θ | reduced proportional-limit strength (class 3-4) | MPa |
| C24 | fy,θ | reduced effective yield strength (class 1-2) | MPa |
| C25 (=G25) | Ea,θ | reduced elastic modulus | MPa |

No pass/fail check in-sheet; θ vs a required Tcritic is decided upstream (fire-resistance tool).

### Calculation steps
1. `(ky_theta, kp_theta, kE_theta) = reduction_factors(θ)` — piecewise-linear interpolation of
   Table 3.1 between the two bracketing 100°C rows (or the 20↔100°C row, both ky=kp=kE=1).
2. `fy_theta = fyk * ky_theta` [C24]
3. `fp_theta = fyk * kp_theta` [C23]
4. `Ea_theta = Ea * kE_theta` [C25]

### Lookup tables
Table 3.1 (θ°C → ky,θ, kp,θ, kE,θ), ascending 20..1200 in 100°C steps, linear interpolation,
**no extrapolation outside [20,1200]** — identical to `strutture.shared.fire_reduction.tables.TABLE_3_1`.
Reuse verbatim; do not re-type.

### Constants
None beyond Table 3.1 (already a shared constant).

### Suspected bugs / fragile spots
- **Confirmed bug (workbook only, not the shared module):** the workbook's `FORECAST.LINEAR`
  formulas reference a *hardcoded* 2-row bracket (e.g. `D11:D12,B11:B12` for the 550°C sheet
  bracketing 500–600°C) that must be **manually re-pointed** for each θ — the cell literally says
  `"INTERPOLATION RANGE MUST BE EDITED"`. If θ moves outside the currently-selected bracket without
  updating the range, `FORECAST.LINEAR` silently extrapolates using the wrong segment's slope
  (Table 3.1 is not one straight line — e.g. ky,θ is flat at 1.0 up to 400°C then drops), giving a
  silently wrong (usually unconservative, since extrapolated ky/kp/kE can exceed the true
  monotonic-decreasing values) result with no error. Re-implementing via `interp_lookup` (generic,
  bracket picked automatically, raises `KeyNotFound` out of range) eliminates this class of bug
  entirely — this is the reason to reuse the shared module rather than port the formula.
- 550c sheet: `G25={=+C25}` is a duplicate/display-only cell, not a distinct output.

### Golden test case
Input: `fyk=355, Ea=210000` for three θ:
```
θ=550: ky=0.625, kp=0.27,   kE=0.455  -> fy,θ=221.875 fp,θ=95.85  Ea,θ=95550
θ=600: ky=0.470, kp=0.18,   kE=0.310  -> fy,θ=166.85  fp,θ=63.9   Ea,θ=65100
θ=700: ky=0.230, kp=0.075,  kE=0.130  -> fy,θ=81.65   fp,θ=26.625 Ea,θ=27300
```
(600 and 700 land exactly on Table 3.1 nodes, no interpolation; 550 interpolates between the
500 and 600°C rows.)

---

## Tool 2: `ca-taglio-non-armato-v2` — shear capacity, RC section w/o shear reinforcement (per 1m strip)

### Purpose
NTC 2018 §4.1.2.3.5.1(?), shear capacity VRd of a section without transverse reinforcement
(≈ EC2 6.2.2). Sheet name `1m` and `bw=1000mm` confirm this is a **per-metre-width strip** check
(typical for slabs/footings), same convention as v1.

### Delta vs v1 (`ca-taglio-non-armato` v1, see diff)
1. **fck is now a direct input** (C3, e.g. 32 MPa), not derived. v1 computed
   `fck = Rck*0.83` via formula; v2 has fck as a free user cell — Rck (C2) becomes purely
   informational/unused downstream (still shown, not fed into fck anymore). Validate fck
   independently against Rck if both given (no in-sheet cross-check).
2. **New inputs replacing direct Asl entry**: v1 took `Asl` [mm²] directly as a scalar input; v2
   adds `N°` (bar count, B11) and `Ø` (bar diameter mm, B12) and computes
   `Asl = N° * π*Ø²/4` [B13]. This is a UX-only change (same downstream physics), but changes the
   input contract: the tool now needs bar count + diameter, not a pre-computed area.
3. All other formulas (d, scp, k, vmin, rl, VRd,1, VRd,2, VRd) are unchanged, only default example
   values differ (h 500→250mm, c 50→68mm, Rck 35→40).
4. No new pass/fail check added — v2 (like v1) only outputs the capacity VRd; there's no VEd/demand
   input or comparison in this sheet.

### Inputs
| cell | symbol | meaning | unit | type | cached example |
|---|---|---|---|---|---|
| B2 | Rck | characteristic cube strength | MPa | float >0 | 40 |
| B3 | fck | characteristic cylinder strength | MPa | float >0 (direct input, see delta #1) | 32 |
| B5 | γc | partial factor concrete | - | float, typ. 1.5 | 1.5 |
| B7 | h | section depth | mm | float >0 | 250 |
| B8 | c | cover to bar axis | mm | float >0, <h | 68 |
| B9 | bw | section width (per-metre strip) | mm | float >0 (typically 1000) | 1000 |
| B11 | N° | number of longitudinal bars | - | int >0 | 5 |
| B12 | Ø | bar diameter | mm | float >0, enum of commercial sizes | 12 |
| B14 | NEd | axial force on section | kN | float, can be 0 or compressive(+) | 0 |

### Outputs
| cell | symbol | meaning | unit |
|---|---|---|---|
| B4 | fcd | design compressive strength | MPa |
| B10 | d | effective depth | mm |
| B13 | Asl | tension steel area | mm² |
| B15 | σcp | mean compressive stress | MPa |
| B17 | k | size effect factor | - |
| B18 | vmin | minimum shear stress term | - |
| B19 | ρl | longitudinal reinforcement ratio | - |
| B21 | VRd,1 | capacity, EC2-style term | kN |
| B22 | VRd,2 | capacity, minimum-shear term | kN |
| B23 | VRd | governing capacity = max(VRd,1, VRd,2) | kN |

No pass/fail in-sheet (capacity-only tool; comparison to VEd happens elsewhere).

### Calculation steps
1. `fcd = fck * 0.85 / γc` [B4]
2. `d = h - c` [B10]
3. `Asl = N° * π*Ø²/4` [B13]
4. `σcp = min(NEd*1000/(bw*d), 0.2*fcd)` if NEd*1000/(bw*d) < 0.2*fcd else `0.2*fcd` [B15]
   (as written: `IF(NEd*1000/(bw*h?)... )` — verified: uses `B7*B9` = h*bw, **not** d*bw — see bug below)
5. `k = min(1 + sqrt(200/d), 2)` [B17]
6. `vmin = 0.035 * k^1.5 * sqrt(fck)` [B18]
7. `ρl = Asl / (bw*d)` [B19]
8. `VRd,1 = ( (0.18*k*(100*ρl*fck)^(1/3) / γc) + 0.15*σcp ) * bw*d / 1000` [B21]
9. `VRd,2 = (vmin + 0.15*σcp) * bw*d / 1000` [B22]
10. `VRd = max(VRd,1, VRd,2)` [B23]

### Lookup tables
None (no fill-down table in this sheet).

### Constants
`0.85` (fcd concrete long-term factor), `0.2` (σcp cap fraction of fcd), `0.18`, `0.15`, `0.035`
(EC2 6.2.2 empirical constants), `100`, `200` (unit-normalizing constants inside k/ρl terms),
`/1000` (N→kN).

### Suspected bugs / fragile spots (re-verified against formulas)
- **σcp formula uses `h` not `d`**: `B15 = IF(NEd*1000/(B7*B9) < 0.2*fcd, NEd*1000/(B7*B9), 0.2*fcd)`
  — `B7*B9 = h*bw`, the gross section area, whereas EC2 defines σcp = NEd/Ac using the gross
  concrete area too, so **this is actually correct per EC2** (σcp uses Ac = h·bw, not d·bw) — not a
  bug, flagged only because it's easy to mis-port as `d*bw` by analogy with the VRd terms.
- With `NEd=0` (both golden examples), σcp=0 regardless, so this branch is never exercised by the
  cached values — **verify the h-vs-d formula against a nonzero-NEd case before trusting the port**.
- v2's decoupling of fck from Rck (delta #1) means a user can enter an inconsistent pair
  (e.g. Rck=40 but fck=45) with no in-sheet warning — carry a validation warning in the port.

### Golden test case
Input: `Rck=40, fck=32, γc=1.5, h=250, c=68, bw=1000, N°=5, Ø=12, NEd=0`
Output: `fcd=18.1333, d=182, Asl=565.487, σcp=0, k=2, vmin=0.56, ρl=0.00310707,
VRd,1=93.9254, VRd,2=101.92, VRd=101.92` (all kN as stated).

---

## Tool 3: `acciaio-sezione-h-rimpiattata` (Rev01) — plated/built-up H-section properties

### Purpose
Section properties (A, centroid, Iy, Wpl,x, Wpl,y) of an H-profile reinforced with welded flange
plates, per EC3 §6.1/6.2.5(?) for the plastic-modulus/utilization checks that follow in the same
sheet (utilization checks are informational text, not re-derivable formulas — see below).
**Rev01 supersedes Rev00**: Rev01 adds an **Iy/Iz (second moment of area) column** (O, P) per
sub-element, entirely missing in Rev00 — Rev00 only computed A, static moments and Wpl terms, not
bending stiffness. Also Rev01 adds header labels (`"[mm]"`, `"Baricentro"`, ref. profile names)
and a `Mz,Rd` label row absent in Rev00. Port Rev01 only.

### Inputs
| cell | symbol | meaning | unit | type | cached example |
|---|---|---|---|---|---|
| B1 | H | base H-profile height | mm | float >0 | 114 (≈HEA120) |
| B2 | B | base H-profile flange width | mm | float >0 | 120 |
| B6 | b1 | plate 1 width (bottom flange plate) | mm | float >0 | 120 |
| C6 | h1(=t1) | plate 1 thickness | mm | float >0 | 8 |
| C9 | t4 | web-adjacent plate thickness input | mm | float >0 | 8 |
| V7 | Fy | steel yield strength | MPa | float >0 | 355 |
| V8 | γM0 | partial factor | - | float, typ. 1.0–1.05 | 1.05 |
| T22,T38,T40,T48,T50 | M_Edz, N_Ed, N_Rd, M_Edy, Mc_Rdy | **hardcoded design-action strings**, parsed via `RIGHT(text,n)` | kN,kN·mm | text-embedded numbers (fragile, see bugs) | 20655.94 / 8.36 / 855.38 / 4668.33 / 40368.57 |

Table (5-row fixed BOM, not fill-down — A1..A5 are named sub-elements of the built-up section,
each row = one rectangular sub-area):
columns `b [mm], h [mm], A [mm²], xi, yi (centroid of sub-area), xN, yN (section centroid, same
formula repeated per row), |xi-xN|, |yi-yN|, A·Δx, A·Δy, Wpl,x,i, Wpl,y,i, Iy,i [cm⁴] (about own
axis + parallel axis, ×2 variant with/without reinforcement O vs P)`. User-editable columns: `b, h`
(geometry per plate/flange, some hardcoded like A5=0 meaning "no 5th plate" by default), everything
else is formula.

### Outputs
| cell | symbol | meaning | unit |
|---|---|---|---|
| G6/H6 | xN, yN | section centroid | mm |
| M13 | Wpl,x | plastic modulus, minor(?) axis, ÷1000 to cm³ | cm³ |
| N13 | Wpl,y | plastic modulus, major(?) axis, ÷1000 to cm³ | cm³ |
| O13 | Iy | 2nd moment, reinforced section | cm⁴ |
| P13 | Iy (base profile only) | 2nd moment, unreinforced reference | cm⁴ |
| V19/V45 | Mc,Rdz / Mc,Rdy | plastic moment resistance = Wpl*Fy/γM0 | kN·mm |
| V23/V49/Z34/V39 | utilization ratio checks | text w/ pass "O.K." | - |

Pass/fail checks (all text-concatenation "< 1.000 —> O.K." style, not boolean cells):
- M_Edz/Mc_Rdz < 1.0 [row23]
- M_Edy/Mc_Rdy < 1.0 [row49]
- N_Ed/Nc_Rd < 1.0 [row39]
- combined: N_Ed/N_Rd + M_Edy/My_Rd + M_Edz/Mz_Rd < 1.0 [row34, EC3 6.2.1 (6.2)]

### Calculation steps (per sub-element i=1..5, then aggregate)
1. `A_i = b_i * h_i` [D col]
2. `xN = Σ(A_i*x_i) / ΣA_i`, `yN = Σ(A_i*y_i) / ΣA_i` [G,H — **same formula copy-pasted into every
   row**, only computed once effectively]
3. `Δx_i = |x_i - xN|`, `Δy_i = |y_i - yN|` [I,J]
4. `Wpl,x,i = A_i*Δy_i`, `Wpl,y,i = A_i*Δx_i` [M,N] (plastic modulus contribution = area × distance
   to the *opposite* axis — Wpl,x uses Δy, Wpl,y uses Δx)
5. `Iy,i = (h_i*b_i³/12 + A_i*Δx_i²) / 10000` [O] (own-axis inertia about local y + parallel-axis
   term; `/10000` converts mm⁴→cm⁴); `P` column repeats without the `A_i*Δx_i²` term for
   reference/base-profile-only rows (A1–A3 only; A4/A5 marked "-", i.e. not applicable/blank)
6. `Wpl,x = ΣM_i / 1000` [M13], `Wpl,y = ΣN_i / 1000` [N13] (mm³→cm³)
7. `Iy = ΣO_i` [O13], `Iy,base = ΣP_i` [P13] (already in cm⁴)
8. Rows 16–50 (Mc,Rd, utilization ratios, combined check) are **not live formulas driven by steps
   1–7** — see bug note; do not port as calculation steps, port only Fy/γM0 as reusable constants.

### Lookup tables
None — fixed 5-row BOM, not a real fill-down table.

### Hardcoded constants
`10000` (mm⁴→cm⁴), `1000` (mm³→cm³, and N·mm→kN·mm framing), row A5 defaults to `b=0` (element
disabled by zeroing width, not by removing the row) — a "no-op" convention to watch for.

### Suspected bugs / fragile spots (re-verified)
- **H6 formula asymmetry**: `H6 = (D6*F6+D7*F7+D8*F8+D9*F9+D10*E10)/(SUM(D6:D10))` — the last term
  uses `D10*E10` (area×**x**-coordinate) instead of `D10*F10` (area×**y**-coordinate) like the
  other four terms. Confirmed by re-reading: row10 (A5) has `D10=0` (width forced to 0), so this
  term is currently inert (`0*E10=0`), masking the bug — **if A5 is ever given a nonzero width,
  yN will be silently wrong**. Must fix to `D10*F10` in the port.
- Rows 16–50 are a pasted external "midas Gen" report, not formulas driven by the geometry table:
  `Mc,Rdy` (row44/45, 40368.57 kN·mm) comes from a hardcoded `"119400.0000 mm³"` text literal, not
  from computed `M13` (Wpl,x=101.76 cm³ → 101760*355/1.05=34400 kN·mm ≠ 40368.57 printed).
  `T22,T38,T40,T48,T50` extract numbers via fragile `RIGHT(text,n)` string parsing off adjacent
  hardcoded strings. **Do not port rows 16–50 as calculations** — only port the geometry/property
  table (rows 1–13); treat Fy/γM0 (V7/V8) as the only reusable inputs from that block.

### Golden test case
Geometry: `H=114, B=120`; A1: b=120,h=8; A2: b=5,h=98; A3: b=120,h=8; A4: b=8,h=105; A5: b=0,h=105.
```
A1: A=960  x=0      y=110  Iy=141.468 cm4 (base 115.2)
A2: A=490  x=0      y=57   Iy=13.5096 cm4 (base 0.102083)
A3: A=960  x=0      y=57   Iy=141.468 cm4 (base 115.2)
A4: A=840  x=64     y=57   Iy=189.642 cm4 (base n/a)
A5: A=0    x=-64    y=57   Iy=0
xN=16.5415mm  yN=57mm
Wpl,x=101.76 cm3   Wpl,y=79.7302 cm3
Iy(total)=486.087 cm4   Iy,base=230.502 cm4
Fy=355 MPa  γM0=1.05
```
(Rows 16–50 "checks" reproduce a pasted external report and are not reliable golden values for the
geometry calc — see bug note above.)
