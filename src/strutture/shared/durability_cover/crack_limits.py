"""Crack-width limit selection, NTC2018 Tab. 4.1.IV (Tabelle!M56:Q62)."""
from .models import CrackWidthClass, EnvironmentalCondition, LoadCombination, ReinforcementSensitivity
from .tables import CRACK_WIDTH_LIMITS


def crack_width_limit(condizione: EnvironmentalCondition, combinazione: LoadCombination,
                       sensibilita: ReinforcementSensitivity) -> CrackWidthClass | None:
    """Crack-width class (w1/w2/w3) applicable for the given exposure/combination/sensitivity.

    Returns `None` for the cells the sheet leaves blank (aggressive/molto aggressive + sensibile
    armatura): NTC2018 requires a decompression check there rather than a crack-width limit.
    """
    key = (condizione, combinazione, sensibilita)
    if key not in CRACK_WIDTH_LIMITS:
        raise ValueError(f"unknown combination {key!r}")
    return CRACK_WIDTH_LIMITS[key]
