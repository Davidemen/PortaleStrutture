"""Step 5: one row per depth slice of `shared.soil_layers.depth_grid(z_max_m, dz_m)` — Δσ (both
methods), Δσ'v, Eed, the slice's oedometric strain increment ΔH,i and the running cumulative
settlement (docs/specs/geo-cedimenti-edometrico.md, calculation steps 2b/2d/2e). The sheet's
reset-to-0-past-cutoff "capped" column M is not reproduced (docs/architecture-batch2.md §7
"edometrico M": same numeric result either way) — `cumulativo_cm` here is the unconditional running
sum for every row; `cedimento.py` reads it at the cutoff depth."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.soil_layers import SoilLayer, depth_grid, effective_overburden
from strutture.shared.units import m_to_cm

from .models import MetodoTensioni
from .modulo_edometrico import eed_kpa
from .tensione_indotta import tensione_indotta


class RigaResult(BaseModel):
    """One 10 cm-default depth slice: both Δσ methods, the effective overburden increase, the
    applicable Eed, the slice's settlement increment and the running cumulative settlement."""

    model_config = ConfigDict(frozen=True)

    z_m: float = Field(description="Profondità dal piano di posa della fondazione", json_schema_extra={"unit": "m"})
    delta_sigma_approssimato_kPa: float = Field(description="Δσv,q approssimato (spread 2:1)", json_schema_extra={"unit": "kPa"})
    delta_sigma_newmark_kPa: float | None = Field(description="Δσv,q esatto (Newmark)", json_schema_extra={"unit": "kPa"})
    delta_sigma_kPa: float = Field(description="Δσv,q utilizzato per il cedimento (per `metodo_tensioni`)", json_schema_extra={"unit": "kPa"})
    sigma_v0_kPa: float = Field(
        description=(
            "Tensione litostatica efficace σ'v0: incremento Δσ'v sotto il piano di posa in "
            "modalità legacy (falda sempre al piano di posa, D ignorato); tensione totale dal "
            "piano campagna (γ·D + incremento, con falda opzionale) in modalità standard"
        ),
        json_schema_extra={"unit": "kPa"},
    )
    eed_kPa: float | None = Field(
        description="Modulo edometrico applicabile (assente = stratigrafia non copre z, solo in modalità legacy)",
        json_schema_extra={"unit": "kPa"},
    )
    delta_h_cm: float = Field(description="Incremento di cedimento della fetta ΔH,i", json_schema_extra={"unit": "cm"})
    cumulativo_cm: float = Field(description="Cedimento cumulato ΣΔH,i fino a questa profondità", json_schema_extra={"unit": "cm"})


def genera_righe(
    q_prime_kPa: float,
    b_m: float,
    l_m: float,
    gamma_kN_m3: float,
    layers: tuple[SoilLayer, ...],
    *,
    metodo: MetodoTensioni,
    dz_m: float,
    z_max_m: float,
    legacy_compat: bool,
    d_m: float = 0.0,
    water_table_m: float | None = 0.0,
) -> tuple[RigaResult, ...]:
    """One `RigaResult` per point of `depth_grid(z_max_m, dz_m)`. `delta_h_cm` is 0 at z=0 (the
    sheet's degenerate first slice, calculation step 2d). Raises `shared.tables.KeyNotFound` (via
    `modulo_edometrico.eed_kpa`) as soon as `legacy_compat=False` and a slice falls outside the
    stratigraphy — never a silent 0.

    `sigma_v0_kPa` (docs/architecture-batch2.md §7 review finding HIGH): in `legacy_compat=True`
    it stays the sheet's own Δσ'v below the base (`d_m`/`water_table_m` ignored, water table
    always at the base — frozen). In standard mode it is the total effective stress from ground
    level, `γ·D` plus the buoyant/total increment below the base; `water_table_m=None` means a
    dry profile (no buoyancy), the default `0.0` reproduces the old call sites unchanged."""
    griglia = depth_grid(z_max_m, dz_m)
    righe: tuple[RigaResult, ...] = ()
    cumulativo_m = 0.0
    for indice, z_m in enumerate(griglia):
        tensione = tensione_indotta(q_prime_kPa, b_m, l_m, z_m, metodo=metodo)
        if legacy_compat:
            sigma_v0_kPa = effective_overburden(gamma_kN_m3, z_m)
        else:
            falda_di_riferimento_m = water_table_m if water_table_m is not None else float("inf")
            sigma_v0_kPa = effective_overburden(gamma_kN_m3, d_m + z_m, water_table_m=falda_di_riferimento_m)
        eed = eed_kpa(layers, z_m, legacy=legacy_compat)
        delta_h_m = _incremento_m(eed, tensione.utilizzato_kPa, z_m, griglia[indice - 1] if indice else None)
        cumulativo_m += delta_h_m
        righe = (
            *righe,
            RigaResult(
                z_m=z_m,
                delta_sigma_approssimato_kPa=tensione.approssimato_kPa,
                delta_sigma_newmark_kPa=tensione.newmark_kPa,
                delta_sigma_kPa=tensione.utilizzato_kPa,
                sigma_v0_kPa=sigma_v0_kPa,
                eed_kPa=eed,
                delta_h_cm=m_to_cm(delta_h_m),
                cumulativo_cm=m_to_cm(cumulativo_m),
            ),
        )
    return righe


def _incremento_m(eed_kPa: float | None, delta_sigma_kPa: float, z_m: float, z_precedente_m: float | None) -> float:
    """ΔH,i = Δz·Δσv,q/Eed; 0 at the first (degenerate) slice or when `eed_kPa` is `None`
    (legacy-mode zero contribution past the stratigraphy)."""
    if z_precedente_m is None or eed_kPa is None:
        return 0.0
    return (z_m - z_precedente_m) * delta_sigma_kPa / eed_kPa
