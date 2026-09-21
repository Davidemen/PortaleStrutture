# ca-pilastri — Spec

Workbooks: `pilastri-rettangolari.xlsx` (sheets `Pilastri rettangolari`, `Tabelle`) and
`pilastri-circolari.xlsx` (sheets `Pilastri circolari`, `Tabelle`). Two tools sharing the `Tabelle`
material-lookup sheet and nearly identical calc logic; circular differs mainly in geometry (D vs L1×L2)
and an equivalent-square trick for shear. **MRd is a user input in both tools** (H24, unlocked) — the
sheet does NOT compute an M-N interaction domain; it only checks a user-supplied MRd against demand.
Columns `GJ:GU` (rect) / `DG:EJ` (circ) are rebar-layout/CAD-coordinate helper tables (bar drawing
positions around the perimeter) — irrelevant to the engineering result, excluded below.

## Shared: `Tabelle` sheet lookups
- `Tabelle!M45:P49` — steel class → M=name, N=fyk[MPa], O=ftk[MPa], P=σamm[MPa]. Key: exact text
  (B450C, FeB22k, FeB32k, FeB38k, FeB44k). Exact-match VLOOKUP, no interpolation.
- `Tabelle!M34:O41` — concrete class → M=name (C20/25…C50/60), N=Rck[MPa], O=fck=Rck·0.83[MPa].
  Exact-match VLOOKUP.
- γs=1.15, γc=1.5 hardcoded per **NTC2018 Tab.4.1.V**.
- fcd = 0.85·fck/γc (**NTC2018 §4.1.2.1.1.1**, αcc=0.85 hardcoded).
- fyd = fyk/γs (**NTC2018 §4.1.2.1.1.3**).

---
## Tool: pilastri-rettangolari

