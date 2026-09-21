# Divergences — `strutture.shared.soil_stress.under_point` (Fadum superposition, sheet `500`)

Sheet: `geo-cedimenti`, sheet `500`/`400`/`350` (`docs/specs/geo-cedimenti-elastico.md` Tool 1,
PUNTO mode). Golden cases `500`/`400`/`350` all have `F7=F8=F9=F10` (point O exactly centred), so
this bug is numerically invisible in every cached golden case (spec: "PUNTO axis pairing unverified
for off-center points").

| Cell | Sheet behaviour | Fixed behaviour | Clause | Numeric impact on golden case |
|---|---|---|---|---|
| `500!M:T` ("Ofga" block) | Pairs `(F7, F9)` — both are segments of the **same** side (`O'd`, split by point O into F7+F9) — into one sub-rectangle. Not a valid corner rectangle for the point-outside-loaded-area superposition. | `under_point` builds each of the 4 sub-rectangles by pairing one x-split (`x`, `B-x`) with one y-split (`y`, `L-y`) — always one segment from each side, never two segments of the same side. | Classical Fadum/Newmark 4-rectangle superposition (Poulos & Davis) | None: `F7=F8=F9=F10=2000` in all 3 golden cases, so `(F7,F9)` and any cross-side pair (`F7,F8` etc.) are numerically identical. See below for an off-centre case where it does matter. |
| `500!AK:AR` ("Ocde" block) | Pairs `(F10, F8)` — both segments of the other side (`O'g`). Same defect as above, mirrored. | Same fix as above. | Same | Same (invisible on the golden cases). |

## Da verificare → resolved by construction

The spec explicitly asks for the pairing to be **re-derived and tested against an asymmetric
point** rather than trusted from the sheet's own reference figure. `under_point` was verified two
ways, independent of the sheet:

1. **Interior point**, B=6 m, L=4 m, q=100 kPa, point (1, 1) m from the (0,0) corner, z=2 m: direct
   numerical double integration of the Boussinesq point-load kernel over the loaded rectangle gives
   Δσz ≈ 57.8464 kPa (1200×1200 midpoint rule); `under_point` reproduces it to 2e-4 relative.
2. **Exterior point** (same rectangle), point (-1, 1) m — 1 m beyond the B=0 edge: the same brute
   force integral gives Δσz ≈ 15.0638 kPa; `under_point`'s signed superposition (one of the four
   parts negative) matches to 2e-4 relative.

Both cross-checks use the *cross-side* pairing implemented in `point.py`. The sheet's *same-side*
pairing (`newmark_corner(q, F7, F9, z) + newmark_corner(q, F10, F8, z)`, i.e. the analogue of
`newmark_corner(q, x, B-x, z) + newmark_corner(q, y, L-y, z)`) gives a numerically different,
uncorroborated result for any off-centre point — see
`tests/shared/soil_stress/test_point.py::test_pairs_one_segment_from_each_side_not_same_side`.

No `legacy_compat` flag is exposed for this fix: the golden cases cannot distinguish the two
pairings (see above), so there is no cached spreadsheet number to reproduce, and shipping a
demonstrably-wrong alternate branch with no test coverage of its own would violate "never invent a
clause" more than it would preserve compatibility. If a future golden case with an off-centre point
surfaces and requires the sheet's literal same-side pairing, add `legacy_compat` to the *consuming*
tool (`geotechnics.cedimenti_elastico`) and have it call `newmark_corner` directly with the sheet's
literal column pairing instead of `under_point`.
