"""Effective overburden q' at the founding level and effective unit weight γ' for the Nγ term,
accounting for a water table. EN 1997-1 Annex D works with effective stresses but does not itself
prescribe how to average γ' when the water table falls inside the failure wedge below the base;
this reuses the sheets' single-γ convention (`shared.soil_layers.overburden.effective_overburden`)
for q', and [A] linearly averages the buoyant and full unit weight over the depth B' below the
base for γ' (standard Terzaghi/Meyerhof practice) — flagged as an assumption to confirm with the
engineer (docs/architecture-phase4.md §C).
"""
import math

from strutture.shared.soil_layers.overburden import GAMMA_WATER_KN_M3, effective_overburden


def sovraccarico_efficace_kpa(gamma_kn_m3: float, profondita_piano_posa_m: float, profondita_falda_m: float | None) -> float:
    """q' [kPa] at the founding depth `profondita_piano_posa_m` below ground level, given a
    water table at `profondita_falda_m` below the same reference (`None` = no water table)."""
    water_table_m = math.inf if profondita_falda_m is None else profondita_falda_m
    return effective_overburden(gamma_kn_m3, profondita_piano_posa_m, water_table_m=water_table_m)


def gamma_efficace_kn_m3(
    gamma_kn_m3: float, profondita_piano_posa_m: float, b_eff_m: float, profondita_falda_m: float | None,
) -> float:
    """γ' [kN/m³] for the 0.5·γ'·B'·Nγ term: buoyant when the water table is at/above the base,
    full (`gamma_kn_m3`) when it is at/below (base + B'), linearly interpolated in between."""
    if profondita_falda_m is None:
        return gamma_kn_m3
    gamma_sommerso = gamma_kn_m3 - GAMMA_WATER_KN_M3
    profondita_falda_sotto_base_m = profondita_falda_m - profondita_piano_posa_m
    if profondita_falda_sotto_base_m <= 0:
        return gamma_sommerso
    if profondita_falda_sotto_base_m >= b_eff_m:
        return gamma_kn_m3
    frazione = profondita_falda_sotto_base_m / b_eff_m
    return gamma_sommerso + frazione * (gamma_kn_m3 - gamma_sommerso)
