# Sisma — NTC 2018 §3.2 Seismic Action Spectrum

Workbook: `sisma.xls[x]`, sheets `Sisma` (main), `Foglio2` (dead/unused), `Tabelle` (lookups), `Comuni` (shared byte-identical with `vento/Comuni`).

Case-insensitivity note: Excel text comparisons (`I25="slv"`, `I26="A"`, etc.) are case-insensitive. Any reimplementation MUST lower/upper-case both sides before comparing, or dropdown values ("SLV","B",...) will never match literal formula strings ("slv").

---

## Tool 1 — `comune-lookup`
**Purpose:** Resolve Provincia/Regione from Comune name (no code clause; administrative lookup feeding site-hazard step).
**Inputs:** `Sisma!I4` Comune (free text, dropdown-like, ex "Brembate")
**Outputs:**
| cell | symbol | meaning | cached |
|---|---|---|---|
| I5 | Provincia | `=VLOOKUP(I4,Comuni!D:J,6,FALSE)` | "Bergamo" |
| I6 | Regione | `=VLOOKUP(I4,Comuni!D:J,7,FALSE)` | "Lombardia" |
**Table:** `Comuni!D1:J8102` — key col D (Comune name), exact match. Col I mirrors col B (Provincia), col J mirrors col A (Regione), via per-row `=B{row}`/`=A{row}` fill-down (7443+626+... rows, all cached in CSV). Shared 1:1 with `vento` unit's Comuni sheet.

## Tool 2 — `vita-riferimento`
**Purpose:** NTC18 §2.4.3 — vita di riferimento VR and return periods TR for the 4 limit states (§3.2.1, eq. 3.2.1: TR = −VR/ln(1−PVR)).
**Inputs:**
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| I7 | VN | vita nominale | anni | number | 50 |
| I8 | Classe | classe d'uso | - | enum I,II,III,IV | "II" |
**Outputs:**
| cell | symbol | meaning | cached |
|---|---|---|---|
| I9 | Cu | coefficiente d'uso, `=HLOOKUP(I8,Tabelle!C2:F3,2,FALSE)` | 1 |
| I10 | VR | `=I9*I7` | 50 anni |
| D13/E13 | TR,SLO | `=ROUND(-I9*I7/LN(1-0.81),0)` | 30 anni |
| D14/E14 | TR,SLD | `=ROUND(-I9*I7/LN(1-0.63),0)` | 50 anni |
| D15/E15 | TR,SLV | `=ROUND(-I9*I7/LN(1-0.10),0)` | 475 anni |
| D16/E16 | TR,SLC | `=ROUND(-I9*I7/LN(1-0.05),0)` | 975 anni |
(C13:C16 are display-string concatenations of the same, e.g. `"SLO="&...&" anni"`.)
**Table:** `Tabelle!C2:F3` — header row2 = classe (I,II,III,IV), row3 = Cu (0.7,1,1.5,2). Exact match, HLOOKUP.

## Tool 3 — `parametri-sito` (site hazard + soil/topo amplification)
**Purpose:** NTC18 §3.2.2/§3.2.3.2.1, Tab. 3.2.IV/3.2.V. ag, F0, T*C are NOT computed here — they are direct manual user inputs, normally read off the official INGV seismic-hazard grid for the comune/TR pair (workbook has no reticolo lookup for these three).
**Inputs:**
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| I26 | categoria sottosuolo | soil category | - | enum A-E | "B" |
| I27 | categoria topografica | topographic category | - | enum T1-T4 | "T1" |
| I28 | T*C | period at start of constant-velocity branch | s | number (manual) | 0.272 |
| I29 | F0 | max spectral amplification factor | - | number (manual) | 2.436 |
| I30 | ag | peak horizontal ground accel. | g | number (manual) | 0.098 |
**Outputs:**
| cell | symbol | meaning | cached |
|---|---|---|---|
| I31 | Cc | stratigraphic period-correction, `=VLOOKUP(I26,Tabelle!D7:F11,3,FALSE)` | 1.42718 |
| I32 | Ss | stratigraphic amplification, `=VLOOKUP(I26,Tabelle!D7:F11,2,FALSE)` | 1.2 |
| I33 | ST | topographic amplification, `=VLOOKUP(I27,Tabelle!A7:B10,2,FALSE)` | 1 |
| I34 | S | `=I33*I32` (soil coeff.) | 1.2 |
**Tables:**
- `Tabelle!A7:A10→B7:B10`: categoria topografica → ST. T1=1, T2=1.2, T3=1.2, T4=1.4 (Tab. 3.2.V). Exact key match.
- `Tabelle!D7:D11→E7:E11(Ss),F7:F11(Cc)`: categoria sottosuolo A-E, exact key match.
  - Cc: A=1, B=`1.1*T*C^-0.2`, C=`1.05*T*C^-0.33`, D=`1.25*T*C^-0.5`, E=`1.15*T*C^-0.4` (Tab. 3.2.IV).
  - Ss: A=1; B=`clip(1.40−0.40·F0·ag, [0.4,1.2])`; C=`clip(1.70−0.60·F0·ag,[1,1.5])`; D=`clip(2.40−1.50·F0·ag,[0.9,1.8])`; E=`clip(2.00−1.10·F0·ag,[1,1.6])`.

