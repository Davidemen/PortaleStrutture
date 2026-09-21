# Plinti Isolati (Isolated Footings) — Implementation Spec

Source workbook `...Plinti isolati.xlsx`, sheets: `INPUT`, `CHECKS`, `LC Reactions`, `LCC Reactions`, `LCC Foundations`, `LCC Foundations STC BASE`.
Governing code: NTC 2018 §6.4.2/§6.4.3 (fondazioni superficiali — capacità portante, scorrimento, ribaltamento) ?, §6.2.4.1 (combinazione carichi permanenti γG per approcci STR/EQU), EC2 §7.2/§7.3 (limitazione tensioni in esercizio, fessurazione) applied via Circolare 2019 §4.1.2.2.4 ?.

One footing (node 1832) only in this workbook instance; the CHECKS sheet fills down one row per load combination (1728 rows total, but only rows 6:542 — 537 combos — are wired into any aggregation; rows 543:1728 are dead padding, see §7). `LC Reactions` holds 25 named elementary load cases (SWL, DL, INST, LL, LR, S, S_DRIFT, CR(...), W±X/Y_±cpi, E_STR_X/Y/Z(RS)); `LCC Foundations` (539 rows) and `LCC Foundations STC BASE` (1725 rows, unused by this instance) hold the linear-combination coefficients; `LCC Reactions` = SUMPRODUCT of the two → one row per combo with (Fx,Fy,Fz,Mx,My,Mz); `INPUT!A3:H541` re-imports `LCC Reactions` unchanged and adds the footing geometry/material block + aggregation helper columns; `CHECKS` re-derives the full per-combo check from `INPUT` row + geometry.

## Tool 1: `fond-plinti-isolati-verifica-combinazione` — single footing, single combination check

### Purpose
For one footing geometry + one factored combination (N,V,M at pedestal top), computes self-weight, base actions (with lever-arm transfer to footing base + user eccentricity), soil contact pressure (rigid-footing σ=N/A±6M/(B·L²), core/kern rule e<L/6), sliding safety factor, overturning safety factor (both directions) and compressed-base ratio. NTC 2018 §6.4.2.1 / §6.2.4.1 (approcci STR/EQU, γG1) ?; sliding/overturning per §6.4.3.1 ?. Sheet `CHECKS`, one fill-down row (row 6 = combo 1, shown; formula pattern identical to row 542).

