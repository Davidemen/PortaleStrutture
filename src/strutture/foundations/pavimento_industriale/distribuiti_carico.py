"""Combined load for `pav-carichi-distribuiti` (spec calculation steps 1-3): daN/m² inputs to the
ULS/frequent-SLS combined pressure."""
from pydantic import BaseModel, ConfigDict, Field

from .tables import DAN_PER_KN_M2


class CaricoDistribuitoResult(BaseModel):
    """`pav-carichi-distribuiti` outputs G9-G12 (combined loads)."""

    model_config = ConfigDict(frozen=True)

    g_kN_m2: float = Field(description="Carico permanente distribuito G", ge=0, json_schema_extra={"unit": "kN/m2", "symbol": "G"})
    q_kN_m2: float = Field(description="Carico variabile distribuito Q", ge=0, json_schema_extra={"unit": "kN/m2", "symbol": "Q"})
    q_slu_kN_m2: float = Field(description="Carico combinato SLU q_SLU = G*γG + Q*γQ", ge=0, json_schema_extra={"unit": "kN/m2", "symbol": "q_SLU"})
    q_sle_freq_kN_m2: float = Field(description="Carico combinato SLE frequente q_SLE,f = G + Q*ψ1", ge=0, json_schema_extra={"unit": "kN/m2", "symbol": "q_SLE,f"})


def carico_distribuito(
    g_daN_m2: float, q_daN_m2: float, gamma_g: float, gamma_q: float, psi1: float,
) -> CaricoDistribuitoResult:
    """spec steps 1-3."""
    g_kn_m2 = g_daN_m2 / DAN_PER_KN_M2
    q_kn_m2 = q_daN_m2 / DAN_PER_KN_M2
    return CaricoDistribuitoResult(
        g_kN_m2=g_kn_m2, q_kN_m2=q_kn_m2,
        q_slu_kN_m2=g_kn_m2 * gamma_g + q_kn_m2 * gamma_q,
        q_sle_freq_kN_m2=g_kn_m2 + q_kn_m2 * psi1,
    )
