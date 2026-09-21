"""Welded-mesh reinforcement (rete elettrosaldata) area + capacity, shared by the distributed-load
and concentrated-load checks (spec "pav-carichi-distribuiti" step 10-11 / "pav-carichi-concentrati"
step 12 -- same formulas, same mesh in both sheets' cached example). Reuses `shared.rebar_catalog`
instead of re-deriving `pi/4*phi^2`."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.rebar_catalog import asw_per_m

from .tables import REBAR_LEVER_ARM_FACTOR

MM_PER_M = 1000.0
ONE_MESH_LAYER = 1  # `asw_per_m` legs parameter: one wire per spacing pitch (not a stirrup leg count).


class ArmaturaResult(BaseModel):
    """Mesh area per metre and reinforced-section moment capacity."""

    model_config = ConfigDict(frozen=True)

    as_mm2_m: float = Field(description="Area della rete elettrosaldata per metro As", gt=0, json_schema_extra={"unit": "mm2/m", "symbol": "A_s"})
    mrd_Nmm_m: float = Field(description="Momento resistente della sezione armata Mrd", gt=0, json_schema_extra={"unit": "Nmm/m", "symbol": "M_Rd"})


def armatura(phi_mm: float, passo_mm: float, d_mm: float, fyd_MPa: float) -> ArmaturaResult:
    """As = phi^2*pi/4*1000/passo; Mrd = As*0.9*d*fyd/1000."""
    as_mm2_m = asw_per_m(phi_mm, ONE_MESH_LAYER, passo_mm)
    mrd_nmm_m = as_mm2_m * REBAR_LEVER_ARM_FACTOR * d_mm * fyd_MPa / MM_PER_M
    return ArmaturaResult(as_mm2_m=as_mm2_m, mrd_Nmm_m=mrd_nmm_m)