### Inputs
| cell | symbol | meaning | unit | type/enum/range | cached (ULS1, row6) |
|---|---|---|---|---|---|
| INPUT!I{row} (via CHECKS!B) | family | combo family label, e.g. "ULS STR","STR EQK","SLS CHA","ULS EQU","EQK EQU" | - | text, `B=IF(LEFT(family,3)="SLS",LEFT(family,3),RIGHT(family,3))` → one of STR/EQU/EQK/SLS | "ULS STR"→"STR" |
| INPUT!C/D/E/F/G/H{row} | Fx,Fy,Fz,Mx,My,Mz | column-base reaction for this combo (= LCC Reactions row) | kN,kN,kN,kNm,kNm,kNm | numeric, from Tool-0 combo table | 0.131665, 5.37205, 220.927, -36.4022, 1.31727, -0.0608972 |
| INPUT!P3,P4 | AX,BY | plinth plan dimensions | mm | user, >0 | 4000, 4000 |
| INPUT!P5 | H | plinth height | mm | user, >0 | 800 |
| INPUT!P6 | h | plinth depth (soil cover above footing top) | mm | user, ≥0 | 4500 |
| INPUT!P7,P8 | aX,aY | pedestal plan dims | mm | user, ≥0 (0 = no pedestal) | 0, 0 |
| INPUT!P9,P10 | ssup,sinf | pedestal height above/below grade | mm | user, ≥0 | 0, 0 |
| INPUT!P11 | s | haunch/lip offset added to lever arm (NOT the rebar spacing of same name, see §7) | mm | user | 50 |
| INPUT!P12,P13 | eX,eY | user-applied load eccentricity | mm | user | 0, 0 |
| INPUT!P34 | γ_earth | soil unit weight | kN/m³ | user | 20 |
| INPUT!P35 | φ | soil friction angle | ° | user | 30 |
| (constant) | γ_conc | concrete unit weight | kN/m³ | hardcoded 25 in formula | 25 |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| CHECKS!C,D,E | Wplinth,Wped,Wearth | self-weight components | kN | 320, 0, 1440 |
| CHECKS!F | γW | permanent-load factor: STR→1.35, EQU→0.9, else→1 | - | 1.35 |
| CHECKS!G,J | NX=NY | total factored vertical load = Fz+(Wplinth+Wped+Wearth)·γW | kN | 2596.93 |
| CHECKS!H,K | VX,VY | \|Fx\|, \|Fy\| | kN | 0.131665, 5.37205 |
| CHECKS!I,L | MYY,MXX | base moment = \|My or Mx\| + V·(H+s)/1000 + N·(eY or eX)/1000 | kNm | 1.42918, 40.9685 |
| CHECKS!M,T | e | eccentricity = M/N | m | 0.000550, 0.015776 |
| CHECKS!N,U | Case | "internal" if 1000·e < AX/6 (or BY/6), else "external" | - | "internal","internal" |
| CHECKS!Q,R (int.) / P (ext.) | σt,min/max or σt | contact pressure, internal: `10·(N·1e3/(AX·BY))·(1∓6e/AX)`; external (triangular, uplift): `10·2·(N·1e3)/(BY·y·1e3)`, y from O=`3·(AX/2000−e)` | kg/cm² | 1.62174/1.62442 |
| CHECKS!S,Z | compressed ratio | X:`1` if internal else `y/(AX/1000)`; same for Y | - | 1, 1 |
| CHECKS!AA | σt (total) | MAX(P:R)+MAX(W:Y) − N·10⁴/(AX·BY) (superposed biaxial approx.) | kg/cm² | 1.66283 |
| CHECKS!AC,AF | Mrib,X/Y | overturning moment = MYY / MXX | kNm | 1.42918, 40.9685 |
| CHECKS!AD,AG | Mstab,X/Y | stabilizing moment = N·(AX or BY)/2000 | kNm | 5193.85, 5193.85 |
| CHECKS!AE,AH | μX,μY | overturning safety factor = Mstab/Mrib, ">100" if Mrib=0 or ratio>100 | - | ">100" |
| CHECKS!AJ | S (shear resultant) | √(VX²+VY²) | kN | 5.37366 |
| CHECKS!AL | fS | tan(φ) | - | 0.57735 |
| CHECKS!AM | μsl | sliding safety factor = N·fS/S, capped ">100"/`100` on error/>100 | - | ">100" |
| CHECKS!AO | ribaltamento | MIN(μX,μY) — governing overturning ratio | - | ">100" |
| CHECKS!AP | COMPRESSED | MIN(S,Z) — governing compressed-base ratio (1 = no uplift) | - | 1 |
| **PASS/FAIL** | | σt(AA) ≤ σ_slu or σ_sle (Tool-2 input, by family); μsl≥1; μX,μY≥1; AP=1 (or ≥ min required, e.g. NTC seismic ≥0.??) | | |

### Calculation steps (dependency order)
1. `family = IF(LEFT(comboType,3)="SLS", LEFT(3), RIGHT(3))` [CHECKS!B]
2. `γW = IF(family="STR",1.35, IF(family="EQU",0.9,1))` [F]
3. `Wplinth = AX·BY·H·25/1e9` [C]; `Wped = aX·aY·(ssup+sinf)·25/1e9` [D]; `Wearth = (AX·BY−aX·aY)·h·γ_earth/1e9` [E] — mm³→m³ factor 1e-9 baked in.
4. `N = Fz + (Wplinth+Wped+Wearth)·γW` [G,J]
5. `VX=|Fx|`, `VY=|Fy|` [H,K]
6. `MYY = |My| + VX·(H+s)/1000 + N·eX/1000`; `MXX = |Mx| + VY·(H+s)/1000 + N·eY/1000` [I,L]
7. `eccX = MYY/N`; `eccY = MXX/N` [M,T]
8. Core check vs AX/6, BY/6 → internal/external [N,U]
9. Contact pressure per branch (step above) → σt,min/max or triangular σt [O..R, V..Y]
10. Compressed-length ratio [S,Z]; combined σt [AA]
11. Overturning: Mrib = MYY or MXX; Mstab = N·(AX or BY)/2000; μ = Mstab/Mrib [AC-AH]; governing μ=MIN [AO]
12. Sliding: S=√(VX²+VY²); fS=tan(φ); μsl=N·fS/S [AJ-AM]
13. Governing compressed ratio = MIN(S,Z) [AP]

