# ca-mensole — Spec

Workbook: `mensola-tozza.xlsx` (sheets: `Mensola tozza`, `Tabelle`). One tool.

## Tool: mensola-tozza (Progetto e verifica di mensole tozze)

### 1. Purpose + code refs
Verifies an RC short corbel ("mensola tozza", a ≤ ~h, strut-and-tie behaviour) loaded by a vertical
force PEd (and optional horizontal HEd) applied at distance `a` from the column face, per
**NTC 2018 §4.1.6.1.3** (Mensole tozze e denti Gerber) using strut-and-tie: steel-tie capacity PRS,
concrete-strut capacity PRC, hierarchy check PRS ≤ PRC (ductile failure), and PR > PEd. Material
factors γc, γs per **NTC2018 Tab. 4.1.V**; fcd formula per **NTC2018 §4.1.2.1.1.1**. Clause for the
strut/tie formulas themselves and for the 0.2·d, 0.4, 0.8, 0.5·PEd/fyd constants: "?" (matches a
known Italian design-guide formulation, not independently verified against the NTC text).

### 2. Inputs (sheet `Mensola tozza`)
| cell | symbol | meaning | unit | type/range | example |
|---|---|---|---|---|---|
| H5 | a | distanza del carico dal filo pilastro | mm | number* | 177 |
| H6 | h | altezza mensola | mm | number* | 450 |
| H7 | b | larghezza mensola | mm | number* | 800 |
| H8 | c | copriferro (asse barra) | mm | number* | 50 |
| H9 | PEd | carico verticale | kN | number* | 136 |
| H10 | HEd | carico orizzontale | kN | number* | 0 |
| H14 | — | tipo di acciaio | — | enum {B450C,FeB22k,FeB32k,FeB38k,FeB44k} (H14:H15 list $BU$16:$BU$20) | "B450C" |
| H15 | — | tipo di cls | — | enum {C20/25…C50/60} (list $BU$5:$BU$12) | "C32/40" |
| H16 | n° | n. ferri orizzontali | — | int* | 8 |
| H17 | Ø | diametro ferri orizzontali | mm | number* | 12 |
| H18 | n° | n. ferri inclinati | — | int* | 0 |
| H19 | Ø | diametro ferri inclinati | mm | number* | 0 |
| H22 | — | inclinazione armatura inclinata | ° | number* | 0 |
| H24 | n° | n. staffe orizzontali | — | int* | 3 |
| H25 | Ø | diametro staffe orizzontali | mm | number* | 12 |
| H29 | — | staffe verticali previste? | — | enum {SI,NO} | "NO" |

`H14`/`H15` values must match a row in the local BU-column lookup and (indirectly) in `Tabelle`'s
material tables — exact text match, no fallback.

### 3. Outputs
| cell | symbol | meaning | unit | cached value |
|---|---|---|---|---|
| H23 | As,lnk | area minima staffe/tiranti orizzontali richiesta | mm² | 226.195 |
| H28 | PRS | capacità lato acciaio (tie) | kN | 495.937 |
| H31 | PRC | capacità lato calcestruzzo (strut) | kN | 1595.16 |
| H32 | ΔPR | contributo armatura inclinata | kN | 0 |
| H33 | PR | capacità portante globale | kN | 495.937 |
| C34 | — | esito verifica (3-way text) | — | "Verifica soddisfatta: Pr > Ped" |
| A36 | — | nota area staffe insufficiente | — | "" |

C34 logic: `IF(PRS>PRC, "Gerarchia...non verificata", IF(PR>PEd, "...soddisfatta...", "...non soddisfatta..."))`
— hierarchy check first (brittle strut failure if steel stronger than concrete), else ULS check.
A36: `IF(n°staffe·2·π·Østaffe²/4 < As,lnk, "NOTA: As > di As,lnk", "")` (factor 2 = two legs/stirrup).

### 4. Calculation steps (dependency order)
Material props (sheet `Mensola tozza`, using `Tabelle` lookups):
1. `Z5` = γs = 1.15 (hardcoded, NTC Tab 4.1.V)
2. `Z6` = γc = 1.5 (hardcoded)
3. `Z7` = VLOOKUP(H14, Tabelle!M45:P49, col 3) → ftk [MPa] — **computed but never referenced downstream** (see §7)
4. `Z8` = fyd = VLOOKUP(H14, Tabelle!M45:P49, col 2) / Z5 = fyk/γs [MPa] → 391.304
5. `Z9` = fcd = VLOOKUP(H15, Tabelle!M34:O41, col 3) · 0.85 / Z6 = 0.85·fck/γc [MPa] → 18.8133

Geometry:
6. `H11` = d = h − c [mm] → 400
7. `H12` = z = h − 2c [mm] → 350 — **computed but unused downstream** (see §7)
8. `H13` = l = a + 0.2·d [mm] → 257 (effective/equivalent shear span)

Steel areas:
9. `H20` = As,hor = n°hor · π · Øhor² / 4 [mm²] → 904.779
10. `H21` = As,incl = n°incl · π · Øincl² / 4 [mm²] → 0

Minimum tie steel:
11. `H23` = As,lnk = IF(a < 0.5h, 0.25·As,hor, 0.5·PEd·1000/fyd) [mm²] → a=177 < 0.5·450=225 ⇒ 0.25·904.779 = 226.195

