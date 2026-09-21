# Divergences — `strutture.members.ca_mensole` (tool `ca-mensola-tozza`)

## FIX — `H30` type mismatch (string vs number)

- **Cell**: `Mensola tozza!H30` = `IF(H29="SI","1.5",1)`.
- **Sheet behaviour**: returns the *string* `"1.5"` on the SI branch and the *number* `1` on the
  NO branch. `H31` multiplies `H30` into an arithmetic expression, so Excel auto-coerces the
  string and the numeric result is unaffected.
- **Fixed behaviour**: `capacita.coefficiente_c` always returns a plain `float` (`1.0` or `1.5`),
  in both `legacy_compat` modes.
- **Clause**: n/a (type-safety fix, not a code-clause change).
- **Numeric impact on the golden case**: none (`H29="NO"` in the golden case, `c=1` either way).

## FIX — `H14` dropdown/table mismatch: `FeB22k` selectable but missing from `Tabelle!M45:P49`

- **Cell**: `Mensola tozza!H14` (dropdown `BU16:BU20` = B450C/FeB22k/FeB32k/FeB38k/FeB44k) vs.
  `Tabelle!M45:P49` (rows M45:M49 = B450C/B500C/FeB32k/FeB38k/FeB44k — no `FeB22k` row).
- **Sheet behaviour**: confirmed against the workbook (LibreOffice recalculation, not just spec
  §7): selecting `FeB22k` in `H14` makes `Z8=VLOOKUP(H14,Tabelle!M45:P49,2,FALSE())` return
  `#N/A`, which propagates to `H28`, `H33`, `C34` (also `#N/A`). `B500C` is the mirror-image bug:
  present in the table but never reachable via the dropdown (already excluded from
  `GradoAcciaioMensola`, per spec §7/architecture.md §6).
- **Fixed behaviour**: `legacy_compat=True` reproduces the crash (`materiali` raises `CalcError`
  for `FeB22k` in legacy mode). `legacy_compat=False` fixes it via the shared union rebar table
  (`strutture.shared.materials.rebar`, merge C1 in `docs/architecture.md` §3), which does carry a
  `FeB22k` row (`fyk=215 MPa`).
- **Clause**: n/a (data-table consistency fix, not a code-clause change).
- **Numeric impact on the golden case**: none (golden case uses `B450C`).

## DROP — dead cells `Z7`, `H12`

- **Cells**: `Mensola tozza!Z7` (`=VLOOKUP(H14,...,3)`, mislabelled "fyk" but actually computes
  ftk; confirmed unused — no downstream formula references it) and `H12` (`z=h-2c`, also unused;
  `H13` uses `H11`, not `H12`).
- **Decision**: not ported (per `docs/architecture.md` §6, "Dead cells across units ... ca-mensole
  `Z7`,`H12` — DROP").
- **Numeric impact**: none, neither cell feeds any output.

## Da verificare — `As,lnk` two-branch formula continuity at `a = 0.5h`

- **Cell**: `Mensola tozza!H23` = `IF(a<0.5h, 0.25*As,hor, 0.5*PEd*1000/fyd)`.
- The two branches (`0.25*As,hor` vs `0.5*PEd/fyd`) have no visible smoothing/interpolation and
  are not guaranteed continuous at the threshold; spec §7 flags this as unverified against the
  clause behind the formula (marked "?" in spec §6).
- **Decision**: kept identical in both `legacy_compat` modes ("Da verificare" — not changed
  pending confirmation of the source clause). Boundary tested (`a == 0.5h` takes the long-span
  branch, strict `<` in the sheet's `IF`).

## Da verificare — strut-and-tie formula constants (0.2, 0.4, 0.8, 0.9, 1.5)

- Per spec §1/§6, the strut/tie capacity formulas themselves (`PRS`, `PRC`, `ΔPR`, the
  `l = a + 0.2d` shear-span offset, and the `c=1.5` stirrup amplification) match a known Italian
  design-guide formulation but are not independently verified against the NTC2018 text (clause
  "?" throughout). Reproduced as-is in both modes pending confirmation.
