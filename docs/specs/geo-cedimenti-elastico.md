# Cedimenti Elastici (Elastic Settlement) — Implementation Spec

Source sheets: `Elastico_centrale_Newmark`, `500`/`400`/`350` (identical formulas, only
inputs differ — see diff), `Elastico_Timoshenko_Goodier` (μ=0.2), `_2` (μ=0.25),
`_3` (μ=0.35, "semplificato"). No NTC/Circolare clause numbers appear anywhere in
any of the 5 sheets — governing basis is classical elasticity theory (Newmark 1942
corner-of-rectangle stress integration; Timoshenko & Goodier 1970 flexible-rectangle
displacement formulas), generically covered by NTC2018 §6.4.3? / Circolare 2019
C6.4.3? ("cedimenti" SLE checks). Mark all clause refs "?".

Shared physics: vertical stress increment Δσz beneath a corner of a loaded
rectangle at depth z is q·Iz(a,b) with a=side1/z, b=side2/z (Newmark closed form);
settlement = Σ Δz·Δσz(z)/E(z) over sublayers (numerical integration, not the
alternative closed-form Ic/Boussinesq route used only as a QA cross-check).

## Recommendation on tool boundaries
Two tools, not five:
1. **`cedimento-elastico-newmark`** — one Newmark corner-of-rectangle stress
   helper reused twice: `modalita=CENTRO` (`Elastico_centrale_Newmark`, point
   forced to geometric center, 4 equal quadrants) and `modalita=PUNTO`
   (`500`/`400`/`350`, arbitrary point via up to 4 unequal sub-rectangles + an
   independent single-rectangle corner check "O'"). Same formulas, `500`/`400`/`350`
   are golden cases (`350`,`400` not re-read per instructions).
2. **`cedimento-elastico-timoshenko-goodier`** — base on `_3` ("semplificato"),
   the *only* variant that actually finishes the calculation. `Elastico_Timoshenko_Goodier`
   (μ=0.2) and `_2` (μ=0.25) are earlier drafts left in a broken state (see bug
   list) — do not port their per-layer IF logic; μ is just a user input (0–0.5),
   not three separate tools.

---

## Tool 1: `cedimento-elastico-newmark` — Newmark corner-of-rectangle integration

### Purpose
Immediate (elastic) settlement of a rectangular flexible foundation via numerical
integration, layer by layer, of the Newmark corner-of-rectangle vertical-stress
influence factor. `CENTRO` mode: settlement under the geometric center (sum of 4
equal quadrants). `PUNTO` mode: settlement under an arbitrary point (sum of up to
4 unequal sub-rectangles sharing that point as common corner), plus an independent
single-rectangle "corner" settlement at a comparison point O'.

### Shared sub-routine `newmark_corner(side_a, side_b, q, z_grid, layers)`
For each z in the depth grid (fixed step, from foundation base downward):
`n1=side_a/z, n2=side_b/z, den=1+n1²+n2², num=(n1·n2)²`
`angle = 2·n1·n2·√den·(den+1)/((den+num)·den) + atan(2·n1·n2·√den/(den−num))`
`+ π if num>den` (keeps the arctan branch continuous when den−num flips sign).
`Iz·q = q/(4π)·angle`; `E(z)` = modulus of the stratigraphy layer containing z
(range lookup, "0 if no layer matches" — see bugs); `Δs = Δz·(Iz·q)/E(z)` (0 if
`E(z)=0`, mirroring `IFERROR(...,0)`); rectangle settlement = Σ Δs.