### Lookup tables
None internal to this tool (φ, γ_earth are scalar user inputs, not table lookups).

### Constants
- Concrete unit weight 25 kN/m³ (buried in C,D formulas, not a named input cell).
- mm³→m³ conversion 1e-9; kN·1e3→N and MPa→kg/cm² combined into the literal factors `10` (single-direction pressure) and `10^4` (combined AA formula).
- `1.5·20` = 30mm buried in rebar effective-depth formula (Tool 2) assumes a 20mm bar half-diameter margin, independent of actual φ.

### Suspected bugs / fragile spots
- **AA (total σt) double-counts/undercounts the uniform term**: `MAX(P:R)+MAX(W:Y) − N·1e4/(AX·BY)` is an ad-hoc superposition of two uniaxial trapezoids minus one baseline term; it is not the exact biaxial-bending corner pressure. Re-verify against a manual biaxial check before trusting σt near corners.
- **AM (μsl) inverts on failure**: `IFERROR(IF(N·fS/S>100,">100",N·fS/S),100)` — if the ratio is genuinely <1 (unsafe), the formula still returns the ratio (e.g. 0.8), so a "fail" case is not specially flagged; only division errors (S=0) return `100` (a *pass-looking* value), which is misleading for a zero-shear combo (should probably be "n/a"/∞-safe, not literal 100... actually 100 here reads as "very safe", coincidentally not wrong, but see next point).
- **INPUT!P16/P19/P20 "min sliding ratio" convention conflict**: `IF(MIN(range)=0, ">100", MIN(range))` — a family MIN of 0 (a genuinely unsafe/undefined combo) is displayed as ">100" (i.e. *safe-looking* text), the opposite convention from AE/AH/AL(compressed-area check) which... actually AJ4/AK4 IF(MIN=0,">100",MIN) is used consistently for μX/μY/μsl families too — verify this isn't silently masking a real sliding failure (MIN(μsl)=0 would mean S=0/no shear in that combo, edge case not a failure, but the ">100" label could be misread by a reviewer as "sliding safety factor >100" when it really means "no shear demand in governing combo").
- **`s` symbol reused for two different quantities**: `INPUT!O11="s"/P11=50mm` (haunch/lip lever-arm offset added to H) vs `INPUT!S11="s"/T11=12.2cm` (rebar spacing). A re-implementer must not conflate them.
- **CHECKS rows 543:1728 are dead**: formulas reference `INPUT!row` up to 1725, but INPUT only has data through row 541 (539 combos); INPUT rows >541 are blank → these formulas silently evaluate on zero reactions (self-weight only), and none of the aggregation ranges (`INPUT!AH4:AN10`, hardcoded to end at CHECKS row 542) reference them. Treat rows 543:1728 as inert/do not port.
- **AD32:AD36 "(ø20+ø16)/0.2" reference block**: a static area-per-metre note (`(3.14+2.01)/0.2=25.75` cm²/m) not consumed by any other formula in the given range — looks like leftover documentation scratch, not part of the design output; do not treat as a real check.

### Golden test case (ULS1, node 1832)
```
input: AX=4000mm BY=4000mm H=800mm h=4500mm aX=aY=0 ssup=sinf=0 s(offset)=50mm eX=eY=0 γ_earth=20kN/m3 φ=30°
       Fx=0.131665kN Fy=5.37205kN Fz=220.927kN Mx=-36.4022kNm My=1.31727kNm family=STR
output: Wplinth=320 Wped=0 Wearth=1440 γW=1.35 N=2596.93kN VX=0.131665 VY=5.37205
        MYY=1.42918kNm MXX=40.9685kNm eccX=0.000550m eccY=0.015776m case=internal/internal
        σt,X=[1.62174,1.62442] σt,Y=[1.58467,1.66149] σt,total=1.66283 kg/cm2
        μX=">100" μY=">100" ribaltamento=">100" μsl=">100" AP(compressed)=1
```

