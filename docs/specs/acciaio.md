# Acciaio — Steel Tools Spec

Two independent tools, share only the `Materiali` lookup sheet (used by tool 1 only). No cross-links found between tool 1 and tool 2 in the provided cellmaps.

---

## Tool 1: `column-check` (EC3 H-column stability + resistance)
Sheet: `acciaio-colonne-ec3/column-check.txt` (+ `materiali.txt` for γM, fyk/fuk lookup)

### 1. Purpose / code refs
Verifies a steel H/I column (or box, via generic section props) for: cross-section classification (given, not computed), shear resistance (web/wings), bending resistance about y-y and z-z, uniaxial buckling (flexural, y-y and z-z), lateral-torsional buckling (LTB), shear buckling of web, and combined axial+biaxial-bending stability per **EN1993-1-1 §6.2 (resistance), §6.3.1 (flexural buckling), §6.3.2 (LTB), §6.3.3 Annex B (interaction factors kyy/kyz/kzy/kzz, method 2), §6.2.6 (shear buckling, §6.2.6(6) rotated to Annex/EC3-1-5 hw/t check)**. Critical elastic LTB moment Mcr uses the 3-factor (C1) formula from **EC3-ENV Annex F / ECCS**.

### 2. Inputs
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| E5 | — | section name | — | text input | "550x450x8x16 + plate 100x16" |
| H6 | b | flange/base width | mm | input | 280 |
| H7 | h | section height | mm | input | 500 |
| H8 | tw | web thickness | mm | input | 8 |
| H9 | tf | flange thickness | mm | input | 12 |
| H10 | A | gross area | mm² | input | 10528 |
| H11 | steel grade | — | enum S235/S275/S355/Q235/Q345 | "Q345" |
| H12 | γM0 | partial factor (resistance) | — | input | 1 |
| H13 | γM1 | partial factor (buckling) | — | input | 1 |
| G16 | processing | — | enum cold formed/hot finished | "hot finished" |
| Y16 | class | cross-section class | — | enum class 1/2/3/4 | "class 3" |
| P5,P6 | Iyy,Izz | 2nd moment of area | mm⁴ | input | 4.7206e8, 4.3924e7 |
| P7,P8 | Wel,y, Wpl,y | y-y section moduli | mm³ | input | 1.8883e6, 2.0928e6 |
| P10,P11 | Wel,z, Wpl,z | z-z section moduli | mm³ | input | 3.1375e5, 4.7802e5 |
| P13 | IT | torsion constant | mm⁴ | input | 405255 |
| P14 | E | Young's modulus | MPa | input | 206000 |
| P15,P16 | iy, iz | radii of gyration | mm | input | 211.752, 62.5921 |
| J19 | Nsd | design axial force | kN | input | 172.326 |
| J20 | My,sd | design moment y-y | kNm | input | 120.689 |
| J21 | Mz,sd | design moment z-z | kNm | input | 0.0063970 |
| J22 | Vy,sd | shear on web (z-dir) | kN | input | 29.2057 |
| J23 | Vz,sd | shear on wings (y-dir) | kN | input | 0.00235166 |
| Y19 | Lcr,yy | effective buckling length y-y | mm | =18850·0.874565 | 16485.6 |
| Y20 | Lcr,zz | effective buckling length z-z | mm | =1800·1.15728 | 2083.1 |
| Y64 | Ly | column length (undeformed, y-y) | mm | input | 18850 |
| AV42 | lT | torsional buckling length | mm | input | 1800 |
| AZ33 | C1 | LTB moment-diagram factor | — | input (from "valori C1" table) | 1.871 |
| AJ61,AJ62 | diagram type y,z | — | enum 1/2/3a/3b | 1, 1 |
| AI45,AN45 | Mj,y, Mj,z | secondary end moment | kNm | input | 0.0069573, 0.0224413 |
| AI52,AN52/AI51/AN51 | Mmax,y/z, dmax | for diagram type 2 | kNm/mm | input | 0 (dmax) |

