"""ISO 834 standard fire curve + EN1993-1-2 Table 3.1 reduction factors, shared by every
`*-incendio` tool. Pure functions + frozen result models only; no `Tool` is registered here."""
from .iso834 import gas_temperature_C
from .models import ReductionFactors
from .reduction_factors import reduction_factors
from .tables import TABLE_3_1

__all__ = [
    "TABLE_3_1",
    "ReductionFactors",
    "gas_temperature_C",
    "reduction_factors",
]