---

## Tool 2: `fond-plinti-isolati-inviluppo-armatura` — governing-combo envelope, sliding/overturning/pressure aggregation, flexural reinforcement design, SLS stress checks

### Purpose
Given the Tool-1 output table (one row per combo, 537 used rows) plus a fixed family→row-range map, computes per-family (ULS STR, STR EQK, SLS CHA, SLS FRE, SLS QP, ULS EQU, EQK EQU) the governing (max/min) soil pressure, sliding ratio, overturning ratio and compressed-area ratio + which combo governs (XLOOKUP by value); sizes the bottom/top flexural mesh from the envelope soil pressure; and checks concrete/steel stresses at SLS (quasi-permanent, characteristic, frequent) against NTC/EC2 limits (0.45fck, 0.6fck, 0.8fyk, 200/220/240 N/mm² crack-control limits) ?. Sheet `INPUT` rows 3-38 (uses `INDIRECT`/`XLOOKUP` against `CHECKS` ranges).

### Inputs
| input | one row = | columns (unit) | user-data columns |
|---|---|---|---|
| Tool-1 output table, 537 rows (`CHECKS!A6:AP542`) | one load combination's fully-computed check | A comboName; B family(STR/EQU/EQK/SLS); M,T eccX,eccY(m); AA σt(kg/cm²); S,Z compressed ratio; AO overturning ratio; AM sliding ratio; AP min(S,Z) | none — this is Tool-1's output, not user input |
| family→row-range map (`INPUT!AE4:AG10`, hardcoded) | one combo family | AC label ("ULS STR"…), AE row-count (216,48,192,42,6,9,24), AF/AG cumulative start/end row in CHECKS (running: AF{n}=AG{n-1}+1) | none — hardcoded constants |
| INPUT!T3,T4 | fyk,γs | rebar yield strength, partial factor | N/mm²,- | user (500, 1.15) |
| INPUT!T6 | Rck | concrete cube strength | N/mm² | user (45) |
| INPUT!T11,T12 | s,c | rebar spacing, concrete cover | cm | user (12.2, 8) |
| INPUT!T22,T24 | Φx,man / Φy,man | manual override bar diameter | mm | user (20,20) |
| INPUT!L39,L40 | σ_slu,σ_sle | allowable soil bearing pressure, ULS/SLS | kg/cm² | user (2, 1.5) |

