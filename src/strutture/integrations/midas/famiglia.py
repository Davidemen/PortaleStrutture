"""`suggest_famiglia`: table-driven mapping from a combination's name/classification to a Famiglia
suggestion (docs/integrations/MIDAS.md §3 famiglia.py). Pure; the UI lets the engineer override the
suggestion per combination."""
from strutture.shared.load_table import Famiglia

from .combinations import Combination

# (substring in NAME, Famiglia when "EQU" is also in NAME, Famiglia otherwise). Checked in order,
# most specific limit state first, so e.g. "SLV-EQU1" resolves to SLV_EQU, not the generic SLV_STR.
_NAME_RULES: tuple[tuple[str, Famiglia, Famiglia], ...] = (
    ("SLV", "SLV_EQU", "SLV_STR"),
    ("SISM", "SLV_EQU", "SLV_STR"),
    ("SLU", "SLU_EQU", "SLU_STR"),
    ("STR", "SLU_EQU", "SLU_STR"),
)
_SLE_NAME_RULES: tuple[tuple[str, Famiglia], ...] = (
    ("FREQ", "SLE_FREQ"),
    ("QP", "SLE_QP"),
    ("PERM", "SLE_QP"),
    ("RARA", "SLE_RARA"),
    ("CAR", "SLE_RARA"),
    ("SLE", "SLE_RARA"),
)
_ACTIVE_RULES: dict[str, Famiglia] = {"STRENGTH": "SLU_STR", "SERVICE": "SLE_RARA"}


def suggest_famiglia(combination: Combination) -> Famiglia | None:
    """Name pattern first, then `ACTIVE` (`STRENGTH` -> SLU_STR, `SERVICE` -> SLE_RARA)."""
    name = combination.name.upper()
    is_equ = "EQU" in name
    for pattern, equ_famiglia, str_famiglia in _NAME_RULES:
        if pattern in name:
            return equ_famiglia if is_equ else str_famiglia
    for pattern, famiglia in _SLE_NAME_RULES:
        if pattern in name:
            return famiglia
    return _ACTIVE_RULES.get(combination.active.upper())
