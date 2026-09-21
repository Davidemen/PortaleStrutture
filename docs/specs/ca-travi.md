# ca-travi — RC rectangular beam design/verification + shear w/o stirrups

Workbooks: `ca-travi` (sheets `Travi sez. rettangolare`, `Tabelle`), `ca-taglio-non-armato` (sheet `Foglio1`).
`ca-travi/Tabelle` == `ca-mensole/Tabelle` structurally (13 differing constants) → implement as ONE shared `materiali-cls-acciaio` module, reused by both units.

## Tool 0 — `materiali-cls-acciaio` (shared data/lookup module, complexity S)
Purpose: resolve concrete/steel class → design properties. NTC2008 §4.1.2.1.1 (fcd), §11.2.10.1 (fck=0.83·Rck), §4.1.2.1.1.3 (fyd).
Sheet `Tabelle`. Inputs: concrete class string (e.g. "C35/45"), steel class string (e.g. "B450C").
Tables:
- `Tabelle!M34:R41` — key=concrete class (M), Rck(N), fck=N*0.83(O), fcm=O+8(P), Ecm=22000*(P/10)^0.3(Q), fctm=0.3*fck^(2/3)(R). Exact match.
- `Tabelle!M45:P50` — key=steel class(M), fyk(N), ftk(O), σamm(P). Exact match.
Outputs: fck, fctm, ftk, fyd = fyk/γs.
Also hosts crack-width table `Tabelle!N67:R93` (see Tool 5) and cover/exposure tables (`Tabelle!X14:AA21`, `N14:R20`, `N23:R29`, `T15:U20`) — NOT used by ca-travi's two units in the given cell maps; not modeled here (used elsewhere, e.g. cover-durability tool).

## Tool 1 — `armatura-minima-massima` (complexity S)
Purpose: min/max tensile reinforcement, NTC2008 §4.1.6.1.1 (EC2 9.2.1.1).
Sheet `Travi sez. rettangolare`.
Inputs: B[H6]=600mm, H[H7]=400mm, tipo cls[H9]="C35/45", n1[H11*]=5, Ø1[H12*]=20mm, n2[H13*]=0, Ø2[H14*]=0mm.
Steps:
- `As,o [AM32]` = n1·π·Ø1²/4 + n2·π·Ø2²/4 = 1570.8 mm²
- `As,min [AM32 check]` = MAX(0.0013·B·d, 0.26·B·d·fctm/fyk) where d≈H30/AM30... **actually uses H, not d**: `Z12 = MAX(0.0013*H6*AM30, 0.26*H6*AM30*fctm/fyk)`, AM30=z=0.9*(H-c) (297) — NOT d=H-c=330. Uses lever arm z as proxy for d/effective height in min-steel formula (cell ref: `AM30`). = 238.937 mm² for H6=600,c=70.
- `Y13` = IF(As,o < As,min,"OK","NO") → "OK"
- `As,max [Z14]` = 0.04·B·H = 9600 mm²; `Y15` = IF(As,o>As,max,"OK","NO") → "OK"
- `Ast,min [Z16]` = 1.5·B (mm²/m, shear-reinf minimum ratio×1000) = 900; `Y17`=IF(passo_staffe1[H16] < Ast,min·1000/H16 ... → check vs AM33 area) "OK"
- `p,min [Z18]` = MIN(1000/3, 0.8·z[AM30]) = 237.6 mm; `Y19` = IF(p2[H18? see bug]>H16,"OK","NO")

## Tool 2 — `verifica-flessione-slu` (complexity M)
Purpose: ULS bending moment resistance, simple reinforcement rectangular stress block, NTC2008 §4.1.2.1.2.
Inputs: Med[H24*]=318 kNm, fyd, fcd, d[Z31]=H7-H10=330mm, As,o[AM32].
Steps:
- `d [Z31]` = H7 − H10 = 330 mm
- `y [Z32]` = As,o·fyd / (B·fcd) / 0.81 = 66.395 mm (0.81 = concrete rectangular-stress-block reduction factor, ≈0.8·1.0125)
- `MRd [Z33]` = As,o·fyd·(d − 0.81·y/2) /1e6 = 207.01 kNm
- `verifica [Y34]` = IF(MRd>Med,"OK","NO") → **"NO"** (cached example fails: Med 318 > MRd 207)
- `tasso di sfruttamento [Z35]` = Med/MRd = 1.536