## Tool 4 — `fattori-struttura`
**Purpose:** NTC18 §3.2.3.5/§7.3.1 — damping correction η and behaviour factor q for horizontal component; §7.3.3.2 vertical component factor.
**Inputs:**
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| I37 | ξ | smorzamento viscoso | % | number | 5 |
| I39 | q0 | max behaviour factor | - | number (manual, depends on structural typology) | 1.5 |
| I40 | regolare in altezza | height regularity | - | enum SI/NO | "SI" |
| I25 (via N25) | stato limite | limit state | - | enum SLO/SLD/SLV/SLC | "SLV" |
| I44 | q,v | vertical behaviour factor | - | number (manual, NTC fixes ≈1.5) | 1.5 |
**Outputs:**
| cell | symbol | meaning | cached |
|---|---|---|---|
| N25 | (internal) `=IF(I25="slv","slu",IF(I25="slc","slu","sle"))` | "slu" |
| I38 | η | `=SQRT(10/(5+I37))` | 1 |
| I41 | q | `=IF(N25="slu",IF(I40="si",I39,I39*0.8),1)` | 1.5 |
| I45 | η,v | `=1/I44` (labelled "coefficiente dissipativo", unusual naming — see bugs) | 0.666667 |
Note: I44/I45 are computed but **not consumed** by any formula elsewhere in the sheet — no vertical spectrum table exists here (see bugs §7).

## Tool 5 — `parametri-spettro`
**Purpose:** NTC18 §3.2.3.2.1 — corner periods of the horizontal spectrum.
**Inputs:** I31 (Cc), I28 (T*C), I30 (ag) [I49 depends on I31,I28; I50 depends on I30 only]
**Outputs:**
| cell | symbol | expression | cached |
|---|---|---|---|
| I49 | TC | `=I31*I28` (=Cc·T*C) | 0.388193 s |
| I48 | TB | `=I49/3` | 0.129398 s |
| I50 | TD | `=4*I30+1.6` (ag in g) | 1.992 s |

## Tool 6 — `spettro-risposta` (main output)
**Purpose:** NTC18 §3.2.3.2.1 eq. 3.2.4–3.2.7 — elastic/design response spectrum Se(T)/Sd(T), horizontal component, sampled every 0.05 s from 0 to 5 s (96 points, index rows 55-149 in sheet, i.e. k=0..94).
**Inputs:** N25 (slu/sle flag), I29 (F0), I30 (ag), I34 (S), I38 (η), I41 (q), I48 (TB), I49 (TC), I50 (TD)
**Calculation (indexed step, k=0..94):**
- T₀ = 0 (row55). Tₖ = IF(Tₖ₋₁+0.05 < TD, Tₖ₋₁+0.05, IF(Tₖ₋₁≥TD, Tₖ₋₁+0.05, TD)) for k≥1 — i.e. step +0.05 s, but insert one exact breakpoint at T=TD before continuing past it. Last row (k=94, row149) is hardcoded T=5 (not formula).
- Se,raw(Tₖ):
  - 0≤T<TB: `η·ag·S·F0·[T/TB + (1/F0)·(1−T/TB)]`
  - TB≤T<TC: `η·ag·S·F0`
  - TC≤T<TD: `η·ag·S·F0·(TC/T)`
  - T≥TD: `η·ag·S·F0·(TC·TD/T²)`
  (N column, cell N{row})
