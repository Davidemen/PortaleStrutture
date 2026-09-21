"""Westergaard infinite-plate-on-Winkler-foundation UDL bending moments for `pav-carichi-distribuiti`
(spec calculation steps 4-5). `/1000` is the sheet's own unit-fix baked into the coefficients, kept
as-is (not a divergence -- both `legacy_compat` modes use it, only the *check denominator* diverges,
see `distribuiti_verifiche.py`)."""
from pydantic import BaseModel, ConfigDict, Field

WESTERGAARD_UDL_COEFFICIENT_SUP = 0.1682
WESTERGAARD_UDL_COEFFICIENT_INF = 0.1612
MOMENT_UNIT_FIX = 1000.0


class MomentiDistribuitoResult(BaseModel):
    """`pav-carichi-distribuiti` outputs G16/H16 (ULS) and G17/H17 (frequent SLS)."""

    model_config = ConfigDict(frozen=True)

    m_slu_sup_Nmm_m: float = Field(description="Momento flettente ULS, fibra superiore", json_schema_extra={"unit": "Nmm/m", "symbol": "M_SLU,sup"})
    m_slu_inf_Nmm_m: float = Field(description="Momento flettente ULS, fibra inferiore", json_schema_extra={"unit": "Nmm/m", "symbol": "M_SLU,inf"})
    m_sle_freq_sup_Nmm_m: float = Field(description="Momento flettente SLE frequente, fibra superiore", json_schema_extra={"unit": "Nmm/m", "symbol": "M_SLE,f,sup"})
    m_sle_freq_inf_Nmm_m: float = Field(description="Momento flettente SLE frequente, fibra inferiore", json_schema_extra={"unit": "Nmm/m", "symbol": "M_SLE,f,inf"})


def _momento(q_kN_m2: float, lambda_mm1: float, coefficient: float) -> float:
    return (coefficient * q_kN_m2 / lambda_mm1**2) / MOMENT_UNIT_FIX


def momenti_distribuito(q_slu_kN_m2: float, q_sle_freq_kN_m2: float, lambda_mm1: float) -> MomentiDistribuitoResult:
    """spec steps 4-5."""
    return MomentiDistribuitoResult(
        m_slu_sup_Nmm_m=_momento(q_slu_kN_m2, lambda_mm1, WESTERGAARD_UDL_COEFFICIENT_SUP),
        m_slu_inf_Nmm_m=_momento(q_slu_kN_m2, lambda_mm1, WESTERGAARD_UDL_COEFFICIENT_INF),
        m_sle_freq_sup_Nmm_m=_momento(q_sle_freq_kN_m2, lambda_mm1, WESTERGAARD_UDL_COEFFICIENT_SUP),
        m_sle_freq_inf_Nmm_m=_momento(q_sle_freq_kN_m2, lambda_mm1, WESTERGAARD_UDL_COEFFICIENT_INF),
    )
