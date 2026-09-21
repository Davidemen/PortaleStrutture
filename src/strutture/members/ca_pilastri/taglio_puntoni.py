"""Step: strut coefficient ac (EC2 6.2.3), rows CX31-CX38."""
from strutture.shared.divergences import legacy
from strutture.shared.units import kn_to_n

STRUT_COEFFICIENT_TENSION = 1.0  # CX32
STRUT_COEFFICIENT_LOW_THRESHOLD = 0.25  # CX36 = 0.25*fcd
STRUT_COEFFICIENT_MID_THRESHOLD = 0.5  # CX37 = 0.5*fcd
STRUT_COEFFICIENT_MID = 1.25  # CX34


def sigma_cp(ned_kN: float, ac_mm2: float) -> float:
    """CX31: σcp = Ned/Ac."""
    return kn_to_n(ned_kN) / ac_mm2


def coefficiente_ac(sigma_cp_MPa: float, fcd_MPa: float, *, legacy_compat: bool) -> float:
    """CX38 selector between the CX32..CX35 candidates.

    The sheet tests `H7<0` (column clear height, always > 0) instead of `σcp<0`: the intended
    "sotto tensione" branch is unreachable in the sheet — see docs/divergences/ca-pilastri.md.
    Under `legacy_compat=False` the corrected condition (`σcp<0`) is used; with the current input
    domain (Ned always > 0, pilastro semplicemente compresso) this never changes the result.
    """
    tension = False if legacy("ca-pilastri/ramo-morto-coefficiente-ac", legacy_compat) else sigma_cp_MPa < 0
    if tension:
        return STRUT_COEFFICIENT_TENSION
    if sigma_cp_MPa < STRUT_COEFFICIENT_LOW_THRESHOLD * fcd_MPa:
        return 1.0 + sigma_cp_MPa / fcd_MPa
    if sigma_cp_MPa < STRUT_COEFFICIENT_MID_THRESHOLD * fcd_MPa:
        return STRUT_COEFFICIENT_MID
    return 2.5 * (1.0 - sigma_cp_MPa / fcd_MPa)
