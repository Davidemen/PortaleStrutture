"""Step 6: critical depth Z,crit — the depth where Δσv,q(z) = 0.1·Δσ'v(z), the classical
"significant depth" criterion. The sheet sets up a Cardano cubic solver for exactly this equation
(cells B24:B28) but never assembles the root into a usable value — B18 (Z,crit) is a plain
hard-coded manual cell, left at 10000 cm in the cached run (docs/specs/geo-cedimenti-edometrico.md
"Suspected spreadsheet bugs" #1; docs/architecture-batch2.md §7 "edometrico B18/B24:B28"). Solved
here by bisection (`shared.numeric.bisect`) against the SAME Δσ the tool integrates for the
settlement (`metodo_tensioni`), not just the sheet's spread formula, so the criterion always
matches what `righe.py` actually sums."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.divergences import legacy
from strutture.shared.numeric import bisect
from strutture.shared.report import CalcError
from strutture.shared.soil_layers import effective_overburden

from .models import MetodoTensioni
from .tensione_indotta import tensione_indotta

_CRITERIO_FRAZIONE = 0.1  # Δσv,q = 0.1·Δσ'v: il criterio classico di profondità significativa
_Z_MIN_RICERCA_M = 1e-3
_Z_MAX_RICERCA_M = 1000.0


class ProfonditaCriticaResult(BaseModel):
    """The auto-computed root, and the value actually applied to the settlement sum (manual
    override, or the sheet's disabled-cutoff default in legacy mode, when no override is given)."""

    model_config = ConfigDict(frozen=True)

    z_crit_calcolato_m: float = Field(
        description="Profondità critica calcolata (criterio Δσv,q = 0.1·Δσ'v)",
        json_schema_extra={"unit": "m", "symbol": "Z_crit,calc"},
    )
    z_crit_utilizzato_m: float = Field(
        description="Profondità critica utilizzata per il cedimento (manuale se impostata, altrimenti calcolata)",
        json_schema_extra={"unit": "m", "symbol": "Z_crit", "highlight": True},
    )


def calcola_z_crit(
    q_prime_kPa: float,
    b_m: float,
    l_m: float,
    gamma_kN_m3: float,
    *,
    metodo: MetodoTensioni,
    d_m: float = 0.0,
    water_table_m: float | None = 0.0,
) -> float:
    """Root of `Δσv,q(z) − 0.1·σ'v0(z) = 0` in `[_Z_MIN_RICERCA_M, _Z_MAX_RICERCA_M]`. Raises
    `CalcError` if no root exists in that range (e.g. an unrealistically small `gamma`).

    `σ'v0(z)` is the total effective stress from ground level, `γ·D` plus the increment below
    the base (docs/architecture-batch2.md §7 review finding HIGH: the classical criterion
    compares against the *total* stress, not just the increment). Defaults `d_m=0.0`,
    `water_table_m=0.0` reproduce the previous call sites unchanged (increment below the base,
    water table always at z=0); `water_table_m=None` means a dry profile (no buoyancy)."""

    def scarto(z_m: float) -> float:
        delta_sigma_kPa = tensione_indotta(q_prime_kPa, b_m, l_m, z_m, metodo=metodo).utilizzato_kPa
        falda_di_riferimento_m = water_table_m if water_table_m is not None else float("inf")
        sigma_v0_kPa = effective_overburden(gamma_kN_m3, d_m + z_m, water_table_m=falda_di_riferimento_m)
        return delta_sigma_kPa - _CRITERIO_FRAZIONE * sigma_v0_kPa

    try:
        return bisect(scarto, _Z_MIN_RICERCA_M, _Z_MAX_RICERCA_M)
    except ValueError as errore:
        raise CalcError(f"impossibile calcolare la profondità critica Z,crit: {errore}") from errore


def profondita_critica(
    q_prime_kPa: float,
    b_m: float,
    l_m: float,
    gamma_kN_m3: float,
    *,
    metodo: MetodoTensioni,
    z_crit_input_m: float | None,
    legacy_compat: bool,
    z_max_m: float,
    d_m: float = 0.0,
    water_table_m: float | None = 0.0,
) -> ProfonditaCriticaResult:
    """`z_crit_input_m` (manual override in standard mode / the sheet's free B18 cell in legacy
    mode) always wins when given. Otherwise: standard mode uses the computed root; legacy mode
    reproduces the sheet's cached default — a value past the depth table, disabling the cutoff —
    since the sheet never assembles the root it computes into B18. `d_m`/`water_table_m` feed the
    same total-stress reference as `righe.sigma_v0_kPa`; callers must pass `d_m=0.0,
    water_table_m=0.0` for `legacy_compat=True` to keep it frozen (`tool.run` does)."""
    calcolato_m = calcola_z_crit(q_prime_kPa, b_m, l_m, gamma_kN_m3, metodo=metodo, d_m=d_m, water_table_m=water_table_m)
    if z_crit_input_m is not None:
        utilizzato_m = z_crit_input_m
    elif legacy("geo-cedimenti-edometrico/z-crit-manuale-non-derivata", legacy_compat):
        utilizzato_m = z_max_m + 1.0
    else:
        utilizzato_m = calcolato_m
    return ProfonditaCriticaResult(z_crit_calcolato_m=calcolato_m, z_crit_utilizzato_m=utilizzato_m)
