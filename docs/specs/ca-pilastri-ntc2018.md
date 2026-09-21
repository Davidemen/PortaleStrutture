# ca-pilastri-ntc2018 — Spec (DELTA vs ca-pilastri.md)

Workbooks: `pilastri-rettangolari.xlsx`, `pilastri-circolari.xlsx` (NTC2018 + Circolare 2019 revision).
Same two tools, same `Tabelle` sheet (byte-identical to the NTC2008 version — reuse that lookup logic
unchanged). **Read `docs/specs/ca-pilastri.md` first**; this file only documents what changed. Title
cells (A1/A2) were reworded to reference "NTC2018 e Circolare" — cosmetic.

## Row-shift note (both sheets)
A new row 4 header ("DATI DI INPUT") was inserted, but **only in the main input/output column range**
(A,G,H,I,J,K,L) — the material-property/confinement side-annex (columns P,Y,Z,AB,CW,CX,CY,CR,CS,CT,DA)
was NOT shifted and keeps the exact same row numbers as the NTC2008 sheet (Z5,Z6,Z7,Z8,Z9,Z13,Z14,
Z15,Z16,Z17,Y18,Y20,CX20‑CX47,DA25‑27,hcr,Z24/Z25 — all unchanged addresses). Net effect: every
**main-flow** input/output cell address is old-address **+1 row**; every **side-annex** cell keeps
its NTC2008 address, with only its cell *references* into the main flow bumped by 1.
Circular sheet mirrors this exactly (main flow shifted +1; DK:EJ/DG:EJ drawing-helper columns still
excluded, irrelevant to the engineering result).

---
## Tool: pilastri-rettangolari

### 1. Purpose + code refs
Unchanged from ca-pilastri.md §Tool:pilastri-rettangolari/1, same checks, same clause set
(NTC2018 §4.1.2.1.1.1/.3, §4.1.2.1.3.2, §7.4.4.2.1 "?", §7.4.6.2.1/.2, §4.1.6.1.3). **MRd is still
a pure user input** (now at H25, unlocked) — no M-N domain is computed.

### 2. Inputs (sheet `Pilastri rettangolari`) — new addresses
| cell | symbol | meaning | unit | type/range | cached |
|---|---|---|---|---|---|
| H6 | L1 | lato base | mm | number* | 400 |
| H7 | L2 | lato altezza | mm | number* | 400 |
| H8 | H | altezza netta pilastro | mm | number* | 3500 |
| H9 | — | tipo acciaio | — | enum $DA$7:$DA$11 (unchanged list) | "B450C" |
| H10 | — | tipo cls | — | enum $CX$7:$CX$14 (unchanged list) | "C25/30" |
| H11 | Ned | azione assiale | kN | number* | 1200 |
| H12 | Ved | taglio agente | kN | number* | 150 |
| H13 | Med | momento agente | kNm | number* | 80 |
| H14 | c | copriferro (asse barra) | mm | number* | 50 |
| H15 | — | numero ferri verticali | — | int* | 8 |
| H16 | Ø | diametro ferri verticali | mm | number* | 16 |
| H17 | Ø | diametro staffe | mm | number* | 10 |
| H18 | p | passo staffe | mm | number* | 150 |
| H25 | MRd | momento resistente (**external input**), unlocked; validation note "H25 None: 0" ⇒ numeric ≥0 | kNm | number* | 160 |
| J54 (new) | β | coefficiente vincolo per luce libera inflessione, hardcoded | — | =1 | 1 |
| Z27 | — | numero ferri lato corto L1 | — | int* (unchanged addr) | 3 |

### 3. Outputs — new addresses (unchanged addr in *italics*)
| cell | symbol | meaning | cached |
|---|---|---|---|
| *Z17* | VRd | taglio resistente [kN] | 322.696 |
| *Y18* | — | verifica taglio | "OK" |
| *Y20* | — | verifica gerarchia (uses H25/H8 now) | "OK" |
| H24 / J24 | rs | As/Ac + check | 0.0100531 / "OK" (**check simplified, §7**) |
| G26 / K26 | — | verifica flessione / tasso % (label "T.L." not "Tasso") | "Mrd > Med -> OK" / 50 |
| G28 / K28 | — | verifica compressione / tasso % | "Nrd > Ned -> OK" / 53.15 |
| J53 | λlim | snellezza limite (**FIXED, §7**) | 34.2904 |
| J55 | l0 | luce libera inflessione = H·β (**FIXED, §7**) | 3500 |
| J56 | i | raggio d'inerzia, ora su sezione lorda (**CHANGED, §7**) | 115.47 |
| J57 | λ | snellezza | 30.3109 |
| J58 | — | verifica snellezza (λ<λlim) | "OK" |
| J61‑J65 | — | dettagli costruttivi (Ø min long., interasse max long., As min, Ø min staffe, interasse max staffe) | all "OK" |

