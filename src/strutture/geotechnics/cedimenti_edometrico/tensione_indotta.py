"""Step 3: load-induced vertical stress increase Δσv,q(z) under the centre of the footing, by the
sheet's approximate 2:1-type spread AND by the exact Newmark integral (docs/specs/geo-cedimenti-
edometrico.md, calculation step 2a; docs/architecture-batch2.md §1.1 "expose `metodo_tensioni`").
At z=0 both are exactly q' (`spread_2to1` handles z=0 directly; Newmark needs z>0 so it is left
`None` there, matching the sheet's T column which also starts at z=10 cm)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.soil_stress import spread_2to1, under_center

from .models import MetodoTensioni


class TensioneIndotta(BaseModel):
    """Both methods, plus the one selected by `metodo_tensioni` for the settlement calculation."""

    model_config = ConfigDict(frozen=True)

    approssimato_kPa: float = Field(description="Δσv,q approssimato (spread 2:1 del foglio)", json_schema_extra={"unit": "kPa"})
    newmark_kPa: float | None = Field(description="Δσv,q esatto (Newmark), assente a z=0", json_schema_extra={"unit": "kPa"})
    utilizzato_kPa: float = Field(description="Δσv,q utilizzato per il calcolo del cedimento", json_schema_extra={"unit": "kPa"})


def tensione_indotta(q_prime_kPa: float, b_m: float, l_m: float, z_m: float, *, metodo: MetodoTensioni) -> TensioneIndotta:
    approssimato_kPa = spread_2to1(q_prime_kPa, b_m, l_m, z_m)
    newmark_kPa = None if z_m <= 0 else under_center(q_prime_kPa, b_m, l_m, z_m)
    if metodo == "approssimato":
        utilizzato_kPa = approssimato_kPa
    else:
        utilizzato_kPa = q_prime_kPa if newmark_kPa is None else newmark_kPa
    return TensioneIndotta(approssimato_kPa=approssimato_kPa, newmark_kPa=newmark_kPa, utilizzato_kPa=utilizzato_kPa)
