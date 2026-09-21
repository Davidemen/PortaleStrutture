# ca-pilastri-ec2 — Delta Spec (EC2 variant vs NTC2018)

DELTA of `docs/specs/ca-pilastri.md`. Workbooks: same two files, extra sheets `Ret._UNI EN 1992-1-1
2005` (rect) and analogous circular sheet, both titled "Progetto e verifica pilastri in c.a. secondo
UNI EN 1992-1-1:2005". All row/col layout is shifted **+1 row** vs the NTC2018 sheet (an extra
"Tipologia di pilastro" label row inserted at top) and **+1 helper column-block row** later (new
"rapporto meccanico di armatura" row) — cell letters below are the EC2 sheet's own addresses, not
directly comparable 1:1 to the NTC2018 spec's cell letters. Everything not listed here is IDENTICAL
to `ca-pilastri.md` (same inputs semantics, same Tabelle lookups, same shear/hierarchy/detailing
logic, same bugs #2–#7 of the base spec unless noted fixed below).

## Shared: unchanged
`Tabelle!M45:P49` (steel), `Tabelle!M34:O41` (concrete), γs=1.15, γc=1.5 — identical constants and
lookups, EN1992-1-1 Tab.2.1N values coincide numerically with NTC2018 Tab.4.1.V. αcc=0.85 is
**still hardcoded** in fcd=fck·0.85/γc even on the "EC2" sheet — EN1992-1-1 §3.1.6(1) recommends
αcc=1.0 (0.85 is the Italian NAD choice), so this sheet is really "EC2 with Italian NAD", not pure
EC2 ("?", not flagged as a diff since formula text is byte-identical to NTC2018 sheet).

---
## Tool: pilastri-rettangolari-ec2 (delta vs rect NTC2018 tool)

### 1. Deltas + governing clauses
1. **ν1 in VRdc (shear, EC2 6.2.2(6))** — NTC sheet hardcodes ac·**0.5**·fcd; EC2 sheet uses
   ac·**ν1**·fcd where ν1 = `CX28` = 0.6·(1−fck/250) (VLOOKUP fck from `Tabelle!M34:Q41` col 3).
   Cell: `Z15(VRdc)` formula gains a `*CX28` factor. This is the correct EC2 6.2.2(6) reduction
   factor for shear-compression capacity, replacing the crude ν=0.5 constant.
2. **Slenderness limit, EC2 §5.8.3.1(1)** (was NTC §4.1.6.1.3 "25/√n" heuristic): fully replaced by
   `λlim = 20·A·B·C/√n` with A=0.7 (hardcoded, EC2 default for unknown creep φef), B=√(1+2ω)
   (ω=mechanical reinforcement ratio, new row `rapporto meccanico di armatura` = `CX49` =
   fyd·As/(fcd·Ac)), C=0.7 (hardcoded, EC2 default for unknown moment ratio rm), n = Ned·1000/
   (Ac·fcd) — **and this EC2 formula correctly includes ×1000**, fixing the NTC sheet's missing-×1000
   bug (base spec §7.1) as a side effect of the rewrite. Cell: row "Snellezza limite" `J`.
3. **Detailing, EC2 §9.5.2(1) min bar Ø**: 12mm (NTC) → **8mm** (EC2) — cell `J`="Diametro minimo
   barre long.".
4. **Detailing, EC2 §9.5.3(3) stirrup spacing (non-confined)**: candidates `12·Ø_long`/`250mm` (NTC)
   → `20·Ø_long`/`400mm` (EC2) — cells `CX` at "Passo massimo staffe" rows (the two `MIN()` inputs).
5. **Detailing, EC2 §9.5.3(3) added 3rd spacing candidate**: "Interasse massimo staffe" check becomes
   `MIN(CX20,CX21,MIN(H6,H7))` (rect: adds "not more than least column dimension b") vs NTC's
   `MIN(CX20,CX21)` — EC2 explicitly caps stirrup spacing at the column's smaller side, NTC sheet
   omitted this candidate (arguably an NTC-side gap, now closed).
6. **Detailing, EC2 §9.5.2(2) min longitudinal steel coefficient**: `0.002·Ac` (EC2) vs `0.003·Ac`
   (NTC) as one of the two min-As candidates (other candidate `0.10·Ned/fyd` unchanged).
7. **Min-As combination rule fixed**: "Area minima barre long." check uses `MAX(CX25,CX26)` (EC2,
   correct — EC2 9.5.2(2) requires As≥max of the two candidates) vs NTC's `MIN(CX25,CX26)` (base
   spec did not flag this as a bug, but comparison shows EC2 is the standard-correct combinator).