### 4. Calculation steps — deltas from ca-pilastri.md §4 (same numbering intent, new refs)
Steps 1‑27 of the base spec are structurally identical; every H/G/J/K/Y reference used there is now
+1 row (γs/γc/fyd/fcd/cotθ lookups at Z5‑Z9/Z13 unchanged; e_min/MedEcc/MedCalc/Ac/As/rs now at
H19‑H24; VRdc/VRds/VRd still Z15/Z16/Z17). Only real formula changes:
- **CX38 (ac selector)**: `=IF(H11=0, CX32, IF(CX31<CY36,CX33,IF(CX31<CY37,CX34,CX35)))` — condition
  is now `Ned=0` (H11) instead of NTC2008's dead `H7<0` (column height). ac=1 branch now reachable
  when there is genuinely no axial load, though still not `σcp<0` (net tension) as one might expect.
- **H24 (rs) check, J24**: `=IF(H24<0.04,"OK","NO")` — **dropped the NTC2008 min-ratio comparison**
  (`rs>MAX(DA25:DA27)`); now only checks the 4% ceiling. DA25:27 (min-ratio envelope) are still
  computed but no longer feed this check (min-ratio is still enforced separately via the row-63
  "Area minima barre long." detailing check).
- **J53 (λlim)**: `=25/SQRT(H11*1000/((H6*H7)*Z9))` — **the NTC2008 kN→N bug is fixed**: Ned (H11,
  kN) is now ×1000 before dividing by Ac·fcd (N). Formula/constant "25" otherwise unchanged.
- **J54 (β, new)** = 1 (hardcoded, unlocked but never exposed as a real user field in this sheet).
- **J55 (l0)** = `=H8*J54` — **replaces the NTC2008 hardcoded l0=3000mm**; now l0 = H·β = column clear
  height × β (β=1 ⇒ l0=H exactly, i.e. free length equal to the input clear height).
- **J56 (i)** = `=SQRT(((MIN(H6:I7))^3*(MAX(H6:I7))/12)/((H6)*(H7)))` — **now uses gross L1×L2**
  (no `−2c`); NTC2008 used net/core dimensions. For square section this is exactly L/√12.
- **J57 (λ)** = J55/J56. **J58 (verifica)** = `IF(J57<J53,"OK","NO")`.

### 5. Lookup tables
Unchanged — see ca-pilastri.md §5 (Tabelle!M45:P49, M34:O41 exact-match VLOOKUPs; CX45:CX47 and
CX20:CX23 local candidate tables, same formulas, refs bumped +1 only where they point into main flow).

### 6. Hardcoded constants — deltas
- γs=1.15, γc=1.5, αcc=0.85, α=90°, ν1=0.5, cotθ clamp [1,2.5] — **all unchanged**.
- **NEW**: β=1 (buckling-length coefficient, J54) — replaces the old flat l0=3000mm constant.
- 175mm confined-zone spacing candidate, λlim coefficient "25" — **still present, unchanged/unexplained**.
- Ac min-steel envelope multipliers 0.003/0.10·Ned/fyd/0.01 — unchanged (though no longer consumed by
  the rs pass/fail cell, §4).

### 7. Suspected bugs / fragile spots — status vs ca-pilastri.md §7
1. **λlim units bug — FIXED.** J53 now includes the ×1000 kN→N conversion (confirmed: cached 34.2904
   = 25/√(1,200,000/2,257,600), matches hand calc; NTC2008 gave 1084.36).
2. **l0=3000mm hardcoded, unrelated to H — FIXED.** l0 now = H·β (β=1); still no way to model a real
   effective-length factor other than 1 (β is a constant, not exposed for a fixed/pinned choice) — a
   reimplementation should treat β as a real input (default 1) rather than a silent constant.