### 3. Outputs (checks)
| cell | symbol | meaning | cached |
|---|---|---|---|
| J26 | web shear check | "OK"/"NO" if G26>J22 | "OK" (ratio 3.21%) |
| J36 | wing shear check | "OK"/"NO" if G36>J23 | "OK" |
| H33 | MRd,y check | "OK" if D33>J20 (class1/2 plastic) | "OK", MRd,y=651.4 kNm |
| H43 | MRd,z check | "OK" if D43>J21 | "OK", MRd,z=108.2 kNm |
| M53 | biaxial y-y buckling+bending (uniaxial method) | "OK" if J53>J20 | "OK" |
| M54 | biaxial z-z | "OK" if J54>J21 | "OK" |
| X55 | v54<1 check | "OK" | "OK" |
| K56 | simplified interaction I56<1 | "< 1 - OK" | 0.0344 |
| AA47 | Annex B interaction (yy eq.) Y47<1 | "< 1" | 0.2303 |
| Y48 | → OK/NO | "OK" |
| AA50 | Annex B interaction (zz eq.) Y50<1 | "< 1" | 0.2062 |
| Y52 | → OK/NO | "OK" |
| R75 | shear buckling Vb,Rd vs Vz,sd | ">29.21 kN -> Verified" | verified |
| O59 | LTB necessity flag | text | "No allowance for lateral-torsional buckling necessary" |
| W29,W32 | χy, χz (flexural buckling reduction) | — | 0.588068, 0.886636 |
| BC17 | buckling curve (yy) | "a/b/c/d" | "b" |

