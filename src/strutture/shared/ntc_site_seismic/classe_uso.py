"""NTC 2018 §2.4.2 Tab. 2.4.II — coefficiente d'uso Cu by classe d'uso (Sisma!I9)."""
from strutture.shared.tables import exact_lookup

from .models import ClasseUso
from .tables import COEFFICIENTE_USO


def coefficiente_uso(classe_uso: ClasseUso) -> float:
    """Cu, `Tabelle!C2:F3` HLOOKUP by classe d'uso (I/II/III/IV)."""
    return exact_lookup(COEFFICIENTE_USO, classe_uso)
