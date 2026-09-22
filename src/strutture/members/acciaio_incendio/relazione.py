"""Public entry points for `acciaio_incendio`'s two `Tool`s (docs/architecture-phase2.md §6): each
tool has its own input/output model, so each gets its own `relazione(inputs, output)` callable
rather than sharing a single composed function (compare `ca_travi.relazione`, one tool per package).
See `relazione_resistenza.py`/`relazione_proprieta.py` for what each restates.
"""
from .relazione_proprieta import relazione_proprieta
from .relazione_resistenza import relazione_resistenza

__all__ = ["relazione_proprieta", "relazione_resistenza"]
