"""Ground-surface -> foundation-base depth shift, mirroring the sheets' own
`IF(B-D<0,0,B-D)` / `IF(C-D<0,0,C-D)` truncation (spec "Calculation steps", step 1: "convert
ground-surface depths to depth-below-foundation-base"). Kept in both modes -- it is the intended
depth reference, not a bug. A layer left with zero (or negative) thickness below the base -- fully
above the embedment -- is dropped: it never matches any `z > 0` lookup in the sheet's own IF-chain
either, so dropping it changes nothing downstream.
"""
from strutture.shared.soil_layers import SoilLayer

# Layer bounds are typically "nice" decimals (originally entered in cm); the subtraction below can
# land a ULP away from that value (`4.80 - 1.10 == 3.6999999999999997`), which would then miss an
# exact-multiple-of-`dz` boundary in `shared.soil_layers.layer_at`'s `<=` comparison. Rounding to
# nanometre precision (`1e-9` m) discards that noise without affecting any physical result.
_ROUNDING_DECIMALS_M = 9


def shift_to_base(layers: tuple[SoilLayer, ...], embedment_m: float) -> tuple[SoilLayer, ...]:
    """`layers` given from the ground surface -> the same stratigraphy measured from the
    foundation base, `embedment_m` below the ground surface. Contiguous, ascending-from-0 ground
    layers stay contiguous, ascending-from-0 after the shift (the layer straddling `embedment_m`
    is the first to keep a positive top)."""
    shifted: list[SoilLayer] = []
    for layer in layers:
        top_m = round(max(0.0, layer.z_top_m - embedment_m), _ROUNDING_DECIMALS_M)
        bottom_m = round(max(0.0, layer.z_bot_m - embedment_m), _ROUNDING_DECIMALS_M)
        if bottom_m > top_m:
            shifted.append(SoilLayer(z_top_m=top_m, z_bot_m=bottom_m, modulo_MPa=layer.modulo_MPa))
    return tuple(shifted)
