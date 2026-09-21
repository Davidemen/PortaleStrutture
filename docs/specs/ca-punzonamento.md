# CA Punzonamento (Punching Shear) — Implementation Spec

Source workbook, sheet `Shotblast_225N` (cellmap: `build/cellmaps/ca-punzonamento/shotblast-225n.txt`). Governing code: EN 1992-1-1 (EC2) §6.4 (punching shear), with §9.4.3 for minimum shear-reinforcement area. Sheet `Shotblast_375N` is a byte-identical-formula clone with 11 different inputs (golden case #2, not read here per task instructions — use as an independent regression check when re-implementing).

## Tool 1: `ca-punzonamento` — column/pile punching shear check + shear-reinforcement design

### Purpose
Full punching-shear design for a flat slab/raft column (or pile) connection: (1) stress check at the column-face perimeter u0 against vRd,max (EC2§6.4.5(3)N?, simplified), (2) a brute-force search over the control-perimeter distance a∈[0.5d,2d] to find the governing perimeter ui (EC2§6.4.4(2)?, extended beyond the textbook fixed-2d check), (3) concrete-only capacity check vRd,ci at that governing perimeter (EC2§6.4.4(1)-(2)), and, if that fails, (4) design of radial/circumferential vertical shear reinforcement ("cuciture") per EC2§6.4.5(1) and §9.4.3(2)/(9.11), including the u0,out perimeter beyond which reinforcement is not needed (EC2§6.4.5(4)).

### Inputs
| cell | symbol | meaning | unit | type/enum/range | cached example |
|---|---|---|---|---|---|
| D2 | Ved | Design shear (SLU+SLV) at column | kN | number>0 | 225 |
| D3 | pterreno | Soil bearing pressure from FEM (raft), subtracted from Ved | MPa | number≥0 | 0 |
| D4 | A | Column side 1 (0 ⇒ column is circular, use D7) | mm | number≥0 | 400 |
| D5 | B | Column side 2 | mm | number≥0 | 400 |
| D6 | H | Slab/raft thickness | mm | number>0 | 500 |
| D7 | D | Circular column/pile diameter (used only if D4=0) | mm | number≥0 | 0 |
| D8 | fck | Concrete cylinder strength | MPa | number>0 | 35 |
| D9 | c | Cover | mm | number>0 | 50 |
| D13 | β | Load-eccentricity factor, EC2§6.4.3(6) fig. | - | enum via H13:K13={1, 1.15, 1.4, 1.5} (≈axisym./interior/edge/corner col.) | 1.15 |
| D21 | umanuale | Manual override of ui perimeter; "x" = no override (MIN ignores text) | mm | number or "x" | "x" |
| D24 | A_amanuale | Manual override of A_a; "x" = no override | mm2 | number or "x" | "x" |
| D27 | px | Tension-rebar spacing, x-dir | mm | number>0 | 200 |
| D28 | py | Tension-rebar spacing, y-dir | mm | number>0 | 200 |
| D29 | φx | Tension-rebar diameter, x-dir | mm | number>0 | 20 |
| D30 | φy | Tension-rebar diameter, y-dir | mm | number>0 | 20 |
| D31 | padd-x | Extra top-up rebar spacing, x (0=none) | mm | number≥0 | 0 |
| D32 | padd-y | Extra top-up rebar spacing, y (0=none) | mm | number≥0 | 0 |
| D33 | φadd-x | Extra top-up rebar diameter, x | mm | number≥0 | 0 |
| D34 | φadd-y | Extra top-up rebar diameter, y | mm | number≥0 | 0 |
| D46 | a1,eff | Actual distance of 1st stirrup perimeter from column face | mm | number, checked in [0.3d,0.5d] | 400 |
| D47 | bu | Distance of last stirrup perimeter from u0,out | mm | number, checked <1.5d | 380 |
| D52 | st | Tangential spacing between stirrups on a perimeter | mm | number, checked <1.5d | 200 |
| D55 | φ | Vertical stirrup ("cucitura") diameter | mm | dropdown list "8,10,12,14,16,28,20,22" (28 is a likely typo for 18, see §7) | 12 |
| D58 | n | Actual number of stirrups placed per circumferential row | - | integer≥ n(f) [D57] | 8 |

Derived-but-unlocked (formula cells marked `*`, effectively re-derivable, not free inputs): D10 dx=D6-D9-D29/2, D12 d=(D10+D11)/2, D20 amanuale (see step 5), D53 Asw,min (see step 19).

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| D16 | u0 | Column-face control perimeter | mm | 1600 |
| D17 | uRd,max | Max punching stress at u0 (simplified) | MPa | 3.96667 |
| D18/F18 | uEd,0 | Stress at u0 / pass-fail | MPa | 0.37609 / "Verificato" (D18<D17) |
| D20 | a (governing, "amanuale") | Distance of governing control perimeter from column | mm | 860 |
| D22 | ui | Governing control perimeter length | mm | 7003.54 |
| D37 | uRd,i | Concrete-only punching capacity at ui | MPa | 0.471968 |
| D38/F38 | uEd,i | Stress at ui / pass-fail (gates need for reinforcement) | MPa | 0.08592 / "Verificato" |
| C40 | message | "…NON NECESSARIO" or "…NECESSARIO PROGETTO ARMATURE VERTICALI" | text | "PROGETTO DELLE ARMATURE VERTICALI NON NECESSARIO." |
| D41 | u0,out | Perimeter beyond which no shear reinf. needed | mm | 1274.97 |
| D53 | Asw,min | Minimum area per stirrup (EC2 9.4.3(2)) | mm2 | 58.318 |
| D57 | n(f) | Required stirrups per row (min-area based) | - | -12 (meaningless, see §7) |
| D59 | V'Rd,c | Concrete term of combined capacity | kN | 1066.01 |
| D60 | VRd,s | Steel term (n[D58]·VRd,cs(1)[D56]) | kN | 501.679 |
| D61/F61 | VRrd | Total resistance with reinf. / pass-fail (VRrd>Ved·β) | kN | 1567.68 / "Verificato" |
| D62 | Ved/Vrd | Utilization ratio, final check | - | 0.165052 |

### Calculation steps
1. Effective depth: `dx[D10]=H[D6]-c[D9]-φx[D29]/2`; `dy[D11]=H[D6]-c[D9]-φx[D29]-φy[D30]/2` (dy nested under dx, i.e. subtracts full φx then half φy); `d[D12]=(dx+dy)/2`.
2. Column perimeter: `u0[D16] = D4=0 ? π·D[D7] : 2·(A[D4]+B[D5])`.
3. `uRd,max[D17] = 0.2·0.85·fck[D8]/1.5` (simplified vRd,max, see §7).
4. Net reduced shear at column face: `Ved,Red,0[D15] = Ved[D2]·β[D13] - pterreno[D3]·(D4=0 ? π·(D7/2)^2 : A·B)/1000`; `uEd,0[D18]=Ved,Red,0·1000/(u0·d)`; `F18 = uEd,0<uRd,max ? "Verificato" : "Non verificato"`.
5. **Governing-perimeter search** (fill-down table `AO2:AX152`, 151 rows, index i=2..152, `x=AP_i=0.5+0.01·(i-2)` up to 2.0): for each x, `a_i=x·d`; `ui_i = MIN(umanuale[D21], D4=0 ? π·(D7+2a_i) : 2(A+B)+2π·a_i)`; `A_a,i = A·B+4·MIN(A,B)·a_i+π·a_i²`; `Vred,i = Ved·β - pterreno·A_a,i/1000`; `uRd,i(x) = CRd,c[D25]·k[D26]·(100·ρ[D35]·fck)^(1/3)·(2d/a_i)`; `uEd,i(x)=Vred,i·1000/(ui_i·d)`; `ratio_i=uEd,i(x)/uRd,i(x)`. Then `x* = argmax_i(ratio_i)` [row154: `MAX(AW2:AW152)` → `VLOOKUP` back to AX column for the winning x]; `a[D20] = x*·d`. (In the golden case the ratio is monotonically increasing in x, so x*=2.0 — the search degenerates to the classic a=2d perimeter; see §7.)
6. `ui[D22] = MIN(umanuale[D21], D4=0 ? π·(D7+2a) : 2(A+B)+2π·a)` using `a[D20]` from step 5.
7. `A_a[D23]` = same rounded-rectangle-area formula using `a[D20]`.
8. `CRd,c[D25]=0.18/1.5`; `k[D26]=MIN(1+√(200/d),2)`.
9. Reinforcement ratios: `H29=π·φx²/4` (bar area); `ρx[I29]=H29/(px·d)`; symmetric for `ρy[I30]` via φy,py. Top-up bars: `ρaddx[I33]=padd-x=0 ? 0 : π·φaddx²/4/(padd-x·d)`; symmetric `ρaddy[I34]`. `ρx,tot[K31]=ρx+ρaddx`; `ρy,tot[K32]=ρy+ρaddy`; `ρ[D35]=√(ρx,tot·ρy,tot)`, must be <0.02.
10. `Ved,Red,ui[D36] = Ved·β - pterreno·MIN(A_a[D23], A_amanuale[D24])/1000`.
11. `uRd,i[D37] = CRd,c·k·(100·ρ·fck)^(1/3)·(2d/a[D20])`.
12. `uEd,i[D38] = Ved,Red,ui·1000/(ui[D22]·d)`; `F38 = uEd,i<uRd,i ? "Verificato" : "Non verificato"` → gates C40 message and whether steps 13-19 outputs are meaningful (see §7).
13. `u0,out[D41] = Ved·β·1000/(CRd,c·k·(100·ρ·fck)^(1/3)·d)` (EC2§6.4.5(4)).
14. `k'd[D42] = (u0,out - 2·(A+B))/(2π)` — radius to u0,out beyond the straight sides.
15. `sr,max[D43]=0.75d`; `a1,min[D44]=0.3d`; `a1,max[D45]=0.5d`; check `a1,eff[D46]` ∈[a1,min,a1,max] (F46 message).
16. `bu[D47]` input, checked <1.5d (F47). `au[D48]=k'd[D42]-bu[D47]`; `au-a1[D49]=au-a1,eff[D46]`.
17. `n(rows)[D50] = CEILING(au-a1 / sr,max, 1) + 1` (CEILING rounds toward +∞, i.e. Python `math.ceil`, including for negative args — verified against cached −1 result); `sr[D51]=(au-a1)/(n-1)`.
18. `st[D52]` input, checked <1.5d (F52).
19. `Asw,min[D53] = 0.08·√fck·sr[D51]·st[D52]/(450·1.5)` (EC2 eq 9.11, vertical links: fyk=450 baked in, factor "1.5 sinα+cosα"→1.5 for α=90°).
20. `VRd,cs,min[D54] = (uEd,i[D38]-0.75·uRd,i[D37])·ui[D22]·d/1000` — required steel-side force at the ui perimeter (EC2 eq 6.52 rearranged).
21. `H55 = π·φ[D55]²/4` (1-leg area). `fywd,ef[H56] = 250+0.25d` **(no cap against fywd — see §7)**. `VRd,cs(1)[D56] = 1.5·(d/sr[D51])·H55·H56/1000` — resistance of one stirrup summed around one radial perimeter.
22. `n(f)[D57] = CEILING(VRd,cs,min/VRd,cs(1), 1)`.
23. `V'Rd,c[D59] = 0.75·uRd,i[D37]·ui[D22]·d/1000`; `VRd,s[D60] = n[D58]·VRd,cs(1)[D56]`; `VRrd[D61]=VRd,s+V'Rd,c`; `F61 = VRrd>Ved·β ? "Verificato" : "Non verificato"`; `Ved/Vrd[D62]=Ved·β/VRrd`.

### Lookup tables
- `H13:K13` β dropdown: {1.0, 1.15, 1.4, 1.5} keyed by column position (interior w/o eccentricity, interior, edge, corner) — exact-match enum, no interpolation.
- `D55` dropdown, literal list "8,10,12,14,16,28,20,22" (mm) — flat enum, not a range table.
- Search table `AO2:AX152` (step 5): key = row index i (⇔ x=a/d from 0.5 to 2.0 step 0.01); not a value lookup but an exhaustive scan whose max (`row154`) is read back via `VLOOKUP(MAX(AW2:AW152), AW2:AX152, 2, FALSE)`.

### Constants (hardcoded in formulas)
- `0.2·0.85/1.5` — simplified vRd,max coefficient (§7, deviates from EC2§6.4.5(3)N `0.5·ν·fcd`).
- `0.18/1.5` — CRd,c (EC2§6.4.4(1)).
- `200`, cap `2` — k=MIN(1+√(200/d),2) (EC2§6.4.4(1)).
- `0.02` — max ρl (EC2§6.4.4(1)).
- `0.75d`(sr,max), `0.3d`/`0.5d`(a1,min/max), `1.5d`(max bu/st) — EC2§9.4.3?/Fig 6.22 layout rules.
- `0.08/(450·1.5)` — Asw,min coefficient, fyk=450 MPa baked in (EC2 eq 9.11).
- `250+0.25d` — fywd,ef (EC2 eq 6.52).
- `1.5` factor in VRd,cs(1) and `0.75` factor in V'Rd,c/VRd,cs,min — EC2 eq 6.52 split of concrete/steel contributions.
- Search range `[0.5, 2.0]` step `0.01` for a/d (151 samples) — spreadsheet-specific brute-force, no code basis.

### Suspected spreadsheet bugs / fragile spots
1. `D55` validation list "8,10,12,14,16,28,20,22" — breaks the even-mm progression; "28" is almost certainly a typo for "18" (re-verified: literal string in validation, not a formula).
2. `E14` = `IF(D14="a=d",D12,IF(D14="a=1.5d",1.5·D12,IF(D14="a=2d",2·D12,"")))` always evaluates to `""`/None because `D14` itself is the numeric formula `=2*D12` (860), never one of those text labels — dead/orphaned logic from an earlier version where D14 was a dropdown (K14:K16 still hold the old "a=d"/"a=1.5d"/"a=2d" option strings). Safe to drop; note for parity only.
3. `E55` unit label is `"mm2"` for the stirrup **diameter** `φ[D55]` — should be `"mm"`; cosmetic only, `H55` computes the area correctly with its own π/4·φ².
4. `fywd,ef[H56]=250+0.25d` has no `MIN(...,fywd)` cap required by EC2 eq 6.52; not triggered at d=430mm here (357.5 < fyd) but will silently overstate stirrup efficiency for thicker slabs (d≳560mm with fyd=391.3, γs=1.15).
5. Rows/cells 41-62 (u0,out through VRrd) are **not gated** by the `F38`/`C40` "reinforcement needed?" check — they always compute, and when reinforcement is genuinely unnecessary (as in this golden case) several intermediate values go negative and lose physical meaning (`k'd[D42]=-51.7`, `n(rows)[D50]=-1`, `VRd,cs,min[D54]=-807`, `n(f)[D57]=-12`). A re-implementation should still compute them (for parity/testing) but must not assert engineering sense on them outside the `F38="Non verificato"` branch.
6. The governing-perimeter search (step 5) is monotonically increasing here, landing on the table's upper bound `a/d=2.0` — i.e., for this input set the 151-row brute force is equivalent to just evaluating at `a=2d`. Not provably true for all inputs (e.g. `pterreno>0` where `Vred,i` decreases with `a`) — keep the full scan rather than hardcoding `a=2d`, and use the second golden case (375N) to confirm behavior at different inputs before ever simplifying it away.

### Golden test case (Shotblast_225N)
```
inputs: Ved=225 kN, pterreno=0 MPa, A=400 mm, B=400 mm, H=500 mm, D=0 mm, fck=35 MPa, c=50 mm,
        beta=1.15, px=py=200 mm, phix=phiy=20 mm, paddx=paddy=0, phiaddx=phiaddy=0,
        a1eff=400 mm, bu=380 mm, st=200 mm, phi_stirrup=12 mm, n_stirrups=8
derived: dx=440, dy=420, d=430 mm
outputs: u0=1600 mm, uRd_max=3.96667 MPa, uEd0=0.37609 MPa -> Verificato (rate 0.0948)
         a_governing=860 mm (=2d), ui=7003.54 mm, A_a=3.85952e6 mm2
         uRd_i=0.471968 MPa, uEd_i=0.08592 MPa -> Verificato (rate 0.182046)
         message="PROGETTO DELLE ARMATURE VERTICALI NON NECESSARIO."
         u0_out=1274.97 mm, Asw_min=58.318 mm2, VRd_cs1=62.7098 kN
         V'Rd_c=1066.01 kN, VRd_s=501.679 kN, VRrd=1567.68 kN -> Verificato (Ved/Vrd=0.165052)
search-table sample rows: i=2 (x=0.50,a=215mm) -> ui=2950.88, A_a=649220.12, uRd_i=1.88787, uEd_i=0.20392, ratio=0.108016
                          i=77 (x=1.25,a=537.5mm) -> ui=4977.21, A_a=1.92763e6, uRd_i=0.75515, uEd_i=0.12090, ratio=0.160101
                          i=152 (x=2.00,a=860mm)  -> ui=7003.54, A_a=3.85952e6, uRd_i=0.471968, uEd_i=0.08592, ratio=0.182046 (=row154 max)
```
