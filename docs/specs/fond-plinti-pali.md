# Pile Caps by Strut-and-Tie (fond-plinti-pali) — Implementation Spec

Workbook: pile-cap ("plinto su pali") design, EN 1992-1-1 (EC2) §6.5 (struts/ties/nodes), §9.8.1 (pile cap detailing),
§6.4 (punching), §6.2.2 (shear at reduced distance av). Sheets: `Footing check` (engine, one fill-down row per load
combination "LCC" + single-cell envelope/design block), `Supporto` (rebar catalog + pile/plinth coordinates),
`LC Reactions` (raw MIDAS per-load-case reactions, paste-in), `Per Relazione` (report view, pure cross-sheet refs).

Column/row addresses below are on `Footing check` unless prefixed `Supporto!`. All pile forces/moments come from a
column N, Mx, My, Vx(Fx), Vy(Fy) delivered per **load combination** (LCC, not single load case) pasted into B:I from
MIDAS ("PASTE DATA FROM MIDAS"); `LC Reactions` holds the pre-combination per-load-case values (identical layout to
the isolated-footings workbook — Node, Load case, Fx..Mz [kN,kN,kN,kNm,kNm,kNm], one row per (node, case), e.g.
`SW,DL,L,LR,INST,W±X/Y(±CPI),CR(DEAD/LEFT/RIGHT),S(DRIFT/ACC),T±,SLV_X/Y(RS)`); the LCC-to-LC combination logic
itself is not in the provided sheets (done externally / pasted-in already combined).

## Per Relazione — report contents (no new logic, only refs into `Footing check`)
1. Materials: fyk, fck. 2. Geometry: pile count/pattern, spacing X/Y, plinth X/Y/H, pedestal height, eccentricities.
3. Base reinforcement X-X and Y-Y: As,min, governing N/M/Mu for both design cases, cover, assumed ø, As_req_flexural,
   spacing, #rebars/m, ø, As_real. 4. Strut-and-tie: Nmin/Nmax on piles; main strut check (d, lever arm, θ, Fus_strut,
   sRd,max, Lb, stirrup ø/spacing/count, wt, ws, Acs, Fns, Verified + utilization); tie XY/X/Y checks (θ, utilization,
   Fut, α, ø rebar, tot rebars, At, Fnt, Verified). 5. Shear check (VEd, Øpile, av, VEd', k, ρ, νRd,c, νRd,c,min, VRd,c,
   T.L.) and punching check (Øpile, 2l>3·Ø gate, u, VRd,max, T.L.). Top reinforcement and the "simplified method"
   tension-rod block (see Tool 4 notes) are **not** surfaced in the report.

---
## Tool 1: `pali-inviluppo-carichi` — pile axial load/moment envelope per LCC
### Purpose
For every load combination, resolve the total column force/moment (N, Vx, Vy, Mx, My) into axial demand on each pile
group and per-pile N via rigid-cap equilibrium; take global Nmin/Nmax and extreme M for downstream design. EC2 §9.8.1
(pile as compression member) / plane-sections rigid-cap assumption (not codified, textbook method).
### Inputs (per-LCC table B6:I10639, fill-down; ~10634 rows)
One row = one load combination. Columns: B Node[-], C LCC name[SLU1.., SLV_1.., SLU_EQU..][str], D Fx[kN], E Fy[kN],
F Fz=N[kN], G Mx[kNm], H My[kNm], I Mz[kNm] (I unused downstream). User-pasted data (all `*` unlocked).
Scalars: AR6 AX(plinth dim X)[mm]=4000, AR7 BY[mm]=4000, AR8 H(plinth height)[mm]=1200, AR12 c(cover)[mm]=50,
AR16 +ex[mm]=0, AR17 +ey[mm]=0, AR18 #PILES[-]=4, AR19 #X[-]=2, AR20 #Y[-]=2, AR21 Lx(pile spacing X)[m]=2,
AR22 Ly(pile spacing Y)[m]=2, AM23="case selector" (derived, see step 8), AM23 dropdown driving Case1..4.
### Outputs
Per row: R=N/pile[kN], S=ΔMy(Vx)[kNm], T=ΔMx(Vy)[kNm], U=ΔMy(ex)[kNm], V=ΔMx(ey)[kNm], W=Mx,final[kNm],
X=My,final[kNm], Y=|M_outplane/M_principal| ratio, Z=ΔN(My)[kN], AA=ΔN(Mx)[kN], AB=Nmin,pile[kN], AC=Nmax,pile[kN].
Envelope: AF12/BC7 Nmin,env[kN]=244.236, AG12/BD7 Nmax,env[kN]=896.061, AF26/AG26 max |Mx|/|My| over all rows,
AF30/AG30 max |Vx|/|Vy|, AV7/AZ7 N_max (=MAX(F)), AV8/AZ8 associated My/Mx via XLOOKUP, AV13/AZ13 My/Mx_max(+),
AV14/AZ14 …(-), each drives Tool 2.
### Calculation steps (row i, dependency order)
1. `R_i = F_i / AR18` — per-pile share of total axial force (only valid form for Case 1/4 symmetric grids; see bug).
2. `S_i = D_i*AR8/1000`, `T_i = E_i*AR8/1000` — shear × plinth height → moment at pile head from Vx/Vy (arm = H).
3. `U_i = R_i*AR18*AR16/1000`, `V_i = R_i*AR18*AR17/1000` — moment from eccentricities ex/ey (both 0 in golden case).
4. `W_i = G_i + V_i - T_i`; `X_i = H_i - U_i + S_i` — final Mx/My at pile-head level.
5. `Y_i = |ratio W/X or X/W|` selected by `AM23` case (branchy IF chain; only used for a diagnostic ratio, not fed
   downstream except indirectly through case string).
