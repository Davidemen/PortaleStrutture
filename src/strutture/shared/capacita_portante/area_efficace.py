"""Effective (Meyerhof) area of an eccentrically loaded rectangular footing (EN 1997-1 Annex D.1):
B' = B - 2·eB, L' = L - 2·eL, swapped so that B' <= L' (Annex D always takes B' as the shorter
side). Strip footing (L' -> infinity) is handled explicitly via `nastriforme=True`: only eB
applies, and the reported area is per metre of run.

The swap can flip which PHYSICAL axis (B or L) ends up in `b_eff_m`/`l_eff_m` — e.g. an
eccentricity large enough on the L side alone can make the L-direction effective length shorter
than the B-direction one. `AreaEfficace.scambiato` flags this so callers that need to relate a
direction back to the physical B/L axes (e.g. `carico_limite.esponente_m`'s `direzione_h`) can
compensate; see `carico_limite._direzione_effettiva`.
"""
import math

from strutture.shared.report import CalcError

from .models import AreaEfficace


def area_efficace(b_m: float, l_m: float, eb_m: float = 0.0, el_m: float = 0.0) -> AreaEfficace:
    """Effective area of a b_m x l_m footing with eccentricities eb_m (along B), el_m (along L)."""
    if b_m <= 0 or l_m <= 0:
        raise CalcError(f"Le dimensioni della base B={b_m} m e L={l_m} m devono essere positive.")
    if abs(eb_m) >= b_m / 2.0:
        raise CalcError(f"L'eccentricità eB={eb_m:.4g} m deve essere minore di B/2={b_m / 2.0:.4g} m.")
    if abs(el_m) >= l_m / 2.0:
        raise CalcError(f"L'eccentricità eL={el_m:.4g} m deve essere minore di L/2={l_m / 2.0:.4g} m.")
    b_eff = b_m - 2.0 * abs(eb_m)
    l_eff = l_m - 2.0 * abs(el_m)
    scambiato = b_eff > l_eff
    corto, lungo = (l_eff, b_eff) if scambiato else (b_eff, l_eff)
    return AreaEfficace(b_eff_m=corto, l_eff_m=lungo, a_eff_m2=corto * lungo, nastriforme=False, scambiato=scambiato)


def area_efficace_nastriforme(b_m: float, eb_m: float = 0.0) -> AreaEfficace:
    """Effective area per metre of run of a strip footing (base width b_m, no length limit):
    B' = B - 2·eB, L' -> infinity, A' = B' (per metre)."""
    if b_m <= 0:
        raise CalcError(f"La larghezza della base B={b_m} m deve essere positiva.")
    if abs(eb_m) >= b_m / 2.0:
        raise CalcError(f"L'eccentricità eB={eb_m:.4g} m deve essere minore di B/2={b_m / 2.0:.4g} m.")
    b_eff = b_m - 2.0 * abs(eb_m)
    return AreaEfficace(b_eff_m=b_eff, l_eff_m=math.inf, a_eff_m2=b_eff, nastriforme=True, scambiato=False)
