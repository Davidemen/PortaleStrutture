"""Minimum cover for durability, cmin,dur (Tabelle!E30/E31, NTC2018 Tab. 4.1.III)."""
from strutture.shared.tables import KeyNotFound

from .models import ExposureClass, ReinforcementType, StructuralClass
from .tables import _MIN_COVER_TABLES


def min_cover_mm(structural_class: StructuralClass, exposure_class: ExposureClass,
                  reinforcement_type: ReinforcementType = "ordinaria") -> float:
    """Minimum cover for durability cmin,dur [mm] given structural class S (1..6) and exposure."""
    table = _MIN_COVER_TABLES[reinforcement_type]
    key = (structural_class, exposure_class)
    if key not in table:
        raise KeyNotFound(f"no cmin,dur entry for structural_class={structural_class!r}, "
                           f"exposure_class={exposure_class!r}")
    return table[key]