### 4. Calculation steps (dependency order)
1. `fyk[H14] = VLOOKUP(H11, Materiali!H19:J23, 2)/γM0[H12]` = 345 MPa; `fuk[H15]=VLOOKUP(...,3)/H12` = 450 MPa.
2. `BC[BC17] curve` = f(processing[G16], h/b): hot+h/b≤2→"b", hot+h/b>2→"c", cold+h/b≤2→"c", else "d".
3. Section: `iy[P15], iz[P16]` given; `class[Y16]` given; `Av,z[P9]=1.2·(h−2tf)·tw` = 4569.6mm² (web shear area); `Av,y[P12]=2·b·tf` = 6720mm² (wing shear area).
4. `Iw[AI10]=Izz·(h−tf)²/4` = 2.6151e12 mm⁶ (warping const.); `G[AI9]=E/(2·(1+0.3))` = 79230.8 MPa.
5. `Ncr,y[Y21]=π²·E·Iyy/Lcr,yy²/1000` = 3531.51 kN; `Ncr,z[Y22]=π²·E·Izz/Lcr,zz²/1000` = 20580.2 kN; `Ncr,t[AV38]=(1/i0²[AV41])·(G·IT+π²·E·Iw/lT²)/1000`, `i0²[AV41]=iy²+iz²`=48756.7 mm² → Ncr,t=34315.3 kN.
6. Slenderness: `λ̄yy[W23]=(A·fyk/Ncr,y/1000)^0.5`=1.01415; `λ̄zz[W24]=(A·fyk/Ncr,z/1000)^0.5`=0.420105; `λ0[AI35]=√(Wel,y·fyk/Mcr)` = 0.226433.
7. Imperfection α: `α_yy[Y25]=IF(hot,0.34,0.21)`; `α_zz[Y26]=IF(hot,0.49,0.34)` (curve-based, NOT via BC17 — see bug#2). `αLT`(row28 BC)=IF(BC17="a",0.21,"b"→0.34,"c"→0.49,0.76).
8. `φyy[W27]=0.5·(1+α_yy·(λ̄yy−0.2)+λ̄yy²)`=1.15266; `φzz[W28]` analog=0.64217.
9. `χyy[W29]=MIN(1,1/(φyy+√(φyy²−λ̄yy²)))`=0.588068; `χzz[W32]`analog=0.886636.
10. Mcr (elastic LTB moment) `[AI11]=C1·(π²·E·Izz/Lcr,zz²)·√(Iw/Izz+(Lcr,zz²·G·IT)/(π²·E·Izz))` = 1.27057e10 Nmm.
11. `MRd,y[D33]`: class1/2→Wpl,y; class3→Wel,y; class4→Wel,y (with reduced fy' if Vz,sd>0.5·Vy,Rd, else fy) → `fy'[G31]=IF(J23<0.5·G26, fyk, (1−(2·J22/G26−1)²)·fyk)`; `MRd,y=fy'·W/1e6/γM1`=651.446 kNm. `MRd,z[D43]` analog with Wpl,z/Wel,z and `fy'[G41]`.
12. Web shear resistance `Vpl,Rd[G26]=Av,z·fyk/√3/1000`=910.2 kN (check `J26=IF(G26>Vy,sd,"OK")`). Wing shear `Vpl,Rd2[G36]=Av,y·fyk/√3/1000`=1338.53 kN, check J23.
13. Slenderness for shear buckling: `hw/t[AC27]=(h−2tf)/tw`=59.5; limit `72·ε·η[AD27]=72·0.825324·1.2`=71.308 (ε=`√(235/fyk)`[L30]=0.825324, η=`IF(fyk>460,1,1.2)`[L31]=1.2) → shear buckling check required since hw/t<72εη? Actually K32 flags "Shear buckling check" needed (borderline).
14. Shear buckling capacity: `cw[C67]=0.83/F65` where `F65[F65]=hw/(86.4·η·ε)`=0.834409 → C67=0.994716; `Vb,Rd2[C76]=cw·fyk·hw·tw/(√3·γM1)/1000`=910.2 kN; contribution from flanges `Vbf,Rd[H74]=I71+G69` where `G69[G69]=cw·fyk·b·tf/(√3·γM0)/1000`=754.492 and `I71=(b·tf²·fyk)/(V67·γM0)·(1−(My,sd/Mf,Rd[R63])²)/1000`=2.59872 kN (V67 = "B" per Annex A table). `Vb,Rd[O75]=MIN(Vbf,Rd, Vb,Rd2)`=757.091 kN → verified against Vz,sd (=J22, mislabeled Vy,sd in formula but is the web shear).
15. LTB necessity `[O59]`: not required if `(MAX(My,sd,Mz,sd)·1e6/i0²) < λLT,0² OR λ̄0 < λLT,0` (λLT,0[AF43]=0.4) → TRUE here, so kyy/kzy method still computed but LTB reduction not governing.
16. Method-2 interaction factors kyy,kyz,kzy,kzz (Annex B, class1/2/3 → elastic, uses Cmy,Cmz,CmLT computed per moment-diagram type 1/2/3a/3b selected via AJ61/AJ62, aggregated at AM64/AM65/AM66). Final: `kyy[X42]`=0.807385, `kyz[X43]`=0.839168, `kzy[X44]`=0.823658, `kzz[X45]`=0.856082.
17. Combined check yy `[Y47] = Nsd/(χyy·Npl/γM1) + kyy·My,sd/(χLT·Wpl,y·fyk/γM1) + kyz·Mz,sd/(Wpl,z·fyk/γM1)`=0.230307 <1 OK. Combined zz `[Y50]` analog with χzz,kzy,kzz = 0.206155 <1 OK.
18. Fallback simplified checks: `M53=MIN(MRd,y·(1−n)/(1−0.5a), MRd,y)` (n=`H46`=Nsd/(A·fyk/1000)=0.0474445, a=`H48`=MIN((A−2·b·tf)/A,0.5)=0.361702); `M54` analog for z-z with a=`H50`=MIN((A−2·h·tw)/A,0.5)=0.240122; power interaction `I56=(My,sd/MRd,y)^a[B52=2] + (Mz,sd/MRd,z)^h[H52=MAX(5n,1)]`=0.0343815 <1 OK.

### 5. Lookup tables
- `Materiali!H19:J23` (H=grade text, I=fyk, J=ftk): S235=235/360, S275=275/430, S355=355/510, Q345=345/450, Q235=235/360. Key=exact text match (VLOOKUP FALSE, col H), cols I(fyk)/J(ftk) selected by index 2/3.
- "Valori di C1" table (not in cellmap, referenced as external sheet) → AZ33 is a manual input (1.871), not computed from a formula here.

### 6. Hardcoded constants
- γM0/γM1 = 1 (H12,H13) as **user-entered inputs**, not linked to Materiali sheet (NTC/EC3 default 1.05) — see bug §7.
- λLT,0 = 0.4 (AF43), β = 0.75 (AF44) — EC3 §6.3.2.3 recommended values for general case.
- ε factor uses fyk=235 reference (√(235/fy)) — EN1993-1-1 Table 5.2 note.
- Buckling curve α values 0.21/0.34/0.49/0.76 — EN1993-1-1 Table 6.1.
- G = E/2.6 (Poisson 0.3 hardcoded) — standard steel value.

### 7. Suspected bugs / fragile spots
- **γM0=H12, γM1=H13 hardcoded to 1** as free user inputs, disconnected from `Materiali!E4` (γM0=1.05) / `Materiali!E5` (γM1=1.05). If user forgets to set them to 1.05, all resistance/stability checks are non-conservative by ~5%. Verified: no formula links H12/H13 to Materiali sheet (unlike H14/H15 which do VLOOKUP into Materiali).
- **fuk[H15]** divides ultimate strength by γM0 (should conceptually use γM2=1.25 for fracture, per Materiali!D6); also fuk is not referenced by any other visible formula — appears dead/unused, and its γM0 division is questionable if ever wired up.
- **α_yy[Y25]/α_zz[Y26]** (imperfection factors) are computed directly from `IF(G16="hot finished",...)` hardcoded pairs (0.34/0.21 and 0.49/0.34) instead of being derived from the already-computed buckling curve `BC17`. This duplicates/could diverge from the curve-letter logic if EC3 Table 6.2 curve-selection rules change; a fragile double-source-of-truth.
- Row 75 label `R63` used in `I71` formula (`(My,sd/R63)^2`) — R63 is `Mfk` (flange-only moment resistance), reasonable, but confirm not confusing with `Q61` in same row; low risk, no error found.
- Shear-buckling section mixes `J22` (Vy,sd, web) into the wing-shear-area formulas' checks (`R75` message references `J22`) while row headers alternate "for yy"/"for zz" — variable naming is inconsistent (Vy,sd/Vz,sd swapped vs. web/wing labels in rows 22-23) — verify sign/axis convention before reuse; not confirmed as a numeric bug, only a naming-consistency risk.

### 8. Golden test case
```
H6=280 H7=500 H8=8 H9=12 H10=10528 H11=Q345 H12=1 H13=1 G16=hot finished
P5=4.72063e8 P6=4.39243e7 P7=1888250 P8=2092830 P10=313745 P11=478016 P13=405255 P14=206000 P15=211.752 P16=62.5921
J19(Nsd)=172.326 J20(My,sd)=120.689 J21(Mz,sd)=0.00639699 J22(Vy,sd)=29.2057 J23(Vz,sd)=0.00235166
Y19(Lcr,yy)=16485.6 Y20(Lcr,zz)=2083.1 AV42(lT)=1800 Y64(Ly)=18850 AZ33(C1)=1.871
→ fyk=345 fuk=450 BC17=b Ncr,y=3531.51kN Ncr,z=20580.2kN Ncr,t=34315.3kN
  λ̄yy=1.01415 λ̄zz=0.420105 χyy=0.588068 χzz=0.886636 λ̄0=0.226433 Mcr=1.27057e10 Nmm
  MRd,y=651.446kNm MRd,z=108.242kNm Vpl,Rd(web)=910.2kN Vpl,Rd(wings)=1338.53kN
  kyy=0.807385 kyz=0.839168 kzy=0.823658 kzz=0.856082
  Y47(yy interaction)=0.230307 (<1 OK) Y50(zz interaction)=0.206155 (<1 OK)
  I56(power interaction)=0.0343815 (<1 OK) Vb,Rd=757.091kN (>29.2057 verified)
  ALL CHECKS = OK
```

---

## Tool 2: `resistenza` (steel strength/stiffness reduction in fire)
Sheet: `acciaio-incendio/resistenza.txt`

### 1. Purpose / code refs
Computes reduced yield strength, ultimate strength and elastic modulus of structural steel at elevated temperature for a given fire-exposure duration (ISO 834 standard fire curve), per **EN1993-1-2 §3.2.1, Table 3.1** (reduction factors kfy, kE vs. temperature). Temperature from time uses a simplified unprotected-steel gas-temperature correlation (ISO 834 curve fit), **not** the full EN1991-1-2 heat-transfer/section-factor method — no Am/V, no protection, so this is a conservative/simplified nomogram-style tool, not a full thermal analysis.

### 2. Inputs
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| D2 | grade | steel grade | — | enum S235/S275/S355 | "S355" |
| D3 | E | reference (20°C) elastic modulus | MPa | input | 210000 |
| B9…B32 | t | fire exposure duration, fill-down 5→120 step 5 | min | input | 5,10,…,120 |

### 3. Outputs (per row, indexed by t)
| cell (row 9 shown) | symbol | meaning | unit | cached (t=5min) |
|---|---|---|---|---|
| D4 | fy(20°C) | base yield strength | MPa | 355 |
| D5 | fu(20°C) | base ultimate strength | MPa | 510 |
| C9 | θ | gas/steel temperature at t | °C | 576.41 |
| D9 | Kfy | yield-strength reduction factor at θ | — | 0.543128 |
| E9 | KE | modulus reduction factor at θ | — | 0.378410 |
| F9 | fu,θ | reduced ultimate strength | MPa | 276.995 |
| G9 | fy,θ | reduced yield strength | MPa | 192.810 |
| H9 | Eθ | reduced elastic modulus | MPa | 79466.0 |

### 4. Calculation steps (dependency order, row i = 9..32, t=5..120 step5)
1. `fy(20°C)[D4] = IF(D2="s235",235,IF(D2="s275",275,355))` = 355 MPa (grade text compare is case-insensitive in Excel).
2. `fu(20°C)[D5] = IF(D2="s235",360,IF(D3="s275",430,510))` = 510 MPa — **note D3, not D2, in 2nd branch (bug, §7)**.
3. `θᵢ[Cᵢ] = 20 + 345·log10(8·tᵢ + 1)` — ISO 834 standard fire curve, °C, t in minutes.
4. `Oᵢ[floor bracket] = FLOOR(θᵢ/100,1)·100` (lower 100°C bracket), `Pᵢ = Oᵢ+100` (upper bracket).
5. `Kfy,ᵢ[Dᵢ] = VLOOKUP(Pᵢ,Tab,2) + (VLOOKUP(Oᵢ,Tab,2) − VLOOKUP(Pᵢ,Tab,2))·(Pᵢ−θᵢ)/100` — linear interpolation of Table 3.1 col "Kfy" between the two bracketing 100°C rows (Tab = B35:D47).
6. `KE,ᵢ[Eᵢ]` — same formula, using Tab col "KE".
7. `fu,θ,ᵢ[Fᵢ] = fu(20°C)·Kfy,ᵢ` (fire code doesn't distinguish fu reduction; uses same Kfy).
8. `fy,θ,ᵢ[Gᵢ] = fy(20°C)·Kfy,ᵢ`.
9. `Eθ,ᵢ[Hᵢ] = E(20°C)·KE,ᵢ`.

### 5. Lookup tables
`B35:D47` — EN1993-1-2 Table 3.1 (reduction factors vs. temperature). Key col B (°C, 20..1200 step 100, exact rows 20,100,200,…1200); col C=Kfy, col D=KE. Interpolation: exact match via VLOOKUP(…,FALSE) at bracket endpoints, then linear interpolation vs. θ (step 3 formula above) — table itself is exact/step values, not pre-interpolated.

### 6. Hardcoded constants
- `20 + 345·log10(8t+1)` — ISO 834 nominal fire curve formula (EN1991-1-2 Annex, standard temp-time curve), constants 20(°C ambient), 345, 8 are code-fixed.
- fy/fu base values 235/360, 275/430, 355/510 MPa — steel grade nominal values (EN10025), duplicated independently from `acciaio-colonne-ec3/materiali.txt` (same numbers, separate hardcoded table — no shared reference).
- Table 3.1 values (kfy, kE columns, rows 20–1200°C) — EN1993-1-2 Table 3.1 verbatim.

### 7. Suspected bugs / fragile spots
- **D5 (fu 20°C) formula bug**: `=IF(D2="s235",360,IF(D3="s275",430,510))` — second condition tests `D3` (=210000, the elastic modulus number) instead of `D2` (grade text). Since D3 is never "s275", this branch is always false, so **S275 grade always returns fu=510 (the S355 value) instead of 430**. Only S235 (first branch) and S355 (fallback) compute correctly. Verified by reading formula text directly.
- Case-insensitive text compare (`"s235"` vs dropdown `"S235"`) works correctly in Excel by default — flagged as looking suspicious but confirmed NOT a bug.
- fu,θ [Fᵢ] reuses `Kfy` (yield reduction factor) rather than a dedicated ultimate-strength reduction factor — EN1993-1-2 doesn't tabulate a separate fu reduction, so this is standard practice, not a bug.
- No bounds check on `t`; formula θ=20+345log10(8t+1) is unbounded — for t>120min (beyond table's last row) the tool has no row, and if reused for t→0 gives θ→20°C only at t=0 exactly (fine, monotonic).