6. `Z_i = |(X_i/AR21)/AR20|`, `AA_i = |(W_i/AR22)/AR19|` — extra axial force per pile from My, Mx (moment/lever-arm/#piles-per-row).
7. `AB_i = R_i - Z_i - AA_i` (Nmin,pile,i), `AC_i = R_i + Z_i + AA_i` (Nmax,pile,i); blank string if the raw sum is 0.
8. Case selector `AM23 = "Case 1"` if (#X=2,#Y=2,Lx≠0,Ly≠0,#PILES=4); `"Case 2"` if (#X=2,#Y=1,Lx≠0,Ly=0,#PILES=2);
   `"Case 3"` if (#X=1,#Y=2,Lx=0,Ly≠0,#PILES=2); `"Case 4"` if (#X=1,#Y=1,Lx=0,Ly=0,#PILES=1); else unsupported.
9. Envelope: `AF12 = MIN(AB6:AB15000) + AR24/AR18/1.4*0.9` (Nmin, self-weight added at *favourable* factor — see bug);
   `AG12 = MAX(AC6:AC15000) + AR24/AR18` (Nmax, self-weight at full unfavourable factor).
10. Self-weight `AR24 (W) = AR6/1000*AR7/1000*AR8/1000*25*AR25 + AR26`, γG1 `AR25=1.3`; `AR26 (G1)` is a **job-specific
    hardcoded** additional-load formula (backfill/paving loads on the plinth), not general.

---
## Tool 2: `pali-armatura-flessione` — X-X/Y-Y bottom+top slab reinforcement
### Purpose
Design the plinth as a wide beam spanning between pile rows (simplified beam-on-2-supports method), governing Mu
picked from two envelope cases (max N with its M, and max M with its N); EC2 §9.3.1.1 (min reinf.) / general flexure.
### Inputs
AG6 fyk[N/mm²]=450, AR8 H[mm]=1200, AR12 c[mm]=50, AR19/AR20 #X/#Y, AR21/AR22 Lx/Ly[m], AR72 γS=1.15, from Tool1:
AV7/AZ7 N_max[kN], AV8/AZ8 associated M[kNm], AV13/AZ13 M_max(+)[kNm], AV14/AZ14 M_max(-)[kNm]. User picks bottom
rebar ø (AV19/AZ19, default 24mm) and spacing (AV24/AZ24, default 100mm); top ø (AV41/AZ41 default 20mm), spacing
(AV47/AZ47 default 200mm).
### Outputs
AV5/AZ5 As,min[mm²/m]=2160 (bottom, 0.18%), AV34/AZ34 As,min,top[mm²/m]=1080 (0.09%), AV20/AZ20 As_req_flexural
[mm²/m]=3406.67/3241.8, AV23/AZ23 As_req (=MAX with As,min), AV28/AZ28 As_real[mm²/m]=4523.89 (both dirs, bottom),
AV45/AZ45 top As_real (@ø20/200 default → 1570.8 mm²/m).
### Calculation steps
1. `As,min = 1000*AR8*0.0018` (bottom), `1000*AR8*0.0009` (top) — 0.18%/0.09% of gross 1m×H strip.
2. Case A Mu (using N_max path): `Mu_A = IF(Case3, |AV8|, IF(Case2, (N+γ)*Lx/4+|AV8|, (N+γ)*0.5*Lx/4+|AV8|))` where
   `(N+γ)` reads `AR24` self-weight column via `$AR$24` add-on inside the SAME cell (see AV9/AZ9 formula).
3. Case B Mu (using M_max path): `Mu_B = IF(Case3, MAX(AV13,|AV14|), IF(Case2, (N₂+γ)*Lx/4+MAX(...), (N₂+γ)*0.5*Lx/4+MAX(...)))`,
   N₂ found via `XLOOKUP(AV13 or AV14, X-column, F-column)` — picks the N paired with whichever of M(+)/M(-) is larger in
   magnitude.
4. `As_req_flexural = MAX(Mu_A,Mu_B)*1e6 / ((AR8 - c - 1.5*ø_assumed) * fyd)`, `fyd = fyk/γS = 391.3 N/mm²`.
5. `As_req = MAX(As_req_flexural, As,min)`.
6. Bar pick: `ø_inches = ø_mm/25.4`; `VLOOKUP(ø_inches, Supporto!D4:F28, 3, FALSE)` → area[mm²]; `#rebars/m =
   CEILING(1000/@spacing,1)`; `As_real = area * #rebars/m`. Top reinforcement uses `ø²*3.14/4*#rebars/m` directly
   (literal 3.14, not `PI()` — see bugs).
7. Top Mu uses same case logic but with **negated** N (`-N`) and the (-)/(+) moment envelope swapped, representing
   hogging under net uplift/tension pile condition.

---
## Tool 3: `pali-strut-tie-check` — EC2 §6.5 strut, node and tie verification
### Purpose
Verify the main diagonal compression strut from pile to column node, the concrete node stress, and three ties
(diagonal XY, and orthogonal X, Y) that equilibrate the strut's horizontal component, per EC2 §6.5.2 (struts),
§6.5.4 (nodes), §6.5.3/§9.8.1 (ties, EC2 rebar-as-tie).
### Inputs
BC7=Nmin,env[kN] (tie force, from Tool1 AF12), BD7=Nmax,env[kN] (strut force, from Tool1 AG12), AR21/AR22 Lx/Ly[m],
AR8 H[mm], AG7 fck[N/mm²], AR71 γC=1.5, AR12 c[mm], BG13/Lb[mm]=600 (=pile ø, support width), BG14 ø_stirrup[mm]
(computed from tie rebar selections, see step 6), BG15 clear spacing[mm]=0(user), BL19/BL29/BL40 tie-rebar-ø **in
decimal inches** (hardcoded user input, e.g. 1.25984 = 32 mm) for XY/X/Y ties, BL21/BL31/BL42 tot rebars per tie[-].
### Outputs
BG5 LXY[m]=1.41421 (diag pile spacing), BG8 θ[°]=38.128 (clamped ≥25°), BG9 Fus_strut[kN]=1451.3, BG12 sRd,max
[MPa]=13.9148, BG18 ws[mm]=512.046, BG19 Acs[mm²]=262191, BG21 Fns[kN]=3648.34, BF22 "Verified"/"Not verified",
BI22 utilization=0.398. Tie XY: BL9 utilizationXY=0.4, BL10 Fut_XY[kN]=456.657, BL13/BL14 Fut_X/Fut_Y[kN]=615.734,
BL12 utilizationX&Y=0.6. Tie X: BL32 At,X[mm²]=3619.11, BL34 Fnt,X[kN]=1416.18, BK35 Verified (utilization BN36=0.435).
Tie Y mirrors (BL43,BL45,BK46,BN47).
### Calculation steps
1. `LXY (BG5) = SQRT(Lx²+Ly²)/2` [m] — half-diagonal, distance pile-centre to plinth centre.
2. `h-wt/2 (BG6) = H/1000 - wt/2/1000` — lever arm to tie centroid; `wt (BG17) = c+2*MAX(top-ø-cover terms)+ø_stirrup+c`
   (fed back from step 6, circular-looking but resolved because stirrup ø/2 default assumed then iterated by user).
3. `tanθ (BG7) = BG6/BG5`; `θ (BG8) = MAX(25°, DEGREES(ATAN(tanθ)))` — EC2 §6.5.2(2) min strut angle 25° enforced;
   `"-"` (no strut) if Case 4 (single pile under column, no strut-and-tie mechanism).
4. `Fus_strut (BG9) = Nmax,env / SIN(θ)` (Case1/2/3) or `= Nmax,env` (Case4, direct bearing).
5. `sRd,max (BG12) = MIN(σ1Rd,max, σ2Rd,max, σ3Rd,max)` from AR75/AR76/AR77 (node classes, §6.5.4): σ1=CCC node
   `1.18*(1-fck/250)/0.85*fcd`, σ2=CCT (1 tie dir) `(1-fck/250)*fcd`, σ3=CCT (2 tie dirs) `0.88*(1-fck/250)*fcd`;
   golden case governed by σ3=13.9148 MPa (both X and Y ties present).
6. `Acs (BG19) = ws²` (Case1/2/3) or `AR10*AR11` (Case4, column area) — strut cross-section at node, `ws` = strut
   width projected onto the node face using `wt` and θ.
7. `Fns (Fns design resistance, BG21) = sRd,max * Acs / 1000` [kN]; `Strut Check (BF22) = "Verified" if Fns>Fus_strut`.
8. Tie XY: `Fut_XY (BL10) = Fus_strut(BG9) * cos(θ)` — horizontal component of the main strut = XY tie demand.
9. Tie X/Y (BL13/BL14) = `Fut_XY * cos(45°)` (α=45° for square grid, `BL11=DEGREES(ATAN(Ly/Lx))`), i.e. XY tie force
   resolved onto the X and Y axes.
10. Rebar sizing per tie: `ø_stirrup = VLOOKUP(ø_inches, Supporto!D4:E28, 2, FALSE)`; `At = tot_rebars *
    VLOOKUP(ø_inches, Supporto!D4:F28, 3, FALSE)`; `Fnt = At * fyd / 1000` (fyd=fyk/γS); `Verified if Fnt > Fut`.
11. A parallel, secondary strut/tie set (cols BP:BX) repeats steps 3-10 using **Nmin,env** (pile in tension) and is
    labelled "Only for Pile in tension"; it is never surfaced in Per Relazione (dead/manual-check path).

---
## Tool 4: `pali-verifica-taglio-punzonamento` — shear & punching (EC2 §6.2.2, §6.4)
### Purpose
Beam shear at a section reduced by proximity to the support (av<2d rule, §6.2.2(6)) and punching shear check for
each pile (§6.4.2/6.4.4, waived if piles are far enough apart).
### Inputs
AR58/AR59 column bx,by[mm]=700, AR62 H[mm]=1200, AR68 cover[mm]=50, AR85 ø_long[mm]=24 (assumed, "simplified
method" — independent default from Tool 2's own ø), AR78 Nsd[kN] = Tool1 `AV7 + AR24` (max column N + self-weight),
AR79 Msd,y[kNm]=775 **hardcoded literal**, AR80 Msd,x[kNm]=710.5 **hardcoded literal** (not linked to envelope — see
bug), AR97 av[mm]=470 **hardcoded** (doc says "considered Ø/5" = 120mm, actual value unrelated), AR107 Øpile[mm]=600,
AR60/AR61 plinth AX/BY[mm], AR90 As_real,tot[mm²] (from a parallel lever-arm tension-tie sub-calc, rows 55-93, not
detailed further here as it is unused by the report except via AV28≡As_real feeding step 3 below).
### Outputs
AR86 d[mm]=1102, AR96 VEd[kN]=1537.33, AR98 VEd'[kN]=327.834, AR99 k[-]=1.42601, AR100 ρ[-]=0.00102629, AR101
νRd,c[N/mm²]=0.254358, AR102 νRd,c,min[N/mm²]=0.337154, AR103 VRd,c[kN]=1486.18, AR104 T.L.[-]=0.220589 (Verified if
<1). Punching: AQ108/AQ109 text gate, AS108/AS109 "OK"/"NO", AR110 u[mm]=2800, AR111 VRd,max[kN]=17220.1, AR112
T.L.[-]=0.17855.
### Calculation steps
1. `d (AR86) = H - cover - 2*ø_long_assumed` [mm] = 1200-50-2*24 = 1102.
2. `VEd (AR96) = Nsd/2` — half the total axial demand (one pile row's worth of shear crossing the critical section).
3. `av (AR97)` = user input (should be ≈Øpile/5 per its own label, but is a disconnected literal — bug).
4. `VEd' (AR98) = VEd * av/(2d)` — §6.2.2(6) shear-enhancement reduction (linear in av/2d, valid only av<2d).
5. `k (AR99) = 1 + SQRT(200/d) ≤ 2.0` (not clamped in formula — see bug).
6. `ρ (AR100) = As_real,X-X(bottom) / (b*d)`, `b=AR60` (plinth width).
7. `νRd,c (AR101) = 0.12*k*(100*ρ*fck)^(1/3)`; `νRd,c,min (AR102) = 0.035*k^1.5*fck^0.5`.
8. `VRd,c (AR103) = MAX(νRd,c,νRd,c,min) * b * d / 1000`; `T.L. (AR104) = VEd'/VRd,c` (Verified if ≤1).
9. Punching gate: for each direction, `IF(2·l_pile-spacing*1000 > 3*Øpile, "OK","NO")` — if piles are far enough
   apart individual pile punching perimeters don't overlap the column's, so only the column-face punching (below)
   governs; no per-pile punching cone check is implemented in this sheet.
10. `u (AR110) = 2*(bx+by)` — column perimeter (0-distance punching perimeter, i.e. checked AT the column face, not
    at the usual 2d offset — see bug).
11. `VRd,max (AR111) = 0.5*u*d*0.6*(1-fck/250)*fcd/1000` [kN] (EC2 §6.4.5 max punching resistance at the column
    face); `T.L. (AR112) = Nsd/VRd,max`.

---
## Lookup tables (`Supporto`)
- `Supporto!C4:F28` — bar catalogue, one row per commercial size. C=nominal size (US # 2.5-14 or "ØNN" metric
  10-32mm). **Key column for all VLOOKUPs is D** (=diameter **in decimal inches**, `E/25.4` for metric rows, literal
  fraction string for US rows) — col E=ø[mm], col F=area[mm²] (`π·E²/4`). Exact-match VLOOKUP (`FALSE`); metric callers
  must pre-convert mm→inches (`/25.4`) before looking up.
- `Supporto!L33:M36` — case-name lookup, key=`AM23` string ("Case 1".."Case 4") → long description.
- `Supporto!D34:E38` — plinth corner coordinates (±AX/2, ±BY/2), diagram-only.
- `Supporto!D42:E45` — pile coordinates (±Lx/2, ±Ly/2 per pile), diagram-only; `K42:L43` reference undefined cells
  `AY19/AY20` → cached `#VALUE!` (dead formulas, ignore).
- `Supporto!D52:E57` — ACI318 strut-type β-factor table (tension/boundary/interior/other), present for reference
  only; **no formula in `Footing check` reads it** (EC2 sheet uses its own §6.5.4 node-stress formulas instead).

## Constants baked into formulas
- Rebar area: `π·ø²/4` (exact) for the catalogue and bottom-tie/X/Y-tie areas; **top reinforcement uses literal
  `3.14`** instead of `PI()` (AV51/AZ51) — small, inconsistent precision loss.
- `0.85` in `fcd = 0.85*fck/γC` (EC2 long-term/sustained-load factor, §3.1.6).
- `0.18%`/`0.09%` minimum reinforcement ratios (bottom/top) — not EC2's `0.26·fctm/fyk` formula (which is computed
  separately at AR93 but never combined into `As,min`, see bug).
- Node-stress factors `1.18`, `0.88` in §6.5.4 CCC/CCT formulas — standard EC2 coefficients, correctly used.
- `25°` minimum strut inclination (EC2 §6.5.2(2)) hardcoded as a floor via `MAX(25,ATAN(...))`.
- Self-weight `AR26 (G1)`: `4*0.3*0.68*25*γG1 + 48.804*4*γG1 + 13*16*γG1` — fully job-specific (column self-weight +
  two point/area loads on the plinth top), not a general formula; must be exposed as a free-form user input in the
  Python port, not hardcoded.

## Suspected spreadsheet bugs / fragile spots
1. **Nmin envelope self-weight factor mismatch** (`AF12`): divides `AR24` (built with γG1=1.3, cell AR25) by a
   hardcoded `1.4`, then multiplies by `0.9` — the 1.4 doesn't match AR25's 1.3; looks like an attempt to convert
   unfavourable→favourable self-weight (γ=0.9) but through the wrong unfavourable divisor.
2. **Tie-rebar diameter input is decimal inches** (`BL19/BL29/BL40`, e.g. `1.25984` for 32 mm) with no mm-facing
   label — easy to mis-key; the bottom/top flexural rebar inputs (`AV19/AV41` etc.) are plain mm by contrast.
3. **Msd,y/Msd,x hardcoded** (`AR79=775`, `AR80=710.5`) in the shear/punching "simplified method" block, disconnected
   from the live envelope maxima (`AV13=862.42`, `AZ13=790.552` from Tool 1) — will silently go stale if load combos
   change.
4. **`av` (AR97=470mm) contradicts its own doc string** ("considered distance Ø/5" → 600/5=120mm expected).
5. **`k` factor (AR99)** not clamped to EC2's required `≤2.0` ceiling (formula is `1+SQRT(200/d)` only).
6. **Punching perimeter `u` (AR110)** is taken at the column face (`2*(bx+by)`), not at the standard `2d` offset
   from the loaded area per EC2 §6.4.2 — likely an intentional "pile-cap as single unit" simplification but not
   labelled as such.
7. **0.26·fctm/fyk minimum ratio (AR93)** is computed but never combined into `As,min`/`As,req` — dead check.
8. Rebar catalogue VLOOKUPs are exact-match (`FALSE`) against floating-point inch conversions (`mm/25.4`) — any
   accumulated rounding in a caller's mm→inch conversion causes `#N/A`→`IFERROR→0` (silently zeroing a design qty).
9. Secondary "pile in tension" strut/tie block (`BP:BX`) duplicates ~80% of the main block's logic with Nmin instead
   of Nmax, but is never reported and its activation condition is implicit (always computed, not gated on Nmin<0).

## Golden test case (Case 1: 4 piles, 2×2, cached values)
```
inputs: AX=4000mm BY=4000mm H=1200mm c=50mm #PILES=4 #X=2 #Y=2 Lx=2m Ly=2m ex=ey=0
        fyk=450 MPa fck=32 MPa bx=by=700mm Øpile=600mm
Tool1 envelope: Nmin_env=244.236 kN  Nmax_env=896.061 kN
  row SLU4 (LCC): N=1899.96kN Mx_in=9.91203 My_in=-169.805 -> Wfinal=11.0284 Xfinal=-188.942 Nmin,pile=424.997 Nmax,pile=524.982
  row SLU_EQU1:   N=1184.09kN -> AB=212.703 AC=379.345
Tool2 X-X: As_min=2160 mm2/m  As_req_flexural=3406.67 mm2/m  ø24@100 -> As_real=4523.89 mm2/m
     Y-Y: As_req_flexural=3241.8 mm2/m -> As_real=4523.89 mm2/m (same detailing)
Tool3 strut: LXY=1.41421m theta=38.128deg Fus_strut=1451.3kN sRd,max=13.9148MPa Acs=262191mm2 Fns=3648.34kN
             utilization=0.398 -> Verified
     tie XY: Fut_XY=456.657kN util=0.4;  tie X/Y: Fut=615.734kN each, util=0.6
     tie X:  ø32mm 8 rebars At=3619.11mm2 Fnt=1416.18kN util=0.435 -> Verified (tie Y identical by symmetry)
Tool4 shear: d=1102mm VEd=1537.33kN av=470mm VEd'=327.834kN k=1.42601 rho=0.00102629
             nRd,c=0.254358 nRd,c,min=0.337154 VRd,c=1486.18kN T.L.=0.220589 -> Verified
      punching: 2000>1800 both dirs -> OK; u=2800mm VRd,max=17220.1kN T.L.=0.17855 -> Verified
```
