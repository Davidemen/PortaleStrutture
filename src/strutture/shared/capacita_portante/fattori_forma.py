"""sq, sγ, sc — EN 1997-1 Annex D.2 (drained) / D.3 (undrained) shape factors, rectangular
footing B' x L' (B' <= L').

Drained (Annex D.2, Table D.2):
    sq = 1 + (B'/L')·sinφ'
    sγ = 1 - 0.3·(B'/L')
    sc = (sq·Nq - 1) / (Nq - 1)                    for φ' > 0
    sc = 1 + 0.2·(B'/L')                            φ' -> 0 limit (l'Hôpital), == the undrained D.3 form
Undrained (Annex D.3): sc = 1 + 0.2·(B'/L').

Strip footing (L' -> infinity, B'/L' -> 0): all three factors -> 1, handled explicitly (the
"L'/B'" ratio is not evaluated as a genuine division when `nastriforme=True`).
"""
import math

from .models import FattoriForma

STRIP_FOOTING_SHAPE_FACTORS = FattoriForma(sq=1.0, sgamma=1.0, sc=1.0)


def fattori_forma(b_eff_m: float, l_eff_m: float, phi_deg: float, nq: float, *, nastriforme: bool = False) -> FattoriForma:
    """Drained shape factors. `nq` is the drained Nq (from `fattori_portanza`); pass `phi_deg=0`
    with any `nq=1.0` to get the φ'->0 limit (sc = 1 + 0.2·B'/L'), matching the undrained form."""
    if nastriforme:
        return STRIP_FOOTING_SHAPE_FACTORS
    if b_eff_m <= 0 or l_eff_m <= 0:
        raise ValueError(f"b_eff_m e l_eff_m devono essere > 0, ricevuti {b_eff_m}, {l_eff_m}")
    ratio = b_eff_m / l_eff_m
    phi_rad = math.radians(phi_deg)
    sq = 1.0 + ratio * math.sin(phi_rad)
    sgamma = 1.0 - 0.3 * ratio
    sc = 1.0 + 0.2 * ratio if phi_deg == 0.0 else (sq * nq - 1.0) / (nq - 1.0)
    return FattoriForma(sq=sq, sgamma=sgamma, sc=sc)


def fattori_forma_non_drenata(b_eff_m: float, l_eff_m: float, *, nastriforme: bool = False) -> float:
    """sc for the undrained D.3 formula: sc = 1 + 0.2·B'/L' (1.0 for a strip footing)."""
    if nastriforme:
        return 1.0
    if b_eff_m <= 0 or l_eff_m <= 0:
        raise ValueError(f"b_eff_m e l_eff_m devono essere > 0, ricevuti {b_eff_m}, {l_eff_m}")
    return 1.0 + 0.2 * (b_eff_m / l_eff_m)
