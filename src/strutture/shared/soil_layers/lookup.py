"""Range lookup of the layer covering a given depth.

Fixes the sheet bug (`docs/architecture-batch2.md` §7 "edometrico J, newmark S, 500 L"): a depth
past the last layer's `z_bot_m`, or falling in a gap, used to look up as 0 (`IFERROR(...,0)`,
silently zeroing that slice's settlement contribution). `legacy=True` reproduces that behaviour
(returns `None`, meaning "zero contribution" to the caller) so `legacy_compat` tools can still
match the golden cases; the code-standard default raises instead of ever returning 0 silently."""
from strutture.shared import divergences
from strutture.shared.tables import KeyNotFound

from .models import SoilLayer


def layer_at(layers: tuple[SoilLayer, ...], z_m: float, *, legacy: bool = False) -> SoilLayer | None:
    """The layer whose `[z_top_m, z_bot_m)` covers `z_m` (first layer's band is closed at both
    ends, `[z_top_m, z_bot_m]`, matching the sheet's row-0 special case). Raises `KeyNotFound` when
    no layer covers `z_m`, unless `legacy=True` (then returns `None`)."""
    for index, layer in enumerate(layers):
        lower_inclusive = index == 0
        if (z_m >= layer.z_top_m if lower_inclusive else z_m > layer.z_top_m) and z_m <= layer.z_bot_m:
            return layer
    # local parameter is named `legacy` (clashing with the `divergences.legacy` marker function by
    # design, see module docstring); imported qualified to avoid shadowing it.
    if divergences.legacy("soil-layers-coverage-and-weighting/lookup-strato-zero-oltre-copertura", legacy):
        return None
    raise KeyNotFound(f"la stratigrafia non copre la profondità z={z_m} m")
