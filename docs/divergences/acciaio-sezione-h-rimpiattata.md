# Divergences — `acciaio-sezione-h-rimpiattata`

Golden case (Rev01/Rev00 default): H=114mm, B=120mm, tf=8mm, tw=5mm, piatto A4 b=8/h=105mm, piatto
A5 disabled (b=0).

| Cell | Sheet behaviour | Fixed behaviour | Clause | Numeric impact on golden case |
|---|---|---|---|---|
| `Rev00/Rev01!H6` | `yN = (D6*F6+...+D9*F9+D10*E10)/SUM(D6:D10)` — the last term uses row 10's **x** (`E10`) instead of its **y** (`F10`). Architecture §7 "H6 last yN term uses x". | Every term uses the element's own y. | Weighted-average centroid | None: A5's area is 0 in the golden case, so `D10*(x or y)=0` either way. Manifests once a 2nd plate is given nonzero area — e.g. `piatti=[{b:10,h:105},{b:10,h:105}]` on the golden geometry: legacy yN≈27.45mm vs fixed yN=57.00mm (test `test_yn_bug_is_fixed_when_both_plates_are_active`). |
| `Rev00/Rev01!C7` | Web clear height `=114-2*C6` hard-codes `114` instead of referencing `B1` (the H-profile height input). Changing `B1` away from 114 leaves the web/top-flange placement unchanged while the plates (whose y does reference `B1/2`, see `F9`) still move — an internally inconsistent geometry. | Web height `= h_profilo_mm - 2*tf_mm`, always consistent with the actual input. | Section geometry | None (golden case already has H=114). Manifests for any other `h_profilo_mm` — e.g. H=200mm on the golden flange/web/plate dims: legacy Ix≈613 cm4 (still built around the phantom 114mm web) vs fixed Ix≈2020 cm4 (test `test_web_height_uses_the_real_h_profilo_when_fixed`, checked independently against the closed-form doubly-symmetric I-section formula). |
| `Rev00/Rev01!F8` | Bottom-flange centroid `=+B9/2` — reuses the **first plate's own thickness** (`B9`) as a proxy for `tf/2`, instead of `C6/2`. Harmless only while `B9==C6` (the sheet's own default, 8=8). | `y = tf_mm/2`. | Section geometry | None (golden case has B9=C6=8). Manifests when the plate thickness differs from `tf` — e.g. a 20mm plate on the golden profile moves the modelled bottom-flange centroid to 10mm instead of 4mm (test `test_bottom_flange_position_bug_is_fixed`). |

## Da verificare

- **`Wpl,x`/`Wpl,y` (sheet columns M/N) are not the true plastic modulus.** They sum
  `A_i * |distance from the ELASTIC centroid|`, which only equals the true equal-area-PNA plastic
  modulus for a doubly symmetric profile with no plates on the strong axis; for the weak axis it
  is **always 0** for an unreinforced profile (all base elements sit at `xi=0=xN`), and is wrong
  whenever plates are asymmetric. Not listed in architecture-batch2.md §7, so kept as a genuine
  simplification rather than asserted as "the" bug: `legacy_compat=True` reproduces the sheet's
  approximation verbatim (`plastico.wpl_x_legacy_mm3`/`wpl_y_legacy_mm3`); `legacy_compat=False`
  computes the true value via the equal-area plastic neutral axis (`shared.numeric.bisect`).
- **Unused `B2` ("B profile") input cell.** `B2` is never referenced by any formula in either
  sheet (the flange width used everywhere is `B6`). The port keeps a single `b_profilo_mm` input
  (mapped to `B6`) and does not model a separate, decorative `B2`.

## Kept as-is (generalisation, not a bug)

- **`piatti` table (up to 10 rows) vs. the sheet's fixed 2 plate slots (A4/A5).** Rows beyond the
  first two are placed by alternating sides and stacking outward on the same side
  (`elementi.elementi_piatti_generale`), which is the natural extension of the sheet's A4(+x)/A5
  (-x, mirrored) pair; only meaningful under `legacy_compat=False` (§9 does not cover this unit).
- **Plate height (`h_mm`) is a free input**, not a derived cell — the sheet computes it from the
  web height (`C9=C7+3.5+3.5`); the general table has no formula cells (architecture-batch2.md
  §2), so the caller supplies the sheet's own computed value directly for oracle/golden fidelity.
