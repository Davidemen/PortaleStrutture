"""bq, bγ, bc — EN 1997-1 Annex D.2 (drained) / D.3 (undrained) base-inclination factors, for a
base inclined at α to the horizontal (α = 0 for the ordinary horizontal base).

Drained (Annex D.2):
    bq = bγ = (1 - α·tanφ')²
    bc = bq - (1 - bq) / (Nc·tanφ')            φ' > 0
Undrained (Annex D.3):
    bc = 1 - 2α / (π + 2)
    (bq, bγ are not used by the undrained formula; reported as 1.0 for completeness.)

α is the MAGNITUDE of the base inclination to the horizontal (its sign only encodes a direction,
not an increase in capacity): both formulas use |α|, so a negative `alpha_deg` gives the same
factors as its positive counterpart, never bq/bc > 1 (a negative signed α would otherwise flip
the sign inside the parenthesis and inflate the factor above 1, which Annex D.4 never intends).
"""
import math

from .models import FattoriInclinazioneBase

_PI_PLUS_2 = math.pi + 2.0  # EN 1997-1 Annex D.3


def fattori_inclinazione_base(alpha_deg: float, phi_deg: float, nc: float) -> FattoriInclinazioneBase:
    """Drained bq, bγ, bc for a base inclined at `alpha_deg` to the horizontal (phi_deg > 0)."""
    if phi_deg <= 0.0:
        raise ValueError("fattori_inclinazione_base richiede phi_deg > 0 (usare la formula non drenata per phi_deg=0)")
    if not (-90.0 < alpha_deg < 90.0):
        raise ValueError(f"alpha_deg deve essere in (-90, 90), ricevuto {alpha_deg}")
    alpha_rad = math.radians(abs(alpha_deg))
    phi_rad = math.radians(phi_deg)
    bq = bgamma = (1.0 - alpha_rad * math.tan(phi_rad)) ** 2
    bc = bq - (1.0 - bq) / (nc * math.tan(phi_rad))
    return FattoriInclinazioneBase(bq=bq, bgamma=bgamma, bc=bc)


def fattori_inclinazione_base_non_drenata(alpha_deg: float) -> FattoriInclinazioneBase:
    """Undrained bc = 1 - 2α/(π+2); bq = bγ = 1.0 (unused by the undrained formula)."""
    if not (-90.0 < alpha_deg < 90.0):
        raise ValueError(f"alpha_deg deve essere in (-90, 90), ricevuto {alpha_deg}")
    alpha_rad = math.radians(abs(alpha_deg))
    bc = 1.0 - 2.0 * alpha_rad / _PI_PLUS_2
    return FattoriInclinazioneBase(bq=1.0, bgamma=1.0, bc=bc)
