"""NTC2018 Tab. 4.1.I — Rck (cube strength) by concrete class."""
from strutture.shared.tables import exact_lookup

from .models import ConcreteClass
from .tables import CONCRETE_RCK_MPA


def rck(classe: ConcreteClass) -> float:
    """Rck, MPa (ca-fessurazione!MATERIALE CLS B3:B14 / ca-travi!Tabelle N34:N41)."""
    return exact_lookup(CONCRETE_RCK_MPA, classe)