- Output ordinate: `Sd(Tₖ) = IF(N25="slu", Se,raw/q, Se,raw)` — divides by behaviour factor q only for ULS-type states (SLV/SLC); SLO/SLD (SLE) output the elastic value unreduced. (J column)
- H column: text flag `"Td"`/`"TD"` (case varies, cosmetic) when Tₖ=TD, else "".
**Outputs:** table `I55:J149` = (T [s], Sd or Se [g]) — 95 points.
**No explicit pass/fail cells** exist in this sheet; it is a spectrum generator, not a verifica.

---

## Shared data
- `Comuni!D:J` (7443+~700 rows) — Comune→Provincia/Regione, byte-identical to `vento/Comuni`; build once, reuse across units.
- `Tabelle!C2:F3` — Cu by classe d'uso (reused wherever VR is needed).
- `Tabelle!A7:F11` — ST/Ss/Cc lookup block by categoria topografica/sottosuolo.

## Upstream (values that in practice come from elsewhere)
- I28 (T*C), I29 (F0), I30 (ag): sourced from INGV national seismic-hazard grid for the comune's coordinates and the chosen TR (SLV here); not derivable from this workbook alone — treat as required manual/external inputs to Tool 3.
- Comune (I4) likely shared with `vento` and `neve` units' comune selector.

## Suspected bugs / fragile spots
1. **`Tabelle!E8` (Ss, categoria sottosuolo B) wrong lower clip bound.** Formula clips to `[0.4, 1.2]`; NTC Tab.3.2.IV requires `[1.00, 1.20]` for category B (all other categories C/D/E use correct bounds 1/1.5, 0.9/1.8, 1/1.6). Only manifests when `1.40−0.40·F0·ag < 1.0` (very high F0·ag ≈ >1.0), not triggered by the golden case (raw value 1.3045→clipped 1.2). Re-implement with lower bound 1.00.
2. **Vertical component (I44/I45) computed but unused** — no vertical spectrum table is built from η,v/q,v anywhere in the extracted cellmaps; either out of scope for this workbook or a dead/incomplete feature.
3. **`Foglio2` sheet is dead/broken**: references `$E$8,$E$9,$E$5,$E$6,$E$15..$E$18` which are blank/out-of-range in this workbook (not in the 22-44 row block shown), producing cached `0`s and an explicit `#DIV/0!` at S42. Do not port; looks like an abandoned scratch copy of the spectrum calc (compare its T,S formulas — same NTC structure as Tool 6, different cell layout).
4. **`Tabelle!D14:D16`** duplicate CC/SS/ST lookups referencing `Sisma!$F$14`, `Sisma!R8:R12` (outside the extracted Sisma range, likely blank) — orphaned/unused legacy formulas, not referenced by any cell in Tool 1-6. Ignore.
5. **Case-sensitivity mismatch by convention only**: `N25` compares `I25` (uppercase dropdown "SLV"/"SLC") against lowercase literals `"slv"/"slc"` — works in Excel (case-insensitive compare) but will silently always-fail in a case-sensitive language if ported naively.
6. **H-column "Td" vs "TD" label** inconsistent casing across rows 56-90 ("Td") vs 94-149 ("TD") — cosmetic only, values unaffected.

## Golden test case
```
Input:
  comune=Brembate, VN=50, classe=II, statoLimite=SLV,
  categoriaSottosuolo=B, categoriaTopografica=T1,
  Tc_star=0.272, F0=2.436, ag=0.098, xi=5, q0=1.5,
  regolareAltezza=SI, q_vert=1.5
Output:
  provincia=Bergamo, regione=Lombardia
  cu=1, VR=50
  TR_SLO=30, TR_SLD=50, TR_SLV=475, TR_SLC=975
  Cc=1.42718, Ss=1.2, ST=1, S=1.2
  eta=1, q=1.5, eta_vert=0.666667
  TB=0.129398, TC=0.388193, TD=1.992
  spettro: (T=0, Sd=0.1176) (T=TB=0.129398, Sd=0.190982)
           (T=TC=0.388193, Sd=0.190982) (T=TD=1.992, Sd=0.0372179)
           (T=5.0, Sd=0.00590732)  [96 points total, step 0.05s]
```