### Outputs
| cell | symbol | meaning | unit | cached (per family, row16-22 pattern) |
|---|---|---|---|---|
| INPUT!L16 | σt,max (ULS STR) | MAX(CHECKS!AA over family range) | kg/cm² | 1.91656 |
| INPUT!N16 | governing combo | XLOOKUP(L16, AA-range, A-range) | - | "ULS_CR96" |
| INPUT!P16 | μsl,min (ULS STR) | MIN(CHECKS!AM over family range), ">100" if MIN=0 | - | 80.1776 |
| INPUT!R16 | governing combo | XLOOKUP(P16, AM-range, A-range) | - | "ULS_CR96" |
| (rows 17-22 repeat for STR EQK/SLS CHA/SLS FRE/SLS QP/ULS EQU/EQK EQU) | | | | 1.34935/96.97 (EQK_7); 1.40068/86.04 (SLS CHA160); 1.32108/">100" (SLS FRE42/1); 1.30679/">100" (SLS QP6/1); 1.24675/85.13 (ULS EQU9); 1.3658/89.24 (EQK EQU7) |
| INPUT!L25 | min compressed ratio (ULS STR) | MIN(CHECKS!S,Z over family) | - | 1 |
| INPUT!P25 | μ overturning,min (ULS STR) | MIN(CHECKS!AO over family), ">100" if 0 | - | 25.185 |
| (rows 26-31 repeat per family) | | | | see golden case |
| INPUT!T34/T35 | ex,max / ex,min | MAX/MIN(CHECKS!M6:M542) — over ALL 537 combos, not per family | m | 0.00983574 / 3.2885e-05 |
| INPUT!T36/T37 | ey,max / ey,min | MAX/MIN(CHECKS!T6:T542) | m | 0.0885579 / 0.00105179 |
| INPUT!T5,T7,T8 | fyd,fck,fctm | fyk/γs; 0.83·Rck; 0.3·fck^(2/3) | N/mm² | 434.783, 37.35, 3.35208 |
| INPUT!T13,T14 | Mx,SLU My,SLU | envelope ULS-type bending moment (see step 6) | kNm | 1533.25, 1533.25 |
| INPUT!T16,T17 | Asx,Asy required | flexural steel area | cm² | 56.787, 56.787 |
| INPUT!T18,T19 | Asx,min Asy,min | 2·0.1%·(AX·BY/100) minimum steel | cm² | 64, 64 |
| INPUT!T20,T21 | Nx,Ny | bar count = CEILING((L_net/10−2c)/s +1, 1) | - | 33, 33 |
| INPUT!T22,T24 | Φx,Φy | computed min bar diameter from As/N, ≥ manual override | mm | 20, 20 |
| INPUT!T26 | Φmin | min bar diameter from 0.26·(fctm/fyk)·b·d rule | mm | 14 |
| INPUT!T30/U30 | TOP layout X/Y | "⌈N/2+0.5⌉φΦ" | - | "17φ20" |
| INPUT!T31/U31 | BOTT layout X/Y | "NφΦ" | - | "33φ20" |
| INPUT!X16/X17,X18/X19 | σc,x/y,QP ; σs,x/y,QP | concrete/steel stress under quasi-permanent envelope moment | N/mm² | 3.35865 / 138.361 |
| INPUT!X20/X21,X22/X23 | σc,x/y,CHA ; σs,x/y,CHA | under characteristic envelope moment | N/mm² | 3.59996 / 148.301 |
| INPUT!AB22/AB23 | σs,x/y,FREQ | under frequent envelope moment | N/mm² | 139.873 |
| **checks** X26/X27/X28/X29/X30 vs AA26..30 | σc,QP<0.45fck; σs,QP<220; σc,CHA<0.6fck; σs,CHA<0.8fyk; σs,FREQ<240 | N/mm² | 3.35865<16.8075 OK; 138.361<220 OK; 3.59996<22.41 OK; 148.301<400 OK; 139.873<240 OK |

