# Muro di Sostegno a Mensola (Cantilever Retaining Wall) — NTC 2018

Source: workbook sheet "Tratto A" (golden case). Sheets B–E share the identical formula
set with different geometry/soil inputs (4 extra golden cases). Unit = SI (m, kN, kNm, kPa, °)
unless noted; angles stored in ° (col I/H) are converted to rad via `RADIANS()` before use.

## Tratto A vs B — soil-category parameterization (required)
`I18` (SS, sottosuolo coeff.) and the adjacent `I19` (ST) differ in *how* they are produced,
not in the physics:
- **Tratto B**: `I18={=IF((1.7-0.6*ag*F0)<1,1,IF((1.7-0.6*ag*F0)>1.5,1.5,1.7-0.6*ag*F0))}` —
  this is exactly NTC Table 3.2.V for **category C**, computed live from `ag`(I15)/`F0`(I16).
- **Tratto A**: `I18` is instead a **hardcoded user input** (`I*=1.5`), and the formula that
  would compute it is parked one row down in `F18`/`F19` as a side "what-if" check: `F18` uses
  the **category E** coefficients (`2-1.1·ag·F0`, clamp [1,1.6]), `F19` uses the **category D**
  coefficients (`2.4-1.5·ag·F0`, clamp [0.9,1.8]) — mislabeled under the "ST" row. Row-3 comment
  explains: *"già verificato che qualora il terreno dovesse risultare D (Ss=1.8) o E (Ss=1.6)
  non cambia nulla a livello di risultati"* — i.e. the engineer manually pre-checked that using
  the worse-case D or E soil category doesn't change the verification outcome, then froze `I18`
  at the category-C value (1.5) as a fixed input.
- **Tool parameterization**: expose `SS(category, ag, F0)` as one function implementing NTC
  Table 3.2.V for all 5 categories (A/B/C/D/E, formulas/clamps below), driven by the `Classe`
  dropdown (A,B,C,D,E), and always compute — never hardcode. `ST` (topographic) is NOT
  ag/F0-dependent in the code (NTC Table 3.2.VI: T1=1.0, T2/T3=1.2, T4=1.4); Tratto A's F19 use
  of an SS-shaped formula there is spreadsheet cruft, not a real ST formula (see bugs §7).

NTC 3.2.V (SS, clamped, x = ag·F0):
| Category | formula | clamp |
|---|---|---|
| A | 1.00 | fixed |
| B | 1.40 − 0.40x | [1.00, 1.20] |
| C | 1.70 − 0.60x | [1.00, 1.50] |
| D | 2.40 − 1.50x | [0.90, 1.80] |
| E | 2.00 − 1.10x | [1.00, 1.60] |

## Tool decomposition (interconnected, share one geometry/soil input block)
1. `spinta-terra-statica-sismica` — active earth-pressure coeff. Ka/Kae (Coulomb / Mononobe-Okabe) + driving forces, 6 static + 2 seismic load combos. **Upstream for all others.**
2. `verifica-ribaltamento-scorrimento` — overturning & sliding checks, static+seismic.
3. `verifica-pressioni-terreno` — foundation bearing pressure distribution + eccentricity check.
4. `armatura-paramento` — vertical stem rebar (As).
5. `armatura-fondazione-valle` — toe footing rebar.
6. `armatura-fondazione-monte` — heel footing rebar.

