"""PUNTO step: settlement at an arbitrary point O of the O'-rectangle (4 sub-rectangles), plus the
independent single-rectangle corner check at O' (`docs/specs/geo-cedimenti-elastico.md` Tool 1,
PUNTO steps 1-7).

`legacy_compat=False` uses `shared.soil_stress.under_point`, which fixes the sheet bug at
`500!M/N,AK/AL` (`docs/architecture-batch2.md` §7): the sheet's "Ofga" block pairs `(e1, e1')` --
both splits of the *same* side of the O'-rectangle -- and "Ocde" pairs `(e2', e2)`, likewise; a
valid corner sub-rectangle needs one split from each side. `legacy_compat=True` reproduces the
sheet's literal 4-block formula so the oracle fixtures (symmetric points, where the bug is
numerically invisible) still match bit-for-bit; see `docs/divergences/geo-cedimenti-elastico.md`
for the asymmetric hand case that tells the two apart.
"""
from strutture.shared.divergences import legacy
from strutture.shared.report import CalcError
from strutture.shared.soil_layers import SoilLayer, depth_grid
from strutture.shared.soil_stress import newmark_corner, under_point

from .integrate import Slice, integrate_settlement

# "500!K7:K87": the K column (z) fill-down reaches row 87 (z=810cm), but every block's own Δz/Δs
# columns (e.g. "S"/"T" of the "Ofga" block) stop one row short, at row 86 -- 80 real terms,
# z=10..800cm -- verified against the golden `I3=1.58273cm` (one block alone) and `C2=6.33092cm`.
LEGACY_Z_MAX_M = 8.00
LEGACY_DZ_M = 0.10


def _legacy_point_sigma(q_kPa: float, e1_m: float, e2_m: float, side_p_m: float, side_q_m: float, z_m: float) -> float:
    """Literal sheet formula: "Ofga"(e1,e1') + "Oabc"(e1',e2') + "OeO'f"(e2,e1) + "Ocde"(e2',e2)."""
    e1_complement_m, e2_complement_m = side_p_m - e1_m, side_q_m - e2_m
    if min(e1_m, e2_m, e1_complement_m, e2_complement_m) < 0:
        raise CalcError(
            "modalità PUNTO, riproduzione del foglio: il punto O deve restare dentro il rettangolo O'gbd "
            "(il foglio non gestisce punti esterni)"
        )
    return (
        newmark_corner(q_kPa, e1_m, e1_complement_m, z_m)
        + newmark_corner(q_kPa, e1_complement_m, e2_complement_m, z_m)
        + newmark_corner(q_kPa, e2_m, e1_m, z_m)
        + newmark_corner(q_kPa, e2_complement_m, e2_m, z_m)
    )


def punto_settlement(
    q_kPa: float,
    side_p_m: float,
    side_q_m: float,
    e1_m: float,
    e2_m: float,
    layers: tuple[SoilLayer, ...],
    *,
    z_max_m: float,
    dz_m: float,
    legacy_compat: bool = False,
) -> tuple[tuple[Slice, ...], tuple[Slice, ...]]:
    """O-point slices (sheet's `C2`) and O'-corner slices (sheet's `C3`)."""
    grid = (
        depth_grid(LEGACY_Z_MAX_M, LEGACY_DZ_M)[1:]
        if legacy("geo-cedimenti-elastico/blocco-500-profondita-integrazione-troncata", legacy_compat)
        else depth_grid(z_max_m, dz_m)[1:]
    )

    if legacy("geo-cedimenti-elastico/punto-o-accoppiamento-lati-errato", legacy_compat):

        def sigma_o(z_m: float) -> float:
            return _legacy_point_sigma(q_kPa, e1_m, e2_m, side_p_m, side_q_m, z_m)
    else:

        def sigma_o(z_m: float) -> float:
            return under_point(q_kPa, side_p_m, side_q_m, e1_m, e2_m, z_m).total

    def sigma_o_prime(z_m: float) -> float:
        return newmark_corner(q_kPa, side_p_m, side_q_m, z_m)

    o_slices = integrate_settlement(grid, layers, sigma_o, legacy_compat=legacy_compat)
    o_prime_slices = integrate_settlement(grid, layers, sigma_o_prime, legacy_compat=legacy_compat)
    return o_slices, o_prime_slices