8. **New explicit max-As check**: EC2 adds a standalone "Area massima barre long." row,
   `J=0.04·Ac`, `L=IF(J>=As,"OK","NO")` — NTC sheet folds this into the `rs<0.04` check on H24/J24
   only; EC2 duplicates it as its own detailing line (cosmetic, not a numeric delta).
9. Text-only: title cell, "PROPRIETÁ"→"PROPPRIETÁ" typo (cosmetic), "T.L."→ same in rect ("Tasso" in
   circ tool, cosmetic wording only).

### 2. Inputs — identical cells/roles to base spec, shifted +1 row
H6=L1(400), H7=L2(400), H8=H(3500), H9=acciaio, H10=cls, H11=Ned(1200), H12=Ved(150), H13=Med(80),
H14=c(50), H15=nFerri(8), H16=Ø ferri(16), H17=Ø staffe(10), H18=passo staffe(150), H25=MRd(160,
external input, unchanged role). Z27→row-shifted "numero ferri lungo L1"=3 (same cell name pattern).

### 3. Outputs — same roles, shifted rows; two behave differently (see golden case)
Z17(VRd), Y18(taglio OK), Y20(gerarchia OK), H24/J24(rs+check), G26/K26(flessione), G28/K28
(compressione), row54 J (λlim, new formula), row58 J (λ), row58/66 "Verifica" (OK/NO, **now can
legitimately fail** — see golden case), rows 61-66 detailing (5 checks + 1 new max-As check = 6).

### 4. Calculation steps — only the changed ones (others identical to base spec §4, shifted)
1. `CX28 = ν1 = 0.6*(1-VLOOKUP(H10,Tabelle!M34:Q41,3,FALSE)/250)` → 0.54024.
2. `Z15 = VRdc = z*L1*ac*CX28*fcd*(cotα+cotθ)/(1+cotθ²)/1000` (was `*0.5*fcd`).
3. `CX49 (ω) = Z8(fyd)*H24(As)/Z9(fcd)/H23(Ac)` → mechanical reinforcement ratio.
4. `n = H11(Ned)*1000/(H6*H7)(Ac)/Z9(fcd)` (dimensionless axial load ratio, correct ×1000).
5. `λlim = 20*0.7*SQRT(1+2*CX49)*0.7/SQRT(n)`.
6. `l0 = β*H` with β=1 hardcoded (renamed "Coeff. Per l0", same role as base spec's l0 row but now
   at least multiplies the real H8 input — β itself still fixed at 1, not derived from end
   conditions, "?").
7. `i (radius of gyration)` — formula UNCHANGED from NTC sheet (still net/core-section based,
   base spec §7.6 caveat applies identically).
8. Detailing thresholds: min bar Ø=8 (was 12); stirrup spacing candidates 20·Ø/400mm (was 12·Ø/
   250mm) + new `MIN(H6,H7)` candidate; min-As=MAX(0.002·Ac, 0.10·Ned/fyd); max-As=0.04·Ac (new row).

### 5. Lookup tables — unchanged from base spec, plus:
`Tabelle!M34:Q41` col 3 = fck (same column as base spec's O, just VLOOKUP'd with a wider table
reference `M34:Q41`) — feeds ν1.

### 6. Hardcoded constants (new/changed vs base spec §6)
- ν1 formula 0.6·(1−fck/250) replaces hardcoded 0.5 (EC2 6.2.2(6)).
- λlim: A=0.7, C=0.7 hardcoded defaults (EC2 5.8.3.1(1) notes 1&3 fallbacks — should ideally be
  computed from creep ratio and end-moment ratio rm, not assumed).
