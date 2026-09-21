"""Step 1: self-weight of plinth, pedestal and soil cover (docs/specs/fond-plinti-isolati.md Tool-1
steps 3, cells `CHECKS!C,D,E`)."""
from pydantic import BaseModel, ConfigDict, Field

GAMMA_CALCESTRUZZO_KNM3 = 25.0  # buried literal in CHECKS!C,D (`*25`), not a user input in the sheet.


class PesiPropri(BaseModel):
    """Self-weight components of the footing + pedestal + soil cover, in kN."""

    model_config = ConfigDict(frozen=True)

    w_plinto_kN: float = Field(description="Peso proprio del plinto", ge=0, json_schema_extra={"unit": "kN"})
    w_pedestal_kN: float = Field(description="Peso proprio del bicchiere/pilastrino", ge=0, json_schema_extra={"unit": "kN"})
    w_terreno_kN: float = Field(description="Peso del terreno di ricoprimento", ge=0, json_schema_extra={"unit": "kN"})


def pesi_propri(
    ax_m: float, by_m: float, h_plinto_m: float, h_interro_m: float,
    a_pedestal_m: float, b_pedestal_m: float, h_pedestal_sopra_m: float, h_pedestal_sotto_m: float,
    gamma_terreno_kNm3: float, *, gamma_calcestruzzo_knm3: float = GAMMA_CALCESTRUZZO_KNM3,
) -> PesiPropri:
    """Self-weight of the plinth slab, the pedestal above it, and the soil covering the footing."""
    if ax_m <= 0 or by_m <= 0 or h_plinto_m <= 0:
        raise ValueError(f"ax_m, by_m, h_plinto_m must be > 0, got {ax_m}, {by_m}, {h_plinto_m}")
    area_pianta_m2 = ax_m * by_m
    area_pedestal_m2 = a_pedestal_m * b_pedestal_m
    w_plinto = area_pianta_m2 * h_plinto_m * gamma_calcestruzzo_knm3
    w_pedestal = area_pedestal_m2 * (h_pedestal_sopra_m + h_pedestal_sotto_m) * gamma_calcestruzzo_knm3
    w_terreno = (area_pianta_m2 - area_pedestal_m2) * h_interro_m * gamma_terreno_kNm3
    return PesiPropri(w_plinto_kN=w_plinto, w_pedestal_kN=w_pedestal, w_terreno_kN=w_terreno)
