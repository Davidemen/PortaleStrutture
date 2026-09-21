"""Step 3: transfer of column-top N/V/M to the footing base, with lever arms (docs/specs/
fond-plinti-isolati.md Tool-1 steps 4-6, `CHECKS!G,H,I,J,K,L`)."""
from pydantic import BaseModel, ConfigDict, Field

from .pesi_propri import PesiPropri


class AzioniBase(BaseModel):
    """Factored vertical load and base moments/shears, after self-weight and lever-arm transfer."""

    model_config = ConfigDict(frozen=True)

    n_kN: float = Field(description="Carico verticale totale alla base N", json_schema_extra={"unit": "kN"})
    vx_kN: float = Field(description="Taglio alla base in direzione X", ge=0, json_schema_extra={"unit": "kN"})
    vy_kN: float = Field(description="Taglio alla base in direzione Y", ge=0, json_schema_extra={"unit": "kN"})
    myy_kNm: float = Field(description="Momento alla base My (flette intorno a Y, eccentricità lungo X)",
                            ge=0, json_schema_extra={"unit": "kNm"})
    mxx_kNm: float = Field(description="Momento alla base Mx (flette intorno a X, eccentricità lungo Y)",
                            ge=0, json_schema_extra={"unit": "kNm"})


def azioni_base(
    fz_kN: float, fx_kN: float, fy_kN: float, mx_kNm: float, my_kNm: float,
    pesi: PesiPropri, gamma_w: float, h_plinto_m: float, offset_leva_m: float, ex_m: float, ey_m: float,
) -> AzioniBase:
    """N/V/M transferred to the footing base: N adds the factored self-weight; My/Mx pick up the
    shear's lever arm (H + offset) and the user eccentricity's contribution N*e."""
    n_kN = fz_kN + (pesi.w_plinto_kN + pesi.w_pedestal_kN + pesi.w_terreno_kN) * gamma_w
    if n_kN <= 0:
        raise ValueError(f"il carico verticale totale alla base deve essere positivo (compressione), got {n_kN}")
    vx_kN = abs(fx_kN)
    vy_kN = abs(fy_kN)
    leva_m = h_plinto_m + offset_leva_m
    myy_kNm = abs(my_kNm) + vx_kN * leva_m + n_kN * ex_m
    mxx_kNm = abs(mx_kNm) + vy_kN * leva_m + n_kN * ey_m
    return AzioniBase(n_kN=n_kN, vx_kN=vx_kN, vy_kN=vy_kN, myy_kNm=myy_kNm, mxx_kNm=mxx_kNm)
