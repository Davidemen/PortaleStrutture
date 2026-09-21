"""Step 1: convert every dimensional scalar of `EdometricoInput` to SI once at the boundary
(docs/architecture-batch2.md §9-D1). `strati` needs no conversion (`shared.soil_layers.SoilLayer`
is already SI-only); `d` (embedment) is already in metres in both unit systems — the sheet's own
cell is metres, not centimetres, see `models.py` — so it is never converted. Every step downstream
computes in SI."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.units import cm_to_m, kgcm2_to_kpa, kgm3_to_knm3

from .models import EdometricoInput


class IngressoSI(BaseModel):
    """`EdometricoInput`'s dimensional scalars, converted to m / kN/m³ / kPa."""

    model_config = ConfigDict(frozen=True)

    b_m: float = Field(gt=0)
    l_m: float = Field(gt=0)
    d_m: float = Field(ge=0)
    gamma_kN_m3: float = Field(gt=0)
    q_kPa: float = Field(gt=0)
    z_crit_input_m: float | None = Field(default=None, gt=0)
    dz_m: float = Field(gt=0)
    z_max_m: float = Field(gt=0)
    falda_m: float | None = Field(default=None, ge=0)


def converti_in_si(inputs: EdometricoInput) -> IngressoSI:
    """Identity when `sistema_unita == "SI"`; otherwise cm->m, kg/m³->kN/m³, kg/cm²->kPa. `d` is
    always metres (never converted, see module docstring); `falda` converts like any other length."""
    if inputs.sistema_unita == "SI":
        return IngressoSI(
            b_m=inputs.b, l_m=inputs.l, d_m=inputs.d, gamma_kN_m3=inputs.gamma, q_kPa=inputs.q,
            z_crit_input_m=inputs.z_crit_input, dz_m=inputs.dz, z_max_m=inputs.z_max,
            falda_m=inputs.falda,
        )
    return IngressoSI(
        b_m=cm_to_m(inputs.b), l_m=cm_to_m(inputs.l), d_m=inputs.d,
        gamma_kN_m3=kgm3_to_knm3(inputs.gamma), q_kPa=kgcm2_to_kpa(inputs.q),
        z_crit_input_m=cm_to_m(inputs.z_crit_input) if inputs.z_crit_input is not None else None,
        dz_m=cm_to_m(inputs.dz), z_max_m=cm_to_m(inputs.z_max),
        falda_m=cm_to_m(inputs.falda) if inputs.falda is not None else None,
    )
