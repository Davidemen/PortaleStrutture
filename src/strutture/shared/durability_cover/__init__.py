"""Durability/exposure/cover data shared by the CA (cemento armato) member tools.

See docs/BUILD_CONTRACT.md "Shared modules"; sources: `ca-travi`/`ca-mensole`/`ca-pilastri`
sheet 'Tabelle'.
"""
from .cover import min_cover_mm
from .crack_limits import crack_width_limit
from .exposure import environmental_condition
from .models import (
    CrackWidthClass,
    EnvironmentalCondition,
    ExposureClass,
    LoadCombination,
    ReinforcementSensitivity,
    ReinforcementType,
    StructuralClass,
)

__all__ = [
    "CrackWidthClass",
    "EnvironmentalCondition",
    "ExposureClass",
    "LoadCombination",
    "ReinforcementSensitivity",
    "ReinforcementType",
    "StructuralClass",
    "crack_width_limit",
    "environmental_condition",
    "min_cover_mm",
]
