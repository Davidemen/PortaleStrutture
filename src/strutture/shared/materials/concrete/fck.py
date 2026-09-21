"""NTC2018 Tab. 4.1.I — fck (cylinder strength) by concrete class.

`legacy_compat=True` reproduces the sheets' fill-down `fck = 0.83*Rck` (ca-travi/ca-mensole/
ca-pilastri!Tabelle O34:O41, and ca-fessurazione!MATERIALE CLS C3:C14 except the manually
corrected C11). `legacy_compat=False` uses the NTC2018 literal fck (see docs/divergences/materials.md)."""
from strutture.shared.tables import exact_lookup

from .models import ConcreteClass
from .rck import rck
from .tables import CONCRETE_FCK_LITERAL_MPA, K_RCK_TO_FCK_LEGACY


def fck(classe: ConcreteClass, *, legacy_compat: bool = False) -> float:
    """fck, MPa."""
    if legacy_compat:
        return K_RCK_TO_FCK_LEGACY * rck(classe)
    return exact_lookup(CONCRETE_FCK_LITERAL_MPA, classe)
