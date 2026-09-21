"""Effective overburden σ'v0(z), buoyant below the water table, as the oedometric sheet computes
it (`docs/specs/geo-cedimenti-edometrico.md` step 2b: `Δσ'v = (γ−γw)·1e-6·z`, water table baked in
at z=0). Generalised to a configurable water-table depth; `water_table_m=0.0` (fully submerged
from the reference level down) reproduces the sheet exactly."""

GAMMA_WATER_KN_M3 = 9.80665  # 1000 kg/mc * 9.80665 m/s^2, matches units.KPA_PER_KGCM2's g


def effective_overburden(gamma_kn_m3: float, z_m: float, *, water_table_m: float = 0.0, gamma_water_kn_m3: float = GAMMA_WATER_KN_M3) -> float:
    """σ'v0 [kPa] at depth `z_m` below the reference level, for a homogeneous soil of total unit
    weight `gamma_kn_m3`, with a water table at `water_table_m` below the same reference (buoyant
    unit weight `gamma_kn_m3 - gamma_water_kn_m3` applies below it). Called with `z_m` measured
    from the foundation base and `water_table_m=0.0`, this is exactly the sheet's Δσ'v (the
    overburden *increase* below the base, not the absolute overburden from the ground surface)."""
    if z_m < 0:
        raise ValueError(f"effective_overburden: z_m must be >= 0, got {z_m}")
    if water_table_m < 0:
        raise ValueError(f"effective_overburden: water_table_m must be >= 0, got {water_table_m}")
    if z_m <= water_table_m:
        return gamma_kn_m3 * z_m
    gamma_buoyant = gamma_kn_m3 - gamma_water_kn_m3
    return gamma_kn_m3 * water_table_m + gamma_buoyant * (z_m - water_table_m)