### 1. Purpose + code refs
Design/verify a rectangular (or square) RC column in "CD B" (ductility class B) — combined
axial+bending capacity check (MRd vs MEd, given MRd as input), pure compression check, shear
(strut-and-tie, EC2 6.2.3 / **NTC2018 §4.1.2.1.3.2**), capacity-design shear ("gerarchia delle
resistenze", **NTC2018 §7.4.4.2.1** — "?" exact sub-clause), min/max reinforcement ratio
(**NTC2018 §7.4.6.2.1**, EC8 5.4.3.2.2), stirrup/confinement spacing (**NTC2018 §7.4.6.2.2**), and
slenderness (**NTC2018 §4.1.6.1.3** / EC2 5.8.3.1).

### 2. Inputs (sheet `Pilastri rettangolari`)
| cell | symbol | meaning | unit | type/range | cached |
|---|---|---|---|---|---|
| H5 | L1 | lato 1 (base) | mm | number* | 400 |
| H6 | L2 | lato 2 (altezza) | mm | number* | 400 |
| H7 | H | altezza netta pilastro | mm | number* | 3500 |
| H8 | — | tipo acciaio | — | enum $DA$7:$DA$11 {B450C,FeB22k,FeB32k,FeB38k,FeB44k} | "B450C" |
| H9 | — | tipo cls | — | enum $CX$7:$CX$14 {C20/25…C50/60} | "C25/30" |
| H10 | Ned | azione assiale | kN | number* | 1200 |
| H11 | Ved | taglio agente | kN | number* | 150 |
| H12 | Med | momento agente | kNm | number* | 80 |
| H13 | c | copriferro (asse barra) | mm | number* | 50 |
| H14 | — | numero ferri verticali (totale) | — | int* | 8 |
| H15 | Ø | diametro ferri verticali | mm | number* | 16 |
| H16 | Ø | diametro staffe | mm | number* | 10 |
| H17 | p | passo staffe | mm | number* | 150 |
| H24 | MRd | momento resistente (**external input**, e.g. from an M-N domain tool) | kNm | number* | 160 |
| Z27 | — | numero ferri lungo lato corto L1 | — | int* | 3 |

### 3. Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| Z17 | VRd | taglio resistente | kN | 322.696 |
| Y18 | — | verifica taglio (VRd>Ved) | — | "OK" |
| Y20 | — | verifica gerarchia resistenze (VRd>MRd/H) | — | "OK" |
| J23(H23) | rs | As/Ac + range check | — | 0.0100531 / "OK" |
| G25 | — | verifica a flessione | — | "Mrd > Med -> OK" |
| K25 | — | tasso sfruttamento flessione | % | 50 |
| G27 | — | verifica a compressione (NRcd>Ned) | — | "Nrd > Ned -> OK" |
| K27 | — | tasso sfruttamento compressione | % | 53.15 |
| J57 | — | verifica snellezza (λ<λlim) | — | "OK" (see §7 bug) |
| K14/K15/K16/K17 | — | detailing warnings (passo, Ø ferri, Ø staffe, passo staffe) | — | "" (all pass) |
| J60/L61/J62/J63/J64 | — | detailing min/max checks (Ø long., interasse long., As,min, Ø staffe, interasse staffe) | — | all "OK" |

### 4. Calculation steps (dependency order)
1. Z5=γs=1.15, Z6=γc=1.5 (hardcoded).
2. Z7 = VLOOKUP(H8,Tabelle!M45:P49,3) = ftk [MPa] → 540 (labelled "fyk" — cosmetic mislabel only, unused downstream).
3. Z8 = fyd = VLOOKUP(H8,Tabelle!M45:P49,2)/Z5 = fyk/γs → 391.304 MPa.
4. Z9 = fcd = VLOOKUP(H9,Tabelle!M34:O41,3)·0.85/Z6 → 14.11 MPa.
5. Z13 = cotθ = CLAMP(CX43, 1, 2.5) → 2.5 (**circular ref**, resolved by Excel iterative calc; see §7).
6. H18 = e_min = MAX(20, 0.05·MAX(H5,H6)) [mm] → 20.
7. H19 = MEd,ecc = Ned·e_min/1000 [kNm] → 24.
8. H20 = MEd = MAX(H19,H12) [kNm] → 80.
9. H21 = Ac = H5·H6 [mm²] → 160000.
10. H22 = As = (π·H15²/4)·H14 [mm²] → 1608.5.
11. H23 = rs = As/Ac → 0.0100531; check OK if rs<0.04 AND rs>MAX(DA25:DA27) (min-steel envelope, step 20-22).
12. CX24 = passo ferri verticali = 2π·((H5/2)−H13)/H14 [mm] → 117.81 (**circular-perimeter formula reused on a rectangular section — suspected bug, §7**); K14 flags if CX24>300.
13. CX29 = a = RADIANS(90°) [rad] (stirrup angle, Z14=90 hardcoded).
14. CX30 = z = 0.9·(H6−H13) [mm] → 315 (internal lever arm).
15. CX31 = σcp = Ned·1000/Ac [MPa] → 7.5.
16. CX32..CX35 = ac candidates: 1 (tension) / 1+σcp/fcd / 1.25 / 2.5·(1−σcp/fcd).
17. CX36,CX37 = 0.25·fcd, 0.5·fcd (thresholds).
18. CX38 = ac = IF(H7<0,CX32,IF(σcp<0.25fcd,CX33,IF(σcp<0.5fcd,CX34,CX35))) → 1.17116. (**`H7<0` should be `σcp<0` — H7 is the column height, always >0, so the "tension" branch is dead code; §7.**)
19. CX39=cotα=1/TAN(CX29)≈0 (α=90°). CX40=cotθ=Z13. CX41=cotθ².
20. CX42 = sin²θ = (π·H16²/4·fyd·2)/(H5·H17·(ac·0.5·fcd)) → 0.123986. CX43 = cotθ = √((1−sin²θ)/sin²θ) → feeds Z13 (step 5).
21. Z15 = VRdc = z·H5·ac·0.5·fcd·(cotα+cotθ)/(1+cotθ²)/1000 [kN] → 358.991 (EC2 6.2.3 strut side).
22. Z16 = VRds = z·(π·H16²/4·2)/H17·fyd·(cotα+cotθ)·sinα/1000 [kN] → 322.696 (stirrup side; ×2 = two legs).
23. Z17 = VRd = MIN(Z15,Z16) → 322.696. Y18 = IF(VRd>Ved,"OK","NO").
24. Y20 = IF(VRd>(H24/(H7/1000)),"OK","NO") → capacity-design shear demand = MRd/H[m] (**missing ×2 for two plastic hinges? "?"**, §7).
25. G25 = IF(H24>H20,"Mrd > Med -> OK","...NO"). K25 = ROUND(H20/H24·100,2) %.
26. H26 = NRcd = Ac·fcd/1000 [kN] → 2257.6 (pure-concrete capacity, no steel term).
27. G27 = IF(H26>Ned,"Nrd > Ned -> OK","...NO"). K27 = ROUND(Ned/H26·100,2) %.
28. CX25=0.003·Ac, CX26=0.1·Ned·1000/fyd, CX27=0.01·Ac [mm²]; DA25..27 = each /Ac → min-ratio envelope used in step 11.
29. Z24(row27) = hcr = IF(H<3·L1, H, MAX(L1,H/6,450)) [mm] → critical (confined) zone height, 583.333.
30. Z25(row28) = passo max staffe confinate = MIN(CX45:CX47) → 128 (candidates: L1/2=200, 175 hardcoded, 8·Ø_long=128).
31. J53 = λlim = 25/√(Ned/(Ac·fcd)) → 1084.36 (**Ned not ×1000: units mismatch, see §7 bug**); constant 25≈20·A·B·C simplified (A=0.7,B=1.1 typical; "?").
32. J55 = i = √[((min(L1,L2)−2c)³·max(L1,L2)−2c)/12) / ((L1−2c)(L2−2c))] [mm] → 86.6 (radius of gyration computed on **net/core dimensions, not gross Ac** — "?").
33. J54=l0=3000 mm (hardcoded free length, independent of H7). J56=λ=l0/i → 34.641. J57=IF(λ<λlim,"OK","NO").
34. Detailing (rows 60-64): Ø_long,min=12 vs H15; interasse_max=300 vs CX24 (step 12); As,min=MIN(CX25,CX26) vs H22; Ø_staffe,min=MAX(CX22,CX23) [CX22=H15/4, CX23 hardcoded from Tabelle "zone confinate" block] vs H16; interasse_max staffe=MIN(CX20,CX21) [CX20=12·H15, CX21=250 hardcoded] vs H17.

