"""Depth-weighted average modulus `Es` over `[0, H]` for the Timoshenko-Goodier tool: any number
of layers via `shared.soil_layers.weighted_modulus` (code-standard) vs the sheet's `H11` hard-wired
to exactly the first 4 rows of the layer table (`docs/architecture-batch2.md` §7 "T-G-3 H11":
`H11 = Σ_{i=11}^{14} Gi·(Fi-Ei) / C7` -- row 15+ never enters the sum, however deep the real
stratigraphy goes)."""
from strutture.shared.soil_layers import SoilLayer, weighted_modulus

MAX_LEGACY_LAYERS = 4


def legacy_weighted_modulus(layers: tuple[SoilLayer, ...], h_m: float) -> float:
    """`Σ Ei·(Fi-Ei) / h_m` over the first `MAX_LEGACY_LAYERS` rows of `layers` ONLY (already
    shifted to the foundation base), using each layer's OWN thickness -- the sheet's `H11` formula
    has no `MIN(...)`/clipping against `h_m` at all, so a layer's thickness is counted in full even
    when it extends past `h_m` (over-counting) just as a layer past position 4 is dropped in full
    (under-counting), whichever way the sheet's fixed 4-row window happens to fall short of or
    past the real profile."""
    considered = layers[:MAX_LEGACY_LAYERS]
    weighted_sum = sum(layer.modulo_MPa * (layer.z_bot_m - layer.z_top_m) for layer in considered)
    return weighted_sum / h_m


def es_weighted_modulus(layers: tuple[SoilLayer, ...], h_m: float, *, legacy_compat: bool = False) -> float:
    if legacy_compat:
        return legacy_weighted_modulus(layers, h_m)
    return weighted_modulus(layers, h_m)
