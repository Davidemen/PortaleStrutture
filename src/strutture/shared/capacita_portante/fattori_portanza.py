"""Nq, Nc, Nγ — EN 1997-1 Annex D.4 bearing capacity factors (rough base).

Closed forms (Annex D.4, eq. D.4-D.6):
    Nq = e^(π·tanφ') · tan²(45° + φ'/2)
    Nc = (Nq - 1) / tanφ'
    Nγ = 2·(Nq - 1)·tanφ'   (rough base; Annex D.4 gives this instead of Vesic's 1.5-coefficient form)

φ' -> 0 limit (used by the undrained D.3 formula, cu = c'): Nq -> 1, Nγ -> 0, and
Nc -> π + 2 by L'Hôpital's rule on (Nq(φ')-1)/tanφ' as φ'->0 (both derivatives w.r.t. φ' at 0
give dNq/dφ' = π+2, d(tanφ')/dφ' = 1), matching the (π+2)·cu term of the undrained formula.
"""
import math

from .models import FattoriPortanza

_NC_LIMITE_PHI_ZERO = math.pi + 2.0


def fattori_portanza(phi_deg: float) -> FattoriPortanza:
    """Nq, Nc, Nγ for the characteristic/design friction angle φ' [deg], φ' >= 0."""
    if phi_deg < 0:
        raise ValueError(f"phi_deg deve essere >= 0, ricevuto {phi_deg}")
    if phi_deg == 0.0:
        return FattoriPortanza(nq=1.0, nc=_NC_LIMITE_PHI_ZERO, ngamma=0.0)
    phi_rad = math.radians(phi_deg)
    nq = math.exp(math.pi * math.tan(phi_rad)) * math.tan(math.radians(45.0) + phi_rad / 2.0) ** 2
    nc = (nq - 1.0) / math.tan(phi_rad)
    ngamma = 2.0 * (nq - 1.0) * math.tan(phi_rad)
    return FattoriPortanza(nq=nq, nc=nc, ngamma=ngamma)