### Calculation steps (dependency order)
1. Build family row-ranges: `AF4=76+140`(=216, hardcoded), then `AF{n}=AG{n-1}+1`, `AG{n}=AF{n}+AE{n}-1`, AE = hardcoded family sizes {216,48,192,42,6,9,24} [INPUT!AE4:AG10].
2. Build INDIRECT range strings `"CHECKS!"&col&AF{n}&":"&col&AG{n}"` for col ∈ {AA(soil),AM(sliding),S(compr.X),Z(compr.Y),AO(overturn),A(comboName),AP(min compr.)} [AH:AN].
3. Per family: `σt,max=MAX(INDIRECT(AH))`, governing combo `=XLOOKUP(σt,max, INDIRECT(AH), INDIRECT(AM_range))` [L,N cols].
4. Per family: `μsl,min = IF(MIN(INDIRECT(AI))=0,">100",MIN(INDIRECT(AI)))`, governing combo via XLOOKUP [P,R].
5. Per family: `min compressed = MIN(INDIRECT(AJ),INDIRECT(AK))` [L25-31]; `μ_overturn,min = IF(MIN(INDIRECT(AL))=0,">100",MIN(INDIRECT(AL)))`, governing via XLOOKUP on AN (=CHECKS!AP, the pre-combined min-compressed column) [P25-31].
6. Global eccentricity envelope (ALL 537 rows, not per family): `ex,max/min=MAX/MIN(CHECKS!M6:M542)`, `ey,max/min=MAX/MIN(CHECKS!T6:T542)`, each with governing combo via XLOOKUP [T34-37].
7. Materials: `fyd=fyk/γs`; `fck=0.83·Rck`; `fctm=0.3·fck^(2/3)` [T5,T7,T8].
8. Envelope ULS bending moment (cantilever beyond pedestal, using worst of ULS STR/SLS QP/ULS EQU/EQK EQU family σt,max, L16,L20,L21,L22): `Mx,SLU = MAX(L16,L20,L21,L22)·(BY/10)·0.5·(AX/20+eY/10)²/1e4` (units: σt kg/cm²→ combined with cm geometry then /1e4 → kNm); `My,SLU` mirrors with AX/BY swapped [T13,T14].
9. Required steel: `As = M·1e6/(0.9·d·fyd)/100`, `d=H−c·10−1.5·20` (mm; 1.5·20=30mm buried effective-depth margin) [T16,T17].
10. Minimum steel: `As,min = 2·0.1%·(AX·BY/100)` [T18,T19] (cm²; 0.1% two-way slab minimum per NTC §4.1.6.1.1 ?).
11. Bar count: `N = CEILING((L_side/10 − 2c)/s + 1, 1)` [T20,T21].
12. Bar diameter: `Φ = MAX(CEILING(10·√(4·MAX(Asx,Asy,min)/N/π),2), Φman)` [T22,T24]; `Φmin = CEILING(10·√(4·0.26·(fctm/500)·100·(H/10−c−1.5·2)·(s/100)/π),2)` [T26].
13. Provided steel area: `As,prov = ODD(N)·π·(MAX(Φy,Φx)/2)²` [X5,X6] (mm²).
14. Neutral-axis depth (cracked, homogenized n=15): `ξ = (15·As,prov/B)·(−1+√(1+2·B·M/(15·As,prov)))` [X7,X8] for QP moment; same formula reused (X11-X14) for CHA/FREQ moments.
15. Concrete/steel stress: `σc = 2·M·1e6/(B·ξ·(H−ξ/3))`; `σs = M·1e6/(As,prov·(H−ξ/3))` [X16-X23, AB22/23], applied to QP, CHA, FREQ moment envelopes respectively (Mx,QP/My,QP at X3/X4 computed the same way as step 8 but with SLS-QP-only pressure MAX(L20); Mx,CHA/My,CHA at X9/X10 with MAX(L18); Mx/My,FREQ at AB20/AB21 with MAX(L19)).
16. Compare to limits: 0.45·fck (QP concrete), 220 N/mm² (QP steel), 0.6·fck (CHA concrete), 0.8·fyk (CHA steel), 240 N/mm² (FREQ steel) [X26-X30 vs AA26-AA30].

### Lookup tables
| range | meaning | key | interpolation |
|---|---|---|---|
| `INPUT!AC4:AE10` | family name → row-count in CHECKS combo table | family label (ULS STR, STR EQK, SLS CHA, SLS FRE, SLS QP, ULS EQU, EQK EQU) | exact match, hardcoded counts {216,48,192,42,6,9,24} (sum 537) |
| `INPUT!AF4:AG10` | family → [start,end] row in CHECKS | derived (AF{n}=AG{n-1}+1) | cumulative, no interpolation |
| `CHECKS!A6:A542` (via `AM` range) | combo-name column used as XLOOKUP return array for every "governing combo" lookup | matched by value equality on the driving column (AA/AM/AO/AP) | exact match, first hit (`_xll.XLOOKUP(...,0,1)` = exact match, search-forward) |

### Constants
- Family row counts 216/48/192/42/6/9/24 (=537 total) hardcoded in `AE4:AE10` — must be re-derived from the actual combo generator, not hardcoded, if combo counts differ from this project.
- Rebar effective-depth margin `1.5·20`=30mm (assumes 20mm bar, independent of actually computed Φ — iterative in Excel, not exact).
- Two-way minimum reinforcement ratio 0.1% (`2·(0.1/100)`, factor 2 = both faces top+bottom) — NTC §4.1.6.1.1 ? (verify clause; this is the beam/slab minimum, applied here to a footing).
- n=15 homogenization coefficient (steel/concrete modular ratio) in ξ formulas — standard but not derived from actual Ec/Es.
- Stress limits 0.45fck, 0.6fck, 0.8fyk, 220/240 N/mm² — EC2 §7.2(3)/(5), §7.3.4 crack-control simplified stress limits ? (exposure class not modeled explicitly; values look like XC2/XC3 defaults).

