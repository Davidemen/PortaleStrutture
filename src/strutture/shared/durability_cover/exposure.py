"""Exposure-group helper, Tabelle!M57:N61 (Gruppo a/b/c -> Condizioni ambientali)."""
from typing import Literal

from strutture.shared.tables import exact_lookup

from .models import EnvironmentalCondition

ExposureGroup = Literal["a", "b", "c"]

# Tabelle!M57:N61.
EXPOSURE_GROUP_TO_CONDITION: tuple[tuple[ExposureGroup, EnvironmentalCondition], ...] = (
    ("a", "ordinarie"),
    ("b", "aggressive"),
    ("c", "molto aggressive"),
)


def environmental_condition(group: ExposureGroup) -> EnvironmentalCondition:
    """Map the sheet's exposure group letter (a/b/c) to its environmental condition label."""
    return exact_lookup(EXPOSURE_GROUP_TO_CONDITION, group)
