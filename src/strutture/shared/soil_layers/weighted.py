"""Depth-weighted average modulus over `[0, h]`, generalising the Timoshenko-Goodier sheet's `H11`
(`docs/architecture-batch2.md` §7 "T-G-3 H11": hard-wired to exactly 4 layers) to any number of
layers, and raising instead of silently ignoring thickness the layer table doesn't cover."""
from strutture.shared.tables import KeyNotFound

from .models import SoilLayer


def weighted_modulus(layers: tuple[SoilLayer, ...], h_m: float) -> float:
    """`Σ Ei·Δzi / h_m` over the portion `[0, h_m]` of each layer (a layer fully or partially
    beyond `h_m` contributes only its overlap with `[0, h_m]`). Raises `KeyNotFound` if `layers`
    does not cover `[0, h_m]` (the fix for the sheet's silent 4-layer truncation). Assumes `layers`
    is already `validate()`d (contiguous, ascending) — a gap strictly between two layers is not
    independently detected here."""
    if h_m <= 0:
        raise ValueError(f"weighted_modulus: h_m must be > 0, got {h_m}")
    covered_to = 0.0
    weighted_sum = 0.0
    for layer in layers:
        overlap = min(layer.z_bot_m, h_m) - max(layer.z_top_m, 0.0)
        if overlap > 0:
            weighted_sum += layer.modulo_MPa * overlap
            covered_to = max(covered_to, min(layer.z_bot_m, h_m))
        if covered_to >= h_m:
            break
    if covered_to < h_m:
        raise KeyNotFound(f"la stratigrafia non copre [0, {h_m}] m (arriva solo a {covered_to} m)")
    return weighted_sum / h_m