### Inputs — CENTRO (`Elastico_centrale_Newmark`)
| Cell | Symbol | Meaning | Unit | Type | Example |
|---|---|---|---|---|---|
| D1 | B | foundation width | cm | input | 350 |
| D2 | L | foundation length | cm | input | 500 |
| D3 | q | uniform contact pressure | kg/cm² | input | 0.5 |
| G1 | D | embedment depth | cm | input | 110 |
| D7:F11 (table) | strato i | up to 5 layers, one row = one layer; cols: B=depth-from-ground top [cm], C=depth-from-ground bottom (=next B, last row hardcoded 12000), F=E [kg/cm²] (often `=raw_kPa/(10·9.80665)`, see constants) | mixed | B,C,F user data | strato1 B=80,F=`5500/(10·9.80665)`→56.08 |
| K7:K97 (fill-down, step 10) | z | depth below foundation base | cm | derived grid, fixed 10 cm step, 91 rows (z=10..910) | K7=10 |

### Inputs — PUNTO (`500`; `400`,`350` golden, same formulas)
| Cell | Symbol | Meaning | Unit | Example (500) |
|---|---|---|---|---|
| C1 | q | contact pressure | kg/cm² | 0.8 |
| G1 | D | embedment depth | cm | 220 |
| F5,F6 | side_p, side_q | full sides of comparison rectangle for O' | cm | 4000, 4000 |
| F7,F8 | e1, e2 | distances from point O to two adjacent edges | cm | 2000, 2000 |
| F9={=F5-F7}, F10={=F6-F8} | e1', e2' | complementary distances (O to opposite edges) | cm | 2000, 2000 |
| D15:F19 (table) | strato i | up to 5 layers, same shape as CENTRO's D7:F11 but rows 15-19 | mixed | strato1 F=100 |
| K7:K87 (fill-down, step 10) | z | depth grid, 81 rows (z=10..810) | cm | — |

### Outputs
| Cell | Meaning | Unit | Check |
|---|---|---|---|
| U6 (CENTRO) | Cedimento (settlement) at center = `T6·4` | cm | golden compare |
| Z6 (CENTRO) | QA cross-check via direct closed-form Ic at center (NOT decomposed) | cm | should ≈ U6, see bug (inconsistent depth truncation) |
| C2 (PUNTO) `="Cedimento O"` = `T6+AB6+AJ6+AR6` | settlement at point O = sum of 4 sub-rectangle contributions | cm | primary output |
| C3 (PUNTO) `="Cedimento O'"` = `AZ6` | settlement at corner O' of the single comparison rectangle | cm | secondary/reference output |

### Calculation steps (dependency order)
CENTRO:
1. Layer table: `D_i={=IF(B_i-$G$1<0,0,B_i-$G$1)}`, `E_i` similarly — convert
   ground-surface depths to depth-below-foundation-base [D7,D8,...].
2. z-grid fill-down k=1..91: `K=10·k`.
3. Per z-row: `L=(B/2)/K, M=(L/2)/K` → `newmark_corner` angle `P`, `Q=q/(4π)·P`,
   `S`=layer-E lookup (nested `IF(AND(K>D_i,K<=E_i),F_i,...,0)`, i=7..11),
   `T=IFERROR(10·Q/S,0)`.
4. `T6=SUM(T7:T1063)` (range far exceeds the 91 filled rows — harmless, extra
   cells are blank/0, but see bug about intended depth).
