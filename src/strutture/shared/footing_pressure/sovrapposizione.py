"""Sheet's biaxial superposition method (docs/specs/fond-plinti-isolati.md steps 9-10, CHECKS!AA):

    sigma_tot = MAX(sigma_x range) + MAX(sigma_y range) - N/(bx*by)

i.e. the two independent uniaxial trapezoids added and de-duplicated of one baseline N/A term.
Documented in §7 as an approximation ("not the exact biaxial-bending corner pressure"); kept
available in normal mode per §9-D2, forced when legacy_compat=True by the calling Tool.
compressed_ratio mirrors CHECKS!S,Z/AP (step 13): MIN of each axis' own compressed-length ratio.
sigma_min extends the same superposition idea symmetrically (min + min - uniform); the sheet
itself has no combined-minimum cell, so this is this module's own, documented completion of the
method, not a divergence.
"""
from strutture.shared.numeric import clamp

from .eccentricity import eccentricities
from .models import BiaxialPressure, UniaxialPressure
from .uniaxial import uniaxial

_BOTH_OUTSIDE_KERN_WARNING = (
    "Risultante fuori dal nocciolo d'inerzia in entrambe le direzioni: la sovrapposizione di "
    "verifiche uniassiali è un'approssimazione poco affidabile in questo regime; usare il metodo "
    "esatto per la pressione di contatto biassiale.")


def sovrapposizione(n_kn: float, mx_knm: float, my_knm: float, bx_m: float, by_m: float) -> BiaxialPressure:
    """Sheet's superposition method for the biaxial contact pressure of a bx_m * by_m footing."""
    ex_m, ey_m = eccentricities(n_kn, mx_knm, my_knm)
    ux = uniaxial(n_kn, my_knm, by_m, bx_m)  # eccentricity ex acts along bx_m
    uy = uniaxial(n_kn, mx_knm, bx_m, by_m)  # eccentricity ey acts along by_m

    sigma_uniform_kpa = n_kn / (bx_m * by_m)
    sigma_max_kpa = ux.sigma_max_kpa + uy.sigma_max_kpa - sigma_uniform_kpa
    sigma_min_kpa = clamp(ux.sigma_min_kpa + uy.sigma_min_kpa - sigma_uniform_kpa, 0.0, sigma_max_kpa)

    ratio_x = 1.0 if ux.in_kern else ux.contact_len_m / bx_m
    ratio_y = 1.0 if uy.in_kern else uy.contact_len_m / by_m
    compressed_ratio = min(ratio_x, ratio_y)

    warning = _BOTH_OUTSIDE_KERN_WARNING if not ux.in_kern and not uy.in_kern else None
    x_pos, x_neg = _side_values(ux, ex_m)
    y_pos, y_neg = _side_values(uy, ey_m)
    corners_kpa = (
        max(0.0, x_neg + y_neg - sigma_uniform_kpa),
        max(0.0, x_pos + y_neg - sigma_uniform_kpa),
        max(0.0, x_pos + y_pos - sigma_uniform_kpa),
        max(0.0, x_neg + y_pos - sigma_uniform_kpa),
    )
    return BiaxialPressure(
        metodo="sovrapposizione", ex_m=ex_m, ey_m=ey_m, in_kern=ux.in_kern and uy.in_kern,
        sigma_max_kpa=sigma_max_kpa, sigma_min_kpa=sigma_min_kpa, compressed_ratio=compressed_ratio,
        corners_kpa=corners_kpa, neutral_axis=None, warning=warning,
    )


def _side_values(side: UniaxialPressure, e_m: float) -> tuple[float, float]:
    """(value on the +side, value on the -side) of a uniaxial result, oriented by the sign of e_m
    (the eccentricity pushes the pressure maximum towards the side it leans to).
    """
    return (side.sigma_max_kpa, side.sigma_min_kpa) if e_m >= 0 else (side.sigma_min_kpa, side.sigma_max_kpa)