### 5. Lookup tables
- `Tabelle!M45:P49` — steel class, key=H8 text, exact match.
- `Tabelle!M34:O41` — concrete class, key=H9 text, exact match.
- `CX45:CX47` (local, rect sheet) — candidates for confined-zone stirrup spacing: L1/2, 175mm, 8·Ø_long; rule = MIN (most restrictive).
- `CX20:CX23` (local) — min/max stirrup Ø and spacing candidates; rule = MIN/MAX as appropriate.

### 6. Hardcoded constants
- γs=1.15, γc=1.5 (Tab.4.1.V); αcc=0.85 (fcd formula).
- Stirrup inclination α=90° (Z14).
- ν1 reduction factor =0.5 baked into VRdc formula (ac·0.5·fcd), not the EC2 ν=0.6(1−fck/250) formula.
- cotθ clamp [1, 2.5] (EC2 6.2.3(2)).
- 175mm hardcoded confined-zone spacing candidate (row 46, "?" source — NTC min stirrup spacing in critical zone).
- Free length l0=3000mm hardcoded (row 54), independent of actual H7 input — likely a leftover default, not linked.
- λlim coefficient "25" (row 53) — undocumented provenance, "?".
- Ac minimum-steel envelope multipliers 0.003, 0.1·(Ned/fyd), 0.01 (rows 25-27) — EC8/NTC7.4.6.2.1 typical 1% min, 4% max reinforcement; the 0.1·Ned/fyd term is the NTC "0.10·Nd/fyd" minimum-axial-based steel rule.