3. **Radius of gyration on net section — CHANGED (now standard).** J56 now uses gross L1×L2 (matches
   the classic i=h/√12 for a rectangular section); the NTC2008 net-section variant is gone.
4. **Circular-perimeter formula reused on rectangular sheet (CX24)** — **still present, unchanged**;
   same bug as ca-pilastri.md §7.2.
5. **ac selector dead branch — changed but still questionable.** Now keyed on `Ned=0` (H11=0) instead
   of the always-false `H(height)<0`; reachable only for the edge case of zero axial force, still not
   the physically-meaningful `σcp<0` (net tension) condition. "?" whether this was an intentional partial
   fix or another typo (`H11=0` vs a plausible intended `CX31<0`).
6. **rs pass/fail simplified — possible regression.** J24 dropped the `rs>MAX(min-ratio envelope)`
   comparison present in NTC2008; the minimum-steel-ratio requirement is only re-enforced elsewhere
   (row 63 "Area minima barre long." vs H23). Functionally the two checks were largely redundant, but
   the redundancy removal means the top-line "rs" cell no longer reports a min-ratio failure directly.
7. **Capacity-design shear demand (Y20, uses H25/(H8/1000))** — unchanged "?" from ca-pilastri.md §7.5
   (still single MRd/H, not 2·MRd/H).
8. **Circular reference for cotθ** — unchanged fragile pattern (Z13↔CX43), same as ca-pilastri.md §7.4.

### 8. Golden test case
```
inputs: L1=400 L2=400 H=3500 acciaio=B450C cls=C25/30 Ned=1200 Ved=150 Med=80 c=50 nFerri=8 ØFerri=16 Østaffe=10 pStaffe=150 MRd=160
fyd=391.304 fcd=14.11 z=315 cotTheta=2.5 sigmaCp=7.5 ac=1.17116 (unchanged from NTC2008 example)
Ac=160000 As=1608.5 rs=0.0100531(OK, single-condition check) eMin=20 MedEcc=24 MedCalc=80
VRdc=358.991 VRds=322.696 VRd=322.696 tagliOK=OK gerarchiaOK=OK
MRd_vs_MEd="Mrd > Med -> OK"(50%) NRcd=2257.6 compressioneOK="Nrd > Ned -> OK"(53.15%)
lambdaLim=34.2904(FIXED, was 1084.36) beta=1 l0=3500(FIXED, was 3000) i=115.47(gross, was 86.6025 net)
lambda=30.3109(was 34.641) snellezzaOK=OK (still passes, but with a real margin now — 34.29 vs 30.31,
not the ~31x-inflated NTC2008 limit)
```

---
## Tool: pilastri-circolari

### 1. Purpose + code refs
Unchanged from ca-pilastri.md — equivalent-square shear transform, same clauses.

### 2. Inputs (sheet `Pilastri circolari`) — new addresses, deltas from rect
| cell | symbol | meaning | cached |
|---|---|---|---|
| H6 | D | diametro | 400 |
| H8 | H | altezza netta | 5000 |
| H9/H10/H11/H12/H13/H14/H15/H16/H17/H18/H25 | (same roles as rect, all +1 vs NTC2008) | B450C/C25\/30/1200/150/80/50/25/16/10/150/160 |
| J61 (new) | β | luce libera inflessione coeff., hardcoded | 1 |
| G6 | — | label formula `=IF(G5="Rettangolare","H","D")` (G5 static "Circolare") — cosmetic, unchanged logic, ref bumped | "D" |

