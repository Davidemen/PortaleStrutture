"""Crack-width class required by NTC2018 Tab. 4.1.IV for the FRE/QPE checks of
`ca-apertura-fessure-semplificata` — resolved from exposure/sensitivity via
`strutture.shared.durability_cover.crack_width_limit`, same pattern as
`ca_travi/fessurazione.py`'s `classe_normativa` step.

`CLASSE_FALLBACK_FRE`/`CLASSE_FALLBACK_QPE` are the sheet's hardcoded pair (w3/w2, the Tab.
4.1.IV row for "condizioni ordinarie + armatura poco sensibile") kept for `legacy_compat=True`.
"""
from strutture.shared.durability_cover import (
    CrackWidthClass,
    EnvironmentalCondition,
    ReinforcementSensitivity,
    crack_width_limit,
)

CLASSE_FALLBACK_FRE: CrackWidthClass = "w3"
CLASSE_FALLBACK_QPE: CrackWidthClass = "w2"


def classe_normativa_fre(condizione: EnvironmentalCondition, sensibilita: ReinforcementSensitivity) -> CrackWidthClass | None:
    """Classe richiesta per la combinazione frequente (Tab. 4.1.IV); `None` se è richiesta una
    verifica a decompressione anziché un limite di ampiezza di fessura."""
    return crack_width_limit(condizione, "frequente", sensibilita)


def classe_normativa_qpe(condizione: EnvironmentalCondition, sensibilita: ReinforcementSensitivity) -> CrackWidthClass | None:
    """Classe richiesta per la combinazione quasi-permanente (Tab. 4.1.IV); `None` se è
    richiesta una verifica a decompressione anziché un limite di ampiezza di fessura."""
    return crack_width_limit(condizione, "quasi permanente", sensibilita)