### Suspected bugs / fragile spots
- **XLOOKUP governing-combo lookups can mis-report on ties**: `_xll.XLOOKUP(value, range, names, 0, 1)` returns the *first* row matching `value` exactly; if two combos in a family produce the identical max/min (common with symmetric ±X/±Y combos), the reported "governing combo" is arbitrary (whichever comes first), not necessarily the physically worst one for downstream sign conventions.
- **Global eccentricity envelope (T34-T37) mixes ALL families** (STR+EQU+EQK+SLS in one MAX/MIN over CHECKS!M6:M542) while every other envelope is per-family — re-implementers must replicate this asymmetry (not a typo per se, but easy to miss).
- **Reinforcement moment envelope (T13/T14, step 8) mixes σt,max from 4 unrelated families** (ULS STR, SLS QP, ULS EQU, EQK EQU) via `MAX(L16,L20,L21,L22)` — SLS QP is a serviceability pressure being fed into what is otherwise an ULS flexural-design moment; verify this isn't a copy-paste error (expected candidates would more plausibly be ULS STR + STR EQK + ULS EQU + EQK EQU, i.e. all ULS-type families, not SLS QP).
- **`AD34="=+AD32"`, `AD35`, `AD36` chain**: static "(ø20+ø16)/0.2" reference detail, not consumed downstream (see Tool 1 §7) — do not port into the design-output table.
- Rows 543:1728 of `CHECKS` are excluded from all `AH:AN` ranges (hardcoded end at row 542) — confirms family counts (537) are the true combo universe for this footing; do not extend ranges if the source combo generator produces a different count without re-deriving `AE4:AE10`.

### Golden test case (aggregated, node 1832)
```
families: ULS STR(216) STR EQK(48) SLS CHA(192) SLS FRE(42) SLS QP(6) ULS EQU(9) EQK EQU(24)
σt,max:      1.91656(ULS_CR96)  1.34935(EQK_7)  1.40068(SLS CHA160)  1.32108(SLS FRE42)  1.30679(SLS QP6)  1.24675(ULS EQU9)  1.3658(EQK EQU7)
μsl,min:     80.1776(ULS_CR96)  96.9745(EQK_7)  86.0386(SLS CHA160)  >100(SLS FRE1)      >100(SLS QP1)     85.1282(ULS EQU9)  89.2418(EQK EQU7)
min compr.:  1(ULS1)            1(EQK_1)        1(SLS CHA1)          1(SLS FRE1)         1(SLS QP1)        1(ULS EQU1)        1(EQK EQU1)
μ_overturn,min: 25.185(ULS_CR96) 25.1329(EQK_15) 27.2732(SLS CHA160) 52.9014(SLS FRE42)  66.3686(SLS QP6)  22.5841(ULS EQU9) 24.0298(EQK EQU15)
global: ex_max=0.00983574m(EQK_20) ex_min=3.2885e-5m(ULS_CR138) ey_max=0.0885579m(ULS EQU9) ey_min=0.00105179m(SLS CHA33)
materials: fyd=434.783 fck=37.35 fctm=3.35208 N/mm2
design: Mx,SLU=My,SLU=1533.25kNm Asx=Asy=56.787cm2 (min 64cm2 governs) Nx=Ny=33 Φx=Φy=20mm Φmin=14mm
        TOP="17φ20" BOTT="33φ20" As,prov=10367.3mm2
SLS stresses: σc,QP=3.35865 σs,QP=138.361 σc,CHA=3.59996 σs,CHA=148.301 σs,FREQ=139.873 N/mm2 — all < limits (16.8075/220/22.41/400/240) → PASS
```