---
## Shared inputs (rows 4–39; feed all 6 tools)
| cell | symbol | meaning | unit | type | example |
|---|---|---|---|---|---|
| I4 | γterr | terrain unit weight (sat.), `=R10*10` (t/m³→kN/m³, g≈10) | kN/m3 | formula, locked to geo-table PPD3 (col R) | 19.7 |
| I5 | γ'terr | terrain unit weight (dry), `=R11*10` | kN/m3 | formula | 15.6 |
| I6 | φ | internal friction angle, `=R7` (PPD3 "effective" angle) | ° | formula | 30.69 |
| I7 | δ | wall-soil friction angle | ° | input | 0 |
| I8 | β | backfill slope | ° | input | 0 |
| I9 | ψ | inner wall face inclination (90=vertical) | ° | input | 90 |
| I10 | ω | foundation base inclination | ° | input | 0 |
| I15 | ag | seismic ground accel. (/g) | - | input | 0.136 |
| I16 | F0 | spectrum amplification factor | - | input | 2.419 |
| I17 | Classe | soil category enum {A,B,C,D,E} | - | dropdown | "C" |
| I18 | SS | subsoil coefficient | - | see above | 1.5 |
| I19 | ST | topographic coefficient enum {T1..T4}→{1.0,1.2,1.2,1.4} | - | input | 1 |
| I20 | S | `=SS*ST` | - | formula | 1.5 |
| I21 | βm | seismic reduction factor (NTC 7.11.3.5.2, wall-type dependent) | - | input | 0.24 |
| I22 | γE(?) | seismic multiplier on thrust (unit label "[kN/m3]" is wrong, see §7) | - | input | 1 |
| I25 | γcls | concrete unit weight | kN/m3 | input | 25 |
| I26 | s_base | stem thickness at base | m | input | 0.49 |
| I27 | s_top | stem thickness at top | m | input | 0.25 |
| I28 | s_fond | footing thickness | m | input | 0.3 |
| I29 | h_muro | stem height | m | input | 2.4 |
| I30 | H_muro | `=I29+I28` total wall height | m | formula | 2.7 |
| I31 | B_valle | toe width (downhill) | m | input | 0.26 |
| I32 | B_monte | heel width (uphill) | m | input | 1.15 |
| I33 | B_fond | `=I31+I26+I32` total footing width | m | formula | 1.9 |
| I34 | A_muro | `=I33*I28+I29*(I26+I27)*0.5` wall+footing area | m2 | formula | 1.458 |
| I35 | x_muro | wall centroid from overturning pole (toe front), split rect+2 triangles/formula in row33 | m | formula | 0.661523 |
| I38 | q | surcharge at top of backfill | kN/m2 | input | 2 |
| I11 | A_terr | `=I32*I29` backfill wedge area | m2 | formula | 2.76 |
| I12,I39 | x_terr,x_Sv | `=I31+I26+I32/2` backfill/surcharge centroid from pole | m | formula | 1.325 |

Geo lookup table `M4:S11` (3 boreholes PPD1/PPD2/PPD3, cols P/Q/R): rows = densità relativa,
Edrained, φ'eff, φ'char, φ'design, γsat, γdry. I4/I5/I6 hand-pick column **R (PPD3)** — engineer's
manual choice of the governing borehole, not a formula-selected min/max. Tool should expose this
as a plain 3-column reference table the user picks from (or just take γ/φ as direct inputs).

---
## Tool 1 — `spinta-terra-statica-sismica`
Purpose: Coulomb active-thrust coeff (static, NTC 6.5.3.1.1/EC7) and Mononobe-Okabe (seismic,
NTC/EC8 §7.11.6.2.1) for 6 static combos (rows 45–50) + 2 seismic combos (rows 80–81).
Inputs: φ,δ,β,ψ,ω (I6–I10), γ's (I4,I25), areas/centroids (I11,I12,I34,I35), ag/F0/S/βm/γE (I15,16,20,21,22), partial factors γG,muro(D)/γφ,terr(J)/γG,terr(N) per combo (table below).
Outputs: per row r: `Wmuro`(G), `Mmuro`(I), `Wterr`(Q), `Mterr`(S), Coulomb ratio terms U,V,W,X; seismic rows add `kh`(Y),`kv`(Z),`θ`(AA).

