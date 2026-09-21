"""Exact ("esatto") biaxial contact pressure: Navier inside the kern, no-tension plane-pressure
solver outside it. See docs/architecture-batch2.md §8-D2 / §9-D2.
"""
from strutture.shared.report import CalcError

from .eccentricity import eccentricities, in_kern_biaxial
from .models import BiaxialPressure
from .navier import biaxial_navier
from .no_tension import biaxial_no_tension


def biaxial(n_kn: float, mx_knm: float, my_knm: float, bx_m: float, by_m: float) -> BiaxialPressure:
    """Contact pressure of a bx_m * by_m rigid footing under N (compression, kN), Mx, My (kNm).

    Raises CalcError if the resultant (ex, ey) falls outside the footing footprint.
    """
    if bx_m <= 0 or by_m <= 0:
        raise ValueError(f"bx_m and by_m must be > 0, got bx_m={bx_m}, by_m={by_m}")
    ex_m, ey_m = eccentricities(n_kn, mx_knm, my_knm)
    if abs(ex_m) >= bx_m / 2.0 or abs(ey_m) >= by_m / 2.0:
        raise CalcError(
            f"La risultante (ex={ex_m:.4g} m, ey={ey_m:.4g} m) cade fuori dalla base del plinto "
            f"({bx_m:.4g} x {by_m:.4g} m): geometria non verificabile.")

    if in_kern_biaxial(ex_m, ey_m, bx_m, by_m):
        return biaxial_navier(n_kn, ex_m, ey_m, bx_m, by_m)

    solution = biaxial_no_tension(n_kn, ex_m, ey_m, bx_m, by_m)
    return BiaxialPressure(
        metodo="esatto", ex_m=ex_m, ey_m=ey_m, in_kern=False,
        sigma_max_kpa=solution.sigma_max_kpa, sigma_min_kpa=0.0, compressed_ratio=solution.compressed_ratio,
        corners_kpa=solution.corners_kpa, neutral_axis=solution.neutral_axis,
    )
