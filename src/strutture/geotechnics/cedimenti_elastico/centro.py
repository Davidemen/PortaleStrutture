"""CENTRO step: settlement at the geometric centre of the loaded rectangle, plus the closed-form
QA cross-check (`docs/specs/geo-cedimenti-elastico.md` Tool 1, CENTRO steps 2-6).

`U6 = 4·Σ newmark_corner(q,B/2,L/2,z)/E(z)·Δz` is algebraically `Σ under_center(q,B,L,z)/E(z)·Δz`
(`under_center = 4·newmark_corner(q,B/2,L/2,z)`, linear in the corner term), and the QA path
`Z6 = Σ q·Ic(z)/E(z)·Δz` is exactly `ic_center` -- both already implemented in `shared.soil_stress`
for this purpose, so this module only wires the depth grid and the two influence functions.

Fixes the "T6 vs Z6" depth-mismatch bug (`docs/architecture-batch2.md` §7 "newmark T6 vs Z6"): the
sheet integrates U6 to z=910 cm but Z6 (its own QA check) only to z=870 cm -- not a like-for-like
comparison. `legacy_compat=True` reproduces both hard-coded depths; `legacy_compat=False` uses one
common, user-set depth for both.
"""
from strutture.shared.divergences import legacy
from strutture.shared.soil_layers import SoilLayer, depth_grid
from strutture.shared.soil_stress import ic_center, under_center

from .integrate import Slice, integrate_settlement

# "T6=SUM(T7:T1063)": R/S/T (unlike L:Q) are only filled down to row 96 -- 90 terms, z=10..900cm --
# verified against the golden U6=3.0768cm (row 97, z=910cm, has no R/S/T at all in the workbook).
LEGACY_MAIN_Z_MAX_M = 9.00
# "Z6=SUM(Z7:Z87)": rows 7..87 inclusive are 81 terms, z=10..810cm -- verified against the golden
# Z6=3.0122cm (not 870cm: the spec's own bug note miscounts the row-87 cutoff by one row).
LEGACY_QA_Z_MAX_M = 8.10
LEGACY_DZ_M = 0.10  # "z-grid step: 10cm hardcoded fill-down"


def centro_settlement(
    q_kPa: float,
    b_m: float,
    l_m: float,
    layers: tuple[SoilLayer, ...],
    *,
    z_max_m: float,
    dz_m: float,
    legacy_compat: bool = False,
) -> tuple[tuple[Slice, ...], tuple[Slice, ...]]:
    """Main-path slices (`under_center`, sheet's U6) and QA slices (`ic_center`, sheet's Z6)."""
    if legacy("geo-cedimenti-elastico/profondita-integrazione-centro-t6-z6-diverse", legacy_compat):
        main_grid = depth_grid(LEGACY_MAIN_Z_MAX_M, LEGACY_DZ_M)[1:]
        qa_grid = depth_grid(LEGACY_QA_Z_MAX_M, LEGACY_DZ_M)[1:]
    else:
        main_grid = depth_grid(z_max_m, dz_m)[1:]
        qa_grid = main_grid

    def sigma_main(z_m: float) -> float:
        return under_center(q_kPa, b_m, l_m, z_m)

    def sigma_qa(z_m: float) -> float:
        return q_kPa * ic_center(b_m, l_m, z_m)

    main_slices = integrate_settlement(main_grid, layers, sigma_main, legacy_compat=legacy_compat)
    qa_slices = integrate_settlement(qa_grid, layers, sigma_qa, legacy_compat=legacy_compat)
    return main_slices, qa_slices
