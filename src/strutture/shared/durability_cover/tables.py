"""Lookup tables for exposure/durability, NTC2018 Tab. 4.1.IV (crack-width limits) and the
minimum-cover table found in `ca-travi`/`ca-mensole`/`ca-pilastri` sheet 'Tabelle'.

Sources (all three sheets carry an identical copy of these tables):
- Crack-width limits: Tabelle!M56:Q62.
- Minimum cover cmin,dur: Tabelle!M14:R20 (armatura ordinaria) and M23:R29 (precompressa),
  keyed by "classe strutturale" S (1..6) x exposure class (X0/XC1/XC2/XC3/XC4).
"""
from .models import (
    CrackWidthClass,
    EnvironmentalCondition,
    ExposureClass,
    LoadCombination,
    ReinforcementSensitivity,
    ReinforcementType,
    StructuralClass,
)

# Tabelle!M56:Q62 -> {(condizione, combinazione, sensibilita): w-class or None if not tabulated
# (NTC2018 requires a decompression check instead of a crack-width limit in that cell).
CRACK_WIDTH_LIMITS: dict[
    tuple[EnvironmentalCondition, LoadCombination, ReinforcementSensitivity], CrackWidthClass | None
] = {
    ("ordinarie", "frequente", "sensibile"): "w2",
    ("ordinarie", "frequente", "poco sensibile"): "w3",
    ("ordinarie", "quasi permanente", "sensibile"): "w1",
    ("ordinarie", "quasi permanente", "poco sensibile"): "w2",
    ("aggressive", "frequente", "sensibile"): "w1",
    ("aggressive", "frequente", "poco sensibile"): "w2",
    ("aggressive", "quasi permanente", "sensibile"): None,
    ("aggressive", "quasi permanente", "poco sensibile"): "w1",
    ("molto aggressive", "frequente", "sensibile"): None,
    ("molto aggressive", "frequente", "poco sensibile"): "w1",
    ("molto aggressive", "quasi permanente", "sensibile"): None,
    ("molto aggressive", "quasi permanente", "poco sensibile"): "w1",
}

# Tabelle!M14:R20 — cmin,dur [mm], armatura ordinaria, keyed by (classe strutturale S, esposizione).
MIN_COVER_ORDINARIA: dict[tuple[StructuralClass, ExposureClass], float] = {
    (1, "X0"): 10, (1, "XC1"): 10, (1, "XC2"): 10, (1, "XC3"): 10, (1, "XC4"): 15,
    (2, "X0"): 10, (2, "XC1"): 10, (2, "XC2"): 15, (2, "XC3"): 15, (2, "XC4"): 20,
    (3, "X0"): 10, (3, "XC1"): 10, (3, "XC2"): 20, (3, "XC3"): 20, (3, "XC4"): 25,
    (4, "X0"): 10, (4, "XC1"): 15, (4, "XC2"): 25, (4, "XC3"): 25, (4, "XC4"): 30,
    (5, "X0"): 15, (5, "XC1"): 20, (5, "XC2"): 30, (5, "XC3"): 30, (5, "XC4"): 35,
    (6, "X0"): 20, (6, "XC1"): 25, (6, "XC2"): 35, (6, "XC3"): 35, (6, "XC4"): 40,
}

# Tabelle!M23:R29 — cmin,dur [mm], armatura da precompressione.
MIN_COVER_PRECOMPRESSA: dict[tuple[StructuralClass, ExposureClass], float] = {
    (1, "X0"): 10, (1, "XC1"): 15, (1, "XC2"): 20, (1, "XC3"): 20, (1, "XC4"): 25,
    (2, "X0"): 10, (2, "XC1"): 15, (2, "XC2"): 25, (2, "XC3"): 25, (2, "XC4"): 30,
    (3, "X0"): 10, (3, "XC1"): 20, (3, "XC2"): 30, (3, "XC3"): 30, (3, "XC4"): 35,
    (4, "X0"): 10, (4, "XC1"): 25, (4, "XC2"): 35, (4, "XC3"): 35, (4, "XC4"): 40,
    (5, "X0"): 15, (5, "XC1"): 30, (5, "XC2"): 40, (5, "XC3"): 40, (5, "XC4"): 45,
    (6, "X0"): 20, (6, "XC1"): 35, (6, "XC2"): 45, (6, "XC3"): 45, (6, "XC4"): 50,
}

_MIN_COVER_TABLES: dict[ReinforcementType, dict[tuple[StructuralClass, ExposureClass], float]] = {
    "ordinaria": MIN_COVER_ORDINARIA,
    "precompressa": MIN_COVER_PRECOMPRESSA,
}