Capacities:
12. `H30` = c = IF(staffe_verticali="SI", "1.5" [text], 1 [number]) → 1 (see §7 — type mismatch bug)
13. `H28` = PRS = [(As,hor·fyd − HEd·1000) · 0.9d / l] / 1000 [kN] → [(904.779·391.304 − 0)·0.9·400/257]/1000 = 495.937
14. `H31` = PRC = [0.4·b·d·fcd·c / (1 + (l/(0.9d))²)] / 1000 [kN] → [0.4·800·400·18.8133·1 / (1+(257/360)²)]/1000 = 1595.16
15. `H32` = ΔPR = As,incl · fyd · sin(radians(angle)) / 1000 [kN] → 0
16. `H33` = PR = PRS + 0.8·ΔPR [kN] → 495.937 (0.8 = empirical reduction on inclined-bar contribution)
17. `C34` = verdict text (see §3)
18. `A36` = stirrup-area note (see §3)

Unrelated helper block `CC19:CM27` on the same sheet computes plot coordinates for the geometry
diagram (`N24` picture) — not part of the engineering calc, not modeled as a tool step.

### 5. Lookup tables (`Tabelle`)
- `Tabelle!M34:O41` — concrete class → props. Key col M (exact text, e.g. "C32/40"); col N=Rck, col O=fck [MPa] (used, col 3). Rows: C20/25…C50/60, exact match (VLOOKUP …,FALSE()).
- `Tabelle!M45:P49` — steel type → props. Key col M (exact text: B450C, B500C, FeB32k, FeB38k, FeB44k); col N=fyk, col O=ftk [MPa]. Exact match. Note: `B500C` exists in this table but is NOT selectable via `H14`'s dropdown (`$BU$16:$BU$20` on sheet `Mensola tozza` only lists B450C/FeB22k/FeB32k/FeB38k/FeB44k).
- `Mensola tozza!BU5:BU12` — local dropdown source for concrete class (H15): C20/25…C50/60 (8 entries, must mirror `Tabelle` class names).
- `Mensola tozza!BU16:BU20` — local dropdown source for steel type (H14): B450C, FeB22k, FeB32k, FeB38k, FeB44k.

### 6. Hardcoded constants
| value | meaning | source |
|---|---|---|
| 1.15 | γs | NTC2018 Tab 4.1.V |
| 1.5 | γc | NTC2018 Tab 4.1.V |
| 0.85 | αcc, concrete design-strength reduction | NTC2018 §4.1.2.1.1.1 |
| 0.2 | shear-span offset coeff. in l = a+0.2d | ? |
| 0.9 | internal-lever-arm factor (0.9d) | standard flexure convention |
| 0.25 | As,lnk reduction factor when a<0.5h | ? |
| 0.5 | As,lnk = 0.5·PEd/fyd factor when a≥0.5h | ? |
| 0.4 | strut effectiveness coeff. in PRC | ? (≈ EC2-style ν) |
| 1.5 (text "1.5") | amplification coeff. c when vertical stirrups present | ? |
| 0.8 | reduction factor on inclined-bar contribution ΔPR in PR | ? |
| 2 | legs/stirrup in A36 check | geometric (closed stirrup) |

### 7. Suspected bugs / fragile spots
- **H30 type mismatch**: `IF(H29="SI","1.5",1)` returns the **string** `"1.5"` on the SI branch but the **number** `1` on the NO branch. `H31` multiplies `H30` into an arithmetic expression — Excel auto-coerces `"1.5"` to 1.5, so numerically it still works, but this is fragile (a re-implementation using strict typing must special-case the string). Re-implement `H30` as a plain number.
- **Z7 (labelled "fyk", actually ftk) is dead**: `Z7 = VLOOKUP(H14,...,col 3)` pulls **ftk** (rottura) despite the adjacent label M-cell reading "Tensione di rottura dell'acciaio" / symbol `Y="fyk"` (label says fyk, formula computes ftk — label/formula mismatch) and — more importantly — **no other formula on the sheet references `Z7`**. Confirmed by grep of all 41 formulas: only `Z8`/`Z9` (not `Z7`) feed `H23/H28/H31/H32`. Do not implement it as a tool output; note it only if reproducing the sheet 1:1.
- **H12 (z = h−2c) is dead**: computed but never referenced by any downstream formula (`H13` uses `H11`, not `H12`). Likely a leftover/legacy variable from an earlier formula version. Omit from the re-implementation's output surface, or keep as a display-only value.
- **B500C unreachable via UI**: present in `Tabelle!M45:P49` but excluded from the `H14` dropdown range `BU16:BU20`, so a user (and thus the re-implementation, if it mirrors the enum) can never select it even though the workbook "supports" it.
- `H23`'s IF-branch is not obviously continuous at `a = 0.5h` (0.25·As,hor vs 0.5·PEd·1000/fyd) — no evidence of a smoothing/interpolation; verify against source code before assuming continuity is required.

### 8. Golden test case
```
in:  a=177mm h=450mm b=800mm c=50mm PEd=136kN HEd=0kN
     steel=B450C concrete=C32/40
     n_hor=8 Ø_hor=12mm n_incl=0 Ø_incl=0mm incl_angle=0°
     n_staffe=3 Ø_staffe=12mm staffe_verticali=NO
out: gamma_s=1.15 gamma_c=1.5 fyd=391.304MPa fcd=18.8133MPa
     d=400mm l=257mm As_hor=904.779mm² As_incl=0mm²
     As_lnk_min=226.195mm² c_coeff=1
     PRS=495.937kN PRC=1595.16kN dPR=0kN PR=495.937kN
     verdict="Verifica soddisfatta: Pr > Ped"
     stirrup_note=""
```
