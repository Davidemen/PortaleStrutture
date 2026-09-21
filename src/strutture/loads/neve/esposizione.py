"""Step (spec calc step 5, `Neve!H14` / `Neve accumulo!H14`): exposure coefficient CE."""
from strutture.shared.tables import exact_lookup

from .tables import EXPOSURE_TABLE


def coefficiente_esposizione(topografia: str) -> float:
    """NTC2018 §3.4.3, Tab. 3.4.I (exposure coefficient CE), exact match on the exposure-class
    dropdown."""
    return exact_lookup(EXPOSURE_TABLE, topografia)
