"""Westergaard point-load stresses for `pav-carichi-concentrati` (spec calculation steps 3-6):
position-dependent formulas (centro/bordo/spigolo), applied once with the ULS load (`sigma_c_max`)
and once with the frequent-SLS load (`sigma_c_t`, spec step 11 reuses the same formula shape)."""
import math

from pydantic import BaseModel, ConfigDict, Field

from .carico_row import PosizioneCarico
from .tables import WESTERGAARD_BORDO, WESTERGAARD_CENTRO, WESTERGAARD_SPIGOLO

KN_TO_N = 1000.0
NOMINAL_MOMENT_DIVISOR = 6.0  # spec step 6: M_SLU = sigma_c,max * h^2/6 (per-mm-width, no /1000).


class TensioniResult(BaseModel):
    """`pav-carichi-concentrati` outputs L7/L8, L21, L17 (loads + ULS stress + nominal moment)."""

    model_config = ConfigDict(frozen=True)

    p_slu_kN: float = Field(description="Carico concentrato di progetto ULS P_SLU = P*γ", gt=0, json_schema_extra={"unit": "kN", "symbol": "P_SLU"})
    p_sle_freq_kN: float = Field(description="Carico concentrato SLE frequente P_SLE,f = P*ψ1", gt=0, json_schema_extra={"unit": "kN", "symbol": "P_SLE,f"})
    sigma_c_max_MPa: float = Field(
        description="Tensione di flessione ULS (Westergaard) σc,max", json_schema_extra={"unit": "MPa", "symbol": "σ_c,max"},
    )  # no lower bound: the corner (spigolo) formula can turn slightly negative for a very large
    # footprint relative to l (oracle case: bx=by=1000mm, l=776.9mm) -- a genuine sheet value, not a bug.
    m_slu_Nmm_m: float = Field(description="Momento nominale ULS M_SLU = σc,max*h^2/6", json_schema_extra={"unit": "Nmm/m", "symbol": "M_SLU"})


def carico_concentrato(p_kN: float, gamma: float, psi1: float) -> tuple[float, float]:
    """spec step 3: (P_SLU, P_SLE,f)."""
    return p_kN * gamma, p_kN * psi1


def sigma_westergaard(posizione: PosizioneCarico, p_kN: float, h_mm: float, l_mm: float, b_mm: float, rr_mm: float) -> float:
    """spec step 4/11: Westergaard point-load stress at the given position, MPa."""
    if posizione == "centro":
        k1, k2 = WESTERGAARD_CENTRO
        return k1 * (p_kN * KN_TO_N) / h_mm**2 * (math.log10(l_mm / b_mm) + k2)
    if posizione == "bordo":
        k1, k2 = WESTERGAARD_BORDO
        return k1 * (p_kN * KN_TO_N) / h_mm**2 * (math.log10(l_mm / b_mm) + k2)
    k1, k3, k4 = WESTERGAARD_SPIGOLO
    return k1 * (p_kN * KN_TO_N) / h_mm**2 * (1.0 - k3 * (rr_mm / l_mm) ** k4)


def tensioni(
    posizione: PosizioneCarico, p_kN: float, gamma: float, psi1: float,
    h_mm: float, l_mm: float, b_mm: float, rr_mm: float,
) -> TensioniResult:
    """spec steps 3-6."""
    p_slu_kn, p_sle_freq_kn = carico_concentrato(p_kN, gamma, psi1)
    sigma_max = sigma_westergaard(posizione, p_slu_kn, h_mm, l_mm, b_mm, rr_mm)
    return TensioniResult(
        p_slu_kN=p_slu_kn, p_sle_freq_kN=p_sle_freq_kn,
        sigma_c_max_MPa=sigma_max, m_slu_Nmm_m=sigma_max * h_mm**2 / NOMINAL_MOMENT_DIVISOR,
    )
