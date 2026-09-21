"""Slice-by-slice settlement integral `w = Σ Δz · Δσz(z) / E(z)` -- the numerical core the spec's
"Shared sub-routine" describes, reused by every Newmark path (CENTRO main + QA, PUNTO O + O').
`sigma_kpa_at` supplies the vertical-stress increment at a given depth (a plain corner, a centre,
or a point superposition, from `shared.soil_stress`); this module only owns the fixed-step
summation, the layer lookup and the kPa/MPa unit conversion.

Fixes the sheet's silent-zero-past-the-layer-table bug (`docs/architecture-batch2.md` §7
"newmark S, 500 L"): `legacy_compat=True` reproduces it (`shared.soil_layers.layer_at(legacy=True)`
contributes zero past coverage); `legacy_compat=False` raises `CalcError` instead.

Also fixes the sheet's right-endpoint Riemann sum: `Δσz(z)` is monotonically decreasing with depth,
so evaluating it at each slice's BOTTOM under-integrates every slice (worst on the first one, which
uses `Δσz(dz)` instead of a value near `q`), systematically under-predicting the settlement.
`legacy_compat=True` reproduces the sheet's right-endpoint evaluation; `legacy_compat=False`
evaluates `Δσz` at each slice's mid-depth instead (the reported `z_m` stays the slice bottom, and
the layer/modulus lookup is unaffected -- only the stress sample point moves).
"""
from collections.abc import Callable
from dataclasses import dataclass

from strutture.shared.report import CalcError
from strutture.shared.soil_layers import SoilLayer, layer_at
from strutture.shared.tables import KeyNotFound
from strutture.shared.units import KPA_PER_MPA

# `shared.soil_layers.depth_grid`'s `step * dz_m` and `ground_to_base.shift_to_base`'s rounded
# layer bounds can each land a ULP apart for the "same" decimal depth (`39 * 0.1 ==
# 3.9000000000000004`, not the canonical `3.9`); rounding every grid depth here before it reaches
# `layer_at`'s `<=` comparison keeps an exact-boundary depth on the intended side.
_ROUNDING_DECIMALS_M = 9


@dataclass(frozen=True)
class Slice:
    """One depth slice of the integration: the stress used, the layer modulus (`None` past
    coverage in legacy mode) and this slice's contribution to the total settlement."""

    z_m: float
    sigma_kPa: float
    modulo_MPa: float | None
    delta_w_m: float


def integrate_settlement(
    z_grid_m: tuple[float, ...],
    layers: tuple[SoilLayer, ...],
    sigma_kpa_at: Callable[[float], float],
    *,
    legacy_compat: bool = False,
) -> tuple[Slice, ...]:
    """One `Slice` per `z_grid_m` entry (assumed ascending, first slice's thickness measured from
    0); `sigma_kpa_at` is called once per slice, at the slice bottom when `legacy_compat=True`, at
    the slice mid-depth otherwise (the layer/modulus lookup always uses the slice bottom `z_m`,
    matching the reported depth)."""
    slices: list[Slice] = []
    previous_z_m = 0.0
    for raw_z_m in z_grid_m:
        z_m = round(raw_z_m, _ROUNDING_DECIMALS_M)
        thickness_m = z_m - previous_z_m
        try:
            layer = layer_at(layers, z_m, legacy=legacy_compat)
        except KeyNotFound as error:
            raise CalcError(str(error)) from error
        sigma_z_m = z_m if legacy_compat else (previous_z_m + z_m) / 2
        sigma_kpa = sigma_kpa_at(sigma_z_m)
        delta_w_m = thickness_m * (sigma_kpa / KPA_PER_MPA) / layer.modulo_MPa if layer is not None else 0.0
        slices.append(Slice(z_m=z_m, sigma_kPa=sigma_kpa, modulo_MPa=layer.modulo_MPa if layer is not None else None, delta_w_m=delta_w_m))
        previous_z_m = z_m
    return tuple(slices)


def total_settlement_m(slices: tuple[Slice, ...]) -> float:
    return sum(s.delta_w_m for s in slices)
