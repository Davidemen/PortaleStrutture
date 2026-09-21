"""Soil stratigraphy table + stress-independent depth helpers (docs/architecture-batch2.md §1.2):
layer row model, cross-row validation, coverage lookup (never returns 0 silently), depth-weighted
average modulus, effective overburden, and the depth-slicing grid. Pure functions, no I/O, no
`Tool` registered — consumed by `strutture.geotechnics.cedimenti_*`."""
from .grid import depth_grid
from .lookup import layer_at
from .models import SoilLayer
from .overburden import GAMMA_WATER_KN_M3, effective_overburden
from .table import MAX_STRATI_ROWS, strati_table_field
from .validate import validate
from .weighted import weighted_modulus

__all__ = [
    "GAMMA_WATER_KN_M3",
    "MAX_STRATI_ROWS",
    "SoilLayer",
    "depth_grid",
    "effective_overburden",
    "layer_at",
    "strati_table_field",
    "validate",
    "weighted_modulus",
]