5. `U6=T6·4` = final settlement at center [cm].
6. QA path: `V=L/B, W=z/(B/2)` → direct Ic (`X`, same functional form as
   Timoshenko-Goodier's Ic, full B/L not halved) `→ Y=q·X → Z=IFERROR(10·Y/S,0)`;
   `Z6=SUM(Z7:Z87)` (only 81 rows, see bug).

Matches the classic Fadum/Newmark 4-rectangle diagram (Poulos & Davis, confirmed
via an in-workbook reference figure): loaded rectangle with corners O'(bottom-left),
g(top-left), b(top-right), d(bottom-right); O'd=F5 and O'g=F6 are its two full
sides; point O splits side O'd into F7 (=x) + F9 (=F5−F7) and splits side O'g
into F8 (=y) + F10 (=F6−F8). The reference figure states "per il punto O:
Oabc+Ocde+OeO'f+Ofga; per il punto O': O'gbd" — i.e. sum 4 sub-rectangle corner
settlements for O, 1 rectangle for O'. PUNTO (per z-row, 4 parallel column
blocks + 1 comparison block, all fed by z-grid K7:K87, each block =
`newmark_corner(side_a,side_b,q,z)` **exactly as the literal cell formulas
below** — do not "clean up" the pairing without re-deriving it, see bug note):
1. "Ofga" (cols M-T): sides `(F7,F9)` → `T6=SUM(T7:T87)`.
2. "Oabc" (cols U-AB): sides `(F9,F10)` → `AB6=SUM(AB7:AB87)`.
3. "OeO'f" (cols AC-AJ): sides `(F8,F7)` → `AJ6=SUM(AJ7:AJ87)`.
4. "Ocde" (cols AK-AR): sides `(F10,F8)` → `AR6=SUM(AR7:AR87)`.
5. `C2 = T6+AB6+AJ6+AR6` (sum of the 4 blocks = settlement at O).
6. "O'gbd" (cols AS-AZ), independent of O: sides `(F6,F5)` → `AZ6=SUM(AZ7:AZ87)`;
   `C3 = AZ6` (single-rectangle corner settlement at reference point O').
7. Layer-E lookup and stratigraphy `D15:F19`: identical pattern to CENTRO.

### Lookup tables
Stratigraphy range lookup (both modes): 5 hardcoded layers, key = z (depth below
foundation base), `IF(AND(z>D_i, z<=E_i), F_i, ...else 0)` chained i=1..5 —
right-open interval, degenerates to 0 (not an error) past layer 5 or if z falls in
a gap.

### Constants
- z-grid step: 10 cm, hardcoded fill-down (not user-configurable).
- Max soil layers: 5 (hardcoded IF chain), rows 7-11 (CENTRO) / 15-19 (PUNTO).
- CENTRO: last layer's ground-surface "to" (C11) hardcoded to 12000 cm (=120 m,
  "infinite" cutoff).
- kPa→kg/cm² conversion baked into some E formulas: `/(10·9.80665)` ≡ `/98.0665`
  (1 kg/cm² = 98.0665 kPa); e.g. `F7={=5500/(10*9.80665)}` (5500 kPa input).

### Suspected bugs / fragile spots
- **CENTRO SUM range mismatch**: `T6=SUM(T7:T1063)` but the z-grid fill-down only
  has data to row 97 (z=910 cm); `Z6=SUM(Z7:Z87)` only to row 87 (z=870 cm). The
  two "equivalent" settlement estimates (U6 vs Z6) are integrated to different max
  depths (910 vs 870 cm) — not a true apples-to-apples QA check; also both caps
  are fixed regardless of B/L (large footings may need >2·B significant depth).
- **E lookup silently returns 0** past the 5th layer or in an uncovered z range,
  and `IFERROR(...,0)` then contributes 0 settlement instead of raising — a
  footing needing >5 layers or with a stratigraphy gap silently under-predicts
  settlement with no warning.
- **E values hardcoded inside formula text** (e.g. `=5500/(10*9.80665)`) rather
  than as a plain input cell — changing stiffness requires editing the formula,
  not just a cell value; easy to break the conversion by mistake.
- PUNTO's "500" sheet input F5=F6=4000 cm (40 m!) vs sibling "400" F5=F6=400 cm —
  not a formula bug, but check this isn't a data-entry error before trusting the
  "500" golden case at face value.
- **PUNTO axis pairing unverified for off-center points**: F7/F9 are the two
  segments of one side (F9=F5−F7), F8/F10 of the other (F10=F6−F8); a valid
  corner rectangle needs one segment from each side. "OeO'f"(F8,F7) and
  "Oabc"(F9,F10) mix sides (valid); "Ofga"(F7,F9) and "Ocde"(F10,F8) each pair
  two segments of the *same* side (looks wrong). Both golden cases have
  F7=F8=F9=F10 (O exactly centered), so a same-side/cross-side mixup is
  numerically invisible there. **Re-derive/test this pairing against an
  asymmetric point before trusting it**, rather than the geometric story above.

