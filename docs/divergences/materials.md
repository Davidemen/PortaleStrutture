# Divergences — `strutture.shared.materials` (`concrete`, `rebar`, `structural_steel`)

Pure data/formula libraries (no `Tool` registration), so there is no `legacy_compat` on a Tool
input model here; instead each function/composer takes its own `legacy_compat: bool = False`
flag where a sheet's tabulated value disagrees with the NTC2018/EN1993-1-1 formula.

## Concrete `fck` fill-down bug (`concrete.fck`)

- **Cell**: `ca-travi/ca-mensole/ca-pilastri!Tabelle O34:O41` and
  `ca-fessurazione!MATERIALE CLS C3:C14` (except `C11`).
- **Sheet behaviour**: every concrete class fills `fck = 0.83*Rck` down the column
  (`ca-travi!Tabelle` row 38: `C35/45` → `fck=37.35`). This is an approximation, not the NTC2018
  Tab. 4.1.I literal (the number in the class name), and it visibly breaks for `C35/45`
  (NTC literal `fck=35`, sheet fill-down `37.35`, a 6.7% overstatement of the design strength via
  `fcd = 0.85*fck/1.5`).
- **Evidence the sheets know it's wrong**: `ca-fessurazione!MATERIALE CLS!C11` (the `C35/45` row)
  is the *only* row in that table not following the `0.83*Rck` formula — it is hardcoded to `35`,
  the correct NTC value, while `ca-travi/ca-mensole/ca-pilastri!Tabelle` never got the same fix
  (merge C4/C5, `docs/architecture.md` §3).
- **Fixed behaviour**: `legacy_compat=False` (default) uses the NTC2018 Tab. 4.1.I literal fck per
  class (`CONCRETE_FCK_LITERAL_MPA` in `concrete/tables.py`); `legacy_compat=True` reproduces the
  `0.83*Rck` fill-down for every class, matching `ca-travi/ca-mensole/ca-pilastri!Tabelle`.
- **Clause**: NTC2018 §4.1.2.1.1.1, Tab. 4.1.I.
- **Numeric impact on `C35/45`** (the worst case; every other class differs by ≤0.5 MPa on fck):
  `fck` 37.35 → 35.0 MPa (−6.3%); `fcm` 45.35 → 43.0 MPa; `Ecm` 34625.5 → 34077.1 MPa; `fctm`
  3.35208 → 3.20996 MPa; `fcd` 21.165 → 19.833 MPa (−6.3%, non-conservative in the sheet).

## Structural steel: thickness band ignored (`structural_steel.fyk_fuk`)

- **Cell**: `acciaio-colonne-ec3!Materiali!H19:J23`.
- **Sheet behaviour**: one `fyk`/`fuk` pair per grade (`S235`→235/360, `S275`→275/430,
  `S355`→355/510), never conditioned on element thickness — effectively always the
  EN1993-1-1 Tab. 3.1 `t<=40mm` band, even for thicker sections where the norm requires the
  reduced `40<t<=80mm` values.
- **Fixed behaviour**: `legacy_compat=False` (default) selects the band from `t_mm` per
  EN1993-1-1 Tab. 3.1 (`S235`: 235/360 vs 215/360; `S275`: 275/430 vs 255/410; `S355`: 355/510 vs
  335/470; `S420`: 420/520 vs 390/520; `S460`: 460/540 vs 430/540 — `S420`/`S460` extend the
  sheet's roster, which only ever exercised `S235/S275/S355`, with the standard EN1993-1-1
  Tab. 3.1 figures). `legacy_compat=True` always returns the `t<=40mm` band regardless of `t_mm`.
- **Clause**: EN1993-1-1 §3.2.1, Tab. 3.1.
- **Numeric impact (`S355`, `t=60mm`)**: `fyk` 355 → 335 MPa (−5.6%, non-conservative in the
  sheet if the section is actually thicker than 40mm).

## Rebar grade legacy classification (`rebar.rebar_properties`)

- Not a formula bug — a classification. NTC2018 §11.3.2 Tab. 11.3.Ia only admits `B450C`/`B450A`
  for new ordinary reinforcement in Italy. The union roster (merge C1, `docs/architecture.md` §3)
  also carries `B500C` (present only in `ca-mensole!Tabelle`, a Eurocode-style grade never
  formally admitted by NTC2008/2018) and the four pre-1996 grades `FeB22k/FeB32k/FeB38k/FeB44k`
  (superseded by NTC2008), plus `RB500W` (pre-NTC2008 welded-mesh classification). Every
  `RebarProperties` carries a `legacy_grade: bool` flag so a caller/UI can warn when a non-current
  grade is selected; the numeric properties themselves are unchanged (no divergence in fyk/ftk —
  the sheets' cached values are used as-is, see the oracle fixture).
- **Clause**: NTC2018 §11.3.2, Tab. 11.3.Ia.

## Da verificare

- **EN1993-1-1 grade roster boundaries.** The task asks for `S235..S460`; this module implements
  `S235, S275, S355, S420, S460` (skipping `S450`, a rarer hot-rolled/sheet-piling grade from
  EN10025-2 Tab. 7 not exercised by any sheet in this build's sources). `S420`/`S460` values are
  the standard EN1993-1-1 Tab. 3.1 figures for normalized fine-grain steels (EN10025-3 `N`
  grades); no sheet in `acciaio-colonne-ec3` tabulates them, so they cannot be cross-checked
  against a cached cell value the way `S235/S275/S355` can — confirm against EN10025-3 before
  relying on `S420`/`S460` for a real check.