## Tool 3 — `verifica-taglio-slu` (complexity M)
Purpose: ULS shear, variable-strut-inclination truss model, NTC2008 §4.1.2.1.3.2 / EC2 6.2.3.
Inputs: VEd[H23*]=138kN, Ø_staffe1[H15*]=12mm, passo1[H16*]=115mm, n bracci[H17]=2, d[Z31], α staffe angle[Z23*]=90°, fcd, fyd, B[H6].
Steps:
- `cotθ [Z22]` = CLAMP(AM42, 1, 2.5) → 2.5 (θ from AM29..AM42 auxiliary chain: AM41=sin²θ from stress ratio, AM42=cotθ derived — see below)
- `VRdc [Z24]` = (B·z[AM38≈0.9d]·0.5·fcd·(cotθ+cotα)/(1+cotα²))/1000, using z=AM30 not shown separately from Tool2's AM30. = 650.276 kN
- `VRds [Z25]` = (B·Ast,area/passo[AM33/H16]·fyd·(cotθ+cotα)·sinα)/1000 = 634.97 kN
- `VRd [Z26]` = MIN(VRdc,VRds) = 634.97 kN
- `verifica [Y27]` = IF(VRd>VEd,"OK","NO") → "OK"
- Auxiliary (θ chain, columns AH:AN rows 39-42): `sinα=AM29(rad)`; `cot α [AM39]`=1/tanα; `cot²θ [AM40]`=Z22²; `sin²θ [AM41]`=As,st·fyd/(B·passo·(z·0.5·fcd))=0.1347; `cotθ [AM42]`=√((1−sin²θ)/sin²θ)=2.535 → feeds back into Z22 (circular-looking but Z22 clamps AM42 which is computed independently from geometry, not from Z22 — not truly circular).

## Tool 4 — `verifica-sle-tensioni` (complexity M)
Purpose: SLS stress limitation (rara & quasi-permanente), NTC2008 §4.1.2.2.5.3, cracked-section elastic analysis, n=15 (homogenization coeff, steel/concrete Es/Ec ratio).
Inputs: Med,rara[H25*]=239kNm, Med,qp[H26*]=200kNm, As,o[AM32], B[H6], d[Z31].
Steps (rara):
- `y [Z38]` = (15·As,o/B)·(−1+√(1+2·B·d/(15·As,o))) = 126.44 mm
- `σc [Z39]` = 2·Med,rara·1e6/(B·y·(d−y/3)) = 21.89 MPa; check `Y40`=IF(σc<0.6·fck,"OK","NO") → "OK"
- `σs [Z41]` = Med,rara·1e6/(As,o·(d−y/3)) = 528.58 MPa; check `Y42`=IF(σs<**360**,"OK","NO") → "NO" — 360 is HARDCODED (see bugs §7)
(quasi-permanente, reuses y=Z38):
- `σc,qp [Z46]` = 2·Med,qp·1e6/(B·y·(d−y/3)) = 18.32 MPa; check `Y47`=IF(σc,qp<0.45·fck,"OK","NO") → "NO"
- `σs (combo-dependent) [Z53]` = IF(combinazione[Y51]="Frequente", σs[Z41], recompute from Med,qp[H26]) = 528.58 MPa

## Tool 5 — `verifica-fessurazione` (complexity M)
Purpose: simplified crack-width check, NTC2008 §4.1.2.2.4 / EC2 §7.3.4 Table.
Inputs: σs[Z53], condiz. ambientali[Y50*]="Ordinarie", combinazione[Y51*]="Frequente", sensibilità[Y52*]="Poco sensibile", classe apertura fessura[Z54*]∈{w1,w2,w3} (default "w3"), Ø max bar[MAX(H12,H14)]=20mm.
Table `Tabelle!N67:R93`: rows keyed by σs[N] descending (160…360) with per-class max bar-Ø thresholds in O(w3),P(w2),Q(w1); R=copy of N (the returned limit). Exact-match VLOOKUP against Ø (fragile, see §7).
Steps:
- `σs,limite [AI54]` = IF(Z54="w1", VLOOKUP(Ømax,Q67:R93,2,FALSE), IF(Z54="w2", VLOOKUP(Ømax,P67:R93,3,FALSE), VLOOKUP(Ømax,O67:R93,4,FALSE))) = 240 MPa (for w3, Ø=20)
- `verifica [Y55]` = IF(σs[Z53]<σs,limite,"OK","NO") → "NO" (528.58 > 240)

