"""Frozen result models for EN 1992-1-1 §6.2.2 / §6.4 shear and punching calculations."""
from pydantic import BaseModel, ConfigDict, Field


class ControlPerimeter(BaseModel):
    """Punching-shear control perimeter u at distance `dist_mm` from a column/pile face (§6.4.2)."""

    model_config = ConfigDict(frozen=True)

    u_mm: float = Field(description="Lunghezza del perimetro di verifica", gt=0, json_schema_extra={"unit": "mm"})
    area_mm2: float = Field(
        description="Area racchiusa dal perimetro di verifica", gt=0, json_schema_extra={"unit": "mm2"}
    )


class VRdC(BaseModel):
    """Concrete-only shear/punching resistance vRd,c (§6.2.2 eq. 6.2.a, §6.4.4 eq. 6.47)."""

    model_config = ConfigDict(frozen=True)

    v_rd_c_MPa: float = Field(description="Resistenza a taglio/punzonamento del solo calcestruzzo", ge=0)
    concrete_term_MPa: float = Field(description="Termine CRd,c*k*(100*rho*fck)^(1/3), prima dell'inviluppo con vmin")
    v_min_MPa: float | None = Field(description="vmin applicato (enhanced by 2d/a when l'incremento è attivo)")
    k1_sigma_cp_MPa: float = Field(description="Contributo k1*sigma_cp per sforzo normale/precompressione")
    enhancement_factor: float | None = Field(
        description="Fattore di incremento 2d/a applicato entro il perimetro 2d (§6.4.4(2)), None se non applicato"
    )


class VRdMax(BaseModel):
    """Maximum punching-shear stress at the column/pile face u0, without reinforcement (§6.4.3(2)/§6.4.5(3))."""

    model_config = ConfigDict(frozen=True)

    v_rd_max_MPa: float = Field(description="Tensione massima di punzonamento al perimetro u0", ge=0)
    nu: float = Field(description="Coefficiente di riduzione della resistenza ν = 0.6*(1 - fck/250)", ge=0)
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione del calcestruzzo fcd", ge=0)


class GoverningScan(BaseModel):
    """Result of an exhaustive scan for the governing sample of a scalar function (spreadsheet fill-down idiom)."""

    model_config = ConfigDict(frozen=True)

    x: float = Field(description="Ascissa del campione che massimizza f(x)")
    value: float = Field(description="Valore f(x) nel punto governante")
    index: int = Field(description="Indice (0-based) del campione governante", ge=0)
