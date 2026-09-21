"""Merged municipality database (regione/provincia/istat/comune + zona sismica/vento/neve).

Public API:
    from strutture.shared.comuni import Comune, lookup_comune, search_comuni, KeyNotFound, AmbiguousComuneError

Build the data file (once, or whenever the source CSVs change) with:
    uv run python -m strutture.shared.comuni.build
"""
from .errors import AmbiguousComuneError, KeyNotFound
from .label import ComuneOption
from .loader import load_comuni, lookup_comune, search_comuni, search_options
from .models import Comune

__all__ = [
    "AmbiguousComuneError",
    "Comune",
    "ComuneOption",
    "KeyNotFound",
    "load_comuni",
    "lookup_comune",
    "search_comuni",
    "search_options",
]