### 7. Suspected bugs / fragile spots
1. **λlim units bug (HIGH, confirmed)**: J53 = `25/SQRT(H10/((H5*H6)*Z9))` uses H10 (Ned) in kN directly against Ac·fcd in N (mm²·MPa=N) — missing ×1000. Cached 1084.36 exactly reproduces 25/SQRT(1200/(160000·14.11)); with correct ×1000 it would be 25/SQRT(1,200,000/2,257,600)=34.3 — a ~31× overstatement of λlim, making the slenderness check almost never fail (non-conservative). Compare consistent ×1000 use elsewhere (CX31 σcp, H26 NRcd). Confirmed identical bug in circular sheet (J60).
2. **Circular-perimeter formula in rectangular sheet (MEDIUM)**: CX24 "passo ferri verticali" = `2*PI()*((H5/2)-H13)/H14` — this is the circular-column bar-spacing formula (circumference/n), copy-pasted unchanged into the rectangular sheet where it's used to check bar spacing (K14, and detailing check row 61). For non-square rectangles this misrepresents actual bar spacing (real spacing is computed correctly elsewhere via GU6/GU7 in the drawing-helper table, but the *check* cell CX24 does not use it).
3. **Dead branch in ac selector (LOW)**: CX38 = `IF(H7<0,CX32,...)` — H7 is column clear height (always >0); the intended condition was almost certainly `CX31<0` (σcp, i.e., net tension), making the "ac=1 under tension" branch unreachable.
4. **Circular reference for cotθ (fragile)**: Z13 depends on CX43 which depends on CX40=Z13 — requires Excel iterative calculation enabled; a from-scratch reimplementation must solve this as a fixed point (or replicate the clamp-then-recompute-once pattern) rather than a plain formula graph.
5. **Capacity-design shear demand (uncertain, "?")**: Y20 uses `MRd/(H/1000)` (single MRd over full clear height) rather than `2·MRd/H` (sum of top+bottom resisting moments, standard capacity-design form) — may be intentional (symmetric single-curvature assumption) but not verifiable from the sheet alone.
6. **Radius of gyration on net section (uncertain, "?")**: J55 uses dimensions reduced by 2·cover in both numerator and denominator instead of gross Ac — nonstandard; same pattern in circular sheet (J62) so likely deliberate but unverified against code.
7. **l0=3000mm hardcoded**, unrelated to H7 input — buckling length not actually derived from the input clear height; flag as a likely template leftover requiring a real user input in the reimplementation.

### 8. Golden test case
```
inputs: L1=400 L2=400 H=3500 acciaio=B450C cls=C25/30 Ned=1200 Ved=150 Med=80 c=50 nFerri=8 ØFerri=16 Østaffe=10 pStaffe=150 MRd=160
fyd=391.304 fcd=14.11 z=315 cotTheta=2.5 sigmaCp=7.5 ac=1.17116
Ac=160000 As=1608.5 rs=0.0100531(OK) eMin=20 MedEcc=24 MedCalc=80
VRdc=358.991 VRds=322.696 VRd=322.696 tagliOK=OK gerarchiaOK=OK
MRd_vs_MEd="Mrd > Med -> OK"(tasso 50%) NRcd=2257.6 compressioneOK="Nrd > Ned -> OK"(tasso 53.15%)
lambdaLim=1084.36(buggy) i=86.6025 l0=3000 lambda=34.641 snellezzaOK=OK
```

---
## Tool: pilastri-circolari

### 1. Purpose + code refs
Same checks as rectangular tool (§ above), for a circular section, plus an equivalent-square
transform for the shear formulas. Same code refs.

### 2. Inputs (sheet `Pilastri circolari`) — deltas from rectangular
| cell | symbol | meaning | unit | type/range | cached |
|---|---|---|---|---|---|
| H5 | D | diametro pilastro | mm | number* | 400 |
| H7 | H | altezza netta | mm | number* | 5000 |
| H8/H9/H10/H11/H12/H13/H14/H15/H16/H17/H24 | (same roles as rect) | | | | 400/25/16/10/150/B450C/C25/30/1200/150/80/50/25/16/10/150/160 |

(No H6 — single diameter; H14=25 vertical bars, arranged around perimeter via the DT/DW/DX/DY
helper table, out of scope.)

### 3. Outputs — same cell roles as rectangular
| cell | symbol | cached |
|---|---|---|
| Z17 VRd | kN | 222.666 |
| Y18 verifica taglio | | "OK" |
| Y20 gerarchia | | "OK" |
| H23 rs | | 0.04 → **J23="NO"** (fails: rs not > max min-ratio envelope; see golden case, cached example is a failing case) |
| G25/K25 flessione | | "Mrd > Med -> OK" / 50% |
| G27/K27 compressione | | "Nrd > Ned -> OK" / 67.68% |
| J64 snellezza | | "OK" (same λlim bug) |
| J60-J71 detailing | | all "OK" |

