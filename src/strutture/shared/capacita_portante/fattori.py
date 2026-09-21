"""Public facade for every EN 1997-1 Annex D factor: bearing-capacity (Nq, Nc, Nγ), shape
(sq, sγ, sc), load-inclination (iq, iγ, ic, exponent m) and base-inclination (bq, bγ, bc)
factors. Implementation is split into one small module per factor family (kept < 150 lines
each, per the modularity rule); this module only re-exports the public functions so callers
have a single, stable import path: `strutture.shared.capacita_portante.fattori`.
"""
from .fattori_base import fattori_inclinazione_base, fattori_inclinazione_base_non_drenata
from .fattori_forma import fattori_forma, fattori_forma_non_drenata
from .fattori_inclinazione import esponente_m, fattori_inclinazione_carico, fattori_inclinazione_carico_non_drenata
from .fattori_portanza import fattori_portanza

__all__ = [
    "esponente_m",
    "fattori_forma",
    "fattori_forma_non_drenata",
    "fattori_inclinazione_base",
    "fattori_inclinazione_base_non_drenata",
    "fattori_inclinazione_carico",
    "fattori_inclinazione_carico_non_drenata",
    "fattori_portanza",
]
