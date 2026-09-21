"""Support-reactions table model shared by `foundations.plinti_isolati` and `foundations.plinti_pali`
(docs/architecture-batch2.md §1.2, §2): row model + table field, grouping and envelope helpers.
Pure data/functions only; no `Tool` is registered here."""
from .envelope import envelope, governing
from .grouping import group_by_famiglia, group_by_nodo
from .models import EnvelopeMode, EnvelopeRow, Famiglia, ReactionRow
from .table import MAX_REAZIONI_ROWS, reazioni_table_field
from .validate import validate_unique_nodo_combo

__all__ = [
    "MAX_REAZIONI_ROWS",
    "EnvelopeMode",
    "EnvelopeRow",
    "Famiglia",
    "ReactionRow",
    "envelope",
    "governing",
    "group_by_famiglia",
    "group_by_nodo",
    "reazioni_table_field",
    "validate_unique_nodo_combo",
]
