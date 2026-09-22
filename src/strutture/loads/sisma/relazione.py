"""Entry point for `sisma`'s "Sviluppo dei calcoli" (docs/architecture-phase2.md §6, wave 3
adoption). One `relazione_*` function per registered `Tool` (`tool.py::TOOLS`), each split into
its own `relazione_*.py` module below <400 lines — the calculation code of this package is never
touched, not one number, not one signature. See each module's own docstring for which package
module(s) it restates and which intermediate (not exposed by that tool's own output model) it
reads straight from the package's own step functions.
"""
from .relazione_completo import relazione_completo
from .relazione_fattori_struttura import relazione_fattori_struttura
from .relazione_parametri_sito import relazione_parametri_sito
from .relazione_spettro import relazione_spettro
from .relazione_vita_riferimento import relazione_vita_riferimento

__all__ = [
    "relazione_completo",
    "relazione_fattori_struttura",
    "relazione_parametri_sito",
    "relazione_spettro",
    "relazione_vita_riferimento",
]
