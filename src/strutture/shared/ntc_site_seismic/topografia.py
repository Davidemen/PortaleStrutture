"""NTC 2018 Tab. 3.2.V — ST (amplificazione topografica) by categoria topografica (Sisma!I33)."""
from strutture.shared.tables import exact_lookup

from .models import CategoriaTopografica
from .tables import FATTORE_TOPOGRAFICO_ST


def fattore_topografico_st(categoria_topografica: CategoriaTopografica) -> float:
    """ST, `Tabelle!A7:B10` (Tab. 3.2.V)."""
    return exact_lookup(FATTORE_TOPOGRAFICO_ST, categoria_topografica)