### 3. Outputs — same cell roles as rect (addresses per §3 above, circular geometry)
| cell | meaning | cached |
|---|---|---|
| Z17 VRd [kN] | | 222.666 |
| Y18/Y20 taglio/gerarchia | | OK/OK |
| H24/J24 rs | | 0.04 → **"NO"** (still fails at the 4% ceiling; check now single-condition like rect) |
| G26/K26 flessione | | "Mrd > Med -> OK" / 50% |
| G28/K28 compressione | | "Nrd > Ned -> OK" / 67.68% |
| J60 λlim | | 30.3891 (**FIXED**, was 960.988) |
| J62 l0 | | 5000 (**FIXED**, =H·β, was hardcoded 3000) |
| J63 i | | 100 (**CHANGED**, =D/4 gross, was (D−2c)/4=75 net) |
| J64 λ | | 50 (was 40) |
| J65 verifica | | **"NO"** — λ(50) is now > λlim(30.39): the fixed formula makes this golden case FAIL slenderness (NTC2008's buggy λlim=960.988 always passed) |
| J68‑J72 dettagli | | all "OK" (unchanged) |

### 4. Calculation steps — deltas from rect tool (§4 above applies identically)
- H22 (Ac) unchanged dead branch: `=IF(G5="rettangolare",H6*H7,PI()*H6^2/4)` → 125664 (G5="Circolare"
  text never matches lowercase "rettangolare", same harmless dead code as ca-pilastri.md §7.2/circ).
- CX17/CX18 (equivalent-square side, `=H22^0.5`) unchanged, used in place of L1/L2 exactly as before.
- **CX38 ac selector**: same `IF(H11=0,...)` change as rect (§4 above) → cached 0.808062 (σcp=9.5493
  > 0.5fcd=7.055 branch, CX35=2.5·(1−σcp/fcd)).
- **J60 (λlim)** = `25/SQRT(H11*1000/((H6^2*PI()/4)*Z9))` — **FIXED** (×1000 added), cached 30.3891
  (25/√(1,200,000/1,773,120)).
- **J61 (β)** = 1 (new, same pattern as rect J54).
- **J62 (l0)** = `=J61*H8` = H·β → 5000 — **FIXED** (was hardcoded 3000, independent of H).
- **J63 (i)** = `=SQRT((PI()*H6^4/64)/(PI()*H6^2/4))` = D/4 (gross) → 100 — **CHANGED** (was
  (D−2c)/4=75, net/core diameter).
- **J64 (λ)** = J62/J63 = 50. **J65 (verifica)** = `IF(J64<J60,"OK","NO")` → **"NO"** with this input set.
- **H24 (rs) check J24** = `IF(H24<0.04,"OK","NO")` — same simplification as rect; at exactly 0.04 the
  strict `<` still fails → "NO" (same outcome as NTC2008, different reasoning: no envelope comparison).

### 5-6. Lookup tables / constants
Same as rect §5-6 plus equivalent-square side = √Ac (CX17/CX18), unchanged mechanism.

### 7. Suspected bugs / fragile spots — status vs ca-pilastri.md §7 (circ)
1. **λlim units bug — FIXED** (J60, same fix as rect).
2. **Dead "rettangolare" branch in Ac (H22) — unchanged**, still harmless (G5 fixed text "Circolare").
3. **l0 hardcoded — FIXED** (J62 = H·β, β=1 constant as in rect; same caveat that β isn't a real
   exposed input).
4. **i on net/core diameter — CHANGED to gross** (J63 = D/4 instead of (D−2c)/4) — now the standard
   circular radius-of-gyration formula.
5. **Equivalent-square shear approximation** — unchanged, still unverified against a specific
   NTC/EC2 circular-column clause ("?").
6. **Slenderness check now materially stricter**: with the golden inputs (D=400, H=5000mm — a fairly
   slender column), the fixed formula gives λ=50 > λlim=30.39 → **fails**, where the buggy NTC2008
   version always passed (λlim≈961). A reimplementation must not silently reuse NTC2008 cached
   "OK" expectations for regression tests on this sheet.
7. Same circular-reference cotθ pattern (Z13/CX43) as rect, unchanged.

### 8. Golden test case
```
inputs: D=400 H=5000 acciaio=B450C cls=C25/30 Ned=1200 Ved=150 Med=80 c=50 nFerri=25 ØFerri=16 Østaffe=10 pStaffe=150 MRd=160
fyd=391.304 fcd=14.11 Ac=125664 As=5026.55 rs=0.04(NO, single-condition check) L1fittizio=354.491
VRdc=222.666 VRds=222.666 VRd=222.666 tagliOK=OK gerarchiaOK=OK
MRd_vs_MEd="Mrd > Med -> OK"(50%) NRcd=1773.11 compressioneOK="Nrd > Ned -> OK"(67.68%)
lambdaLim=30.3891(FIXED, was 960.988) beta=1 l0=5000(FIXED, was 3000) i=100(gross, was 75 net)
lambda=50(was 40) snellezzaOK=NO (FLIPPED from OK to NO vs the NTC2008 golden case — key regression-test signal)
```