### 4. Calculation steps — deltas from rectangular (same numbering intent)
1-4. Same γs, γc, fyd, fcd lookups (identical formulas).
5. Z13 = cotθ clamp(CX43,1,2.5) → 1.98287 (same iterative pattern).
6. H18 = e_min = MAX(20, 0.05·D) → 20 (single dimension, no MAX(H5,H6)).
9. H21 = Ac = IF(G4="rettangolare", H5·H6, π·H5²/4) → 125664 mm². **G4 is always "Circolare" in this sheet (hardcoded label, not the rect sheet's), so the "rettangolare" branch is permanently dead — harmless but confirms this formula was copy-pasted from a shared template (§7).**
   CX17 = "base fittizia" L1 = √Ac → 354.491 mm (equivalent square side). CX18 = "altezza fittizia" L2 = CX17 (same value) — used in place of H5,H6 in the shear formulas (steps 14-22 of rect tool), i.e. VRdc/VRds computed on an equivalent square of the same area as the circle, not on the true circular section shear width.
10. H22 = As = (π·H15²/4)·H14 → 5026.55 mm² (25 bars here vs 8 in rect example).
11. H23 = rs = As/Ac → 0.04 → check fails (0.04 is not <0.04 strictly) → **NO** in the cached example (this is expected code behavior at the 4% ceiling, not a bug).
21-22. Z15/Z16 (VRdc/VRds) use CX17 in place of H5/H6·H5 term (fictitious square width) → 222.666 / 222.666 kN.
27,32. Ac formula for hcr(Z24 row27), slenderness λlim (row60, J60=`25/SQRT(H10/((H5^2*PI()/4)*Z9))` → 960.988) — **same missing-×1000 bug as rectangular §7.1**, confirmed by recompute: 1200/(125664·14.11)=0.000677→√=0.02602→25/=960.9 ✓ matches; correct value would be 25/√(1,200,000/1,773,110)=25/0.823=30.4.
33. J62 = i = √[(π·(D−2c)⁴/64)/(π·(D−2c)²/4)] = (D−2c)/4 [mm] → 75 (core diameter, same net-section pattern as rect §7.6).
34. Detailing checks identical structure (rows 67-71), thresholds recomputed from CX22/23 (Ø staffe) and CX20/21 (passo staffe) using CX17 in place of H5.

### 5-6. Lookup tables / constants
Same as rectangular tool §5-6, plus: equivalent-square side = √Ac (CX17/CX18), used throughout shear
block in place of the two rectangular side lengths.

### 7. Suspected bugs / fragile spots
1. **λlim units bug** — identical defect to rectangular §7.1, confirmed in J60/J63 (cached 960.988 reproduces the no-×1000 formula).
2. **Dead "rettangolare" branch** in H21 (Ac) — copy-paste leftover from a shared template; harmless here since G4 is fixed text "Circolare", but a reimplementation should just hardcode π·D²/4.
3. **Equivalent-square shear approximation**: using a square of side √Ac for VRdc/VRds is a simplification of the circular-section shear check; not independently verified against a specific NTC/EC2 circular-column clause ("?").
4. Same circular-reference cotθ pattern as rectangular tool (§7.4 there).

### 8. Golden test case
```
inputs: D=400 H=5000 acciaio=B450C cls=C25/30 Ned=1200 Ved=150 Med=80 c=50 nFerri=25 ØFerri=16 Østaffe=10 pStaffe=150 MRd=160
fyd=391.304 fcd=14.11 Ac=125664 As=5026.55 rs=0.04(NO) L1fittizio=354.491
VRdc=222.666 VRds=222.666 VRd=222.666 tagliOK=OK gerarchiaOK=OK
MRd_vs_MEd="Mrd > Med -> OK"(tasso 50%) NRcd=1773.11 compressioneOK="Nrd > Ned -> OK"(tasso 67.68%)
lambdaLim=960.988(buggy) i=75 l0=3000 lambda=40 snellezzaOK=OK
```