## Tool 6 — `dettagli-costruttivi-capacity-design` (complexity M)
Purpose: NTC2008 cap.7 ductility-class detailing + capacity-design shear check, §7.4.6.2.2 / §7.4.4.
Inputs: classe duttilità[J58*/J77*]∈{CDA,CDB}, H7, Ø_staffe[H15,H18], Ø_barre[H12,H14], MRc[K78*]=350kNm, MRb[K79]=Z33(Tool2 output)=207.01kNm, Lt[K80*]=8m.
Steps:
- `Lcr [K59]` = IF(CD="CDA", 1.5·H7, H7) = 400 mm
- `p,max zona critica [K60]` = IF(CD="CDA", MIN(H7/4, 24·min(Østaffe), 175, 6·min(Øbarre)), MIN(H7/4, 24·min(Østaffe), 225, 8·min(Øbarre))) = 0 mm (degenerate: min(Østaffe)=MIN(H15,H18)=MIN(12,0)=0 → forces p,max=0; see bug §7)
- `L ancoraggio gancio staffa [K62]` = 10·MAX(Ø_staffe1,Ø_staffe2) = 120 mm
- `VEd,max [K81]` = IF(classe[J77]="cdb",1,1.2)·MRb·MIN(1,MRc/MRb) = 207.01 kN (capacity-design amplification of beam moment capacity, capped at column capacity ratio)
- `verifica [J82]` = IF(VEd,max<VRd[Z26 from Tool3],"OK","NO") → "OK"

## Tool 7 — `taglio-non-armato` (complexity M, separate workbook `ca-taglio-non-armato`)
Purpose: shear resistance without transverse reinforcement, NTC2018 §4.1.2.3.5.1.
Sheet `Foglio1`. Inputs: Rck[B2*]=35MPa, h[B7*]=500mm, c[B8*]=50mm, bw[B9*]=1000mm, Asl[B11*]=1005mm², NEd[B12*]=0kN.
Steps:
- `fck [B3]` = Rck·0.83 = 29.05 MPa
- `fcd [B4]` = fck·0.85/γc[B5=1.5] = 16.462 MPa
- `d [B10]` = h−c = 450 mm
- `σcp [B13]` = MIN(NEd·1000/(bw·d), 0.2·fcd) = 0 MPa
- `k [B15]` = MIN(1+√(200/d), 2) = 1.667 (dimensionless, size effect factor, d in mm)
- `vmin [B16]` = 0.035·k^1.5·√fck = 0.4059
- `ρl [B17]` = Asl/(bw·d) = 0.002233 (capped implicitly ≤0.02 by spec but NOT capped in sheet — see bug)
- `VRd,1 [B19]` = ((0.18·k·(100·ρl·fck)^(1/3)/γc + 0.15·σcp)·bw·d)/1000 = 167.858 kN
- `VRd,2 [B20]` = ((vmin + 0.15·σcp)·bw·d)/1000 = 182.653 kN
- `VRd [B21]` = MAX(VRd,1, VRd,2) = 182.653 kN

## Shared data
- `Tabelle!M34:R41` concrete class table (Rck→fck/fcm/Ecm/fctm), key col M.
- `Tabelle!M45:P50` steel class table (fyk/ftk/σamm), key col M.
- `Tabelle!N67:R93` crack-width σs-limit vs bar-Ø table (3 classes w1/w2/w3), fill-down; raw values in `build/data/ca-travi/Tabelle.csv` rows 67-93.

## Upstream (cross-tool dependencies within ca-travi)
- Tool2 `MRd` [Z33] feeds Tool6 `MRb` [K79] (capacity design).
- Tool3 `VRd` [Z26] feeds Tool6 verifica [J82] pass/fail comparator.
- Tool1 `As,o` [AM32] feeds Tool2 and Tool4.
- Tool0 fcd/fyd/fctm feed Tools 1-4.
- Tool4 `σs` [Z53] feeds Tool5 input.
- `ca-mensole` reuses Tool0's `Tabelle` sheet (13 constants differ — verify before assuming identical cover/exposure tables).

