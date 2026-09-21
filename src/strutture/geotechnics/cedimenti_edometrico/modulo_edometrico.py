"""Step 4: applicable oedometric modulus Eed(z) from the `strati` table (docs/specs/geo-cedimenti-
edometrico.md, calculation step 2c). Never a silent 0 (docs/architecture-batch2.md §7 "edometrico
J, newmark S, 500 L"): `legacy_compat=False` lets `shared.soil_layers.layer_at`'s `KeyNotFound`
propagate — the tool wraps it into a `CalcError` naming the depth; `legacy_compat=True` reproduces
the sheet's `IFERROR(...,0)` collapse by returning `None` for that slice (treated as a zero
settlement increment by `righe.py`, never as a literal division by zero)."""
from strutture.shared.soil_layers import SoilLayer, layer_at
from strutture.shared.units import mpa_to_kpa


def eed_kpa(layers: tuple[SoilLayer, ...], z_m: float, *, legacy: bool) -> float | None:
    layer = layer_at(layers, z_m, legacy=legacy)
    return None if layer is None else mpa_to_kpa(layer.modulo_MPa)