### Golden test case
CENTRO (`Elastico_centrale_Newmark`, B=350,L=500,q=0.5,D=110, layer1 B=80→480cm
E=`5500/(10·9.80665)`=56.0844, layer2 480→580 E=71.3801, layer3 580→660 E=91.7745,
layer4 660→3260 E=71.3801, layer5 3260→12000 E=71.3801):
`U6=3.0768 cm` (settlement at center); `Z6=3.0122 cm` (QA cross-check, ~2% low
due to shorter integration range above).

PUNTO (`500`, q=0.8, D=220, e1=e2=e1'=e2'=2000 cm, O'-rectangle 4000×4000, layer1
0→1500cm(real)/0→1280(from base) E=100, layer2 1500→1600/1280→1380 E=180):
row K=10: `Q(Ofga block)=0.2, T(Δs)=0.02`; row K=810 (last, layer boundary edge):
`Q=0.19208, T=0.019208`. Aggregate: `C2 ("Cedimento O")=6.33092 cm`,
`C3 ("Cedimento O'")=1.59762 cm`, `I3 (check, =T6)=1.58273 cm`.

---

## Tool 2: `cedimento-elastico-timoshenko-goodier` — flexible rectangle, T&G closed form

### Purpose
Immediate settlement under center and edge-midpoint of a flexible rectangular
foundation via Timoshenko & Goodier's closed-form displacement-influence factors
(I1, I2 → IS) combined with a depth/shape correction factor IF read off a chart
(Fig. 3 in the sheet, not a formula) and a single depth-weighted-average soil
modulus Es. Based on `Elastico_Timoshenko_Goodier_3` (only complete variant).

### Inputs
| Cell | Symbol | Meaning | Unit | Type | Example |
|---|---|---|---|---|---|
| C4 | B | foundation width | cm | input | 100 |
| C5 | L | foundation length | cm | input | 100 |
| F4 | D | embedment depth | cm | input | 50 |
| F5 | μ | soil Poisson ratio | — | input, range (0,0.5) | 0.35 |
| C6 | q | contact pressure | kg/cm² | input | 0.92 |
| C7={=C4·5} | H | significant depth (default 5·B, editable) | cm | derived/override | 500 |
| C11:G15 (table) | strato i | ≤4 layers (hardcoded rows 11-14, row15 = "beyond H", C=15000 last "to"); cols C=from,D=to (ground surface), E,F=from/to below foundation base, G=Ei [kg/cm²] | mixed | strato1 C=0,G=180 |
| U33 | IF_centro | chart-read shape/depth correction factor for center point (Fig. 3, manual input — NOT a formula) | — | input | 0.65 |
| U36 | IF_bordo | same, for edge-midpoint | — | input | 0.78 |

### Outputs
| Cell | Meaning | Unit |
|---|---|---|
| N17 | ΔH centro (settlement at center) | mm |
| P17 | ΔH bordo (settlement at edge midpoint) | mm |
| H11 | Es (depth-weighted average modulus over 0..H) | kg/cm² |
| N15/P15 | IS centro/bordo (T&G displacement influence factor) | — |

### Calculation steps
1. `F6={=+C5/C4}` a=L/B (aspect ratio, reused everywhere as `$F$6`).
2. `N12={=+C7/C4*2}` b_centro = 2H/B; `P12={=C7/C4}` b_bordo = H/B.
3. `I1_centro (N13) = 1/π·(a·ln((1+√(a²+1))·√(a²+b²)/a/(1+√(a²+b²+1))) + ln((a+√(a²+1))·√(1+b²)/(a+√(a²+b²+1))))`,
   with b=b_centro; same for edge with b=b_bordo → `P13`.