## Suspected bugs / fragile spots
1. **[Z42 hardcoded 360]** σs SLS-rara limit is hardcoded `360` instead of `0.8·fyk` (formula `IF(Z41<360,...)`); only correct when steel=B450C (fyk=450→0.8·450=360). For any other steel grade selected via H8 (FeB22k fyk=215 etc.) the check silently uses the wrong limit. Contrast: Z47/Y47 (SLE-qp concrete stress) correctly recomputes `0.45*VLOOKUP(H9,...)` dynamically each time.
2. **[AM44 = AM17/2]** "passo zona critica" reference formula divides an apparently-blank cell AM17 (no value in cell map) by 2, always yielding 0; this output is not visibly wired into K60 or any check, but if it were intended to be used it is broken (likely should reference AL26 "passo ferri" or similar).
3. **[K60 degenerate MIN]** `p,max zona critica` = MIN(H7/4, 24·MIN(H15,H18), 175/225, 6/8·MIN(H12,H14)) — when a stirrup type is unused (H18=0, i.e. "Diametro staffe tipo2"=0 as in cached example), `MIN(H15,H18)=0` forces the whole MIN to 0 mm regardless of the real single stirrup diameter. Should probably use H15 alone when H20 (n° bracci tipo2)=0.
4. **[Tool5 exact-match VLOOKUP]** crack-width lookup (`AI54`) uses `FALSE` (exact match) against bar diameter in `N67:R93`; any Ø not present verbatim in the table (e.g., 25 vs 26mm custom) raises `#N/A` instead of interpolating/rounding up — fragile for non-catalog diameters.
5. **[H19 = H16]** "Passo staffe tipo2" is a formula copying H16 (passo staffe tipo1) rather than an independent input, despite tipo2 stirrups (H18/H20) being separately configurable elsewhere — likely intentional (co-located stirrups) but worth confirming with user before reimplementing as two independent inputs.
6. **[AL26 passo ferri, div/0]** `(H6−2·H10)/(H11−1)` divides by zero if only 1 bar type-1 (H11=1) — no guard.
7. Case-text compare `IF(J77="cdb",...)` vs validation list `"CDA,CDB"` (uppercase) — verified NOT a bug: Excel's `=` text comparison is case-insensitive by default.

## Golden test cases
**Tools 1-6 (Travi sez. rettangolare)**, inputs: B[H6]=600mm, H[H7]=400mm, tipo_acciaio[H8]="RB500W"→uses B450C row(?), tipo_cls[H9]="C35/45", c[H10]=70mm, n1[H11]=5, Ø1[H12]=20mm, n2[H13]=0, Ø2[H14]=0, Østaffe1[H15]=12mm, passo1[H16]=115mm, bracci1[H17]=2, Østaffe2[H18]=0, n_bracci2[H20]=0, VEd[H23]=138kN, Med,ulu[H24]=318kNm, Med,rara[H25]=239kNm, Med,qp[H26]=200kNm, classe_dutt[J58/J77]="CDB", MRc[K78]=350kNm, Lt[K80]=8m, cond.amb[Y50]="Ordinarie", combo[Y51]="Frequente", sensib[Y52]="Poco sensibile", classe_fessura[Z54]="w3".
→ fyd=434.783MPa, fcd=21.165MPa, As,min=238.937mm², As,o=1570.8mm², As,max=9600mm², d=330mm, MRd=207.01kNm, flessione="NO", VRdc=650.276kN, VRds=634.97kN, VRd=634.97kN, taglio="OK", σc,rara=21.8885MPa→"OK", σs,rara=528.576MPa→"NO", σc,qp=18.3168MPa→"NO", σs,limite,fessura=240MPa→fessurazione="NO", Lcr=400mm, p,max=0mm, L_ancoraggio=120mm, MRb=207.01kNm, VEd,max=207.01kN, capacity_design="OK".

**Tool 7 (taglio non armato)**, inputs: Rck=35MPa, h=500mm, c=50mm, bw=1000mm, Asl=1005mm², NEd=0kN → fck=29.05MPa, fcd=16.4617MPa, d=450mm, σcp=0, k=1.66667, vmin=0.405896, ρl=0.00223333, VRd,1=167.858kN, VRd,2=182.653kN, VRd=182.653kN.
