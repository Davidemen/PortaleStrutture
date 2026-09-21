"""Step: the strain plane of the governing combination, for the sketch's neutral-axis line only
(schematic, see `shared.sketch`'s "SCHEMA, not scale drawing" composition rule 1). Reuses
`stati_ultimi.risultante_pivot`/`stato_pivot` (public engine primitives) with a SINGLE bisection on
N at a fixed neutral-axis angle — bounded, one-off cost, unlike the exhaustive moment-direction
search in `shared.sezione_ca.verifica.verifica` (docs/architecture-phase4.md §B performance rule:
that search alone costs ~0.5 s and cannot run again just to draw a picture). For a biaxial governing
row the angle is approximated as `atan2(My_Ed, Mx_Ed)` (the exact direction search is skipped on
purpose: the sketch only needs a representative line, not a verified value)."""
from math import atan2, pi

from strutture.shared.numeric import bisect
from strutture.shared.sezione_ca.modelli import Sezione
from strutture.shared.sezione_ca.stati_ultimi import risultante_pivot, stato_pivot

from .models_output import RigaAzione

TOLLERANZA_T = 1e-4  # una sola bisezione grezza, sufficiente per una linea schematica.

PianoDeformazione = tuple[float, float, float]  # (eps0, kx, ky)


def _theta(riga: RigaAzione) -> float:
    if riga.tipo == "uniassiale x":
        return 0.0
    if riga.tipo == "uniassiale y":
        return pi / 2.0
    return atan2(riga.m_ed_y_kNm, riga.m_ed_x_kNm)


def asse_neutro(sezione: Sezione, riga: RigaAzione) -> PianoDeformazione | None:
    """`(eps0, kx, ky)` alla combinazione governante, se `N_Ed` è nel dominio di resistenza;
    `None` altrimenti (nessun asse neutro da disegnare)."""
    theta = _theta(riga)

    def n_di_t(t: float) -> float:
        return risultante_pivot(sezione, theta, t).n_kN

    n_min, n_max = n_di_t(0.0), n_di_t(1.0)
    if not n_min <= riga.n_ed_kN <= n_max:
        return None
    try:
        t = bisect(lambda t: n_di_t(t) - riga.n_ed_kN, 0.0, 1.0, tol=TOLLERANZA_T)
    except ValueError:
        return None
    return stato_pivot(sezione, theta, t)
