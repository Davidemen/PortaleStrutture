"""Design friction / wall-friction angles φd, δd per combination (muro-sostegno rows 45-50/80-81,
cols K/M).

The sheet (`legacy_compat=True`) divides the characteristic ANGLE by the combination's own γφ,terr
(`phi_d = radians(phi_k)/gamma_phi`). NTC2018 Tab. 6.2.II instead defines γφ' as a factor on the
TANGENT of the shear-resistance angle: φ'd = arctan(tan(φ'k)/γφ'). The two only coincide when
γφ,terr = 1 (the M1 rows, STR_1/STR_2); for the M2 rows (γφ,terr = 1.25) the sheet's angle division
under-reduces φ'd (e.g. φ'k=30° -> sheet 24.00° vs. Tab. 6.2.II 24.79°), which is not the norm's
angle for a given γφ. `legacy_compat=False` implements the norm text; the sheet's own division is
kept unchanged under `legacy_compat=True` (see docs/divergences/muro-sostegno.md)."""
import math


def phi_d_rad(phi_deg: float, gamma_phi_terr: float, *, legacy_compat: bool = False) -> float:
    if legacy_compat:
        return math.radians(phi_deg) / gamma_phi_terr
    return math.atan(math.tan(math.radians(phi_deg)) / gamma_phi_terr)


def delta_d_rad(delta_deg: float, gamma_phi_terr: float, *, legacy_compat: bool = False) -> float:
    if legacy_compat:
        return math.atan(math.tan(math.radians(delta_deg))) / gamma_phi_terr
    return math.atan(math.tan(math.radians(delta_deg)) / gamma_phi_terr)
