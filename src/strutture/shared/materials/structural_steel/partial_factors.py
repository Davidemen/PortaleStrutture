"""acciaio-colonne-ec3!Materiali!E4:E6 — coefficienti di sicurezza parziali dell'acciaio strutturale."""
from .models import PartialFactors
from .tables import GAMMA_M0, GAMMA_M1_NON_PONTE, GAMMA_M1_PONTE, GAMMA_M2


def partial_factors(*, ponte: bool = False) -> PartialFactors:
    """γM0/γM1/γM2. `ponte=True` selects γM1 per ponti stradali e ferroviari (Materiali!B5 dropdown)."""
    return PartialFactors(
        gamma_m0=GAMMA_M0,
        gamma_m1=GAMMA_M1_PONTE if ponte else GAMMA_M1_NON_PONTE,
        gamma_m2=GAMMA_M2,
    )