Static combos (rows 45–50), γG,muro / γφ,terr / γG,terr per combo:
| row | combo | γG,muro (D) | γφ,terr (J) | γG,terr (N) |
|---|---|---|---|---|
| 45 | STR_1 (A1-M1-R1) | 1.3 | 1 | 1.3 |
| 46 | STR_2 (A1-M1-R1) | 1 | 1 | 1 |
| 47 | GEO_1 (A2-M2-R2) | 1 | 1.25 | 1.1 |
| 48 | GEO_2 (A2-M2-R2) | 1 | 1.25 | 1.1 |
| 49 | EQU_1 (M2-R2) | 0.9 | 1.25 | 1.1 |
| 50 | EQU_2 (M2-R2) | 0.9 | 1.25 | 1.1 |
(rows 47/49 are duplicates of 48/50 in cached values — see §7 bug #1)

Steps (row r):
1. `φd[r] = RADIANS(I6)/γφ,terr[r]` , `δd[r] = ATAN(TAN(RADIANS(I7)))/γφ,terr[r]`
2. `Wmuro[r]=γcls·Amuro·γG,muro[r]` ; `Mmuro[r]=Wmuro·xmuro`
3. `Wterr[r]=γterr·Aterr·γG,terr[r]` ; `Mterr[r]=Wterr·xterr`
4. Coulomb terms: `U=sin²(ψ+φd)`, `V=sin²ψ·sin(ψ-δd)`, `W=sin(φd+δd)·sin(φd-β)`, `X=sin(ψ-δd)·sin(ψ+β)`
5. `Ka[r] = IF(β≤φd, U/(V·(1+√(W/X))²), U/V)` (row 56/57/…/61, `B` col)
6. Seismic rows (80,81), γE=I22 or D≡0.6(?): `Y=kh=S·ag·βm`, `Z80=kv=+0.5·kh`, `Z81=kv=−0.5·kh`, `AA=θ=ATAN(kh/(1+kv))`
7. Seismic Coulomb→M-O: `U'=sin²(ψ+φd−θ)`, `V'=cos θ·sin²ψ·sin(ψ−δd−θ)`, `W'=sin(φd+δd)·sin(φd−β−θ)`, `X'=sin(ψ−δd−θ)·sin(ψ+β)`, `Kae = U'/(V'(1+√(W'/X'))²)` (same β≤(φd−θ) branch test).
8. Seismic forces get extra `(1+kv)·γE` factor: `SH.terr[r] = 0.5·γG,terr·γterr·H²·cos δd·Kae·(1+kv)·γE`.

---
## Tool 2 — `verifica-ribaltamento-scorrimento` (rows 54–61 static, 85–88 seismic)
Purpose: overturning (ribaltamento) and base sliding (scorrimento) checks, NTC 6.5.3.1.2 /
EC7 §6.5.3/6.5.4. `OR≥1` required.
Inputs (per combo row, from Tool 1): Ka/Kae(B), γQ(C, input: 1.5 static A1 / 0 others / 0.6 seismic), q, Wmuro, Wterr, H(I30).
Steps:
1. `Dq[r]=q·γQ[r]` (surcharge design value)
2. `SH.q=Ka·Dq·H·cos δd` ; `SH.terr=0.5·γG,terr·γterr·H²·cos δd·Ka` (static, no (1+kv)); seismic rows add `·(1+kv)·γE` and use `Kae`.
3. `SV.q,SV.terr` = same ×`sin δd` (=0 here since δ=0)
4. `MRIB[r] = SH.q·H/2 + SH.terr·(H/3 static | H/2 seismic)` (lever arm changes: seismic uses H/2, static H/3 — Mononobe-Okabe applies resultant at higher point per code note)
5. `MSTAB[r] = MV,q + Mterr[r] + Mmuro[r]`  (stabilizing moment)
6. **Output** `OR[r] = MSTAB/MRIB` — pass if ≥1 (γR safety factor already embedded via partial factors).
7. `Ntot[r]=Wmuro+Wterr+SV.q+SV.terr` ; `Rtot[r]=SH.q+SH.terr`
8. **Output** `OS[r] = [tanφd·(Ntot·cosω+Rtot·sinω)] / [−Ntot·sinω+Rtot·cosω]` — sliding safety factor, pass if ≥1.
Static example (row56, STR_1): OR=4.061, OS=2.131. Seismic example (row87, SISMA.1): OR=2.082, OS=1.212.

---
## Tool 3 — `verifica-pressioni-terreno` (rows 66–72 static, 92–95 seismic)
Purpose: eccentricity + Meyerhof-type trapezoid/triangle bearing pressure at base, EC7 Annex D / NTC 6.4.2.1.
Inputs: B_fond/2, Wmuro/Mmuro(Tool1), Wterr/Mterr(Tool1), Ntot/SV(Tool2).
Steps (per combo row r):
1. `e_muro=B/2−xmuro` ; `M_muro=Wmuro·e_muro` (similarly `e_terr`, `M_terr`, `e_Sv`,`M_Sv` for surcharge+vert.thrust)
2. `Mtot=MRIB(from Tool2 stabilizing calc, row56/87 M col)+M_muro+M_terr+M_Sv` ; `Ntot` (from Tool2)
3. `e = Mtot/Ntot`
4. **Output** flag: `"<B/6"` / `">B/6"` — governs whether footing is fully compressed.
5. `B* = IF(|e|≤B/6, 0, 3·(B/2−|e|))` (effective width when resultant outside kern)
6. **Outputs** `pvalle,pmonte`: if B*=0 → trapezoid `N/B ± 6M/B²` (both edges); if e<0 & B*>0 → triangular `2N/B*` at one edge, 0 at other. Pass if pvalle,pmonte ≤ σ_amm (allowable bearing — not computed on this sheet, external check).
Static example (row67, STR_1): e=0.152m (<B/6=0.317), pvalle=91.96 kPa, pmonte=32.32 kPa.
Seismic example (row94, SISMA.1): e=0.400m (>B/6), B*=1.650m, pvalle=110.07 kPa, pmonte=0.

---
## Tool 4 — `armatura-paramento` (rows 133–151) — NTC 4.1.2 flexure, minimum steel not checked here
Purpose: vertical rebar of stem, cantilever bending at base from SH.q+SH.terr of each combo.
Inputs: I133=I28 (s_fond), I134=I26 (s_base), I135=cover=0.06m, I136 fyk=450MPa, I137=fyd=fyk/1.15=391.3MPa (γs=1.15, NTC 4.1.2.1.1.3), I139=bar spacing=0.2m.
Steps (per combo, 6 static rows143-148 + 2 seismic 149-150):
1. `zq=H/2−s_fond` (lever arm of SH.q about stem base) ; `zterr = K(lever of SH.terr from Tool2)−s_fond`
2. `MEd = SH.q·zq + SH.terr·zterr`
3. `As.nec[cm2/m] = MEd·10⁴ / (0.9·(s_base−cover)·1000·fyd)` — 0.9 = assumed lever-arm ratio jd/d, NTC simplified flexure.
4. **Output** `As.nec = MAX(all 8 rows)` (row151) → governing combo.
5. **Output** bar callout: `CONCATENATE(1,"φ",10·CEILING(2·√(As.nec·s/π),0.2),"/",100·s)` → bar Ø[mm] rounded up to 0.2mm step from area formula `As=n·π·(Ø/2)²`, spacing in cm.
Example: As.nec=2.373 cm²/m (governs SISMA.1) → "1φ8/20".

---
## Tool 5 — `armatura-fondazione-valle` (rows 154–169), toe cantilever bending
Inputs: I154=I28,I155=I31(B_valle),I156=cover=0.06,I157=spacing=0.2; per-combo x*(=Tool3 B_valle offset, ties to I31), B*(Tool3 Q col), pvalle/E, p*(interpolated pressure at toe tip).
Steps (per combo row):
1. `p* = IF(B*=0, pmonte+(pvalle−pmonte)·(B−x*)/B, pvalle·(B*−x*)/B*)` — pressure at toe-tip abscissa x* (linear interp along trapezoid/triangle from Tool3).
2. `MEd.p.1 = IF(p*≤pvalle, p*·B_valle²/2, pvalle·B_valle²/2)` (triangular/rect area moment of the smaller pressure block)
3. `MEd.p.2 = ` remaining wedge moment (0.5·B_valle·(pvalle−p*)·(2/3)B_valle, or symmetric case) — together 1+2 = full pressure-diagram moment at toe root.
4. `MEd.fond = −γG,muro·s_fond·γcls·B_valle²/2` (toe self-weight counter-moment, uses combo's own γG,muro D column and γcls F column from Tool1 rows45-50)
5. `MEd.tot = MEd.p.1+MEd.p.2+MEd.fond`
6. **Output** `As.nec[cm2/m] = MEd.tot·10⁴/(0.9·1000·(s_fond−cover)·fyd)` ; governing = `MAX(K161:L168)` (row169, **range bug** — see §7#2) → bar callout via same CONCATENATE formula, spacing I157.
Example row167 (SISMA.1, governs): As.nec=0.387 cm²/m → "1φ4/20".

---
## Tool 6 — `armatura-fondazione-monte` (rows 172–187), heel cantilever bending
Inputs: I172=I28,I173=I32(B_monte),I174=I156,I175=I157; per-combo x**, B*(Tool3), pmonte/S, p**(interp), plus backfill weight Q(Tool1) and surcharge lever.
Steps (per combo):
1. `p** = ` linear interp of pressure at heel-root abscissa x** (mirrors Tool5 step1, using S column/pmonte).
2. `MEd.p = ` negative pressure-diagram moment under heel (sign convention: pressure resists, subtracted) — 3-branch IF matching triangular/trapezoid/partial-uplift cases.
3. `MEd.terr = Wterr[combo]·(B_monte−(B−xterr))` (backfill weight moment about heel root)
4. `MEd.SV = SV.tot[combo]·(x_Sv−x**)` (surcharge vertical component, 0 here since δ=0)
5. `MEd.fond = B_monte·γG,muro·γcls·s_fond²/2` (heel slab self-weight, note: uses `D45`-style combo weight factor cross-referenced from Tool1 row, not the local row — see §7#3)
6. `MEd.tot = MEd.terr+MEd.SV+MEd.fond+MEd.p`
7. **Output** `As.nec = MEd.tot·10⁴/(0.9·1000·(s_fond−cover)·fyd)`; governing = `MAX(M179:M186)` (row187) → bar callout, spacing I175.
Example row185 (SISMA.1, governs): As.nec=2.892 cm²/m → "1φ10/20".

---
## Hardcoded constants
| value | meaning | source |
|---|---|---|
| 1.15 | γs, steel partial factor (I137=I136/1.15) | NTC 4.1.2.1.1.3 |
| 0.9 | assumed lever-arm ratio jd/d in As.nec formulas | simplified flexure design |
| ×10 (I4,I5) | t/m³ → kN/m³ via g≈10 m/s² | unit conversion |
| 1,1.6 / 0.9,1.8 / 1,1.5 / 1,1.2 | SS clamps per category E/D/C/B (NTC 3.2.V) | NTC Tab 3.2.V |
| 0.5 (Z80/Z81 kv=±0.5·kh) | NTC 7.11.6.2.1 vertical seismic coeff. rule | NTC 7.11.6.2.1 |
| CEILING(...,0.2) | round computed bar spacing to 0.2 cm step | drafting convention |

## Lookup tables
- `M4:S11` — 3 boreholes (PPD1/PPD2/PPD3) × 7 geotech properties; **manual pick of column R**, no interpolation.
- `I17` Classe dropdown {A,B,C,D,E} → drives SS (Table 3.2.V, formulas above); not wired to I18 in Tratto A (frozen input) — **must** be wired in the tool.
- `I19` ST dropdown {T1,T2,T3,T4} → {1.0,1.2,1.2,1.4} (NTC Tab 3.2.VI) — table itself not present on sheet (ST is a raw input here); tool should embed it.

## Suspected bugs / fragile spots (verified against formulas above)
1. **Row 47 (GEO_1) is a straight duplicate of row 48 (GEO_2)** in the fill-down `D45:X50` block — CSV shows both rows use γG,muro=1, γφ,terr=1.25, γG,terr=1.1, i.e. GEO_1 and GEO_2 collapse to the same numbers (NTC 2.6.I actually defines GEO_2 with γG,terr=1.0, not 1.1); likely a copy-paste fill-down that wasn't re-parameterized per combo. Re-derive GEO_1/GEO_2 partial factors independently in the tool rather than copying Tratto A's cached values.
2. **`K169={=MAX(K161:L168)}`** spans column **L**, which has no header/data in the toe-rebar table (`As.nec` is column K only) — an accidental extra empty column in the MAX range. Harmless here (blank cells ignored by MAX) but fragile if L is ever populated; tool should just `MAX` over the real As.nec column.
3. **`I22` labeled "γE" / "Fattore importanza del sisma"** but unit shown as `[kN/m3]` (row21) — dimensionally wrong (it's a dimensionless multiplier, value 1, applied to seismic thrust `E87=...*$I$22`). Copy-paste unit label error; verify the intended code meaning (importance factor vs. some other coefficient) before reusing.
4. **`F18`/`F19` (Tratto A only)** compute NTC Table-3.2.V values for categories E and D respectively, but `F19` sits in the row labeled "Coefficiente topografico terreno (ST)" — mislabeled placement; these are dead/manual-check cells, not on the calculation path (`I18` is the real input). A tool built by pattern-matching this row layout would wrongly treat F19 as an ST formula.
5. **`I18` frozen as manual input in Tratto A** vs. **live formula in Tratto B** for the same `Classe="C"` — if `Classe` is changed in Tratto A the SS value silently goes stale. Confirms need to make the SS formula unconditionally live, driven by `Classe`, in the tool (see soil-category parameterization above).
6. **Row 56 `B` (Ka) `IF(RADIANS($I$8)<=(K45), ...)`** — the branch test compares slope angle `β` (constant across all combos) against `K45` (φd of *that specific* combo), so the same geometric β/φ branch condition is re-evaluated per row instead of once; not wrong, just redundant recomputation (minor).

## Golden test case (Tratto A, cached values)
```
inputs: γterr=19.7 γ'terr=15.6 φ=30.69° δ=0° β=0° ψ=90° ω=0°
  ag=0.136 F0=2.419 Classe=C SS=1.5 ST=1 S=1.5 βm=0.24 γE=1
  γcls=25 s_base=0.49 s_top=0.25 s_fond=0.3 h_muro=2.4 B_valle=0.26 B_monte=1.15 q=2
computed geometry: H_muro=2.7 B_fond=1.9 A_muro=1.458 x_muro=0.661523 A_terr=2.76 x_terr=1.325
tool1(STR_1,row45/56): Ka=0.324159 Wmuro=47.385 Wterr=70.6836 SH.terr=30.2597
tool2 static(row56): MRIB=30.7784 MSTAB=125.002 OR=4.06135 Ntot=118.069 OS=2.13092
tool2 seismic(row87,SISMA.1): kh=0.04896 kv=0.02448 θ=0.0477538 Kae(B87)=0.445069
  MRIB=46.1951 MSTAB=96.1554 OR=2.08151 Ntot=90.822 OS=1.21249
tool3 static(row67,STR_1): e=0.151959 (<B/6) pvalle=91.9612 pmonte=32.3216
tool3 seismic(row94,SISMA.1): e=0.399909 (>B/6) B*=1.65027 pvalle=110.069 pmonte=0
tool4(row151): As.nec=2.3726 cm2/m -> "1φ8/20"
tool5(row169): As.nec=0.387055 cm2/m -> "1φ4/20"
tool6(row187): As.nec=2.89234 cm2/m -> "1φ10/20"
```