- Stirrup spacing constants 20·Ø / 400mm (EC2 9.5.3(3)); min bar Ø=8mm (EC2 9.5.2(1)); min-As
  coefficient 0.002 (EC2 9.5.2(2)).
- αcc=0.85 still hardcoded (unchanged; "?" whether intentional NAD retention on the EC2 sheet).

### 7. Suspected bugs / fragile spots (delta-specific)
1. **λlim ×1000 bug is FIXED here** (not present in EC2 sheet) — a reimplementation must NOT port
   the NTC sheet's missing-×1000 bug into the EC2 variant.
2. **A, C = 0.7 hardcoded** in λlim (LOW/uncertain, "?") — EC2 allows more refined A,C from actual
   creep and end-moment data; sheet always uses the conservative-ish defaults regardless of input,
   so λlim never reflects true end conditions.
3. Same cotθ circular reference, same dead `H8<0` ac branch (mislabeled row, same bug as base spec
   §7.3/7.4), same circular-perimeter-formula-on-rectangle bug (base spec §7.2) — all still present,
   unchanged by this variant.
4. **αcc=0.85 retained** on an "EC2" sheet ("?") — arguably should be 1.0 per bare EN1992-1-1, but
   Italian implementation keeps 0.85; not verifiable from the sheet alone which convention was
   intended.

### 8. Golden test case (rect, D≠— rectangular, same inputs as base spec's rect golden case)
```
inputs: L1=400 L2=400 H=3500 acciaio=B450C cls=C25/30 Ned=1200 Ved=150 Med=80 c=50 nFerri=8 ØFerri=16 Østaffe=10 pStaffe=150 MRd=160
nu1=0.54024 VRdc=387.883 VRds=322.696 VRd=322.696 tagliOK=OK gerarchiaOK=OK
omega(CX49)=0.278797 lambdaLim=16.7759 l0=3500 i=86.6025(unchanged) lambda=30.3109 snellezzaOK: NO (30.31 > 16.78, FAILS — contrast with NTC sheet's buggy "OK" at lambdaLim=1084 for the same geometry)
detailing: ØlongMin=8(OK) interasseLongMax uses 12·Ø/400mm-family(unchanged calc) AsMin=MAX(320,306.667)=320mm2 vs As=1608.5(OK) AsMax=0.04*160000=6400 vs As=1608.5(OK)
```
Note: the EC2 slenderness check genuinely fails on this geometry, unlike the NTC2018 sheet's bugged
"OK" — this is the headline behavioral divergence between the two variants for identical inputs.

---
## Tool: pilastri-circolari-ec2 (delta vs circ NTC2018 tool) — same deltas as rect, mirrored

Deltas #1,#2,#3,#4,#6,#7,#8 above apply identically (ν1 in VRdc via `CX28`; λlim EC2 formula with
`H6^2/4*PI()` in place of `H6*H7` for Ac; min bar Ø=8; stirrup spacing 20·Ø/400 with 3rd candidate
`MIN(H6,H7)`→ for circular sheet just `H6`(D) since single dimension; min-As via MAX; new max-As
row). No delta #5 distinction (circular has only D, so "least dimension" candidate is just D itself).

### Golden test case (circ, D=400, H=5000 — same inputs as base spec's circ golden case)
```
inputs: D=400 H=5000 acciaio=B450C cls=C25/30 Ned=1200 Ved=150 Med=80 c=50 nFerri=25 ØFerri=16 Østaffe=10 pStaffe=150 MRd=160
Ac=125664 As=5026.55 rs=0.04 -> NO (same ceiling-fail as NTC sheet)
nu1=0.54024 VRdc=240.586 VRds=222.666 VRd=222.666 tagliOK=OK gerarchiaOK=OK
omega(DB49)=1.1093 lambdaLim=21.3716 l0=5000(beta=1) i=100(unchanged, D/4) lambda=50 snellezzaOK: NO (50 > 21.37, FAILS — again contrasts with NTC sheet's buggy "OK" at lambdaLim=960.988)
```