4. `I2_centro (N14) = b/(2π)·atan(a/b/√(a²+b²+1))`; same for edge → `P14`.
5. `IS = I1 + (1-2μ)/(1-μ)·I2` → `N15` (centro), `P15` (bordo).
6. `IF_centro=U33`, `IF_bordo=U36` — user reads these off the Fig. 3 chart for the
   sheet's D/B and L/B ratios (chart not implementable in closed form — see below).
7. `H11 = Σ_{i=1..4} Gi·(Fi−Ei) / C7` — depth-weighted average Es over the 4
   hardcoded layers spanning 0..H (NOT a fill-down; generalize to N layers for
   reimplementation, weighting by each layer's thickness inside [0,H]).
8. `N17 (ΔH centro) = q·(B/2)·(1−μ)/Es·IS_centro·IF_centro·4·10` [mm]
   (the ×4 accounts for 4-quadrant superposition to reach the center point, ×10
   converts cm→mm).
9. `P17 (ΔH bordo) = q·B·(1−μ)/Es·IS_bordo·IF_bordo·10` [mm] (no ×4: edge point
   needs only the one half-plane, per T&G superposition for an edge point).

### Lookup tables
Fig. 3 chart (IF vs H/B for various L/B, D/B) — not digitized in the workbook;
user reads a value off an embedded image and types it into U33/U36. Cannot be
reproduced as a formula; expose IF as a required, direct user input in the
reimplementation (optionally ship a digitized table as a future enhancement).

### Constants
- `H = 5·B` default (rule-of-thumb "significant depth"), user-overridable via C7.
- Weighted-Es formula hardcoded to exactly 4 layers (G11:G14) — fragile if the
  real stratigraphy needs more layers within H, or H spans beyond row 15's range.
- `×10` unit conversion (cm→mm) baked into the ΔH formulas.

### Suspected bugs / fragile spots
- **`(1−μ)` instead of `(1−μ²)` in the ΔH formulas (N17, P17)**. Classical T&G
  settlement theory uses `(1−ν²)`, and IS itself already correctly uses
  `(1−2μ)/(1−μ)` (unsquared, that's correct for that sub-term). Verified by
  hand: `0.92·100/2·(1−0.35)/138.8·0.505131·0.65·4·10 = 2.8292` matches the
  cached `2.82917`, confirming the sheet literally divides by `(1−μ)` not
  `(1−μ²)`. This under-computes settlement vs. standard theory (since
  `(1−μ)<(1−μ²)` for 0<μ<1). **Reproduce the spreadsheet's `(1−μ)` behavior to
  match the golden case**; flag to engineers that this diverges from textbook
  T&G and may need a corrected mode.
- **`Elastico_Timoshenko_Goodier` (μ=0.2) and `_2` (μ=0.25) are dead/broken**:
  both define a per-layer "IF" column (S in v1, S/AB in v2) that is *never
  filled in* by any formula (confirmed empty in the extracted CSV for every
  row) — so v2's per-layer `ΔH centro/bordo` (`V`, `AE`) always evaluate to 0
  (multiplying by the blank IF cell), and the sheet totals `H8/I8=0`. Do not
  port this per-layer approach; it is superseded by `_3`'s single
  chart-read IF + depth-weighted Es.
- 4-layer hardcode in `H11`: if the real profile's H falls beyond layer 4's
  reach, or has more than 4 distinct layers above H, the average silently
  ignores the extra thickness/layers.

### Golden test case
`Elastico_Timoshenko_Goodier_3`, B=L=100 cm, D=50 cm, μ=0.35, q=0.92 kg/cm²,
H=500 cm, layers (kg/cm²): 0-160cm→180, 160-450→140, 450-450(zero-thick)→280,
450-11950→280:
`H11 (Es)=138.8`, `N15 (IS centro)=0.505131`, `P15 (IS bordo)=0.451165`,
`IF_centro=0.65`, `IF_bordo=0.78` → `N17 (ΔH centro)=2.82917 mm`,
`P17 (ΔH bordo)=1.51615 mm`.
