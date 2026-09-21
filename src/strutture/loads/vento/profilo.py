"""Step (spec §4.10): parametric pressure-vs-height profile p(z) = qb*ce(z).

Generalises Tabelle!K4:Q1005 (a hardcoded 1000-row fill-down with a broken sentinel last row, spec §7)
into `n_sezioni+1` evenly spaced heights from 0 to the building height, with no sentinel row needed.
"""
from .esposizione import coefficiente_esposizione
from .models import ProfiloRiga


def profilo_pressione(
    altezza_edificio_m: float, n_sezioni: int, qb: float, kr: float, z0: float, zmin: float, ct: float
) -> tuple[ProfiloRiga, ...]:
    """Pressure profile at heights z_n = altezza_edificio_m/n_sezioni * n, n = 0..n_sezioni (Tabelle!L, generalised)."""
    passo_m = altezza_edificio_m / n_sezioni
    righe: tuple[ProfiloRiga, ...] = ()
    for n in range(n_sezioni + 1):
        z_m = passo_m * n
        ce = coefficiente_esposizione(z_m, kr, z0, zmin, ct)
        righe = (*righe, ProfiloRiga(z_m=z_m, ce=ce, p_kNm2=qb * ce))
    return righe
